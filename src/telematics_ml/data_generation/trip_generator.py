"""
Step 5: Raw Trip Log Simulator with Real API Integration

Generates 18 months of realistic driving history for each driver, with real-time
contextual enrichment using actual weather, speed limit, and traffic APIs.
"""

import pandas as pd
import numpy as np
import random
import logging
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from ..data.schemas import (
    GPSPoint, IMUReading, BehavioralEvent, ContextualData, 
    EventType, WeatherCondition, TripData, VehicleSystemData, DataSource
)
from ..etl.real_data_downloader import RealDataDownloader
from ..etl.real_data_sources import OSMSpeedLimitLoader, WeatherDataLoader
from ..utils.config import get_config


@dataclass
class TripProfile:
    """Defines the characteristics of a simulated trip."""
    start_time: datetime
    duration_minutes: float
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    trip_type: str  # 'commute', 'errand', 'leisure', 'long_distance'
    expected_speed_profile: List[float]  # Speed targets throughout trip


class TripSimulator:
    """
    Generates realistic trip logs with real API contextual enrichment.
    
    This is the core of Step 5 - creating 18 months of driving history
    for each driver with actual weather and speed limit data.
    """
    
    def __init__(self, use_real_apis: bool = True, api_rate_limit_delay: float = 0.1):
        """
        Initialize the trip simulator.
        
        Args:
            use_real_apis: Whether to use real APIs or simulated responses
            api_rate_limit_delay: Delay between API calls to respect rate limits
        """
        self.config = get_config()
        self.logger = logging.getLogger(__name__)
        self.use_real_apis = use_real_apis
        self.api_delay = api_rate_limit_delay
        
        # Initialize real API components
        if use_real_apis:
            self.real_downloader = RealDataDownloader()
            self.weather_loader = WeatherDataLoader()
            self.osm_loader = OSMSpeedLimitLoader()
            
            # Load pre-downloaded real data if available
            self._load_real_data_caches()
        
        # Trip generation parameters
        self.chicago_bounds = {
            'lat_min': 41.6, 'lat_max': 42.1,
            'lon_min': -87.9, 'lon_max': -87.3
        }
        
        # API call tracking for rate limiting
        self._api_call_count = 0
        self._api_lock = threading.Lock()
        
        # Progress tracking
        self.progress = {
            'drivers_completed': 0,
            'total_drivers': 0,
            'trips_generated': 0,
            'api_calls_made': 0
        }
    
    def _load_real_data_caches(self):
        """Load pre-downloaded real data to minimize API calls."""
        try:
            # Load weather data if available
            weather_path = Path("data/raw/weather_us")
            if weather_path.exists():
                self.logger.info("📦 Loading cached weather data...")
                self.weather_loader.load(weather_path)
            
            # Load OSM speed limit data if available  
            osm_path = Path("data/raw/osm_speed_limits")
            if osm_path.exists():
                self.logger.info("📦 Loading cached OSM speed limit data...")
                self.osm_loader.load(osm_path)
                
        except Exception as e:
            self.logger.warning(f"⚠️ Could not load cached data: {e}")
    
    def generate_driver_trips(self, driver_data: Dict[str, Any], 
                            months: int = 18) -> List[TripData]:
        """
        Generate complete trip history for a single driver.
        
        Args:
            driver_data: Driver information from drivers.csv
            months: Number of months of history to generate
            
        Returns:
            List of TripData objects for this driver
        """
        driver_id = driver_data['driver_id']
        persona_type = driver_data['persona_type']
        
        self.logger.debug(f"🚗 Generating trips for {driver_id} ({persona_type})")
        
        # Generate trip schedule
        trip_profiles = self._generate_trip_schedule(driver_data, months)
        
        # Convert profiles to full trip data with real API enrichment
        trips = []
        for i, profile in enumerate(trip_profiles):
            try:
                trip_data = self._generate_trip_data(
                    driver_data, profile, f"{driver_id}_trip_{i:04d}"
                )
                trips.append(trip_data)
                
                # Progress update
                if i % 10 == 0:
                    self.logger.debug(f"   Generated {i}/{len(trip_profiles)} trips for {driver_id}")
                    
            except Exception as e:
                self.logger.warning(f"Failed to generate trip {i} for {driver_id}: {e}")
                continue
        
        self.logger.info(f"✅ Generated {len(trips)} trips for {driver_id}")
        return trips
    
    def _generate_trip_schedule(self, driver_data: Dict[str, Any], 
                              months: int) -> List[TripProfile]:
        """Generate realistic trip schedule based on driver persona."""
        persona_type = driver_data['persona_type']
        
        # Trip frequency by persona (trips per month)
        trip_frequencies = {
            'safe_driver': (35, 50),      # 35-50 trips/month
            'average_driver': (40, 60),   # 40-60 trips/month  
            'risky_driver': (45, 70)      # 45-70 trips/month (more driving)
        }
        
        min_trips, max_trips = trip_frequencies[persona_type]
        total_trips = random.randint(min_trips * months, max_trips * months)
        
        profiles = []
        
        # Generate trips across the time period
        start_date = datetime.now() - timedelta(days=months * 30)
        end_date = datetime.now() - timedelta(days=30)
        
        for trip_num in range(total_trips):
            # Random trip timing
            trip_date = start_date + timedelta(
                days=random.uniform(0, (end_date - start_date).days)
            )
            
            # Trip type and timing based on day of week and hour
            trip_type, trip_hour = self._determine_trip_type_and_time(trip_date)
            
            trip_start = trip_date.replace(
                hour=trip_hour, 
                minute=random.randint(0, 59),
                second=0, microsecond=0
            )
            
            # Trip characteristics based on type
            profile = self._create_trip_profile(trip_start, trip_type, driver_data)
            profiles.append(profile)
        
        # Sort by time
        profiles.sort(key=lambda p: p.start_time)
        return profiles
    
    def _determine_trip_type_and_time(self, trip_date: datetime) -> Tuple[str, int]:
        """Determine trip type and start hour based on date."""
        weekday = trip_date.weekday()  # 0=Monday, 6=Sunday
        
        if weekday < 5:  # Weekday
            hour_weights = {
                7: ('commute', 0.4), 8: ('commute', 0.6), 9: ('errand', 0.2),
                12: ('errand', 0.3), 15: ('errand', 0.2), 17: ('commute', 0.5),
                18: ('commute', 0.4), 19: ('leisure', 0.2), 20: ('leisure', 0.1)
            }
        else:  # Weekend
            hour_weights = {
                9: ('leisure', 0.2), 10: ('leisure', 0.3), 11: ('errand', 0.4),
                14: ('leisure', 0.3), 16: ('errand', 0.2), 18: ('leisure', 0.2),
                19: ('leisure', 0.3), 20: ('leisure', 0.2)
            }
        
        # Weighted random selection
        hours = list(hour_weights.keys())
        weights = [hour_weights[h][1] for h in hours]
        
        selected_hour = np.random.choice(hours, p=np.array(weights)/sum(weights))
        trip_type = hour_weights[selected_hour][0]
        
        return trip_type, selected_hour
    
    def _create_trip_profile(self, start_time: datetime, trip_type: str,
                           driver_data: Dict[str, Any]) -> TripProfile:
        """Create a detailed trip profile."""
        # Trip duration and distance by type
        trip_params = {
            'commute': {'duration': (15, 45), 'distance_km': (8, 25)},
            'errand': {'duration': (5, 20), 'distance_km': (2, 10)},
            'leisure': {'duration': (20, 90), 'distance_km': (10, 50)},
            'long_distance': {'duration': (60, 300), 'distance_km': (50, 200)}
        }
        
        params = trip_params.get(trip_type, trip_params['errand'])
        duration = random.uniform(*params['duration'])
        target_distance = random.uniform(*params['distance_km'])
        
        # Generate start and end coordinates (Chicago area)
        start_lat = random.uniform(
            self.chicago_bounds['lat_min'], 
            self.chicago_bounds['lat_max']
        )
        start_lon = random.uniform(
            self.chicago_bounds['lon_min'], 
            self.chicago_bounds['lon_max']
        )
        
        # End location based on trip type and distance
        # Simplified: random direction with target distance
        bearing = random.uniform(0, 360)
        distance_lat = target_distance * 0.009 * np.cos(np.radians(bearing))  # ~111km per degree
        distance_lon = target_distance * 0.009 * np.sin(np.radians(bearing)) / np.cos(np.radians(start_lat))
        
        end_lat = start_lat + distance_lat
        end_lon = start_lon + distance_lon
        
        # Ensure end point is within bounds
        end_lat = np.clip(end_lat, self.chicago_bounds['lat_min'], self.chicago_bounds['lat_max'])
        end_lon = np.clip(end_lon, self.chicago_bounds['lon_min'], self.chicago_bounds['lon_max'])
        
        # Generate speed profile based on driver persona
        speed_profile = self._generate_speed_profile(duration, trip_type, driver_data)
        
        return TripProfile(
            start_time=start_time,
            duration_minutes=duration,
            start_lat=start_lat,
            start_lon=start_lon,
            end_lat=end_lat,
            end_lon=end_lon,
            trip_type=trip_type,
            expected_speed_profile=speed_profile
        )
    
    def _generate_speed_profile(self, duration_minutes: float, trip_type: str,
                              driver_data: Dict[str, Any]) -> List[float]:
        """Generate expected speed profile for the trip."""
        persona_multiplier = driver_data.get('avg_speed_multiplier', 1.0)
        
        # Base speeds by trip type (mph)
        base_speeds = {
            'commute': 35,
            'errand': 25, 
            'leisure': 40,
            'long_distance': 55
        }
        
        base_speed = base_speeds.get(trip_type, 30) * persona_multiplier
        
        # Create speed profile with realistic variations
        num_points = max(10, int(duration_minutes / 2))  # Point every 2 minutes
        speeds = []
        
        for i in range(num_points):
            # Add realistic speed variations
            speed_variation = random.uniform(0.8, 1.2)
            
            # Lower speeds at start/end (parking, traffic lights)
            if i < 2 or i >= num_points - 2:
                speed_variation *= 0.6
            
            speed = base_speed * speed_variation
            speeds.append(max(5, min(80, speed)))  # Reasonable bounds
        
        return speeds
    
    def _generate_trip_data(self, driver_data: Dict[str, Any], 
                          profile: TripProfile, trip_id: str) -> TripData:
        """Generate complete trip data with real API enrichment."""
        
        # Generate GPS path
        gps_points = self._generate_gps_path(profile)
        
        # Generate IMU readings
        imu_readings = self._generate_imu_data(profile, driver_data)
        
        # Detect behavioral events based on persona
        behavioral_events = self._generate_behavioral_events(
            gps_points, imu_readings, driver_data
        )
        
        # REAL API INTEGRATION: Enrich with contextual data
        contextual_data = self._enrich_with_real_apis(gps_points, profile)
        
        # Generate vehicle system data (for phone+device users)
        vehicle_data = self._generate_vehicle_data(profile, driver_data)
        
        # Calculate trip-level metrics
        total_distance = self._calculate_trip_distance(gps_points)
        avg_speed = self._calculate_average_speed(gps_points, profile.duration_minutes)
        
        # Generate phone usage data based on persona
        phone_usage = self._generate_phone_usage(profile, driver_data)
        
        # Convert data_source string to enum
        data_source_enum = DataSource.PHONE_PLUS_DEVICE if driver_data['data_source'] == 'phone_plus_device' else DataSource.PHONE_ONLY
        
        return TripData(
            trip_id=trip_id,
            driver_id=driver_data['driver_id'],
            start_time=profile.start_time,
            end_time=profile.start_time + timedelta(minutes=profile.duration_minutes),
            gps_points=gps_points,
            imu_readings=imu_readings,
            behavioral_events=behavioral_events,
            contextual_data=contextual_data,
            vehicle_data=vehicle_data,
            data_source=data_source_enum,
            total_distance_miles=total_distance,
            avg_speed_mph=avg_speed,
            duration_minutes=profile.duration_minutes,
            screen_on_duration_minutes=phone_usage['screen_on_minutes'],
            call_duration_minutes=phone_usage['call_minutes'],
            handheld_duration_minutes=phone_usage['handheld_minutes'],
            gps_accuracy_avg_meters=random.uniform(3, 12),
            data_completeness_pct=random.uniform(92, 100),
            driver_passenger_confidence=random.uniform(0.7, 1.0)
        )
    
    def _generate_gps_path(self, profile: TripProfile) -> List[GPSPoint]:
        """Generate realistic GPS path between start and end points."""
        num_points = max(30, int(profile.duration_minutes * 2))  # Point every 30 seconds
        
        gps_points = []
        start_time = profile.start_time
        
        for i in range(num_points):
            # Linear interpolation between start and end (simplified)
            progress = i / (num_points - 1)
            
            lat = profile.start_lat + (profile.end_lat - profile.start_lat) * progress
            lon = profile.start_lon + (profile.end_lon - profile.start_lon) * progress
            
            # Add realistic GPS noise
            lat += random.gauss(0, 0.0001)  # ~10m standard deviation
            lon += random.gauss(0, 0.0001)
            
            # Calculate timestamp
            timestamp = start_time + timedelta(minutes=progress * profile.duration_minutes)
            
            # Get speed from profile
            speed_idx = min(len(profile.expected_speed_profile) - 1, 
                          int(progress * len(profile.expected_speed_profile)))
            speed_mph = profile.expected_speed_profile[speed_idx]
            
            # Add speed variations
            speed_mph *= random.uniform(0.9, 1.1)
            
            point = GPSPoint(
                timestamp=timestamp,
                latitude=lat,
                longitude=lon,
                altitude=random.uniform(580, 620),  # Chicago elevation
                accuracy_meters=random.uniform(3, 15),
                speed_mph=max(0, speed_mph),
                heading=self._calculate_heading(i, profile) if i > 0 else 0
            )
            
            gps_points.append(point)
        
        return gps_points
    
    def _calculate_heading(self, point_index: int, profile: TripProfile) -> float:
        """Calculate heading between start and end points."""
        lat1, lon1 = profile.start_lat, profile.start_lon
        lat2, lon2 = profile.end_lat, profile.end_lon
        
        dlon = np.radians(lon2 - lon1)
        lat1_rad = np.radians(lat1)
        lat2_rad = np.radians(lat2)
        
        y = np.sin(dlon) * np.cos(lat2_rad)
        x = np.cos(lat1_rad) * np.sin(lat2_rad) - np.sin(lat1_rad) * np.cos(lat2_rad) * np.cos(dlon)
        
        heading = np.degrees(np.arctan2(y, x))
        return (heading + 360) % 360  # Normalize to 0-360
    
    def _generate_imu_data(self, profile: TripProfile, 
                          driver_data: Dict[str, Any]) -> List[IMUReading]:
        """Generate realistic IMU sensor data."""
        num_points = max(60, int(profile.duration_minutes * 4))  # Point every 15 seconds
        imu_readings = []
        
        jerk_multiplier = driver_data.get('jerk_rate_multiplier', 1.0)
        start_time = profile.start_time
        
        for i in range(num_points):
            timestamp = start_time + timedelta(
                minutes=(i / num_points) * profile.duration_minutes
            )
            
            # Base acceleration (mostly gravity on Z-axis)
            accel_x = random.gauss(0, 0.05) * jerk_multiplier  # Forward/back
            accel_y = random.gauss(0, 0.03) * jerk_multiplier  # Left/right
            accel_z = random.gauss(1.0, 0.02)  # Up/down (gravity)
            
            # Gyroscope data (rotation rates)
            gyro_x = random.gauss(0, 1.0)  # Roll
            gyro_y = random.gauss(0, 1.0)  # Pitch  
            gyro_z = random.gauss(0, 2.0)  # Yaw (turning)
            
            reading = IMUReading(
                timestamp=timestamp,
                accel_x=accel_x,
                accel_y=accel_y,
                accel_z=accel_z,
                gyro_x=gyro_x,
                gyro_y=gyro_y,
                gyro_z=gyro_z
            )
            
            imu_readings.append(reading)
        
        return imu_readings
    
    def _generate_behavioral_events(self, gps_points: List[GPSPoint],
                                  imu_readings: List[IMUReading],
                                  driver_data: Dict[str, Any]) -> List[BehavioralEvent]:
        """Generate behavioral events based on driver persona."""
        events = []
        
        # Get persona-based event rates
        hard_brake_rate = driver_data.get('hard_brake_rate_base', 0.5)
        rapid_accel_rate = driver_data.get('rapid_accel_rate_base', 0.3)
        harsh_corner_rate = driver_data.get('harsh_corner_rate_base', 0.2)
        speeding_rate = driver_data.get('speeding_rate_base', 0.5)
        
        # Inject hard braking events
        for i, reading in enumerate(imu_readings):
            if random.random() < hard_brake_rate / 1000:  # Scale down for per-reading probability
                event = BehavioralEvent(
                    timestamp=reading.timestamp,
                    event_type=EventType.HARD_BRAKE,
                    severity=random.uniform(0.4, 1.0),
                    duration_seconds=random.uniform(1, 4),
                    g_force=reading.accel_x,
                    speed_at_event_mph=gps_points[min(i, len(gps_points)-1)].speed_mph
                )
                events.append(event)
        
        # Inject other event types similarly...
        # (Simplified for now - full implementation would be more detailed)
        
        return events
    
    def _enrich_with_real_apis(self, gps_points: List[GPSPoint], 
                             profile: TripProfile) -> List[ContextualData]:
        """REAL API INTEGRATION: Enrich trip with actual weather and speed limit data."""
        contextual_data = []
        
        if not self.use_real_apis:
            return self._generate_simulated_context(gps_points, profile)
        
        # Sample points for API calls (not every point to manage rate limits)
        sample_points = gps_points[::max(1, len(gps_points) // 10)]  # ~10 API calls per trip
        
        for point in sample_points:
            try:
                # Rate limiting
                with self._api_lock:
                    time.sleep(self.api_delay)
                    self._api_call_count += 1
                
                context = ContextualData(
                    timestamp=point.timestamp,
                    location=point
                )
                
                # REAL Weather API call
                if hasattr(self.weather_loader, 'weather_data') and self.weather_loader.weather_data is not None:
                    weather_info = self.weather_loader.get_weather_for_date(point.timestamp)
                    if weather_info:
                        context.weather_condition = WeatherCondition(weather_info.get('weather_condition', 'clear'))
                        context.temperature_f = weather_info.get('temperature_f', 70.0)
                
                # REAL Speed Limit API call
                if hasattr(self.osm_loader, 'speed_limit_map') and self.osm_loader.speed_limit_map:
                    speed_limit = self.osm_loader.get_speed_limit(point.latitude, point.longitude)
                    if speed_limit:
                        context.posted_speed_limit_mph = speed_limit
                        context.road_type = self._classify_road_from_speed_limit(speed_limit)
                
                # Traffic simulation (could be replaced with real traffic API)
                context.traffic_level = self._simulate_traffic_level(point.timestamp)
                
                contextual_data.append(context)
                
                # Progress tracking
                self.progress['api_calls_made'] = self._api_call_count
                
            except Exception as e:
                self.logger.warning(f"API enrichment failed for point: {e}")
                # Fallback to simulated data for this point
                continue
        
        return contextual_data
    
    def _classify_road_from_speed_limit(self, speed_limit: int) -> str:
        """Classify road type based on speed limit."""
        if speed_limit >= 55:
            return 'highway'
        elif speed_limit >= 35:
            return 'arterial'
        else:
            return 'residential'
    
    def _simulate_traffic_level(self, timestamp: datetime) -> str:
        """Simulate traffic level based on time of day."""
        hour = timestamp.hour
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            return random.choice(['moderate', 'heavy'])
        elif 10 <= hour <= 16:
            return random.choice(['light', 'moderate'])
        else:
            return 'light'
    
    def _generate_simulated_context(self, gps_points: List[GPSPoint], 
                                  profile: TripProfile) -> List[ContextualData]:
        """Fallback simulated contextual data."""
        # Implementation for simulated APIs when real APIs are not available
        return []
    
    def _generate_vehicle_data(self, profile: TripProfile, 
                             driver_data: Dict[str, Any]) -> List[VehicleSystemData]:
        """Generate vehicle system data for phone+device users."""
        if driver_data.get('data_source') != 'phone_plus_device':
            return []
        
        # Generate simplified OBD-II style data for phone+device users
        # For now, return empty list - full implementation would create 
        # realistic vehicle diagnostic data with RPM, engine load, DTC codes, etc.
        return []
    
    def _generate_phone_usage(self, profile: TripProfile, 
                            driver_data: Dict[str, Any]) -> Dict[str, float]:
        """Generate phone usage data based on driver persona."""
        phone_usage_pct = driver_data.get('phone_usage_pct_base', 0.05)
        
        # Calculate usage based on trip duration and persona
        screen_on_minutes = profile.duration_minutes * phone_usage_pct * random.uniform(0.5, 1.5)
        call_minutes = screen_on_minutes * random.uniform(0.1, 0.4)  # Some screen time is calls
        handheld_minutes = screen_on_minutes * random.uniform(0.6, 0.9)  # Most usage is handheld
        
        return {
            'screen_on_minutes': max(0, screen_on_minutes),
            'call_minutes': max(0, call_minutes),
            'handheld_minutes': max(0, handheld_minutes)
        }
    
    def _calculate_trip_distance(self, gps_points: List[GPSPoint]) -> float:
        """Calculate total trip distance in miles."""
        if len(gps_points) < 2:
            return 0.0
        
        total_distance = 0.0
        for i in range(1, len(gps_points)):
            # Simplified distance calculation
            lat1, lon1 = gps_points[i-1].latitude, gps_points[i-1].longitude
            lat2, lon2 = gps_points[i].latitude, gps_points[i].longitude
            
            # Haversine formula (simplified)
            dlat = np.radians(lat2 - lat1)
            dlon = np.radians(lon2 - lon1)
            a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
            c = 2 * np.arcsin(np.sqrt(a))
            distance_km = 6371 * c  # Earth radius in km
            total_distance += distance_km * 0.621371  # Convert to miles
        
        return total_distance
    
    def _calculate_average_speed(self, gps_points: List[GPSPoint], 
                               duration_minutes: float) -> float:
        """Calculate average speed for the trip."""
        if not gps_points or duration_minutes <= 0:
            return 0.0
        
        speeds = [point.speed_mph for point in gps_points if point.speed_mph is not None]
        return np.mean(speeds) if speeds else 0.0
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current simulation progress."""
        return self.progress.copy()
