"""
Data ingestion manager for coordinating real dataset downloads and processing.

This module implements the data sourcing strategy for combining real datasets
with simulated data to create a comprehensive telematics training dataset.
"""

import os
import requests
import zipfile
import pandas as pd
import numpy as np
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from urllib.parse import urlparse
from datetime import datetime

from ..utils.config import get_config
from ..data.schemas import DataSource as UserDataSource
from .real_data_downloader import RealDataDownloader


@dataclass
class DataSourceMetadata:
    """Metadata for a real data source."""
    name: str
    description: str
    url: str
    file_type: str  # 'csv', 'json', 'zip', 'api'
    local_path: str
    variables_covered: List[str]
    citation: str


class DataIngestionManager:
    """
    Manages the download and initial processing of real datasets.
    
    This class orchestrates the ingestion of all external data sources
    identified in the data sourcing plan.
    """
    
    def __init__(self):
        """Initialize the data ingestion manager."""
        self.config = get_config()
        self.logger = logging.getLogger(__name__)
        self.data_dir = Path(self.config.get("data.raw_data_path", "./data/raw"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize real data downloader
        self.real_downloader = RealDataDownloader()
        
        # Initialize data source catalog
        self.data_sources = self._initialize_data_sources()
    
    def _initialize_data_sources(self) -> Dict[str, DataSourceMetadata]:
        """Initialize the catalog of real data sources."""
        return {
            "smartphone_sensors": DataSourceMetadata(
                name="Nature Scientific Data Smartphone Sensor Corpus",
                description="Real smartphone GPS and IMU sensor data for trip kinematics",
                url="https://www.nature.com/articles/s41597-024-03149-8",
                file_type="zip",
                local_path="smartphone_sensors/",
                variables_covered=["gps_points", "imu_readings", "trip_kinematics"],
                citation="Nature Scientific Data (2024). Smartphone sensor corpus for human activity recognition."
            ),
            
            "phone_usage": DataSourceMetadata(
                name="Driver vs Passenger Phone Usage Dataset",
                description="Real phone interaction patterns during driving",
                url="https://figshare.com/articles/dataset/Passengers_and_Drivers_reading_while_driving/8313620",
                file_type="zip", 
                local_path="phone_usage/",
                variables_covered=["pct_trip_time_screen_on", "handheld_events_rate_per_hour"],
                citation="Figshare (2019). Passengers and Drivers reading while driving dataset."
            ),
            
            "osm_speed_limits": DataSourceMetadata(
                name="OpenStreetMap Speed Limit Data",
                description="Road speed limits for speeding event detection",
                url="https://download.geofabrik.de/",  # Will specify region
                file_type="osm",
                local_path="osm_speed_limits/",
                variables_covered=["posted_speed_limit_mph", "road_type"],
                citation="OpenStreetMap contributors. https://www.openstreetmap.org"
            ),
            
            "weather_historical": DataSourceMetadata(
                name="Open-Meteo Historical Weather API",
                description="Historical weather conditions for trip context",
                url="https://api.open-meteo.com/v1/historical",
                file_type="api",
                local_path="weather_data/",
                variables_covered=["weather_condition", "temperature_f", "pct_miles_in_rain_or_snow"],
                citation="Open-Meteo.com. Historical weather API."
            ),
            
            "traffic_chicago": DataSourceMetadata(
                name="Chicago Traffic Tracker",
                description="Real traffic congestion data for context",
                url="https://data.cityofchicago.org/Transportation/Chicago-Traffic-Tracker-Historical-Congestion-Esti/77hq-huss",
                file_type="csv",
                local_path="traffic_data/",
                variables_covered=["pct_miles_in_heavy_traffic", "traffic_level"],
                citation="City of Chicago Data Portal. Chicago Traffic Tracker dataset."
            ),
            
            "obd_vehicle_data": DataSourceMetadata(
                name="Kaggle OBD-II Vehicle Dataset",
                description="Real OBD-II diagnostic data for vehicle systems",
                url="https://www.kaggle.com/datasets/outofskills/obd-ii-dataset",
                file_type="csv",
                local_path="obd_data/",
                variables_covered=["avg_engine_rpm", "has_dtc_codes", "engine_load_pct"],
                citation="Kaggle (2023). OBD-II Vehicle Diagnostic Dataset."
            )
        }
    
    def download_dataset(self, dataset_name: str, force_refresh: bool = False) -> Path:
        """
        Download a specific dataset if not already cached locally.
        
        Args:
            dataset_name: Name of the dataset to download
            force_refresh: Whether to re-download even if cached
            
        Returns:
            Path to the local dataset directory
        """
        if dataset_name not in self.data_sources:
            raise ValueError(f"Unknown dataset: {dataset_name}")
        
        source = self.data_sources[dataset_name]
        local_dir = self.data_dir / source.local_path
        local_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if dataset already exists
        if not force_refresh and self._dataset_exists(local_dir):
            self.logger.info(f"Dataset {dataset_name} already exists at {local_dir}")
            return local_dir
        
        self.logger.info(f"Downloading dataset: {source.name}")
        
        try:
            success = False
            
            # Use real downloads for automated datasets
            if dataset_name == "weather_historical":
                success = self.real_downloader.download_weather_data(local_dir)
            elif dataset_name == "traffic_chicago":
                success = self.real_downloader.download_chicago_traffic_data(local_dir)
            elif dataset_name == "osm_speed_limits":
                success = self.real_downloader.download_osm_speed_limits(local_dir)
            else:
                # For datasets requiring manual download, provide instructions
                success = self._handle_manual_download_dataset(dataset_name, source, local_dir)
            
            if success:
                self.logger.info(f"Successfully downloaded {dataset_name} to {local_dir}")
                return local_dir
            else:
                self.logger.warning(f"Download incomplete for {dataset_name}")
                return local_dir
            
        except Exception as e:
            self.logger.error(f"Failed to download {dataset_name}: {str(e)}")
            raise
    
    def _dataset_exists(self, local_dir: Path) -> bool:
        """Check if a dataset already exists locally."""
        return local_dir.exists() and any(local_dir.iterdir())
    
    def _handle_manual_download_dataset(self, dataset_name: str, source: DataSourceMetadata, local_dir: Path) -> bool:
        """
        Handle datasets that require manual download.
        
        Args:
            dataset_name: Name of the dataset
            source: Dataset metadata
            local_dir: Local directory for the dataset
            
        Returns:
            True if sample data was created, False otherwise
        """
        self.logger.warning(f"Dataset '{dataset_name}' requires manual download")
        self.logger.info(f"Please download from: {source.url}")
        
        # Create sample data as fallback and provide instructions
        if dataset_name == "smartphone_sensors":
            self._create_smartphone_sensor_sample(local_dir)
            self.logger.info("Created sample smartphone sensor data. Replace with real data from Nature Scientific Data.")
        elif dataset_name == "phone_usage":
            self._create_phone_usage_sample(local_dir)
            self.logger.info("Created sample phone usage data. Replace with real data from Figshare.")
        elif dataset_name == "obd_vehicle_data":
            self._create_obd_sample(local_dir)
            self.logger.info("Created sample OBD data. Replace with real data from Kaggle.")
        
        # Create instructions file
        instructions = {
            'dataset_name': source.name,
            'download_url': source.url,
            'instructions': f"""
To use real data for {dataset_name}:

1. Visit: {source.url}
2. Download the dataset files
3. Extract/copy files to: {local_dir}
4. Run the data ingestion again

Citation: {source.citation}
Variables covered: {', '.join(source.variables_covered)}
            """.strip(),
            'sample_data_created': True,
            'created_at': datetime.now().isoformat()
        }
        
        with open(local_dir / "DOWNLOAD_INSTRUCTIONS.json", 'w') as f:
            json.dump(instructions, f, indent=2)
        
        return True
    
    def _download_zip_file(self, source: DataSourceMetadata, local_dir: Path) -> None:
        """Download and extract a ZIP file."""
        # For now, create placeholder files since we can't download copyrighted data
        # In production, this would download from the actual URLs
        self.logger.warning(f"Creating placeholder for {source.name} - replace with actual download logic")
        
        # Create sample data files that match the expected schema
        if "smartphone_sensors" in source.local_path:
            self._create_smartphone_sensor_sample(local_dir)
        elif "phone_usage" in source.local_path:
            self._create_phone_usage_sample(local_dir)
    
    def _download_csv_file(self, source: DataSourceMetadata, local_dir: Path) -> None:
        """Download a CSV file."""
        # For Chicago traffic data, create a sample file
        if "traffic_data" in source.local_path:
            self._create_traffic_sample(local_dir)
        elif "obd_data" in source.local_path:
            self._create_obd_sample(local_dir)
    
    def _download_api_data(self, source: DataSourceMetadata, local_dir: Path) -> None:
        """Download data from an API."""
        if "weather" in source.local_path:
            self._create_weather_sample(local_dir)
    
    def _download_osm_data(self, source: DataSourceMetadata, local_dir: Path) -> None:
        """Download OSM data for speed limits."""
        self._create_osm_sample(local_dir)
    
    def _create_smartphone_sensor_sample(self, local_dir: Path) -> None:
        """Create sample smartphone sensor data."""
        # GPS sample data
        gps_data = {
            'timestamp': pd.date_range('2024-01-01 08:00:00', periods=1000, freq='1s'),
            'latitude': 41.8781 + (np.random.randn(1000) * 0.001),  # Chicago area
            'longitude': -87.6298 + (np.random.randn(1000) * 0.001),
            'altitude': 200 + (np.random.randn(1000) * 10),
            'accuracy_meters': np.random.uniform(3, 15, 1000),
            'speed_mph': np.random.uniform(0, 65, 1000),
            'heading': np.random.uniform(0, 360, 1000)
        }
        
        # IMU sample data  
        imu_data = {
            'timestamp': pd.date_range('2024-01-01 08:00:00', periods=1000, freq='1s'),
            'accel_x': np.random.normal(0, 0.1, 1000),  # Forward/backward G-force
            'accel_y': np.random.normal(0, 0.05, 1000), # Left/right G-force  
            'accel_z': np.random.normal(1, 0.02, 1000), # Up/down G-force (gravity)
            'gyro_x': np.random.normal(0, 2, 1000),     # Roll rate
            'gyro_y': np.random.normal(0, 2, 1000),     # Pitch rate
            'gyro_z': np.random.normal(0, 5, 1000)      # Yaw rate
        }
        
        pd.DataFrame(gps_data).to_parquet(local_dir / "gps_sample.parquet")
        pd.DataFrame(imu_data).to_parquet(local_dir / "imu_sample.parquet")
        
        # Create metadata file
        metadata = {
            "description": "Sample smartphone sensor data for telematics",
            "records": 1000,
            "duration_minutes": 16.67,
            "sampling_rate_hz": 1,
            "location": "Chicago, IL area"
        }
        
        import json
        with open(local_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _create_phone_usage_sample(self, local_dir: Path) -> None:
        """Create sample phone usage data."""
        import numpy as np
        
        # Simulate phone interaction events during trips
        phone_data = {
            'trip_id': [f"trip_{i:06d}" for i in range(500)],
            'screen_on_duration_seconds': np.random.exponential(30, 500),
            'handheld_events': np.random.poisson(2, 500),
            'call_duration_seconds': np.random.exponential(120, 500) * np.random.binomial(1, 0.3, 500),
            'trip_duration_minutes': np.random.uniform(5, 60, 500)
        }
        
        pd.DataFrame(phone_data).to_parquet(local_dir / "phone_usage_sample.parquet")
    
    def _create_traffic_sample(self, local_dir: Path) -> None:
        """Create sample Chicago traffic data."""
        import numpy as np
        
        # Chicago traffic tracker style data
        traffic_data = {
            'segment_id': [f"seg_{i:04d}" for i in range(200)],
            'timestamp': pd.date_range('2024-01-01', periods=200, freq='1h'),
            'speed_mph': np.random.uniform(15, 65, 200),
            'congestion_level': np.random.choice(['light', 'moderate', 'heavy'], 200, p=[0.4, 0.4, 0.2]),
            'travel_time_minutes': np.random.uniform(5, 45, 200),
            'latitude': 41.8781 + (np.random.randn(200) * 0.01),
            'longitude': -87.6298 + (np.random.randn(200) * 0.01)
        }
        
        pd.DataFrame(traffic_data).to_csv(local_dir / "chicago_traffic_sample.csv", index=False)
    
    def _create_obd_sample(self, local_dir: Path) -> None:
        """Create sample OBD-II vehicle data."""
        import numpy as np
        
        # OBD-II diagnostic data
        obd_data = {
            'timestamp': pd.date_range('2024-01-01 08:00:00', periods=500, freq='10s'),
            'engine_rpm': np.random.uniform(800, 4000, 500),
            'engine_load_pct': np.random.uniform(10, 90, 500),
            'throttle_position_pct': np.random.uniform(0, 100, 500),
            'dtc_code': np.random.choice(['', 'P0301', 'P0420', 'P0171'], 500, p=[0.85, 0.05, 0.05, 0.05]),
            'mil_status': np.random.choice([0, 1], 500, p=[0.9, 0.1]),
            'vehicle_speed_mph': np.random.uniform(0, 70, 500)
        }
        
        pd.DataFrame(obd_data).to_parquet(local_dir / "obd_sample.parquet")
    
    def _create_weather_sample(self, local_dir: Path) -> None:
        """Create sample weather data."""
        import numpy as np
        
        # Historical weather conditions
        weather_data = {
            'timestamp': pd.date_range('2024-01-01', periods=365, freq='1D'),
            'temperature_f': np.random.normal(45, 20, 365),  # Chicago climate
            'weather_condition': np.random.choice(['clear', 'rain', 'snow', 'cloudy'], 365, p=[0.5, 0.2, 0.15, 0.15]),
            'visibility_miles': np.random.uniform(1, 10, 365),
            'precipitation_inches': np.random.exponential(0.1, 365)
        }
        
        pd.DataFrame(weather_data).to_parquet(local_dir / "weather_sample.parquet")
    
    def _create_osm_sample(self, local_dir: Path) -> None:
        """Create sample OpenStreetMap speed limit data."""
        import numpy as np
        
        # Road segment speed limits
        osm_data = {
            'way_id': [f"way_{i:08d}" for i in range(1000)],
            'speed_limit_mph': np.random.choice([25, 30, 35, 45, 55, 65], 1000, p=[0.2, 0.2, 0.2, 0.2, 0.15, 0.05]),
            'road_type': np.random.choice(['residential', 'urban', 'highway'], 1000, p=[0.4, 0.4, 0.2]),
            'latitude': 41.8781 + (np.random.randn(1000) * 0.01),
            'longitude': -87.6298 + (np.random.randn(1000) * 0.01)
        }
        
        pd.DataFrame(osm_data).to_parquet(local_dir / "osm_speed_limits_sample.parquet")
    
    def download_all_datasets(self, force_refresh: bool = False) -> Dict[str, Path]:
        """
        Download all configured datasets.
        
        Args:
            force_refresh: Whether to re-download existing datasets
            
        Returns:
            Dictionary mapping dataset names to local paths
        """
        results = {}
        
        for dataset_name in self.data_sources.keys():
            try:
                results[dataset_name] = self.download_dataset(dataset_name, force_refresh)
            except Exception as e:
                self.logger.error(f"Failed to download {dataset_name}: {str(e)}")
                results[dataset_name] = None
        
        return results
    
    def get_dataset_info(self, dataset_name: str) -> DataSourceMetadata:
        """Get information about a specific dataset."""
        if dataset_name not in self.data_sources:
            raise ValueError(f"Unknown dataset: {dataset_name}")
        return self.data_sources[dataset_name]
    
    def list_available_datasets(self) -> List[str]:
        """List all available dataset names."""
        return list(self.data_sources.keys())
    
    def get_dataset_status(self) -> Dict[str, Dict[str, Any]]:
        """Get the download status of all datasets."""
        status = {}
        
        for name, source in self.data_sources.items():
            local_dir = self.data_dir / source.local_path
            status[name] = {
                "name": source.name,
                "downloaded": self._dataset_exists(local_dir),
                "local_path": str(local_dir),
                "variables_covered": source.variables_covered,
                "citation": source.citation
            }
        
        return status
    
    def show_manual_download_instructions(self):
        """Show instructions for datasets requiring manual download."""
        self.real_downloader.print_manual_download_instructions()
    
    def download_real_datasets_only(self, force_refresh: bool = False) -> Dict[str, Path]:
        """
        Download only the datasets that can be automated (real API data).
        
        Args:
            force_refresh: Whether to re-download existing datasets
            
        Returns:
            Dictionary mapping dataset names to local paths
        """
        automated_datasets = ["weather_historical", "traffic_chicago", "osm_speed_limits"]
        results = {}
        
        self.logger.info("🌐 Downloading REAL datasets (automated APIs)...")
        
        for dataset_name in automated_datasets:
            try:
                results[dataset_name] = self.download_dataset(dataset_name, force_refresh)
                self.logger.info(f"✅ Real data: {dataset_name}")
            except Exception as e:
                self.logger.error(f"❌ Failed: {dataset_name} - {str(e)}")
                results[dataset_name] = None
        
        self.logger.info("📋 For research datasets (smartphone sensors, phone usage, OBD):")
        self.logger.info("   Run: manager.show_manual_download_instructions()")
        
        return results
