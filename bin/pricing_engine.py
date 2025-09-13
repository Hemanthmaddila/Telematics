#!/usr/bin/env python3
"""
MONTHLY PRICING SYSTEM DEMO

This demonstrates exactly how the "Drive -> Score -> Price" cycle works:
1. Customer drives during September
2. System calculates risk score on October 1st
3. New premium applies for October billing

This is the core business value of the entire telematics system.
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telematics.data.schemas import MonthlyFeatures

class MonthlyPricingEngine:
    """
    Demonstrates the complete monthly pricing cycle.
    
    This is what runs automatically on the 1st of every month
    for every customer in the telematics program.
    """
    
    def __init__(self):
        """Initialize the pricing engine with trained models."""
        
        # Load the production-trained model
        self.model_path = Path("data/production/frequency_model.xgb")
        
        if self.model_path.exists():
            self.risk_model = xgb.XGBClassifier()
            self.risk_model.load_model(str(self.model_path))
            print("✅ Loaded production risk model")
        else:
            print("⚠️ Using fallback model")
            # Fallback: load the fast-track model
            fallback_path = Path("data/final/risk_model.xgb")
            if fallback_path.exists():
                self.risk_model = xgb.XGBClassifier()
                self.risk_model.load_model(str(fallback_path))
            else:
                self.risk_model = None
        
        # Pricing table (business rules)
        self.pricing_table = {
            'base_monthly_premium': 125.00,
            'risk_adjustments': {
                'very_low': -0.25,    # 25% discount
                'low': -0.15,         # 15% discount  
                'medium': 0.0,        # No change
                'high': 0.20,         # 20% surcharge
                'very_high': 0.40     # 40% surcharge
            }
        }
    
    def simulate_monthly_cycle(self, driver_id: str = "driver_000001"):
        """
        Simulate the complete monthly pricing cycle for one customer.
        
        This shows exactly what happens on the 1st of every month.
        """
        
        print("🔄 MONTHLY PRICING CYCLE SIMULATION")
        print("="*50)
        print(f"📋 Customer: {driver_id}")
        print(f"📅 Processing Date: October 1st, 2025")
        print()
        
        # Step 1: Simulate September driving data
        print("📊 STEP 1: September Driving Data Collection")
        september_data = self._simulate_september_driving(driver_id)
        self._print_driving_summary(september_data)
        
        # Step 2: Calculate risk score
        print("\n🎯 STEP 2: Risk Score Calculation")
        risk_score, risk_tier = self._calculate_risk_score(september_data)
        print(f"   Raw Risk Probability: {risk_score:.3f}")
        print(f"   Risk Tier: {risk_tier}")
        
        # Step 3: Calculate new premium
        print("\n💰 STEP 3: Premium Calculation")
        old_premium, new_premium = self._calculate_premium(risk_tier)
        
        # Step 4: Customer notification
        print("\n📱 STEP 4: Customer Notification")
        self._generate_customer_message(september_data, risk_score, old_premium, new_premium)
        
        return {
            'driver_id': driver_id,
            'month': 'September 2025',
            'driving_data': september_data,
            'risk_score': risk_score,
            'risk_tier': risk_tier,
            'old_premium': old_premium,
            'new_premium': new_premium,
            'savings': old_premium - new_premium
        }
    
    def _simulate_september_driving(self, driver_id: str) -> dict:
        """Simulate realistic September driving data for a customer."""
        
        # Simulate different driver types based on driver_id
        if 'safe' in driver_id.lower():
            # Safe driver
            return {
                'total_trips': 42,
                'total_miles_driven': 1250,
                'hard_brake_rate_per_100_miles': 0.8,
                'rapid_accel_rate_per_100_miles': 0.4,
                'speeding_rate_per_100_miles': 0.2,
                'pct_trip_time_screen_on': 2.1,
                'pct_miles_night': 12.0,
                'avg_speed_mph': 28.5,
                'max_speed_over_limit_mph': 3.2,
                'driver_age': 35,
                'years_licensed': 12,
                'prior_at_fault_accidents': 0,
                'vehicle_age': 4
            }
        elif 'avg' in driver_id.lower():
            # Average driver
            return {
                'total_trips': 38,
                'total_miles_driven': 1100,
                'hard_brake_rate_per_100_miles': 2.1,
                'rapid_accel_rate_per_100_miles': 1.5,
                'speeding_rate_per_100_miles': 1.8,
                'pct_trip_time_screen_on': 4.2,
                'pct_miles_night': 18.0,
                'avg_speed_mph': 31.2,
                'max_speed_over_limit_mph': 8.7,
                'driver_age': 28,
                'years_licensed': 6,
                'prior_at_fault_accidents': 1,
                'vehicle_age': 7
            }
        else:
            # Risky driver
            return {
                'total_trips': 35,
                'total_miles_driven': 950,
                'hard_brake_rate_per_100_miles': 4.8,
                'rapid_accel_rate_per_100_miles': 3.2,
                'speeding_rate_per_100_miles': 6.5,
                'pct_trip_time_screen_on': 8.7,
                'pct_miles_night': 25.0,
                'avg_speed_mph': 35.8,
                'max_speed_over_limit_mph': 18.3,
                'driver_age': 22,
                'years_licensed': 2,
                'prior_at_fault_accidents': 2,
                'vehicle_age': 12
            }
    
    def _print_driving_summary(self, data: dict):
        """Print a summary of the customer's September driving."""
        
        print(f"   🚗 Total Trips: {data['total_trips']}")
        print(f"   📏 Miles Driven: {data['total_miles_driven']:,}")
        print(f"   🛑 Hard Brakes: {data['hard_brake_rate_per_100_miles']:.1f}/100mi")
        print(f"   🚀 Rapid Accels: {data['rapid_accel_rate_per_100_miles']:.1f}/100mi")
        print(f"   🏎️  Speeding: {data['speeding_rate_per_100_miles']:.1f}/100mi")
        print(f"   📱 Phone Usage: {data['pct_trip_time_screen_on']:.1f}% of trip time")
        print(f"   🌙 Night Driving: {data['pct_miles_night']:.1f}% of miles")
    
    def _calculate_risk_score(self, driving_data: dict):
        """Calculate risk score using the trained model."""
        
        if self.risk_model is None:
            # Fallback scoring if no model available
            risk_score = (
                driving_data['hard_brake_rate_per_100_miles'] * 0.15 +
                driving_data['speeding_rate_per_100_miles'] * 0.20 +
                driving_data['pct_trip_time_screen_on'] * 0.05 +
                (1 if driving_data['driver_age'] < 25 else 0) * 0.10
            ) / 10
            
            risk_score = min(max(risk_score, 0.01), 0.99)
        else:
            # Use trained model (simplified feature set for demo)
            features = np.array([[
                driving_data['hard_brake_rate_per_100_miles'],
                driving_data['rapid_accel_rate_per_100_miles'], 
                driving_data['speeding_rate_per_100_miles'],
                driving_data['pct_trip_time_screen_on'],
                driving_data['pct_miles_night'],
                driving_data['avg_speed_mph'],
                driving_data['driver_age'],
                driving_data['years_licensed'],
                driving_data['prior_at_fault_accidents'],
                driving_data['vehicle_age']
            ]])
            
            # Pad with zeros to match model's expected feature count
            if hasattr(self.risk_model, 'n_features_in_'):
                expected_features = self.risk_model.n_features_in_
                current_features = features.shape[1]
                if current_features < expected_features:
                    padding = np.zeros((1, expected_features - current_features))
                    features = np.hstack([features, padding])
            
            try:
                risk_score = self.risk_model.predict_proba(features)[0, 1]
            except:
                # Fallback calculation
                risk_score = min(sum([
                    driving_data['hard_brake_rate_per_100_miles'] * 0.03,
                    driving_data['speeding_rate_per_100_miles'] * 0.04,
                    driving_data['pct_trip_time_screen_on'] * 0.01
                ]), 0.95)
        
        # Convert to risk tier
        if risk_score < 0.02:
            risk_tier = 'very_low'
        elif risk_score < 0.05:
            risk_tier = 'low'
        elif risk_score < 0.10:
            risk_tier = 'medium'
        elif risk_score < 0.20:
            risk_tier = 'high'
        else:
            risk_tier = 'very_high'
        
        return risk_score, risk_tier
    
    def _calculate_premium(self, risk_tier: str):
        """Calculate new premium based on risk tier."""
        
        base_premium = self.pricing_table['base_monthly_premium']
        adjustment = self.pricing_table['risk_adjustments'][risk_tier]
        new_premium = base_premium * (1 + adjustment)
        
        print(f"   Base Premium: ${base_premium:.2f}")
        print(f"   Risk Adjustment ({risk_tier}): {adjustment:+.0%}")
        print(f"   New Premium: ${new_premium:.2f}")
        
        return base_premium, new_premium
    
    def _generate_customer_message(self, driving_data: dict, risk_score: float, 
                                 old_premium: float, new_premium: float):
        """Generate the customer notification message."""
        
        savings = old_premium - new_premium
        
        print("   📧 Customer Email/App Notification:")
        print("   " + "-" * 45)
        
        if savings > 0:
            print(f"   🎉 Great news! Your safe driving in September")
            print(f"   earned you a ${savings:.2f} discount for October!")
            print()
            print(f"   Your October premium: ${new_premium:.2f}")
            print(f"   (down from ${old_premium:.2f})")
        elif savings < 0:
            print(f"   ⚠️  Your driving in September resulted in")
            print(f"   a premium increase of ${-savings:.2f} for October.")
            print()
            print(f"   Your October premium: ${new_premium:.2f}")
            print(f"   (up from ${old_premium:.2f})")
        else:
            print(f"   ℹ️  Your driving in September maintained")
            print(f"   your current premium of ${new_premium:.2f}")
        
        print()
        print("   📊 Key areas that affected your score:")
        
        if driving_data['hard_brake_rate_per_100_miles'] > 2.0:
            print("   • Hard braking events - try smoother stops")
        if driving_data['speeding_rate_per_100_miles'] > 2.0:
            print("   • Speeding incidents - watch those speed limits")
        if driving_data['pct_trip_time_screen_on'] > 5.0:
            print("   • Phone usage while driving - hands-free is safer")
        if driving_data['pct_miles_night'] > 20.0:
            print("   • Night driving - extra caution in darkness")
        
        if savings > 0:
            print("   ✅ Keep up the safe driving for continued savings!")


