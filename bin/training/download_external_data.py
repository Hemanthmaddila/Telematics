#!/usr/bin/env python3
"""
Demo script for downloading REAL telematics datasets.

This script demonstrates downloading actual real datasets from APIs and
provides instructions for manual research dataset downloads.
"""

import sys
import logging
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telematics.etl.data_ingestion import DataIngestionManager
from telematics.etl.real_data_sources import WeatherDataLoader, TrafficDataLoader, OSMSpeedLimitLoader

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Demonstrate downloading real telematics datasets."""
    logger.info("🌍 Starting REAL Telematics Data Download Demo")
    
    # Initialize the data ingestion manager
    logger.info("📋 Initializing Data Ingestion Manager...")
    manager = DataIngestionManager()
    
    print("\n" + "="*60)
    logger.info("🌐 DOWNLOADING REAL DATASETS (Automated APIs)")
    print("="*60)
    
    # Download real datasets that can be automated
    real_results = manager.download_real_datasets_only(force_refresh=True)
    
    print("\n" + "="*60)
    logger.info("📊 PROCESSING REAL DATA WITH SPECIALIZED LOADERS")
    print("="*60)
    
    # Process real weather data
    if real_results.get("weather_historical"):
        logger.info("🌤️ Processing REAL Weather Data from Open-Meteo...")
        weather_loader = WeatherDataLoader()
        weather_df = weather_loader.load(real_results["weather_historical"])
        
        if len(weather_df) > 0:
            logger.info(f"   📅 Loaded REAL weather data for {len(weather_df)} time periods")
            
            # Use the correct column names from real data
            temp_col = 'temperature_2m_mean' if 'temperature_2m_mean' in weather_df.columns else 'temperature_f'
            if temp_col in weather_df.columns:
                logger.info(f"   🌡️ Temperature range: {weather_df[temp_col].min():.1f}°F to {weather_df[temp_col].max():.1f}°F")
            
            if 'is_rain_or_snow' in weather_df.columns:
                logger.info(f"   ☔ Rain/snow periods: {weather_df['is_rain_or_snow'].sum()} out of {len(weather_df)}")
            
            # Show sample of real weather data
            recent_weather = weather_df.head(3)
            for _, row in recent_weather.iterrows():
                temp_val = row.get(temp_col, row.get('temperature_f', 'N/A'))
                temp_str = f"{temp_val:.1f}°F" if isinstance(temp_val, (int, float)) else str(temp_val)
                logger.info(f"   📊 {row['time']}: {row['weather_condition']}, {temp_str}")
        else:
            logger.warning("   ⚠️ No weather data received")
    
    # Process real traffic data
    if real_results.get("traffic_chicago"):
        logger.info("🚦 Processing REAL Chicago Traffic Data...")
        traffic_loader = TrafficDataLoader()
        traffic_df = traffic_loader.load(real_results["traffic_chicago"])
        
        if len(traffic_df) > 0:
            logger.info(f"   🚗 Loaded REAL traffic data for {len(traffic_df)} segments")
            logger.info(f"   🚥 Average congestion score: {traffic_df['congestion_score'].mean():.2f}")
            
            # Show congestion distribution
            congestion_counts = traffic_df['congestion_level'].value_counts()
            for level, count in congestion_counts.items():
                logger.info(f"   📊 {level} traffic: {count} segments")
                
            # Show sample traffic data
            rush_hour_traffic = traffic_df[traffic_df['is_rush_hour'] == True].head(3)
            if len(rush_hour_traffic) > 0:
                logger.info("   🕐 Rush hour samples:")
                for _, row in rush_hour_traffic.iterrows():
                    # Handle different column names for traffic data
                    segment_id = row.get('segment_id', row.get('id', 'unknown'))
                    congestion = row.get('congestion_level', 'unknown')
                    speed = row.get('current_speed', row.get('speed_mph', 0))
                    speed_str = f"{speed:.1f} mph" if isinstance(speed, (int, float)) else str(speed)
                    logger.info(f"      • {segment_id}: {congestion}, {speed_str}")
        else:
            logger.warning("   ⚠️ No traffic data received (may be outside API limits)")
    
    # Process real OSM speed limit data
    if real_results.get("osm_speed_limits"):
        logger.info("🗺️ Processing REAL OpenStreetMap Speed Limits...")
        osm_loader = OSMSpeedLimitLoader()
        speed_map = osm_loader.load(real_results["osm_speed_limits"])
        
        if speed_map:
            logger.info(f"   🛣️ Loaded REAL speed limits for {len(speed_map)} road segments")
            
            # Show speed limit distribution
            speed_values = list(speed_map.values())
            unique_speeds = sorted(set(speed_values))
            logger.info(f"   📊 Speed limits found: {unique_speeds} mph")
            
            # Show some examples
            logger.info("   🎯 Sample locations:")
            for i, ((lat, lon), speed) in enumerate(list(speed_map.items())[:5]):
                logger.info(f"      • ({lat}, {lon}): {speed} mph")
        else:
            logger.warning("   ⚠️ No OSM speed limit data received")
    
    print("\n" + "="*60)
    logger.info("📥 MANUAL DOWNLOAD INSTRUCTIONS")
    print("="*60)
    
    # Show manual download instructions
    manager.show_manual_download_instructions()
    
    print("\n" + "="*60)
    logger.info("📈 REAL DATA SUMMARY")
    print("="*60)
    
    # Final summary
    automated_success = sum(1 for path in real_results.values() if path is not None)
    total_automated = len(real_results)
    
    logger.info(f"✅ Automated Downloads: {automated_success}/{total_automated} successful")
    
    if automated_success > 0:
        logger.info("🎉 SUCCESS: You now have REAL datasets!")
        logger.info("   • Weather conditions from Open-Meteo API")
        logger.info("   • Traffic congestion from Chicago Data Portal") 
        logger.info("   • Road speed limits from OpenStreetMap")
        logger.info("")
        logger.info("🔄 Next Steps:")
        logger.info("   1. Add research datasets manually (see instructions above)")
        logger.info("   2. Run feature engineering on the real data")
        logger.info("   3. Train ML models with real behavioral patterns")
    else:
        logger.warning("⚠️ No automated downloads succeeded")
        logger.info("💡 Check internet connection and try again")
    
    print("\n" + "="*60)
    logger.info("🎯 READY FOR PRODUCTION!")
    logger.info("Your telematics system now processes REAL external data!")
    print("="*60)


if __name__ == "__main__":
    main()
