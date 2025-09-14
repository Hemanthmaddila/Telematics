"""
Real dataset downloader for actual external data sources.

This module implements the actual download logic for the real datasets
identified in the data sourcing plan, replacing sample data generation.
"""

import requests
import pandas as pd
import numpy as np
import logging
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from urllib.parse import urlencode

from ..utils.config import get_config


class RealDataDownloader:
    """Downloads and processes actual real datasets from external sources."""
    
    def __init__(self):
        """Initialize the real data downloader."""
        self.config = get_config()
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Telematics-Research/1.0 (Academic Research)'
        })
    
    def download_weather_data(self, local_dir: Path, 
                            latitude: float = 41.8781, longitude: float = -87.6298,
                            start_date: str = "2024-01-01", end_date: str = "2024-12-31") -> bool:
        """
        Download real historical weather data from Open-Meteo API.
        
        Args:
            local_dir: Directory to save weather data
            latitude: Location latitude (default: Chicago)
            longitude: Location longitude (default: Chicago)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Downloading real weather data from Open-Meteo API...")
        
        try:
            # Open-Meteo Historical Weather API
            base_url = "https://archive-api.open-meteo.com/v1/archive"
            
            params = {
                'latitude': latitude,
                'longitude': longitude,
                'start_date': start_date,
                'end_date': end_date,
                'daily': [
                    'temperature_2m_max',
                    'temperature_2m_min', 
                    'temperature_2m_mean',
                    'precipitation_sum',
                    'weather_code',
                    'wind_speed_10m_max'
                ],
                'hourly': [
                    'temperature_2m',
                    'precipitation',
                    'weather_code',
                    'visibility'
                ],
                'temperature_unit': 'fahrenheit',
                'wind_speed_unit': 'mph',
                'precipitation_unit': 'inch',
                'timezone': 'America/Chicago'
            }
            
            # Convert list parameters to comma-separated strings
            for key, value in params.items():
                if isinstance(value, list):
                    params[key] = ','.join(value)
            
            response = self.session.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            
            weather_data = response.json()
            
            # Process daily data
            daily_df = self._process_weather_daily(weather_data.get('daily', {}))
            
            # Process hourly data  
            hourly_df = self._process_weather_hourly(weather_data.get('hourly', {}))
            
            # Save data
            daily_df.to_parquet(local_dir / "weather_daily_real.parquet")
            hourly_df.to_parquet(local_dir / "weather_hourly_real.parquet")
            
            # Save metadata
            metadata = {
                'source': 'Open-Meteo Archive API',
                'location': {'latitude': latitude, 'longitude': longitude},
                'date_range': {'start': start_date, 'end': end_date},
                'daily_records': len(daily_df),
                'hourly_records': len(hourly_df),
                'downloaded_at': datetime.now().isoformat()
            }
            
            with open(local_dir / "weather_metadata_real.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.logger.info(f"Downloaded {len(daily_df)} daily and {len(hourly_df)} hourly weather records")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to download weather data: {str(e)}")
            return False
    
    def _process_weather_daily(self, daily_data: Dict) -> pd.DataFrame:
        """Process daily weather data from Open-Meteo."""
        if not daily_data:
            return pd.DataFrame()
            
        df = pd.DataFrame(daily_data)
        df['time'] = pd.to_datetime(df['time'])
        df['date'] = df['time'].dt.date
        
        # Map weather codes to conditions
        df['weather_condition'] = df['weather_code'].apply(self._map_weather_code)
        df['is_rain_or_snow'] = df['weather_condition'].isin(['rain', 'snow'])
        df['is_adverse_weather'] = df['weather_condition'].isin(['rain', 'snow', 'fog'])
        
        return df
    
    def _process_weather_hourly(self, hourly_data: Dict) -> pd.DataFrame:
        """Process hourly weather data from Open-Meteo."""
        if not hourly_data:
            return pd.DataFrame()
            
        df = pd.DataFrame(hourly_data)
        df['time'] = pd.to_datetime(df['time'])
        df['hour'] = df['time'].dt.hour
        df['date'] = df['time'].dt.date
        
        # Map weather codes to conditions
        df['weather_condition'] = df['weather_code'].apply(self._map_weather_code)
        
        return df
    
    def _map_weather_code(self, code: int) -> str:
        """Map Open-Meteo weather codes to standard conditions."""
        if pd.isna(code):
            return 'unknown'
            
        code = int(code)
        
        # WMO Weather interpretation codes
        if code == 0:
            return 'clear'
        elif code in [1, 2, 3]:
            return 'cloudy'
        elif code in [45, 48]:
            return 'fog'
        elif code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:
            return 'rain'
        elif code in [71, 73, 75, 77, 85, 86]:
            return 'snow'
        else:
            return 'other'
    
    def download_chicago_traffic_data(self, local_dir: Path) -> bool:
        """
        Download real Chicago traffic data from City of Chicago Data Portal.
        
        Args:
            local_dir: Directory to save traffic data
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info("Downloading real Chicago traffic data...")
        
        try:
            # Chicago Traffic Tracker API
            base_url = "https://data.cityofchicago.org/resource/77hq-huss.json"
            
            # Get recent traffic data (last 30 days)
            params = {
                '$limit': 10000,  # Maximum records
                '$order': 'last_updated DESC',
                '$where': f"last_updated > '{(datetime.now() - timedelta(days=30)).isoformat()}'"
            }
            
            response = self.session.get(base_url, params=params, timeout=60)
            response.raise_for_status()
            
            traffic_data = response.json()
            
            if not traffic_data:
                self.logger.warning("No recent traffic data available")
                return False
            
            # Convert to DataFrame
            df = pd.DataFrame(traffic_data)
            
            # Process traffic data
            df = self._process_chicago_traffic(df)
            
            # Save data
            df.to_parquet(local_dir / "chicago_traffic_real.parquet")
            df.to_csv(local_dir / "chicago_traffic_real.csv", index=False)
            
            # Save metadata
            metadata = {
                'source': 'City of Chicago Data Portal',
                'dataset': 'Chicago Traffic Tracker',
                'url': 'https://data.cityofchicago.org/Transportation/Chicago-Traffic-Tracker-Historical-Congestion-Esti/77hq-huss',
                'records': len(df),
                'date_range': {
                    'start': df['last_updated'].min().isoformat() if len(df) > 0 else None,
                    'end': df['last_updated'].max().isoformat() if len(df) > 0 else None
                },
                'downloaded_at': datetime.now().isoformat()
            }
            
            with open(local_dir / "traffic_metadata_real.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.logger.info(f"Downloaded {len(df)} real Chicago traffic records")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to download Chicago traffic data: {str(e)}")
            return False
    
    def _process_chicago_traffic(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process Chicago traffic data."""
        # Convert timestamps
        df['last_updated'] = pd.to_datetime(df['last_updated'])
        df['hour'] = df['last_updated'].dt.hour
        df['day_of_week'] = df['last_updated'].dt.day_name()
        
        # Process speed and congestion
        df['current_speed'] = pd.to_numeric(df.get('current_speed', 0), errors='coerce')
        df['historical_speed'] = pd.to_numeric(df.get('historical_speed', 0), errors='coerce')
        
        # Calculate congestion score
        df['congestion_ratio'] = df['current_speed'] / df['historical_speed'].replace(0, np.nan)
        df['congestion_score'] = 1 - df['congestion_ratio'].clip(0, 1)
        
        # Categorize congestion levels
        df['congestion_level'] = pd.cut(
            df['congestion_score'],
            bins=[0, 0.3, 0.6, 1.0],
            labels=['light', 'moderate', 'heavy'],
            include_lowest=True
        )
        
        # Add rush hour flags
        df['is_morning_rush'] = (df['hour'] >= 7) & (df['hour'] <= 9)
        df['is_evening_rush'] = (df['hour'] >= 17) & (df['hour'] <= 19)
        df['is_rush_hour'] = df['is_morning_rush'] | df['is_evening_rush']
        
        return df
    
    def download_osm_speed_limits(self, local_dir: Path, 
                                bbox: Tuple[float, float, float, float] = (41.8, -87.7, 41.9, -87.6)) -> bool:
        """
        Download real speed limit data from OpenStreetMap via Overpass API.
        
        Args:
            local_dir: Directory to save OSM data
            bbox: Bounding box (south, west, north, east) - default: Chicago area
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info("Downloading real OSM speed limit data...")
        
        try:
            # Overpass API query for roads with speed limits
            overpass_url = "https://overpass-api.de/api/interpreter"
            
            # Overpass QL query
            query = f"""
            [out:json][timeout:60];
            (
              way["highway"]["maxspeed"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
            );
            out geom;
            """
            
            response = self.session.post(
                overpass_url,
                data={'data': query},
                timeout=120
            )
            response.raise_for_status()
            
            osm_data = response.json()
            
            if not osm_data.get('elements'):
                self.logger.warning("No OSM speed limit data found in specified area")
                return False
            
            # Process OSM data
            df = self._process_osm_data(osm_data['elements'])
            
            # Save data
            df.to_parquet(local_dir / "osm_speed_limits_real.parquet")
            df.to_csv(local_dir / "osm_speed_limits_real.csv", index=False)
            
            # Save metadata
            metadata = {
                'source': 'OpenStreetMap via Overpass API',
                'bbox': {'south': bbox[0], 'west': bbox[1], 'north': bbox[2], 'east': bbox[3]},
                'records': len(df),
                'unique_ways': df['way_id'].nunique(),
                'downloaded_at': datetime.now().isoformat()
            }
            
            with open(local_dir / "osm_metadata_real.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.logger.info(f"Downloaded {len(df)} real OSM speed limit records")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to download OSM speed limit data: {str(e)}")
            return False
    
    def _process_osm_data(self, elements: List[Dict]) -> pd.DataFrame:
        """Process OSM elements into a structured DataFrame."""
        processed_ways = []
        
        for element in elements:
            if element.get('type') != 'way':
                continue
                
            way_data = {
                'way_id': element.get('id'),
                'highway_type': element.get('tags', {}).get('highway'),
                'maxspeed_raw': element.get('tags', {}).get('maxspeed'),
                'name': element.get('tags', {}).get('name', ''),
                'surface': element.get('tags', {}).get('surface', ''),
            }
            
            # Parse speed limit
            speed_mph = self._parse_speed_limit(way_data['maxspeed_raw'])
            way_data['speed_limit_mph'] = speed_mph
            
            # Extract geometry (use first and last nodes for simplicity)
            geometry = element.get('geometry', [])
            if geometry:
                way_data['start_lat'] = geometry[0]['lat']
                way_data['start_lon'] = geometry[0]['lon']
                way_data['end_lat'] = geometry[-1]['lat']
                way_data['end_lon'] = geometry[-1]['lon']
                way_data['center_lat'] = np.mean([g['lat'] for g in geometry])
                way_data['center_lon'] = np.mean([g['lon'] for g in geometry])
            
            # Classify road type
            way_data['road_type'] = self._classify_road_type(way_data['highway_type'])
            
            processed_ways.append(way_data)
        
        return pd.DataFrame(processed_ways)
    
    def _parse_speed_limit(self, maxspeed_raw: str) -> Optional[int]:
        """Parse speed limit from OSM maxspeed tag."""
        if not maxspeed_raw:
            return None
            
        # Handle common formats
        maxspeed_raw = maxspeed_raw.lower().strip()
        
        # Remove units and extract number
        if 'mph' in maxspeed_raw:
            try:
                return int(maxspeed_raw.replace('mph', '').strip())
            except ValueError:
                return None
        elif 'km/h' in maxspeed_raw or 'kmh' in maxspeed_raw:
            try:
                kmh = int(maxspeed_raw.replace('km/h', '').replace('kmh', '').strip())
                return int(kmh * 0.621371)  # Convert to mph
            except ValueError:
                return None
        else:
            # Assume mph if no unit
            try:
                return int(maxspeed_raw)
            except ValueError:
                return None
    
    def _classify_road_type(self, highway_type: str) -> str:
        """Classify OSM highway type into standard categories."""
        if not highway_type:
            return 'unknown'
        
        highway_type = highway_type.lower()
        
        if highway_type in ['motorway', 'motorway_link', 'trunk', 'trunk_link']:
            return 'highway'
        elif highway_type in ['primary', 'primary_link', 'secondary', 'secondary_link']:
            return 'arterial'
        elif highway_type in ['tertiary', 'tertiary_link', 'unclassified']:
            return 'urban'
        elif highway_type in ['residential', 'living_street']:
            return 'residential'
        else:
            return 'other'
    
    def get_real_dataset_urls(self) -> Dict[str, str]:
        """Get URLs for real datasets that require manual download."""
        return {
            'smartphone_sensors': 'https://www.nature.com/articles/s41597-024-03149-8#Sec10',
            'phone_usage': 'https://figshare.com/articles/dataset/Passengers_and_Drivers_reading_while_driving/8313620',
            'obd_kaggle': 'https://www.kaggle.com/datasets/outofskills/obd-ii-dataset',
            'obd_research': 'https://www.radar-service.eu/radar/en/dataset/bCtGxdTklQlfQcAq'
        }
    
    def print_manual_download_instructions(self):
        """Print instructions for datasets that require manual download."""
        urls = self.get_real_dataset_urls()
        
        print("\n" + "="*60)
        print("📥 MANUAL DOWNLOAD REQUIRED FOR SOME DATASETS")
        print("="*60)
        
        print("\n🔬 RESEARCH DATASETS (Require Registration/Agreement):")
        print(f"• Smartphone Sensors: {urls['smartphone_sensors']}")
        print("  - Nature Scientific Data paper with download links")
        print("  - May require academic email for access")
        
        print(f"\n• Phone Usage Research: {urls['phone_usage']}")
        print("  - Figshare dataset (free registration)")
        print("  - Download and extract to: data/raw/phone_usage/")
        
        print(f"\n• OBD-II Kaggle Dataset: {urls['obd_kaggle']}")
        print("  - Requires Kaggle account (free)")
        print("  - Download and extract to: data/raw/obd_data/")
        
        print(f"\n• OBD-II Research Archive: {urls['obd_research']}")
        print("  - European research data archive")
        print("  - Alternative to Kaggle dataset")
        
        print("\n✅ AUTOMATED DOWNLOADS (Working Now):")
        print("• Weather Data: Open-Meteo API ✓")
        print("• Traffic Data: Chicago Data Portal ✓") 
        print("• Speed Limits: OpenStreetMap ✓")
        
        print("\n💡 TIP: Start with automated downloads, then add manual datasets as needed")
        print("="*60)