def main():
    """Demonstrate the monthly pricing system."""
    
    print("🚗 TELEMATICS MONTHLY PRICING SYSTEM")
    print("📅 Automated Processing Demo - October 1st, 2025")
    print("=" * 60)
    print()
    
    # Initialize pricing engine
    engine = MonthlyPricingEngine()
    
    print("🔄 Running monthly cycle for 3 different customer types...")
    print()
    
    # Simulate different customer types
    customers = [
        ("driver_safe_001", "Safe Driver"),
        ("driver_avg_002", "Average Driver"), 
        ("driver_risky_003", "Risky Driver")
    ]
    
    results = []
    
    for driver_id, customer_type in customers:
        print(f"\n{'='*20} {customer_type.upper()} {'='*20}")
        result = engine.simulate_monthly_cycle(driver_id)
        results.append(result)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 MONTHLY PROCESSING SUMMARY")
    print("=" * 60)
    
    total_customers = len(results)
    total_savings = sum(r['savings'] for r in results)
    avg_savings = total_savings / total_customers
    
    print(f"   Customers Processed: {total_customers}")
    print(f"   Average Premium Change: ${avg_savings:+.2f}")
    print()
    
    for result in results:
        savings = result['savings']
        symbol = "💚" if savings > 0 else "📈" if savings < 0 else "➡️"
        print(f"   {symbol} {result['driver_id']}: ${savings:+.2f}")
    
    print()
    print("✅ Monthly pricing cycle complete!")
    print("📧 Customer notifications sent")
    print("💳 New premiums effective immediately")


if __name__ == "__main__":
    main()
