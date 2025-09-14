#!/usr/bin/env python3
"""
Demo script for US-scale telematics data downloads.

This script demonstrates downloading real telematics datasets for the ENTIRE
United States, with options for regional testing and full-scale deployment.
"""

import sys
import logging
import time
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telematics.etl.us_scale_downloader import USScaleDownloader

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def show_data_estimates():
    """Show estimated data sizes for US-scale downloads."""
    downloader = USScaleDownloader()
    estimates = downloader.estimate_data_size()
    
    print("\n" + "="*60)
    print("📊 US-SCALE DATA SIZE ESTIMATES")
    print("="*60)
    
    for data_type, estimate in estimates.items():
        if data_type != 'recommendation':
            print(f"📈 {data_type.replace('_', ' ').title()}: {estimate}")
    
    print(f"\n💡 {estimates['recommendation']}")
    print("\n⚠️  WARNING: Full US download can take 2-6 hours and requires:")
    print("   • Stable internet connection")
    print("   • 20GB+ free disk space") 
    print("   • Respect for API rate limits")
    print("="*60)


def demo_sample_regions():
    """Demo download for sample US regions."""
    logger.info("🌎 Starting US Sample Regions Demo")
    
    downloader = USScaleDownloader(max_workers=3, enable_compression=True)
    
    # Show available regions
    print("\n📍 Available US Regions:")
    for region_name, region in downloader.us_regions.items():
        print(f"   • {region.name}: {', '.join(region.states[:5])}" + 
              ("..." if len(region.states) > 5 else ""))
        print(f"     Major cities: {', '.join([city[0] for city in region.major_cities])}")
    
    # Download sample regions
    print(f"\n🚀 Downloading weather data for Midwest and West regions...")
    print("💡 This will take 2-5 minutes and download ~50-100MB")
    
    start_time = time.time()
    
    try:
        results = downloader.download_us_sample_regions(['midwest', 'west'])
        
        elapsed_time = time.time() - start_time
        
        print(f"\n✅ Sample download completed in {elapsed_time:.1f} seconds!")
        
        # Show results
        for region, data in results['weather'].items():
            if data and data.get('record_count', 0) > 0:
                logger.info(f"📊 {region.title()}: {data['record_count']} weather records, "
                           f"{data['size_mb']:.1f}MB")
                logger.info(f"   📁 Saved to: {data['file_path']}")
            else:
                logger.warning(f"⚠️ {region.title()}: No data retrieved")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Sample download failed: {str(e)}")
        return False


