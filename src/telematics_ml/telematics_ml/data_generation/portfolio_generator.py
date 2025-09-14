"""
Step 4: Driver & Vehicle Portfolio Generator

Generates a CSV file with 1,000 unique drivers, each with realistic demographics,
vehicle information, and persona assignments according to the blueprint.
"""

import pandas as pd
import numpy as np
import random
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

from .driver_personas import DriverPersona, PersonaType, create_driver_population
from ..data.schemas import DataSource
from ..utils.config import get_config


class DriverPortfolioGenerator:
    """Generates a realistic portfolio of 1,000 drivers for simulation."""
    
    def __init__(self, random_seed: int = 42):
        """
        Initialize the driver portfolio generator.
        
        Args:
            random_seed: Random seed for reproducible results
        """
        self.config = get_config()
        self.logger = logging.getLogger(__name__)
        
        # Set random seeds for reproducibility
        random.seed(random_seed)
        np.random.seed(random_seed)
        
        self.random_seed = random_seed
    
    def generate_driver_portfolio(self, num_drivers: int = 1000,
                                output_path: Path = None) -> pd.DataFrame:
        """
        Generate a complete driver portfolio according to blueprint Step 4.
        
        Args:
            num_drivers: Number of drivers to generate (default: 1000)
            output_path: Path to save the drivers.csv file
            
        Returns:
            DataFrame containing the driver portfolio
        """
        self.logger.info(f"🚗 Generating driver portfolio: {num_drivers} drivers")
        
        if output_path is None:
            output_path = Path("data/simulated/drivers.csv")
        
        # Step 4a: Create driver personas (Safe, Average, Risky distribution)
        persona_distribution = {
            PersonaType.SAFE_DRIVER: 0.6,      # 60% safe drivers
            PersonaType.AVERAGE_DRIVER: 0.3,   # 30% average drivers  
            PersonaType.RISKY_DRIVER: 0.1      # 10% risky drivers
        }
        
        drivers = create_driver_population(num_drivers, persona_distribution)
        
        # Step 4b: Convert to structured data
        portfolio_data = []
        
        for i, driver in enumerate(drivers):
            # Basic driver information
            driver_record = {
                'driver_id': driver.driver_id,
                'persona_type': driver.persona_type.value,
                
                # Demographics (from persona)
                'driver_age': driver.age,
                'years_licensed': driver.years_licensed,
                
                # Vehicle information (from persona)
                'vehicle_age': driver.vehicle_age,
                'vehicle_make': self._assign_vehicle_make(driver.persona_type),
                'vehicle_model': self._assign_vehicle_model(driver.persona_type),
                
                # Risk history (from persona)
                'prior_at_fault_accidents': driver.prior_at_fault_accidents,
                'prior_claims': max(0, driver.prior_at_fault_accidents + 
                                   random.randint(-1, 2)),  # Claims ≈ accidents
                'prior_violations': self._generate_violations(driver),
                
                # Data source assignment (50/50 split)
                'data_source': driver.data_source.value,
                
                # Account information
                'account_created_date': self._generate_account_date(),
                'policy_start_date': self._generate_policy_date(),
                
                # Persona behavioral parameters (for simulation)
                'hard_brake_rate_base': driver.hard_brake_rate,
                'rapid_accel_rate_base': driver.rapid_accel_rate,
                'harsh_corner_rate_base': driver.harsh_corner_rate,
                'speeding_rate_base': driver.speeding_rate,
                'phone_usage_pct_base': driver.phone_usage_pct,
                'night_driving_pct_base': driver.night_driving_pct,
                'avg_speed_multiplier': driver.avg_speed_multiplier,
                'jerk_rate_multiplier': driver.jerk_rate_multiplier,
                
                # Claim probability (for validation)
                'calculated_claim_probability': driver.calculate_claim_probability()
            }
            
            portfolio_data.append(driver_record)
        
        # Step 4c: Create DataFrame and validate
        portfolio_df = pd.DataFrame(portfolio_data)
        portfolio_df = self._validate_and_clean_portfolio(portfolio_df)
        
        # Step 4d: Save to CSV
        output_path.parent.mkdir(parents=True, exist_ok=True)
        portfolio_df.to_csv(output_path, index=False)
        
        # Step 4e: Generate summary statistics
        self._generate_portfolio_summary(portfolio_df, output_path)
        
        self.logger.info(f"✅ Driver portfolio generated: {len(portfolio_df)} drivers")
        self.logger.info(f"📁 Saved to: {output_path}")
        
        return portfolio_df
    
    def _assign_vehicle_make(self, persona_type: PersonaType) -> str:
        """Assign realistic vehicle makes based on persona."""
        vehicle_preferences = {
            PersonaType.SAFE_DRIVER: [
                'Toyota', 'Honda', 'Subaru', 'Mazda', 'Hyundai'
            ],
            PersonaType.AVERAGE_DRIVER: [
                'Ford', 'Chevrolet', 'Nissan', 'Toyota', 'Honda', 'Kia'
            ],
            PersonaType.RISKY_DRIVER: [
                'BMW', 'Mercedes', 'Audi', 'Dodge', 'Ford', 'Chevrolet'
            ]
        }
        
        makes = vehicle_preferences[persona_type]
        return random.choice(makes)
    
    def _assign_vehicle_model(self, persona_type: PersonaType) -> str:
        """Assign realistic vehicle models based on persona."""
        model_preferences = {
            PersonaType.SAFE_DRIVER: [
                'Camry', 'Accord', 'Outback', 'CX-5', 'Elantra'
            ],
            PersonaType.AVERAGE_DRIVER: [
                'F-150', 'Silverado', 'Altima', 'Corolla', 'Civic', 'Forte'
            ],
            PersonaType.RISKY_DRIVER: [
                '3 Series', 'C-Class', 'A4', 'Challenger', 'Mustang', 'Camaro'
            ]
        }
        
        models = model_preferences[persona_type]
        return random.choice(models)
    
    def _generate_violations(self, driver: DriverPersona) -> int:
        """Generate realistic violation history based on driver persona."""
        base_violation_rates = {
            PersonaType.SAFE_DRIVER: 0.05,      # 5% chance per year
            PersonaType.AVERAGE_DRIVER: 0.15,   # 15% chance per year
            PersonaType.RISKY_DRIVER: 0.35      # 35% chance per year
        }
        
        rate = base_violation_rates[driver.persona_type]
        violations = 0
        
        # Simulate violations over driving history
        for year in range(driver.years_licensed):
            if random.random() < rate:
                violations += 1
                rate *= 0.9  # Slight reduction after each violation
        
        return violations
    
    def _generate_account_date(self) -> datetime:
        """Generate realistic account creation date."""
        # Accounts created in the last 2 years
        start_date = datetime.now() - timedelta(days=730)
        end_date = datetime.now() - timedelta(days=30)
        
        time_between = end_date - start_date
        random_days = random.randrange(time_between.days)
        
        return start_date + timedelta(days=random_days)
    
    def _generate_policy_date(self) -> datetime:
        """Generate realistic policy start date."""
        # Policies start in the last 18 months for our simulation period
        start_date = datetime.now() - timedelta(days=550)  # ~18 months
        end_date = datetime.now() - timedelta(days=30)
        
        time_between = end_date - start_date
        random_days = random.randrange(time_between.days)
        
        return start_date + timedelta(days=random_days)
    
    def _validate_and_clean_portfolio(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean the generated portfolio data."""
        self.logger.info("🔍 Validating driver portfolio data...")
        
        # Check for required columns
        required_columns = [
            'driver_id', 'persona_type', 'driver_age', 'years_licensed',
            'vehicle_age', 'prior_at_fault_accidents', 'data_source'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Data quality checks
        issues = []
        
        # Age validation
        if df['driver_age'].min() < 16 or df['driver_age'].max() > 100:
            issues.append("Invalid driver ages detected")
        
        # Years licensed validation
        invalid_years = df[df['years_licensed'] > (df['driver_age'] - 15)]
        if len(invalid_years) > 0:
            issues.append(f"{len(invalid_years)} drivers with invalid years_licensed")
        
        # Vehicle age validation
        if df['vehicle_age'].min() < 0 or df['vehicle_age'].max() > 30:
            issues.append("Invalid vehicle ages detected")
        
        # Accidents validation
        if df['prior_at_fault_accidents'].min() < 0:
            issues.append("Negative accident counts detected")
        
        # Report issues
        if issues:
            self.logger.warning(f"⚠️ Data quality issues found: {issues}")
            # Fix common issues
            df['years_licensed'] = df.apply(
                lambda row: min(row['years_licensed'], row['driver_age'] - 16), axis=1
            )
            df['prior_at_fault_accidents'] = df['prior_at_fault_accidents'].clip(lower=0)
        
        # Ensure no duplicates
        duplicates = df['driver_id'].duplicated().sum()
        if duplicates > 0:
            self.logger.warning(f"⚠️ Removing {duplicates} duplicate driver IDs")
            df = df.drop_duplicates(subset=['driver_id'])
        
        self.logger.info(f"✅ Portfolio validation complete: {len(df)} valid drivers")
        return df
    
    def _generate_portfolio_summary(self, df: pd.DataFrame, output_path: Path) -> None:
        """Generate and save portfolio summary statistics."""
        summary = {
            'generation_info': {
                'total_drivers': len(df),
                'generation_date': datetime.now().isoformat(),
                'random_seed': self.random_seed
            },
            'demographics': {
                'age_distribution': {
                    'mean': float(df['driver_age'].mean()),
                    'std': float(df['driver_age'].std()),
                    'min': int(df['driver_age'].min()),
                    'max': int(df['driver_age'].max())
                },
                'years_licensed_distribution': {
                    'mean': float(df['years_licensed'].mean()),
                    'std': float(df['years_licensed'].std()),
                    'min': int(df['years_licensed'].min()),
                    'max': int(df['years_licensed'].max())
                }
            },
            'persona_distribution': df['persona_type'].value_counts().to_dict(),
            'data_source_distribution': df['data_source'].value_counts().to_dict(),
            'vehicle_info': {
                'top_makes': df['vehicle_make'].value_counts().head().to_dict(),
                'avg_vehicle_age': float(df['vehicle_age'].mean())
            },
            'risk_factors': {
                'drivers_with_accidents': int((df['prior_at_fault_accidents'] > 0).sum()),
                'avg_accidents': float(df['prior_at_fault_accidents'].mean()),
                'avg_claim_probability': float(df['calculated_claim_probability'].mean())
            }
        }
        
        # Save summary
        summary_path = output_path.parent / "drivers_summary.json"
        import json
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Log key statistics
        self.logger.info("📊 Portfolio Summary:")
        self.logger.info(f"   👥 Total drivers: {summary['generation_info']['total_drivers']}")
        self.logger.info(f"   🎭 Personas: {summary['persona_distribution']}")
        self.logger.info(f"   📱 Data sources: {summary['data_source_distribution']}")
        self.logger.info(f"   🎯 Avg claim probability: {summary['risk_factors']['avg_claim_probability']:.3f}")
        self.logger.info(f"   📁 Summary saved to: {summary_path}")


def main():
    """Main function to run the driver portfolio generation."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Starting Step 4: Driver Portfolio Generation")
    
    generator = DriverPortfolioGenerator(random_seed=42)
    portfolio_df = generator.generate_driver_portfolio(
        num_drivers=1000,
        output_path=Path("data/simulated/drivers.csv")
    )
    
    logger.info("🎉 Step 4 Complete! Driver portfolio ready for Step 5.")
    
    return portfolio_df


if __name__ == "__main__":
    main()
