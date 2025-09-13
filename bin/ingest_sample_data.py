#!/usr/bin/env python3
"""
Demonstration script for the telematics data ingestion system.

This script shows how to download and process all real datasets
according to the data sourcing plan.
"""

import sys
import logging
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telematics.etl.data_ingestion import DataIngestionManager
from telematics.etl.real_data_sources import (
    SmartphoneSensorLoader, PhoneUsageLoader, OSMSpeedLimitLoader,
    WeatherDataLoader, TrafficDataLoader, OBDDataLoader
)
from telematics.utils.config import get_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Demonstrate the complete data ingestion pipeline."""
    logger.info("🚀 Starting Telematics Data Ingestion Demo")
    
    # Initialize the data ingestion manager
    logger.info("📋 Initializing Data Ingestion Manager...")
    ingestion_manager = DataIngestionManager()
    
    # Show available datasets
    logger.info("📊 Available Datasets:")
    for dataset_name in ingestion_manager.list_available_datasets():
        info = ingestion_manager.get_dataset_info(dataset_name)
        logger.info(f"  • {info.name}")
        logger.info(f"    Variables: {', '.join(info.variables_covered)}")
        logger.info(f"    Citation: {info.citation}")
        print()
    
    # Download all datasets
    logger.info("⬇️  Downloading All Datasets...")
    download_results = ingestion_manager.download_all_datasets()
    
    for dataset_name, path in download_results.items():
        if path:
            logger.info(f"✅ {dataset_name}: Downloaded to {path}")
        else:
            logger.error(f"❌ {dataset_name}: Download failed")
    
    print("\n" + "="*60)
    logger.info("🔄 Processing Real Datasets with Specialized Loaders...")
    
    # Process smartphone sensor data
    if download_results.get("smartphone_sensors"):
        logger.info("📱 Processing Smartphone Sensor Data...")
        sensor_loader = SmartphoneSensorLoader()
        gps_points, imu_readings = sensor_loader.load(download_results["smartphone_sensors"])
        logger.info(f"   📍 Loaded {len(gps_points)} GPS points")
        logger.info(f"   📊 Loaded {len(imu_readings)} IMU readings")
    
    # Process phone usage data
    if download_results.get("phone_usage"):
        logger.info("📞 Processing Phone Usage Data...")
        usage_loader = PhoneUsageLoader()
        usage_patterns = usage_loader.load(download_results["phone_usage"])
        logger.info(f"   📈 Average screen-on percentage: {usage_patterns.get('avg_screen_on_pct', 0):.2%}")
        logger.info(f"   📱 Average handheld events per hour: {usage_patterns.get('avg_handheld_events_per_hour', 0):.1f}")
    
    # Process OSM speed limit data
    if download_results.get("osm_speed_limits"):
        logger.info("🗺️  Processing OpenStreetMap Speed Limits...")
        osm_loader = OSMSpeedLimitLoader()
        speed_map = osm_loader.load(download_results["osm_speed_limits"])
        logger.info(f"   🛣️  Loaded speed limits for {len(speed_map)} locations")
        
        # Test speed limit lookup
        sample_lat, sample_lon = 41.8781, -87.6298  # Chicago
        speed_limit = osm_loader.get_speed_limit(sample_lat, sample_lon)
        if speed_limit:
            logger.info(f"   📍 Speed limit at ({sample_lat}, {sample_lon}): {speed_limit} mph")
    
    # Process weather data
    if download_results.get("weather_historical"):
        logger.info("🌤️  Processing Weather Data...")
        weather_loader = WeatherDataLoader()
        weather_df = weather_loader.load(download_results["weather_historical"])
        logger.info(f"   📅 Loaded weather data for {len(weather_df)} days")
        
        # Test weather lookup
        from datetime import datetime
        test_date = datetime(2024, 1, 15)
        weather_info = weather_loader.get_weather_for_date(test_date)
        if weather_info:
            logger.info(f"   🌡️  Weather on {test_date.date()}: {weather_info['weather_condition']}, {weather_info['temperature_f']:.1f}°F")
    
    # Process traffic data
    if download_results.get("traffic_chicago"):
        logger.info("🚦 Processing Traffic Data...")
        traffic_loader = TrafficDataLoader()
        traffic_df = traffic_loader.load(download_results["traffic_chicago"])
        logger.info(f"   🚗 Loaded traffic data for {len(traffic_df)} segments")
        
        # Test traffic lookup
        test_time = datetime(2024, 1, 15, 8, 30)  # Morning rush hour
        traffic_info = traffic_loader.get_traffic_for_location_time(41.8781, -87.6298, test_time)
        if traffic_info:
            logger.info(f"   🚥 Traffic at rush hour: {traffic_info['congestion_level']}, {traffic_info['speed_mph']:.1f} mph")
    
    # Process OBD data
    if download_results.get("obd_vehicle_data"):
        logger.info("🔧 Processing OBD-II Vehicle Data...")
        obd_loader = OBDDataLoader()
        obd_df = obd_loader.load(download_results["obd_vehicle_data"])
        logger.info(f"   🚙 Loaded OBD data for {len(obd_df)} readings")
        
        # Test vehicle summary
        start_time = datetime(2024, 1, 1, 8, 0)
        end_time = datetime(2024, 1, 1, 9, 0)
        vehicle_summary = obd_loader.get_vehicle_summary(start_time, end_time)
        if vehicle_summary:
            logger.info(f"   ⚙️  Average RPM: {vehicle_summary.get('avg_engine_rpm', 0):.0f}")
            logger.info(f"   ⚠️  Has DTC codes: {vehicle_summary.get('has_dtc_codes', False)}")
    
    # Show final status
    print("\n" + "="*60)
    logger.info("📈 Final Dataset Status:")
    status = ingestion_manager.get_dataset_status()
    
    for dataset_name, info in status.items():
        status_icon = "✅" if info["downloaded"] else "❌"
        logger.info(f"{status_icon} {info['name']}")
        logger.info(f"   📂 Path: {info['local_path']}")
        logger.info(f"   📊 Variables: {', '.join(info['variables_covered'])}")
    
    print("\n" + "="*60)
    logger.info("🎉 Data Ingestion Demo Complete!")
    logger.info("📝 Summary:")
    logger.info("   • Real datasets downloaded and processed")
    logger.info("   • Specialized loaders tested for each data type")
    logger.info("   • Data ready for feature engineering and simulation")
    logger.info("   • Next step: Combine with simulated driver personas")


if __name__ == "__main__":
    main()
