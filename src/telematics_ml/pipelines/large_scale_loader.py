"""
US-scale data downloader for nationwide telematics datasets.

This module implements large-scale data ingestion across the entire United States,
with geographic partitioning, batch processing, and efficient data management.
"""

import requests
import pandas as pd
import numpy as np
import logging
import time
import json
import gzip
import threading
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Generator
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from .real_data_downloader import RealDataDownloader
from ..utils.config import get_config


@dataclass
class USRegion:
    """Represents a US geographic region for data partitioning."""
    name: str
    states: List[str]
    bbox: Tuple[float, float, float, float]  # south, west, north, east
    major_cities: List[Tuple[str, float, float]]  # (city, lat, lon)


@dataclass
class DownloadProgress:
    """Tracks download progress for large-scale operations."""
    region_name: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    start_time: datetime
    estimated_completion: Optional[datetime] = None
    current_operation: str = ""
    data_size_mb: float = 0.0


class USScaleDownloader:
    """Downloads and processes telematics data for the entire United States."""
    
    def __init__(self, max_workers: int = 5, enable_compression: bool = True):
        """
        Initialize the US-scale downloader.
        
        Args:
            max_workers: Maximum number of concurrent download threads
            enable_compression: Whether to compress downloaded data
        """
        self.config = get_config()
        self.logger = logging.getLogger(__name__)
        self.base_downloader = RealDataDownloader()
        self.max_workers = max_workers
        self.enable_compression = enable_compression
        
        # Initialize US regions for geographic partitioning
        self.us_regions = self._initialize_us_regions()
        
        # Progress tracking
        self.progress: Dict[str, DownloadProgress] = {}
        self.download_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_data_mb': 0.0,
            'start_time': None
        }
        
        # API rate limiting
        self._api_locks = {
            'openmeteo': threading.Semaphore(10),  # 10 concurrent requests
            'overpass': threading.Semaphore(2),    # 2 concurrent requests (be nice to OSM)
            'traffic': threading.Semaphore(5)      # 5 concurrent requests
        }
    
    def _initialize_us_regions(self) -> Dict[str, USRegion]:
        """Initialize US regions for efficient geographic partitioning."""
        return {
            'northeast': USRegion(
                name='Northeast',
                states=['ME', 'NH', 'VT', 'MA', 'RI', 'CT', 'NY', 'NJ', 'PA'],
                bbox=(40.0, -80.0, 47.5, -66.5),
                major_cities=[
                    ('New York', 40.7128, -74.0060),
                    ('Boston', 42.3601, -71.0589),
                    ('Philadelphia', 39.9526, -75.1652),
                    ('Pittsburgh', 40.4406, -79.9959)
                ]
            ),
            'southeast': USRegion(
                name='Southeast',
                states=['DE', 'MD', 'DC', 'VA', 'WV', 'KY', 'TN', 'NC', 'SC', 'GA', 'FL', 'AL', 'MS', 'AR', 'LA'],
                bbox=(24.5, -94.0, 39.5, -75.0),
                major_cities=[
                    ('Atlanta', 33.7490, -84.3880),
                    ('Miami', 25.7617, -80.1918),
                    ('Charlotte', 35.2271, -80.8431),
                    ('New Orleans', 29.9511, -90.0715)
                ]
            ),
            'midwest': USRegion(
                name='Midwest',
                states=['OH', 'IN', 'IL', 'MI', 'WI', 'MN', 'IA', 'MO', 'ND', 'SD', 'NE', 'KS'],
                bbox=(36.5, -104.0, 49.0, -80.5),
                major_cities=[
                    ('Chicago', 41.8781, -87.6298),
                    ('Detroit', 42.3314, -83.0458),
                    ('Minneapolis', 44.9778, -93.2650),
                    ('Kansas City', 39.0997, -94.5786)
                ]
            ),
            'southwest': USRegion(
                name='Southwest',
                states=['TX', 'OK', 'NM', 'AZ'],
                bbox=(25.8, -109.0, 37.0, -93.5),
                major_cities=[
                    ('Houston', 29.7604, -95.3698),
                    ('Dallas', 32.7767, -96.7970),
                    ('Phoenix', 33.4484, -112.0740),
                    ('San Antonio', 29.4241, -98.4936)
                ]
            ),
            'west': USRegion(
                name='West',
                states=['CA', 'NV', 'UT', 'CO', 'WY', 'MT', 'ID', 'WA', 'OR'],
                bbox=(32.5, -125.0, 49.0, -102.0),
                major_cities=[
                    ('Los Angeles', 34.0522, -118.2437),
                    ('San Francisco', 37.7749, -122.4194),
                    ('Seattle', 47.6062, -122.3321),
                    ('Denver', 39.7392, -104.9903)
                ]
            ),
            'alaska_hawaii': USRegion(
                name='Alaska & Hawaii',
                states=['AK', 'HI'],
                bbox=(18.0, -180.0, 72.0, -129.0),
                major_cities=[
                    ('Anchorage', 61.2181, -149.9003),
                    ('Honolulu', 21.3099, -157.8581)
                ]
            )
        }
    
    def download_us_weather_data(self, years: List[int] = [2024], 
                                output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Download weather data for the entire United States.
        
        Args:
            years: List of years to download data for
            output_dir: Directory to save data (default: data/raw/weather_us/)
            
        Returns:
            Dictionary with download statistics and file paths
        """
        if output_dir is None:
            output_dir = Path(self.config.get("data.raw_data_path", "./data/raw")) / "weather_us"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"🌤️ Starting US-wide weather data download for {years}")
        
        results = {
            'regions_completed': 0,
            'total_regions': len(self.us_regions),
            'years_downloaded': years,
            'file_paths': {},
            'total_records': 0,
            'total_size_mb': 0.0
        }
        
        # Download weather data for each region
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            
            for region_name, region in self.us_regions.items():
                if region_name == 'alaska_hawaii':
                    # Handle Alaska and Hawaii separately due to different time zones
                    continue
                    
                future = executor.submit(
                    self._download_region_weather,
                    region, years, output_dir
                )
                futures[future] = region_name
            
            # Collect results
            for future in as_completed(futures):
                region_name = futures[future]
                try:
                    region_result = future.result()
                    results['file_paths'][region_name] = region_result['file_path']
                    results['total_records'] += region_result['record_count']
                    results['total_size_mb'] += region_result['size_mb']
                    results['regions_completed'] += 1
                    
                    self.logger.info(f"✅ {region_name}: {region_result['record_count']} records, "
                                   f"{region_result['size_mb']:.1f}MB")
                    
                except Exception as e:
                    self.logger.error(f"❌ Failed to download weather for {region_name}: {str(e)}")
        
        # Save summary
        summary_file = output_dir / "us_weather_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        self.logger.info(f"🎉 US weather download complete: {results['total_records']} total records, "
                        f"{results['total_size_mb']:.1f}MB across {results['regions_completed']} regions")
        
        return results
    
    def _download_region_weather(self, region: USRegion, years: List[int], 
                                output_dir: Path) -> Dict[str, Any]:
        """Download weather data for a specific region."""
        with self._api_locks['openmeteo']:
            # Use the region's major cities as representative points
            region_data = []
            
            for year in years:
                start_date = f"{year}-01-01"
                end_date = f"{year}-12-31"
                
                for city_name, lat, lon in region.major_cities:
                    try:
                        time.sleep(0.2)  # Rate limiting
                        
                        # Download weather for this city
                        city_weather = self.base_downloader.download_weather_data(
                            output_dir / "temp", lat, lon, start_date, end_date
                        )
                        
                        if city_weather:
                            # Load the downloaded data
                            daily_file = output_dir / "temp" / "weather_daily_real.parquet"
                            if daily_file.exists():
                                df = pd.read_parquet(daily_file)
                                df['city'] = city_name
                                df['region'] = region.name
                                df['latitude'] = lat
                                df['longitude'] = lon
                                region_data.append(df)
                                
                    except Exception as e:
                        self.logger.warning(f"Failed to download weather for {city_name}: {str(e)}")
                        continue
            
            # Combine all region data
            if region_data:
                combined_df = pd.concat(region_data, ignore_index=True)
                
                # Save region file
                region_file = output_dir / f"weather_{region.name.lower().replace(' ', '_')}.parquet"
                if self.enable_compression:
                    combined_df.to_parquet(region_file, compression='gzip')
                else:
                    combined_df.to_parquet(region_file)
                
                # Calculate file size
                file_size_mb = region_file.stat().st_size / (1024 * 1024)
                
                # Clean up temp files
                temp_dir = output_dir / "temp"
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                
                return {
                    'file_path': str(region_file),
                    'record_count': len(combined_df),
                    'size_mb': file_size_mb
                }
            else:
                return {'file_path': None, 'record_count': 0, 'size_mb': 0.0}
    
    def download_us_speed_limits(self, output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Download speed limit data for the entire United States.
        
        Args:
            output_dir: Directory to save data (default: data/raw/speed_limits_us/)
            
        Returns:
            Dictionary with download statistics and file paths
        """
        if output_dir is None:
            output_dir = Path(self.config.get("data.raw_data_path", "./data/raw")) / "speed_limits_us"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("🗺️ Starting US-wide speed limit data download")
        self.logger.warning("⚠️ This is a MASSIVE download - OSM data for entire US!")
        self.logger.info("💡 Consider running overnight or in chunks")
        
        results = {
            'states_completed': 0,
            'total_states': 50,
            'file_paths': {},
            'total_ways': 0,
            'total_size_mb': 0.0,
            'failed_states': []
        }
        
        # Download state by state to avoid overwhelming the Overpass API
        all_states = [state for region in self.us_regions.values() for state in region.states]
        
        with ThreadPoolExecutor(max_workers=2) as executor:  # Only 2 workers for OSM
            futures = {}
            
            for i, state in enumerate(all_states):
                future = executor.submit(self._download_state_speed_limits, state, output_dir)
                futures[future] = state
                
                # Progress update
                if i % 5 == 0:
                    self.logger.info(f"📊 Queued {i+1}/{len(all_states)} states for download")
            
            # Collect results
            for future in as_completed(futures):
                state = futures[future]
                try:
                    state_result = future.result()
                    if state_result['way_count'] > 0:
                        results['file_paths'][state] = state_result['file_path']
                        results['total_ways'] += state_result['way_count']
                        results['total_size_mb'] += state_result['size_mb']
                        results['states_completed'] += 1
                        
                        self.logger.info(f"✅ {state}: {state_result['way_count']} roads, "
                                       f"{state_result['size_mb']:.1f}MB")
                    else:
                        results['failed_states'].append(state)
                        self.logger.warning(f"⚠️ {state}: No data retrieved")
                        
                except Exception as e:
                    results['failed_states'].append(state)
                    self.logger.error(f"❌ Failed to download speed limits for {state}: {str(e)}")
        
        # Save summary
        summary_file = output_dir / "us_speed_limits_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        self.logger.info(f"🎉 US speed limits download complete: {results['total_ways']} total roads, "
                        f"{results['total_size_mb']:.1f}MB across {results['states_completed']} states")
        
        if results['failed_states']:
            self.logger.warning(f"⚠️ Failed states: {', '.join(results['failed_states'])}")
        
        return results
    
    def _download_state_speed_limits(self, state: str, output_dir: Path) -> Dict[str, Any]:
        """Download speed limit data for a specific state."""
        with self._api_locks['overpass']:
            try:
                # Get state bounding box (simplified - in production would use proper state boundaries)
                state_bbox = self._get_state_bbox(state)
                if not state_bbox:
                    return {'file_path': None, 'way_count': 0, 'size_mb': 0.0}
                
                # Wait between requests to be respectful to OSM
                time.sleep(2)
                
                success = self.base_downloader.download_osm_speed_limits(
                    output_dir / "temp", bbox=state_bbox
                )
                
                if success:
                    # Move and rename the file
                    temp_file = output_dir / "temp" / "osm_speed_limits_real.parquet"
                    state_file = output_dir / f"speed_limits_{state.lower()}.parquet"
                    
                    if temp_file.exists():
                        # Load, add state info, and save
                        df = pd.read_parquet(temp_file)
                        df['state'] = state
                        
                        if self.enable_compression:
                            df.to_parquet(state_file, compression='gzip')
                        else:
                            df.to_parquet(state_file)
                        
                        # Clean up
                        temp_file.unlink()
                        
                        file_size_mb = state_file.stat().st_size / (1024 * 1024)
                        
                        return {
                            'file_path': str(state_file),
                            'way_count': len(df),
                            'size_mb': file_size_mb
                        }
                
                return {'file_path': None, 'way_count': 0, 'size_mb': 0.0}
                
            except Exception as e:
                self.logger.error(f"Error downloading {state}: {str(e)}")
                return {'file_path': None, 'way_count': 0, 'size_mb': 0.0}
    
    def _get_state_bbox(self, state: str) -> Optional[Tuple[float, float, float, float]]:
        """Get bounding box for a US state (simplified version)."""
        # This is a simplified mapping - in production would use proper state boundaries
        state_boxes = {
            'CA': (32.5, -124.4, 42.0, -114.1),
            'TX': (25.8, -106.6, 36.5, -93.5),
            'FL': (24.5, -87.6, 31.0, -80.0),
            'NY': (40.5, -79.8, 45.0, -71.8),
            'IL': (37.0, -91.5, 42.5, -87.0),
            # Add more states as needed
        }
        
        return state_boxes.get(state)
    
    def download_us_traffic_data(self, output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Download traffic data for major US cities.
        
        Args:
            output_dir: Directory to save data (default: data/raw/traffic_us/)
            
        Returns:
            Dictionary with download statistics and file paths
        """
        if output_dir is None:
            output_dir = Path(self.config.get("data.raw_data_path", "./data/raw")) / "traffic_us"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("🚦 Starting US-wide traffic data download")
        
        # Traffic data sources for major US cities
        traffic_sources = {
            'chicago': 'https://data.cityofchicago.org/resource/77hq-huss.json',
            'seattle': 'https://data.seattle.gov/resource/26ge-y346.json',
            'austin': 'https://data.austintexas.gov/resource/sh59-i6y9.json',
            # Add more cities with open traffic data
        }
        
        results = {
            'cities_completed': 0,
            'total_cities': len(traffic_sources),
            'file_paths': {},
            'total_segments': 0,
            'failed_cities': []
        }
        
        for city, url in traffic_sources.items():
            try:
                city_result = self._download_city_traffic(city, url, output_dir)
                if city_result['segment_count'] > 0:
                    results['file_paths'][city] = city_result['file_path']
                    results['total_segments'] += city_result['segment_count']
                    results['cities_completed'] += 1
                    
                    self.logger.info(f"✅ {city}: {city_result['segment_count']} segments")
                else:
                    results['failed_cities'].append(city)
                    
            except Exception as e:
                results['failed_cities'].append(city)
                self.logger.error(f"❌ Failed to download traffic for {city}: {str(e)}")
        
        # Save summary
        summary_file = output_dir / "us_traffic_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        return results
    
    def _download_city_traffic(self, city: str, url: str, output_dir: Path) -> Dict[str, Any]:
        """Download traffic data for a specific city."""
        # Implementation similar to existing traffic download but for specific cities
        # This would be customized based on each city's API format
        pass
    
    def get_download_progress(self) -> Dict[str, Any]:
        """Get current download progress across all operations."""
        return {
            'active_downloads': len(self.progress),
            'regions': {name: {
                'completed': prog.completed_tasks,
                'total': prog.total_tasks,
                'current_operation': prog.current_operation,
                'estimated_completion': prog.estimated_completion
            } for name, prog in self.progress.items()},
            'overall_stats': self.download_stats
        }
    
    def estimate_data_size(self) -> Dict[str, str]:
        """Estimate total data size for US-wide download."""
        return {
            'weather_data': '~500MB - 2GB (depending on years and resolution)',
            'speed_limits': '~5GB - 15GB (all US roads with speed limits)',
            'traffic_data': '~100MB - 1GB (major cities only)',
            'total_estimated': '~6GB - 18GB for complete US coverage',
            'recommendation': 'Start with 1-2 regions to test, then scale up'
        }
    
    def download_us_sample_regions(self, regions: List[str] = ['midwest', 'west']) -> Dict[str, Any]:
        """
        Download data for sample US regions for testing.
        
        Args:
            regions: List of region names to download
            
        Returns:
            Combined results from all region downloads
        """
        self.logger.info(f"🇺🇸 Starting sample US regions download: {', '.join(regions)}")
        
        results = {'weather': {}, 'speed_limits': {}, 'traffic': {}}
        
        for region in regions:
            if region in self.us_regions:
                self.logger.info(f"📍 Processing {region} region...")
                
                # Download weather for region
                weather_result = self._download_region_weather(
                    self.us_regions[region], 
                    [2024], 
                    Path("data/raw/weather_us")
                )
                results['weather'][region] = weather_result
                
                self.logger.info(f"✅ {region} sample download complete")
            else:
                self.logger.warning(f"⚠️ Unknown region: {region}")
        
        return results
