#!/usr/bin/env python3
"""
Step 4: Generate Driver Portfolio

Execute blueprint Step 4 to create drivers.csv with 1,000 unique drivers.
This is the foundation for all subsequent simulation steps.
"""

import sys
import logging
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telematics.simulation.driver_portfolio_generator import DriverPortfolioGenerator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Execute Step 4 of the blueprint."""
    print("\n" + "="*60)
    print("📋 TELEMATICS BLUEPRINT - STEP 4")
    print("🚗 Driver & Vehicle Portfolio Generation")
    print("="*60)
    
    logger.info("🚀 Starting Step 4: Driver Portfolio Generation")
    
    try:
        # Initialize the generator
        generator = DriverPortfolioGenerator(random_seed=42)
        
        # Generate the portfolio
        logger.info("👥 Generating 1,000 unique drivers...")
        portfolio_df = generator.generate_driver_portfolio(
            num_drivers=1000,
            output_path=Path("data/simulated/drivers.csv")
        )
        
        # Display results
        print(f"\n✅ SUCCESS! Generated {len(portfolio_df)} drivers")
        
        print("\n📊 Portfolio Overview:")
        print(f"   🎭 Driver Personas:")
        persona_counts = portfolio_df['persona_type'].value_counts()
        for persona, count in persona_counts.items():
            percentage = (count / len(portfolio_df)) * 100
            print(f"      • {persona}: {count} drivers ({percentage:.1f}%)")
        
        print(f"\n   📱 Data Sources:")
        source_counts = portfolio_df['data_source'].value_counts()
        for source, count in source_counts.items():
            percentage = (count / len(portfolio_df)) * 100
            print(f"      • {source}: {count} drivers ({percentage:.1f}%)")
        
        print(f"\n   📈 Demographics:")
        print(f"      • Average age: {portfolio_df['driver_age'].mean():.1f} years")
        print(f"      • Average driving experience: {portfolio_df['years_licensed'].mean():.1f} years")
        print(f"      • Average vehicle age: {portfolio_df['vehicle_age'].mean():.1f} years")
        print(f"      • Drivers with prior accidents: {(portfolio_df['prior_at_fault_accidents'] > 0).sum()}")
        
        print(f"\n   🎯 Risk Assessment:")
        avg_claim_prob = portfolio_df['calculated_claim_probability'].mean()
        print(f"      • Average claim probability: {avg_claim_prob:.3f} ({avg_claim_prob*100:.1f}%)")
        
        print(f"\n📁 Files Created:")
        print(f"   • data/simulated/drivers.csv")
        print(f"   • data/simulated/drivers_summary.json")
        
        print(f"\n🔄 Next Steps:")
        print(f"   • Step 5: Generate raw trip logs")
        print(f"   • Step 6: Create API simulation functions")
        print(f"   • Step 7: Enrich trip data with contextual information")
        
        print(f"\n🎉 Step 4 Complete! Ready for Phase 2 - Trip Simulation")
        
        return portfolio_df
        
    except Exception as e:
        logger.error(f"❌ Step 4 failed: {str(e)}")
        print(f"\n❌ FAILED: {str(e)}")
        return None


if __name__ == "__main__":
    main()
