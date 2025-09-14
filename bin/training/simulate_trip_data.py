#!/usr/bin/env python3
"""
Step 5: Generate Raw Trip Logs with Real API Integration

Execute blueprint Step 5 to create 18 months of driving history for all 1,000 drivers
with real-time contextual enrichment using actual weather and speed limit APIs.

WARNING: This is a substantial operation that will:
- Generate potentially millions of data points
- Make thousands of real API calls
- Take 30 minutes to several hours to complete
- Require 1-5GB of storage space
"""

import sys
import logging
import time
import json
import pickle
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telematics.simulation.trip_simulator import TripSimulator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Step5Orchestrator:
    """Orchestrates the complete Step 5 trip generation process."""
    
    def __init__(self, use_real_apis: bool = True, max_workers: int = 3,
                 batch_size: int = 50):
        """
        Initialize the Step 5 orchestrator.
        
        Args:
            use_real_apis: Whether to use real APIs for contextual data
            max_workers: Number of concurrent driver processing threads
            batch_size: Number of drivers to process in each batch
        """
        self.use_real_apis = use_real_apis
        self.max_workers = max_workers
        self.batch_size = batch_size
        
        # Initialize trip simulator
        self.simulator = TripSimulator(
            use_real_apis=use_real_apis,
            api_rate_limit_delay=0.2  # 200ms between API calls
        )
        
        # Progress tracking
        self.start_time = None
        self.stats = {
            'drivers_processed': 0,
            'total_drivers': 0,
            'trips_generated': 0,
            'api_calls_made': 0,
            'total_data_points': 0,
            'storage_used_mb': 0.0
        }
    
    def execute_step_5(self, num_drivers: int = None, months: int = 18) -> Dict[str, Any]:
        """
        Execute the complete Step 5 process.
        
        Args:
            num_drivers: Number of drivers to process (None = all drivers)
            months: Number of months of history to generate
            
        Returns:
            Dictionary with execution results and statistics
        """
        logger.info("🚀 Starting Step 5: Raw Trip Log Generation with Real APIs")
        
        self.start_time = time.time()
        
        # Load driver portfolio
        drivers_df = self._load_driver_portfolio()
        
        if num_drivers:
            drivers_df = drivers_df.head(num_drivers)
            logger.info(f"🎯 Processing subset: {num_drivers} drivers")
        
        self.stats['total_drivers'] = len(drivers_df)
        
        # Show estimated scope
        self._show_operation_scope(len(drivers_df), months)
        
        # Get user confirmation for large operations
        if len(drivers_df) > 100 and not self._get_user_confirmation():
            logger.info("❌ Operation cancelled by user")
            return {'status': 'cancelled'}
        
        # Process drivers in batches
        results = self._process_drivers_in_batches(drivers_df, months)
        
        # Generate final summary
        summary = self._generate_final_summary()
        
        logger.info("🎉 Step 5 Complete! Trip generation finished.")
        return summary
    
    def _load_driver_portfolio(self) -> pd.DataFrame:
        """Load the driver portfolio from Step 4."""
        drivers_file = Path("data/simulated/drivers.csv")
        
        if not drivers_file.exists():
            raise FileNotFoundError(
                "❌ drivers.csv not found! Please run Step 4 first to generate the driver portfolio."
            )
        
        drivers_df = pd.read_csv(drivers_file)
        logger.info(f"📄 Loaded {len(drivers_df)} drivers from portfolio")
        
        return drivers_df
    
    def _show_operation_scope(self, num_drivers: int, months: int):
        """Show the estimated scope of the operation."""
        # Estimates
        avg_trips_per_driver = 45 * months  # Average trips per month
        total_trips = num_drivers * avg_trips_per_driver
        
        avg_api_calls_per_trip = 10  # Contextual enrichment calls
        total_api_calls = total_trips * avg_api_calls_per_trip if self.use_real_apis else 0
        
        # Storage estimates
        estimated_size_mb = total_trips * 0.5  # ~500KB per trip
        
        print(f"\n📊 Operation Scope Estimates:")
        print(f"   👥 Drivers: {num_drivers:,}")
        print(f"   📅 Months: {months}")
        print(f"   🚗 Total trips: {total_trips:,}")
        print(f"   🌐 API calls: {total_api_calls:,}" if self.use_real_apis else "   🌐 API calls: 0 (simulation mode)")
        print(f"   💾 Storage: ~{estimated_size_mb:,.0f} MB")
        print(f"   ⏱️  Estimated time: {self._estimate_completion_time(num_drivers)} minutes")
        
        if self.use_real_apis:
            print(f"   🌤️  Real weather data: ✅ Open-Meteo API")
            print(f"   🗺️  Real speed limits: ✅ OpenStreetMap API")
        else:
            print(f"   🤖 Simulated APIs: ✅ No external calls")
    
    def _estimate_completion_time(self, num_drivers: int) -> int:
        """Estimate completion time in minutes."""
        if self.use_real_apis:
            # With API calls: ~30 seconds per driver
            return int((num_drivers * 30) / 60)
        else:
            # Simulation only: ~5 seconds per driver
            return int((num_drivers * 5) / 60)
    
    def _get_user_confirmation(self) -> bool:
        """Get user confirmation for large operations."""
        print(f"\n⚠️  This is a substantial operation!")
        
        if self.use_real_apis:
            print(f"   • Will make thousands of real API calls")
            print(f"   • Please ensure stable internet connection")
            print(f"   • Respects rate limits but may take time")
        
        response = input(f"\n🤔 Continue with Step 5 generation? (y/N): ")
        return response.lower() in ['y', 'yes']
    
    def _process_drivers_in_batches(self, drivers_df: pd.DataFrame, 
                                  months: int) -> Dict[str, Any]:
        """Process drivers in batches for efficient memory usage."""
        total_drivers = len(drivers_df)
        batches = [drivers_df[i:i + self.batch_size] 
                  for i in range(0, total_drivers, self.batch_size)]
        
        logger.info(f"🔄 Processing {total_drivers} drivers in {len(batches)} batches")
        
        all_results = {}
        
        for batch_num, batch_df in enumerate(batches, 1):
            logger.info(f"📦 Processing batch {batch_num}/{len(batches)} "
                       f"({len(batch_df)} drivers)")
            
            batch_results = self._process_driver_batch(batch_df, months, batch_num)
            all_results[f'batch_{batch_num}'] = batch_results
            
            # Progress update
            self.stats['drivers_processed'] += len(batch_df)
            progress_pct = (self.stats['drivers_processed'] / total_drivers) * 100
            
            logger.info(f"✅ Batch {batch_num} complete. "
                       f"Overall progress: {progress_pct:.1f}%")
            
            # Memory management
            if batch_num % 5 == 0:
                logger.info("🧹 Running garbage collection...")
                import gc
                gc.collect()
        
        return all_results
    
    def _process_driver_batch(self, batch_df: pd.DataFrame, months: int, 
                            batch_num: int) -> Dict[str, Any]:
        """Process a single batch of drivers."""
        batch_results = {
            'drivers_in_batch': len(batch_df),
            'trips_generated': 0,
            'api_calls_made': 0,
            'file_paths': []
        }
        
        # Process each driver in the batch
        for _, driver_row in batch_df.iterrows():
            try:
                driver_data = driver_row.to_dict()
                driver_id = driver_data['driver_id']
                
                logger.debug(f"   🚗 Processing {driver_id}...")
                
                # Generate trips for this driver
                trips = self.simulator.generate_driver_trips(driver_data, months)
                
                # Save trip data
                output_path = self._save_driver_trips(driver_id, trips, batch_num)
                
                # Update statistics
                batch_results['trips_generated'] += len(trips)
                batch_results['file_paths'].append(str(output_path))
                self.stats['trips_generated'] += len(trips)
                
                # Update API call count
                progress = self.simulator.get_progress()
                self.stats['api_calls_made'] = progress.get('api_calls_made', 0)
                
                # Calculate data points
                data_points = sum(len(trip.gps_points) + len(trip.imu_readings) 
                                for trip in trips)
                self.stats['total_data_points'] += data_points
                
            except Exception as e:
                logger.error(f"❌ Failed to process {driver_data.get('driver_id', 'unknown')}: {e}")
                continue
        
        return batch_results
    
    def _save_driver_trips(self, driver_id: str, trips, batch_num: int) -> Path:
        """Save trip data for a driver efficiently."""
        # Create batch directory
        batch_dir = Path(f"data/simulated/trips/batch_{batch_num:02d}")
        batch_dir.mkdir(parents=True, exist_ok=True)
        
        # Save as compressed pickle for efficiency
        output_path = batch_dir / f"{driver_id}_trips.pkl"
        
        with open(output_path, 'wb') as f:
            pickle.dump(trips, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        # Update storage statistics
        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        self.stats['storage_used_mb'] += file_size_mb
        
        return output_path
    
    def _generate_final_summary(self) -> Dict[str, Any]:
        """Generate final execution summary."""
        elapsed_time = time.time() - self.start_time
        
        summary = {
            'execution_info': {
                'step': 5,
                'completion_time': datetime.now().isoformat(),
                'elapsed_minutes': elapsed_time / 60,
                'used_real_apis': self.use_real_apis
            },
            'results': self.stats.copy(),
            'performance': {
                'drivers_per_minute': self.stats['drivers_processed'] / (elapsed_time / 60),
                'trips_per_minute': self.stats['trips_generated'] / (elapsed_time / 60),
                'api_calls_per_minute': self.stats['api_calls_made'] / (elapsed_time / 60) if self.use_real_apis else 0
            },
            'data_quality': {
                'avg_trips_per_driver': self.stats['trips_generated'] / self.stats['drivers_processed'] if self.stats['drivers_processed'] > 0 else 0,
                'avg_data_points_per_trip': self.stats['total_data_points'] / self.stats['trips_generated'] if self.stats['trips_generated'] > 0 else 0
            }
        }
        
        # Save summary
        summary_path = Path("data/simulated/step_5_summary.json")
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Log final results
        logger.info("📊 Step 5 Final Results:")
        logger.info(f"   👥 Drivers processed: {self.stats['drivers_processed']:,}")
        logger.info(f"   🚗 Trips generated: {self.stats['trips_generated']:,}")
        logger.info(f"   📊 Data points: {self.stats['total_data_points']:,}")
        logger.info(f"   🌐 API calls: {self.stats['api_calls_made']:,}")
        logger.info(f"   💾 Storage used: {self.stats['storage_used_mb']:.1f} MB")
        logger.info(f"   ⏱️  Total time: {elapsed_time/60:.1f} minutes")
        logger.info(f"   📁 Summary: {summary_path}")
        
        return summary


def main():
    """Execute Step 5 with user options."""
    print("\n" + "="*60)
    print("📋 TELEMATICS BLUEPRINT - STEP 5")
    print("🚗 Raw Trip Log Generation with Real API Integration")
    print("="*60)
    
    # Configuration options
    print(f"\n🔧 Configuration Options:")
    print(f"   1. Quick Test (10 drivers, 1 month)")
    print(f"   2. Small Scale (100 drivers, 6 months)")
    print(f"   3. Medium Scale (500 drivers, 12 months)")
    print(f"   4. Full Scale (1000 drivers, 18 months)")
    print(f"   5. Custom Configuration")
    
    choice = input(f"\n🔢 Choose configuration (1-5): ").strip()
    
    # Set parameters based on choice
    configs = {
        '1': (10, 1, "Quick Test"),
        '2': (100, 6, "Small Scale"),
        '3': (500, 12, "Medium Scale"),
        '4': (1000, 18, "Full Scale")
    }
    
    if choice in configs:
        num_drivers, months, config_name = configs[choice]
        use_real_apis = True
    elif choice == '5':
        num_drivers = int(input("Number of drivers: "))
        months = int(input("Number of months: "))
        use_real_apis = input("Use real APIs? (y/n): ").lower() == 'y'
        config_name = "Custom"
    else:
        logger.error("❌ Invalid choice")
        return
    
    print(f"\n✅ Selected: {config_name}")
    print(f"   👥 Drivers: {num_drivers}")
    print(f"   📅 Months: {months}")
    print(f"   🌐 Real APIs: {'Yes' if use_real_apis else 'No'}")
    
    try:
        # Initialize and run orchestrator
        orchestrator = Step5Orchestrator(
            use_real_apis=use_real_apis,
            max_workers=3,
            batch_size=25
        )
        
        results = orchestrator.execute_step_5(
            num_drivers=num_drivers,
            months=months
        )
        
        if results.get('status') == 'cancelled':
            return
        
        # Show completion message
        print(f"\n🎉 SUCCESS! Step 5 completed successfully!")
        print(f"\n📁 Generated Files:")
        print(f"   • data/simulated/trips/ (trip data by batch)")
        print(f"   • data/simulated/step_5_summary.json")
        
        print(f"\n🔄 Next Steps:")
        print(f"   • Step 6: Create API simulation functions (if needed)")
        print(f"   • Step 7: Enrich trip data with additional context")
        print(f"   • Step 8: Event detection and behavioral analysis")
        
        return results
        
    except KeyboardInterrupt:
        logger.info("🛑 Operation interrupted by user")
        return {'status': 'interrupted'}
    except Exception as e:
        logger.error(f"❌ Step 5 failed: {str(e)}")
        return {'status': 'failed', 'error': str(e)}


if __name__ == "__main__":
    main()
