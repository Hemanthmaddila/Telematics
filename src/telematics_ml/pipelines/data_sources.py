"""
Specialized loaders for processing real external datasets.

Each loader knows how to read, process, and standardize data from specific
external sources identified in the data sourcing plan.
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

from ..data.schemas import (
    GPSPoint, IMUReading, BehavioralEvent, ContextualData, 
    VehicleSystemData, EventType, WeatherCondition
)
from ..utils.config import get_config


class BaseDataLoader(ABC):
    """Base class for all real data source loaders."""
    
    def __init__(self):
        """Initialize the data loader."""
        self.config = get_config()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def load(self, data_path: Path) -> Any:
        """Load and process data from the specified path."""
        pass
    
    @abstractmethod
    def get_processed_data(self) -> Any:
        """Get the processed data in standardized format."""
        pass


class SmartphoneSensorLoader(BaseDataLoader):
    """
    Loader for smartphone sensor data (GPS + IMU).
    
    Processes data from the Nature Scientific Data smartphone sensor corpus
    and similar smartphone-based datasets.
    """
    
    def __init__(self):
        super().__init__()
        self.gps_data: Optional[List[GPSPoint]] = None
        self.imu_data: Optional[List[IMUReading]] = None
    
    def load(self, data_path: Path) -> Tuple[List[GPSPoint], List[IMUReading]]:
        """
        Load smartphone sensor data from files.
        
        Args:
            data_path: Path to directory containing GPS and IMU data files
            
        Returns:
            Tuple of (GPS points, IMU readings)
        """
        self.logger.info(f"Loading smartphone sensor data from {data_path}")
        
        # Load GPS data
        gps_file = data_path / "gps_sample.parquet"
        if gps_file.exists():
            gps_df = pd.read_parquet(gps_file)
            self.gps_data = self._process_gps_data(gps_df)
        else:
            self.logger.warning(f"GPS data file not found: {gps_file}")
            self.gps_data = []
        
        # Load IMU data
        imu_file = data_path / "imu_sample.parquet"
        if imu_file.exists():
            imu_df = pd.read_parquet(imu_file)
            self.imu_data = self._process_imu_data(imu_df)
        else:
            self.logger.warning(f"IMU data file not found: {imu_file}")
            self.imu_data = []
        
        return self.gps_data, self.imu_data
    
    def _process_gps_data(self, gps_df: pd.DataFrame) -> List[GPSPoint]:
        """Convert GPS DataFrame to GPSPoint objects."""
        gps_points = []
        
        for _, row in gps_df.iterrows():
            point = GPSPoint(
                timestamp=pd.to_datetime(row['timestamp']),
                latitude=float(row['latitude']),
                longitude=float(row['longitude']),
                altitude=float(row.get('altitude', 0)),
                accuracy_meters=float(row.get('accuracy_meters', 5.0)),
                speed_mph=float(row.get('speed_mph', 0)),
                heading=float(row.get('heading', 0))
            )
            gps_points.append(point)
        
        self.logger.info(f"Processed {len(gps_points)} GPS points")
        return gps_points
    
    def _process_imu_data(self, imu_df: pd.DataFrame) -> List[IMUReading]:
        """Convert IMU DataFrame to IMUReading objects."""
        imu_readings = []
        
        for _, row in imu_df.iterrows():
            reading = IMUReading(
                timestamp=pd.to_datetime(row['timestamp']),
                accel_x=float(row['accel_x']),
                accel_y=float(row['accel_y']),
                accel_z=float(row['accel_z']),
                gyro_x=float(row['gyro_x']),
                gyro_y=float(row['gyro_y']),
                gyro_z=float(row['gyro_z'])
            )
            imu_readings.append(reading)
        
        self.logger.info(f"Processed {len(imu_readings)} IMU readings")
        return imu_readings
    
    def get_processed_data(self) -> Tuple[List[GPSPoint], List[IMUReading]]:
        """Get the processed GPS and IMU data."""
        return self.gps_data or [], self.imu_data or []


class PhoneUsageLoader(BaseDataLoader):
    """
    Loader for phone usage/distraction data.
    
    Processes data about phone interaction patterns during driving
    from research datasets.
    """
    
    def __init__(self):
        super().__init__()
        self.usage_patterns: Optional[Dict[str, Any]] = None
    
    def load(self, data_path: Path) -> Dict[str, Any]:
        """
        Load phone usage patterns from research data.
        
        Args:
            data_path: Path to phone usage dataset
            
        Returns:
            Dictionary of usage patterns and statistics
        """
        self.logger.info(f"Loading phone usage data from {data_path}")
        
        usage_file = data_path / "phone_usage_sample.parquet"
        if not usage_file.exists():
            self.logger.warning(f"Phone usage file not found: {usage_file}")
            return {}
        
        usage_df = pd.read_parquet(usage_file)
        self.usage_patterns = self._process_usage_data(usage_df)
        
        return self.usage_patterns
    
    def _process_usage_data(self, usage_df: pd.DataFrame) -> Dict[str, Any]:
        """Process phone usage data into standardized patterns."""
        patterns = {
            'avg_screen_on_pct': (usage_df['screen_on_duration_seconds'] / 
                                 (usage_df['trip_duration_minutes'] * 60)).mean(),
            'avg_handheld_events_per_hour': (usage_df['handheld_events'] / 
                                           (usage_df['trip_duration_minutes'] / 60)).mean(),
            'avg_call_duration_pct': (usage_df['call_duration_seconds'] / 
                                    (usage_df['trip_duration_minutes'] * 60)).mean(),
            'patterns_by_trip_length': self._analyze_by_trip_length(usage_df),
            'total_trips_analyzed': len(usage_df)
        }
        
        self.logger.info(f"Processed {len(usage_df)} phone usage records")
        return patterns
    
    def _analyze_by_trip_length(self, usage_df: pd.DataFrame) -> Dict[str, float]:
        """Analyze phone usage patterns by trip length."""
        short_trips = usage_df[usage_df['trip_duration_minutes'] < 15]
        medium_trips = usage_df[(usage_df['trip_duration_minutes'] >= 15) & 
                               (usage_df['trip_duration_minutes'] < 45)]
        long_trips = usage_df[usage_df['trip_duration_minutes'] >= 45]
        
        patterns = {}
        for name, subset in [('short', short_trips), ('medium', medium_trips), ('long', long_trips)]:
            if len(subset) > 0:
                patterns[f'{name}_trips_screen_on_pct'] = (
                    subset['screen_on_duration_seconds'] / 
                    (subset['trip_duration_minutes'] * 60)
                ).mean()
        
        return patterns
    
    def get_processed_data(self) -> Dict[str, Any]:
        """Get the processed phone usage patterns."""
        return self.usage_patterns or {}


class OSMSpeedLimitLoader(BaseDataLoader):
    """
    Loader for OpenStreetMap speed limit data.
    
    Processes road speed limit information for speeding event detection.
    """
    
    def __init__(self):
        super().__init__()
        self.speed_limit_map: Optional[Dict[Tuple[float, float], int]] = None
    
    def load(self, data_path: Path) -> Dict[Tuple[float, float], int]:
        """
        Load OSM speed limit data.
        
        Args:
            data_path: Path to OSM speed limit dataset
            
        Returns:
            Dictionary mapping (lat, lon) to speed limit in mph
        """
        self.logger.info(f"Loading OSM speed limit data from {data_path}")
        
        # Check for real OSM data first, then fall back to sample
        real_osm_file = data_path / "osm_speed_limits_real.parquet"
        sample_osm_file = data_path / "osm_speed_limits_sample.parquet"
        
        if real_osm_file.exists():
            self.logger.info("Loading REAL OSM speed limit data from OpenStreetMap")
            osm_df = pd.read_parquet(real_osm_file)
            self.speed_limit_map = self._process_real_osm_data(osm_df)
        elif sample_osm_file.exists():
            self.logger.info("Loading sample OSM speed limit data")
            osm_df = pd.read_parquet(sample_osm_file)
            self.speed_limit_map = self._process_speed_limits(osm_df)
        else:
            self.logger.warning(f"No OSM speed limit files found in {data_path}")
            return {}
        
        return self.speed_limit_map
    
    def _process_speed_limits(self, osm_df: pd.DataFrame) -> Dict[Tuple[float, float], int]:
        """Process OSM data into a speed limit lookup map."""
        speed_map = {}
        
        for _, row in osm_df.iterrows():
            # Round coordinates to create a lookup grid
            lat_rounded = round(row['latitude'], 4)  # ~11m precision
            lon_rounded = round(row['longitude'], 4)
            speed_limit = int(row['speed_limit_mph'])
            
            speed_map[(lat_rounded, lon_rounded)] = speed_limit
        
        self.logger.info(f"Processed {len(speed_map)} speed limit locations")
        return speed_map
    
    def _process_real_osm_data(self, osm_df: pd.DataFrame) -> Dict[Tuple[float, float], int]:
        """Process real OSM data into a speed limit lookup map."""
        speed_map = {}
        
        for _, row in osm_df.iterrows():
            # Use center coordinates if available, otherwise use start coordinates
            if 'center_lat' in row and 'center_lon' in row:
                lat = round(float(row['center_lat']), 4)
                lon = round(float(row['center_lon']), 4)
            elif 'start_lat' in row and 'start_lon' in row:
                lat = round(float(row['start_lat']), 4)
                lon = round(float(row['start_lon']), 4)
            else:
                continue
                
            # Get speed limit
            if 'speed_limit_mph' in row and pd.notna(row['speed_limit_mph']):
                speed_limit = int(row['speed_limit_mph'])
                speed_map[(lat, lon)] = speed_limit
        
        self.logger.info(f"Processed {len(speed_map)} real OSM speed limit locations")
        return speed_map
    
    def get_speed_limit(self, latitude: float, longitude: float) -> Optional[int]:
        """
        Get the speed limit for a specific location.
        
        Args:
            latitude: GPS latitude
            longitude: GPS longitude
            
        Returns:
            Speed limit in mph, or None if not found
        """
        if not self.speed_limit_map:
            return None
        
        # Round to match our lookup grid
        lat_rounded = round(latitude, 4)
        lon_rounded = round(longitude, 4)
        
        return self.speed_limit_map.get((lat_rounded, lon_rounded))
    
    def get_processed_data(self) -> Dict[Tuple[float, float], int]:
        """Get the processed speed limit map."""
        return self.speed_limit_map or {}


class WeatherDataLoader(BaseDataLoader):
    """
    Loader for historical weather data.
    
    Processes weather information for contextual analysis of driving conditions.
    """
    
    def __init__(self):
        super().__init__()
        self.weather_data: Optional[pd.DataFrame] = None
    
    def load(self, data_path: Path) -> pd.DataFrame:
        """
        Load historical weather data.
        
        Args:
            data_path: Path to weather dataset
            
        Returns:
            DataFrame with processed weather data
        """
        self.logger.info(f"Loading weather data from {data_path}")
        
        # Check for real weather data first, then fall back to sample
        real_weather_file = data_path / "weather_daily_real.parquet"
        sample_weather_file = data_path / "weather_sample.parquet"
        
        if real_weather_file.exists():
            self.logger.info("Loading REAL weather data from Open-Meteo API")
            weather_df = pd.read_parquet(real_weather_file)
            # Real data is already processed by the downloader
            self.weather_data = weather_df
        elif sample_weather_file.exists():
            self.logger.info("Loading sample weather data")
            weather_df = pd.read_parquet(sample_weather_file)
            self.weather_data = self._process_weather_data(weather_df)
        else:
            self.logger.warning(f"No weather files found in {data_path}")
            return pd.DataFrame()
        
        return self.weather_data
    
    def _process_weather_data(self, weather_df: pd.DataFrame) -> pd.DataFrame:
        """Process weather data into standardized format."""
        # Ensure timestamp is datetime
        weather_df['timestamp'] = pd.to_datetime(weather_df['timestamp'])
        weather_df['date'] = weather_df['timestamp'].dt.date
        
        # Categorize precipitation conditions
        weather_df['is_rain_or_snow'] = weather_df['weather_condition'].isin(['rain', 'snow'])
        weather_df['is_adverse_weather'] = weather_df['weather_condition'].isin(['rain', 'snow', 'fog'])
        
        # Temperature categories
        weather_df['temp_category'] = pd.cut(
            weather_df['temperature_f'], 
            bins=[-float('inf'), 32, 50, 70, 90, float('inf')],
            labels=['freezing', 'cold', 'mild', 'warm', 'hot']
        )
        
        self.logger.info(f"Processed {len(weather_df)} weather records")
        return weather_df
    
    def get_weather_for_date(self, date: datetime) -> Optional[Dict[str, Any]]:
        """
        Get weather conditions for a specific date.
        
        Args:
            date: Date to look up weather for
            
        Returns:
            Dictionary with weather conditions, or None if not found
        """
        if self.weather_data is None or len(self.weather_data) == 0:
            return None
        
        date_only = date.date()
        weather_day = self.weather_data[self.weather_data['date'] == date_only]
        
        if len(weather_day) == 0:
            return None
        
        # Take the first record for the day
        row = weather_day.iloc[0]
        
        return {
            'temperature_f': row['temperature_f'],
            'weather_condition': row['weather_condition'],
            'is_rain_or_snow': row['is_rain_or_snow'],
            'is_adverse_weather': row['is_adverse_weather'],
            'visibility_miles': row.get('visibility_miles', 10.0)
        }
    
    def get_processed_data(self) -> pd.DataFrame:
        """Get the processed weather data."""
        return self.weather_data if self.weather_data is not None else pd.DataFrame()


class TrafficDataLoader(BaseDataLoader):
    """
    Loader for traffic congestion data.
    
    Processes traffic information for understanding driving context.
    """
    
    def __init__(self):
        super().__init__()
        self.traffic_data: Optional[pd.DataFrame] = None
    
    def load(self, data_path: Path) -> pd.DataFrame:
        """
        Load traffic congestion data.
        
        Args:
            data_path: Path to traffic dataset
            
        Returns:
            DataFrame with processed traffic data
        """
        self.logger.info(f"Loading traffic data from {data_path}")
        
        traffic_file = data_path / "chicago_traffic_sample.csv"
        if not traffic_file.exists():
            self.logger.warning(f"Traffic file not found: {traffic_file}")
            return pd.DataFrame()
        
        traffic_df = pd.read_csv(traffic_file)
        self.traffic_data = self._process_traffic_data(traffic_df)
        
        return self.traffic_data
    
    def _process_traffic_data(self, traffic_df: pd.DataFrame) -> pd.DataFrame:
        """Process traffic data into standardized format."""
        # Ensure timestamp is datetime
        traffic_df['timestamp'] = pd.to_datetime(traffic_df['timestamp'])
        traffic_df['hour'] = traffic_df['timestamp'].dt.hour
        traffic_df['day_of_week'] = traffic_df['timestamp'].dt.day_name()
        
        # Standardize congestion levels
        congestion_map = {'light': 0.2, 'moderate': 0.5, 'heavy': 0.8}
        traffic_df['congestion_score'] = traffic_df['congestion_level'].map(congestion_map)
        
        # Add rush hour flags
        traffic_df['is_morning_rush'] = (traffic_df['hour'] >= 7) & (traffic_df['hour'] <= 9)
        traffic_df['is_evening_rush'] = (traffic_df['hour'] >= 17) & (traffic_df['hour'] <= 19)
        traffic_df['is_rush_hour'] = traffic_df['is_morning_rush'] | traffic_df['is_evening_rush']
        
        self.logger.info(f"Processed {len(traffic_df)} traffic records")
        return traffic_df
    
    def get_traffic_for_location_time(self, latitude: float, longitude: float, 
                                    timestamp: datetime) -> Optional[Dict[str, Any]]:
        """
        Get traffic conditions for a specific location and time.
        
        Args:
            latitude: GPS latitude
            longitude: GPS longitude  
            timestamp: Time to look up traffic for
            
        Returns:
            Dictionary with traffic conditions, or None if not found
        """
        if self.traffic_data is None or len(self.traffic_data) == 0:
            return None
        
        # Find nearest traffic segment (simplified - in production would use proper geo-indexing)
        traffic_df = self.traffic_data.copy()
        traffic_df['distance'] = ((traffic_df['latitude'] - latitude)**2 + 
                                 (traffic_df['longitude'] - longitude)**2)**0.5
        
        # Get nearest segment within reasonable distance
        nearest = traffic_df[traffic_df['distance'] < 0.01].sort_values('distance')
        
        if len(nearest) == 0:
            return None
        
        # Get record closest in time
        nearest['time_diff'] = abs((nearest['timestamp'] - timestamp).dt.total_seconds())
        best_match = nearest.sort_values('time_diff').iloc[0]
        
        return {
            'congestion_level': best_match['congestion_level'],
            'congestion_score': best_match['congestion_score'],
            'speed_mph': best_match['speed_mph'],
            'is_rush_hour': best_match['is_rush_hour']
        }
    
    def get_processed_data(self) -> pd.DataFrame:
        """Get the processed traffic data."""
        return self.traffic_data if self.traffic_data is not None else pd.DataFrame()


class OBDDataLoader(BaseDataLoader):
    """
    Loader for OBD-II vehicle diagnostic data.
    
    Processes vehicle system information for drivers with OBD-II devices.
    """
    
    def __init__(self):
        super().__init__()
        self.obd_data: Optional[pd.DataFrame] = None
    
    def load(self, data_path: Path) -> pd.DataFrame:
        """
        Load OBD-II diagnostic data.
        
        Args:
            data_path: Path to OBD dataset
            
        Returns:
            DataFrame with processed OBD data
        """
        self.logger.info(f"Loading OBD data from {data_path}")
        
        obd_file = data_path / "obd_sample.parquet"
        if not obd_file.exists():
            self.logger.warning(f"OBD file not found: {obd_file}")
            return pd.DataFrame()
        
        obd_df = pd.read_parquet(obd_file)
        self.obd_data = self._process_obd_data(obd_df)
        
        return self.obd_data
    
    def _process_obd_data(self, obd_df: pd.DataFrame) -> pd.DataFrame:
        """Process OBD data into standardized format."""
        # Ensure timestamp is datetime
        obd_df['timestamp'] = pd.to_datetime(obd_df['timestamp'])
        
        # Process diagnostic trouble codes
        obd_df['has_dtc'] = obd_df['dtc_code'].notna() & (obd_df['dtc_code'] != '')
        obd_df['dtc_severity'] = obd_df['dtc_code'].apply(self._classify_dtc_severity)
        
        # Engine performance categories
        obd_df['engine_performance'] = pd.cut(
            obd_df['engine_rpm'],
            bins=[0, 1000, 2000, 3000, 5000, float('inf')],
            labels=['idle', 'low', 'normal', 'high', 'redline']
        )
        
        # Load categories
        obd_df['load_category'] = pd.cut(
            obd_df['engine_load_pct'],
            bins=[0, 25, 50, 75, 100],
            labels=['light', 'moderate', 'heavy', 'extreme']
        )
        
        self.logger.info(f"Processed {len(obd_df)} OBD records")
        return obd_df
    
    def _classify_dtc_severity(self, dtc_code: str) -> str:
        """Classify diagnostic trouble code severity."""
        if pd.isna(dtc_code) or dtc_code == '':
            return 'none'
        
        # P codes are powertrain (most common)
        if dtc_code.startswith('P'):
            if dtc_code.startswith('P0'):
                return 'moderate'  # Generic powertrain codes
            else:
                return 'manufacturer'  # Manufacturer specific
        elif dtc_code.startswith('B'):
            return 'low'  # Body codes
        elif dtc_code.startswith('C'):
            return 'high'  # Chassis codes
        elif dtc_code.startswith('U'):
            return 'moderate'  # Network codes
        else:
            return 'unknown'
    
    def get_vehicle_summary(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """
        Get vehicle system summary for a time period.
        
        Args:
            start_time: Start of time period
            end_time: End of time period
            
        Returns:
            Dictionary with vehicle system metrics
        """
        if self.obd_data is None or len(self.obd_data) == 0:
            return {}
        
        # Filter data for time period
        period_data = self.obd_data[
            (self.obd_data['timestamp'] >= start_time) & 
            (self.obd_data['timestamp'] <= end_time)
        ]
        
        if len(period_data) == 0:
            return {}
        
        return {
            'avg_engine_rpm': period_data['engine_rpm'].mean(),
            'max_engine_rpm': period_data['engine_rpm'].max(),
            'avg_engine_load_pct': period_data['engine_load_pct'].mean(),
            'has_dtc_codes': period_data['has_dtc'].any(),
            'dtc_count': period_data['has_dtc'].sum(),
            'mil_active': period_data['mil_status'].any(),
            'records_count': len(period_data)
        }
    
    def get_processed_data(self) -> pd.DataFrame:
        """Get the processed OBD data."""
        return self.obd_data if self.obd_data is not None else pd.DataFrame()