def demo_full_us_weather():
    """Demo full US weather data download."""
    logger.warning("⚠️ FULL US WEATHER DOWNLOAD - This is a BIG operation!")
    
    response = input("\n🤔 Do you want to proceed with full US weather download? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        logger.info("📤 Skipping full US download")
        return
    
    logger.info("🌤️ Starting FULL US weather data download...")
    logger.info("📊 This will download weather for all major US cities for 2024")
    logger.info("⏱️ Expected time: 10-30 minutes")
    logger.info("💾 Expected size: 500MB - 2GB")
    
    downloader = USScaleDownloader(max_workers=5, enable_compression=True)
    
    start_time = time.time()
    
    try:
        results = downloader.download_us_weather_data(years=[2024])
        
        elapsed_time = time.time() - start_time
        
        logger.info(f"🎉 FULL US weather download completed in {elapsed_time/60:.1f} minutes!")
        logger.info(f"📊 Total: {results['total_records']} records, {results['total_size_mb']:.1f}MB")
        logger.info(f"🗺️ Regions completed: {results['regions_completed']}/{results['total_regions']}")
        
        # Show regional breakdown
        print("\n📍 Regional Breakdown:")
        for region, file_path in results['file_paths'].items():
            if file_path:
                file_size = Path(file_path).stat().st_size / (1024 * 1024)
                print(f"   ✅ {region.title()}: {file_size:.1f}MB")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Full US weather download failed: {str(e)}")
        return None


def demo_state_speed_limits():
    """Demo speed limit download for select states."""
    logger.info("🗺️ State Speed Limits Demo")
    
    print("\n💡 Speed limit downloads are VERY large!")
    print("   • California alone: ~500MB - 1GB")
    print("   • Full US: ~5GB - 15GB")
    print("   • Takes several hours for full US")
    
    response = input("\n🤔 Download speed limits for California (sample)? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        logger.info("📤 Skipping speed limit download")
        return
    
    logger.info("🛣️ Downloading California speed limits...")
    logger.warning("⚠️ This may take 5-15 minutes and download 500MB+")
    
    downloader = USScaleDownloader(max_workers=1, enable_compression=True)
    
    # For demo, we'll simulate a smaller download
    logger.info("🔧 For demo purposes, downloading a small subset...")
    
    try:
        # Use the base downloader for a small LA area sample
        bbox = (34.0, -118.5, 34.3, -118.1)  # Small LA area
        success = downloader.base_downloader.download_osm_speed_limits(
            Path("data/raw/speed_limits_us"), bbox=bbox
        )
        
        if success:
            logger.info("✅ Sample California speed limits downloaded!")
            logger.info("📁 Data saved to: data/raw/speed_limits_us/")
            
            # Show what a full state download would involve
            print(f"\n📊 Full California would include:")
            print(f"   • ~50,000-100,000 road segments")
            print(f"   • Speed limits for highways, arterials, local roads")
            print(f"   • 500MB - 1GB of compressed data")
            
        else:
            logger.warning("⚠️ Sample download had issues")
            
    except Exception as e:
        logger.error(f"❌ Speed limit demo failed: {str(e)}")


def show_progress_monitoring():
    """Demonstrate progress monitoring for large downloads."""
    logger.info("📊 Progress Monitoring Demo")
    
    downloader = USScaleDownloader(max_workers=3)
    
    print("\n🔍 In a real full-scale download, you would see:")
    print("   • Real-time progress updates")
    print("   • Estimated completion times")
    print("   • Data size tracking")
    print("   • Failed/retry handling")
    
    # Simulate progress display
    print(f"\n📈 Example Progress Display:")
    print(f"   🌤️ Weather: Northeast [████████░░] 80% (ETA: 5 min)")
    print(f"   🗺️ Speed Limits: California [██░░░░░░░░] 20% (ETA: 45 min)")
    print(f"   🚦 Traffic: 15/25 cities complete")
    print(f"   💾 Total downloaded: 2.3GB / ~8GB estimated")


def main():
    """Run the US-scale telematics data demo."""
    logger.info("🇺🇸 Starting US-Scale Telematics Data Demo")
    
    print("\n" + "="*60)
    print("🌎 US-SCALE TELEMATICS DATA PLATFORM")
    print("="*60)
    print("This demo shows how to download real telematics datasets")
    print("for the ENTIRE United States!")
    print("="*60)
    
    # Show data size estimates
    show_data_estimates()
    
    # Demo options
    while True:
        print(f"\n🎯 Demo Options:")
        print(f"   1. Sample Regions (Midwest + West) - RECOMMENDED")
        print(f"   2. Full US Weather Data - BIG DOWNLOAD")
        print(f"   3. State Speed Limits (CA sample) - VERY BIG")
        print(f"   4. Progress Monitoring Demo")
        print(f"   5. Exit")
        
        choice = input(f"\n🔢 Choose an option (1-5): ").strip()
        
        if choice == '1':
            success = demo_sample_regions()
            if success:
                print(f"\n🎉 Sample regions demo completed successfully!")
                print(f"💡 You now have real weather data for major US cities!")
        
        elif choice == '2':
            demo_full_us_weather()
        
        elif choice == '3':
            demo_state_speed_limits()
        
        elif choice == '4':
            show_progress_monitoring()
        
        elif choice == '5':
            break
        
        else:
            print(f"❌ Invalid choice. Please select 1-5.")
    
    print(f"\n🎯 US-Scale Demo Complete!")
    print(f"📊 Summary:")
    print(f"   • You've seen how to scale telematics data to entire US")
    print(f"   • Sample regional downloads work and are practical")
    print(f"   • Full US downloads require planning but are feasible")
    print(f"   • Your system can handle massive real-world datasets!")
    
    print(f"\n🚀 Next Steps:")
    print(f"   1. Run sample regional downloads for testing")
    print(f"   2. Plan full US downloads during off-peak hours")
    print(f"   3. Implement feature engineering on the real data")
    print(f"   4. Train ML models with nationwide patterns")
    
    print(f"\n🇺🇸 Ready for production-scale telematics!")


if __name__ == "__main__":
    main()
