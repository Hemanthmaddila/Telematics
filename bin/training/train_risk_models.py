#!/usr/bin/env python3
"""
PRODUCTION-SCALE PIPELINE: 2-Day Sprint for Robust Model

This scales up our POC to production-level robustness:
- Full 1,000 drivers × 18 months = 18,000 records
- Advanced feature engineering (interaction features, lag features)
- Frequency-Severity model architecture
- Time-series cross-validation
- Professional-grade evaluation metrics

Target: Dramatically improved model performance within 2-day deadline.
"""

import sys
import logging
import time
import json
import warnings
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np
import random

# Suppress warnings
warnings.filterwarnings('ignore')

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telematics.data.schemas import MonthlyFeatures, DataSource

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProductionScalePipeline:
    """
    Production-scale pipeline for robust model training.
    
    Implements advanced techniques for 2-day sprint:
    - Full dataset processing
    - Advanced feature engineering
    - Frequency-Severity modeling
    - Time-series validation
    """
    
    def __init__(self, full_scale: bool = True):
        """Initialize production pipeline."""
        self.full_scale = full_scale
        self.drivers_count = 1000 if full_scale else 200
        self.months_count = 18 if full_scale else 6
        
        # Output paths
        self.output_dir = Path("data/production")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("🏭 Production-Scale Pipeline Initialized")
        logger.info(f"   📊 Scale: {self.drivers_count} drivers, {self.months_count} months")
        logger.info(f"   🎯 Expected records: {self.drivers_count * self.months_count:,}")
    
    def execute_production_pipeline(self) -> Dict[str, Any]:
        """Execute the complete production-scale pipeline."""
        logger.info("\n" + "="*70)
        logger.info("🏭 PRODUCTION-SCALE PIPELINE: ROBUST MODEL TRAINING")
        logger.info("="*70)
        
        start_time = time.time()
        
        try:
            # Step 1: Generate large-scale dataset
            logger.info("📊 Step 1: Generating production-scale dataset...")
            training_data = self._generate_large_scale_data()
            
            # Step 2: Advanced feature engineering
            logger.info("🔧 Step 2: Advanced feature engineering...")
            enhanced_data = self._advanced_feature_engineering(training_data)
            
            # Step 3: Frequency-Severity modeling
            logger.info("💰 Step 3: Training Frequency-Severity models...")
            frequency_model, severity_model = self._train_frequency_severity_models(enhanced_data)
            
            # Step 4: Time-series validation
            logger.info("📈 Step 4: Time-series cross-validation...")
            validation_results = self._time_series_validation(enhanced_data)
            
            # Step 5: Final evaluation and risk scoring
            logger.info("🎯 Step 5: Final evaluation and risk scoring...")
            final_results = self._final_evaluation(enhanced_data, frequency_model, severity_model, validation_results)
            
            elapsed_time = time.time() - start_time
            logger.info(f"\n🎉 PRODUCTION PIPELINE COMPLETE!")
            logger.info(f"⏱️  Total execution time: {elapsed_time/60:.1f} minutes")
            
            return final_results
            
        except Exception as e:
            logger.error(f"❌ Production pipeline failed: {str(e)}")
            raise
    
    def _generate_large_scale_data(self) -> pd.DataFrame:
        """Generate large-scale dataset using optimized sampling."""
        
        # Load existing driver portfolio
        drivers_df = pd.read_csv("data/simulated/drivers.csv")
        
        if self.full_scale:
            # Use all drivers
            selected_drivers = drivers_df
        else:
            # Use balanced sample for testing
            selected_drivers = drivers_df.sample(n=self.drivers_count, random_state=42)
        
        logger.info(f"   📊 Processing {len(selected_drivers)} drivers...")
        
        # Generate monthly records with realistic patterns
        monthly_records = []
        
        for _, driver in selected_drivers.iterrows():
            driver_id = driver['driver_id']
            persona = driver['persona_type']
            
            # Generate 18 months of data per driver
            base_date = datetime.now() - timedelta(days=self.months_count * 30)
            
            for month_offset in range(self.months_count):
                month_date = base_date + timedelta(days=month_offset * 30)
                month_str = month_date.strftime("%Y-%m")
                
                # Generate monthly features with persona-based variation
                monthly_record = self._generate_monthly_record(driver, month_str, month_offset)
                monthly_records.append(monthly_record)
        
        df = pd.DataFrame(monthly_records)
        
        # Add claim target with improved realism
        df = self._add_realistic_claims(df)
        
        logger.info(f"   ✅ Generated {len(df):,} driver-month records")
        logger.info(f"   📊 Claim rate: {df['had_claim_in_period'].mean():.2%}")
        
        return df
    
    def _generate_monthly_record(self, driver: pd.Series, month: str, month_offset: int) -> Dict[str, Any]:
        """Generate realistic monthly record for a driver."""
        
        # Base parameters from driver persona
        persona_params = {
            'safe_driver': {'trip_mult': 0.8, 'risk_mult': 0.3, 'phone_mult': 0.4},
            'average_driver': {'trip_mult': 1.0, 'risk_mult': 1.0, 'phone_mult': 1.0},
            'risky_driver': {'trip_mult': 1.3, 'risk_mult': 2.5, 'phone_mult': 1.8}
        }
        
        params = persona_params.get(driver['persona_type'], persona_params['average_driver'])
        
        # Seasonal adjustments
        month_num = int(month.split('-')[1])
        winter_factor = 1.2 if month_num in [12, 1, 2] else 1.0
        summer_factor = 0.9 if month_num in [6, 7, 8] else 1.0
        
        # Progressive behavioral changes (people get better/worse over time)
        time_trend = 1.0 - (month_offset * 0.02 * random.uniform(0.5, 1.5))  # Slight improvement over time
        
        # Generate all 32 features
        record = {
            'driver_id': driver['driver_id'],
            'month': month,
            
            # Trip volume and basic metrics
            'total_trips': int(45 * params['trip_mult'] * random.uniform(0.7, 1.3)),
            'total_drive_time_hours': random.uniform(25, 80) * params['trip_mult'],
            'total_miles_driven': random.uniform(800, 2500) * params['trip_mult'],
            'avg_speed_mph': random.uniform(22, 35) * driver.get('avg_speed_multiplier', 1.0),
            'max_speed_mph': random.uniform(45, 85) * driver.get('avg_speed_multiplier', 1.0),
            
            # Risk behaviors with persona influence
            'avg_jerk_rate': driver.get('jerk_rate_multiplier', 1.0) * random.uniform(0.2, 1.5),
            'hard_brake_rate_per_100_miles': driver.get('hard_brake_rate_base', 0.5) * params['risk_mult'] * winter_factor * time_trend,
            'rapid_accel_rate_per_100_miles': driver.get('rapid_accel_rate_base', 0.3) * params['risk_mult'] * time_trend,
            'harsh_cornering_rate_per_100_miles': driver.get('harsh_corner_rate_base', 0.2) * params['risk_mult'],
            'swerving_events_per_100_miles': random.uniform(0, 0.5) * params['risk_mult'],
            'speeding_rate_per_100_miles': driver.get('speeding_rate_base', 0.4) * params['risk_mult'] * summer_factor,
            'max_speed_over_limit_mph': random.uniform(0, 25) * params['risk_mult'],
            
            # Time-based exposure
            'pct_miles_night': driver.get('night_driving_pct_base', 0.15) * 100 * random.uniform(0.5, 1.5),
            'pct_miles_late_night_weekend': random.uniform(0, 10) * params['risk_mult'],
            'pct_miles_weekday_rush_hour': random.uniform(5, 35),
            
            # Phone usage
            'pct_trip_time_screen_on': driver.get('phone_usage_pct_base', 0.05) * 100 * params['phone_mult'],
            'handheld_events_rate_per_hour': random.uniform(0, 3) * params['phone_mult'],
            'pct_trip_time_on_call_handheld': random.uniform(0, 5) * params['phone_mult'],
            
            # Vehicle and driver factors
            'avg_engine_rpm': 2100.0 if driver['data_source'] == 'phone_only' else random.uniform(1800, 2500),
            'has_dtc_codes': random.random() < 0.05 if driver['data_source'] == 'phone_plus_device' else False,
            'airbag_deployment_flag': False,  # Rare event
            'driver_age': driver['driver_age'],
            'vehicle_age': driver['vehicle_age'],
            'prior_at_fault_accidents': driver['prior_at_fault_accidents'],
            'years_licensed': driver['years_licensed'],
            'data_source': driver['data_source'],
            
            # Data quality
            'gps_accuracy_avg_meters': random.uniform(3, 12),
            'driver_passenger_confidence_score': random.uniform(0.7, 1.0),
            
            # Environmental context
            'pct_miles_highway': random.uniform(10, 60),
            'pct_miles_urban': random.uniform(40, 90),
            'pct_miles_in_rain_or_snow': winter_factor * random.uniform(5, 25),
            'pct_miles_in_heavy_traffic': random.uniform(15, 45)
        }
        
        return record
    
    def _add_realistic_claims(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add realistic claim predictions based on risk factors."""
        
        def calculate_claim_probability(row):
            """Calculate realistic claim probability based on multiple risk factors."""
            
            # Base annual claim rate varies by persona
            base_rates = {
                'safe_driver': 0.03,     # 3% annual
                'average_driver': 0.07,  # 7% annual  
                'risky_driver': 0.15     # 15% annual
            }
            
            # Get driver info
            driver_info = df[df['driver_id'] == row['driver_id']].iloc[0]
            persona = driver_info.get('driver_id', 'average_driver')  # Fallback
            
            # Map driver_id to persona (simplified)
            if row['prior_at_fault_accidents'] == 0 and row['driver_age'] > 30:
                persona = 'safe_driver'
            elif row['prior_at_fault_accidents'] > 1 or row['driver_age'] < 25:
                persona = 'risky_driver'
            else:
                persona = 'average_driver'
            
            base_annual_prob = base_rates[persona]
            monthly_prob = base_annual_prob / 12  # Convert to monthly
            
            # Risk multipliers
            risk_multiplier = 1.0
            
            # Behavioral risk factors
            risk_multiplier *= (1 + row['hard_brake_rate_per_100_miles'] * 0.3)
            risk_multiplier *= (1 + row['rapid_accel_rate_per_100_miles'] * 0.2)
            risk_multiplier *= (1 + row['speeding_rate_per_100_miles'] * 0.4)
            risk_multiplier *= (1 + row['pct_trip_time_screen_on'] / 100 * 0.5)
            
            # Age factors
            if row['driver_age'] < 25:
                risk_multiplier *= 1.8
            elif row['driver_age'] > 65:
                risk_multiplier *= 1.3
            
            # Vehicle age
            if row['vehicle_age'] > 15:
                risk_multiplier *= 1.2
            
            # Prior history
            risk_multiplier *= (1 + row['prior_at_fault_accidents'] * 0.5)
            
            # Night driving
            risk_multiplier *= (1 + row['pct_miles_night'] / 100 * 0.3)
            
            final_prob = min(monthly_prob * risk_multiplier, 0.25)  # Cap at 25% monthly
            return final_prob
        
        # Calculate probabilities
        df['claim_probability'] = df.apply(calculate_claim_probability, axis=1)
        
        # Generate actual claims
        df['had_claim_in_period'] = df['claim_probability'].apply(lambda p: random.random() < p)
        
        # Generate claim severity for those who had claims
        df['claim_severity'] = 0.0
        claim_mask = df['had_claim_in_period']
        
        # Realistic claim severity distribution (insurance industry data)
        severities = np.random.lognormal(mean=8.5, sigma=1.2, size=claim_mask.sum())  # Log-normal distribution
        severities = np.clip(severities, 1000, 100000)  # $1K to $100K range
        
        df.loc[claim_mask, 'claim_severity'] = severities
        
        return df
    
    def _advanced_feature_engineering(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add advanced features for improved model performance."""
        logger.info("   🔧 Creating interaction features...")
        
        # Interaction features
        df['risk_behavior_score'] = (
            df['hard_brake_rate_per_100_miles'] * 0.3 +
            df['rapid_accel_rate_per_100_miles'] * 0.2 +
            df['speeding_rate_per_100_miles'] * 0.4 +
            df['pct_trip_time_screen_on'] / 100 * 0.1
        )
        
        df['exposure_risk_score'] = (
            df['pct_miles_night'] / 100 * 0.4 +
            df['pct_miles_in_rain_or_snow'] / 100 * 0.3 +
            df['pct_miles_in_heavy_traffic'] / 100 * 0.3
        )
        
        df['young_risky_driver'] = ((df['driver_age'] < 25) & (df['risk_behavior_score'] > df['risk_behavior_score'].median())).astype(int)
        df['high_mileage_risky'] = ((df['total_miles_driven'] > df['total_miles_driven'].quantile(0.8)) & (df['risk_behavior_score'] > df['risk_behavior_score'].median())).astype(int)
        
        # Lag features (previous month behavior)
        logger.info("   📈 Creating lag features...")
        
        df = df.sort_values(['driver_id', 'month'])
        lag_features = ['risk_behavior_score', 'total_miles_driven', 'hard_brake_rate_per_100_miles']
        
        for feature in lag_features:
            df[f'{feature}_lag1'] = df.groupby('driver_id')[feature].shift(1)
            df[f'{feature}_trend'] = df[feature] - df[f'{feature}_lag1']
        
        # Fill NaN values for first month
        lag_columns = [col for col in df.columns if 'lag1' in col or 'trend' in col]
        df[lag_columns] = df[lag_columns].fillna(0)
        
        logger.info(f"   ✅ Added {len(lag_columns) + 4} advanced features")
        
        return df
    
    def _train_frequency_severity_models(self, df: pd.DataFrame) -> Tuple[Any, Any]:
        """Train separate frequency and severity models."""
        
        try:
            import xgboost as xgb
            from sklearn.model_selection import train_test_split
            from sklearn.preprocessing import LabelEncoder
            from sklearn.metrics import mean_squared_error, mean_absolute_error
        except ImportError:
            logger.error("Required ML libraries not available")
            raise
        
        # Prepare features
        feature_columns = [col for col in df.columns if col not in [
            'driver_id', 'month', 'had_claim_in_period', 'claim_severity', 'claim_probability'
        ]]
        
        X = df[feature_columns].copy()
        
        # Handle categorical variables
        categorical_columns = ['data_source']
        label_encoders = {}
        
        for col in categorical_columns:
            if col in X.columns:
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))
                label_encoders[col] = le
        
        # 1. FREQUENCY MODEL (Predicts probability of claim)
        logger.info("   📊 Training frequency model...")
        
        y_frequency = df['had_claim_in_period']
        X_train_freq, X_test_freq, y_train_freq, y_test_freq = train_test_split(
            X, y_frequency, test_size=0.2, random_state=42, stratify=y_frequency
        )
        
        # Class balancing
        scale_pos_weight = (y_train_freq == 0).sum() / (y_train_freq == 1).sum()
        
        frequency_model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=8,
            learning_rate=0.05,
            scale_pos_weight=scale_pos_weight,
            random_state=42,
            eval_metric='logloss'
        )
        
        frequency_model.fit(X_train_freq, y_train_freq)
        
        # Evaluate frequency model
        freq_pred_proba = frequency_model.predict_proba(X_test_freq)[:, 1]
        
        # 2. SEVERITY MODEL (Predicts cost of claim, only for drivers who had claims)
        logger.info("   💰 Training severity model...")
        
        # Only use records where claims occurred
        claim_data = df[df['had_claim_in_period'] == True].copy()
        
        if len(claim_data) > 10:  # Need minimum data for severity model
            X_severity = claim_data[feature_columns]
            y_severity = claim_data['claim_severity']
            
            # Handle categorical variables for severity model
            for col in categorical_columns:
                if col in X_severity.columns:
                    X_severity[col] = label_encoders[col].transform(X_severity[col].astype(str))
            
            if len(claim_data) > 20:  # Enough for train/test split
                X_train_sev, X_test_sev, y_train_sev, y_test_sev = train_test_split(
                    X_severity, y_severity, test_size=0.2, random_state=42
                )
            else:
                # Use all data for training if sample is small
                X_train_sev, X_test_sev = X_severity, X_severity
                y_train_sev, y_test_sev = y_severity, y_severity
            
            severity_model = xgb.XGBRegressor(
                n_estimators=150,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
            
            severity_model.fit(X_train_sev, y_train_sev)
            
            # Evaluate severity model
            sev_pred = severity_model.predict(X_test_sev)
            sev_mae = mean_absolute_error(y_test_sev, sev_pred)
            
            logger.info(f"   📊 Severity model MAE: ${sev_mae:,.0f}")
        else:
            logger.warning("   ⚠️ Insufficient claim data for severity model")
            severity_model = None
        
        # Save models
        frequency_model.save_model(str(self.output_dir / "frequency_model.xgb"))
        if severity_model:
            severity_model.save_model(str(self.output_dir / "severity_model.xgb"))
        
        logger.info("   ✅ Frequency-Severity models trained successfully")
        
        return frequency_model, severity_model
    
    def _time_series_validation(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform time-series cross-validation for robust performance estimation."""
        
        logger.info("   📈 Running time-series cross-validation...")
        
        try:
            import xgboost as xgb
            from sklearn.metrics import roc_auc_score, precision_score, recall_score
            from sklearn.preprocessing import LabelEncoder
        except ImportError:
            return {'error': 'ML libraries not available'}
        
        # Sort by time
        df_sorted = df.sort_values(['driver_id', 'month']).copy()
        unique_months = sorted(df_sorted['month'].unique())
        
        if len(unique_months) < 6:
            logger.warning("   ⚠️ Insufficient time periods for time-series validation")
            return {'validation_type': 'insufficient_data'}
        
        # Time-series splits: train on first N months, test on N+1
        validation_results = []
        
        for i in range(6, len(unique_months)):  # Start from month 6, test on month 7, etc.
            train_months = unique_months[:i]
            test_months = [unique_months[i]]
            
            train_data = df_sorted[df_sorted['month'].isin(train_months)]
            test_data = df_sorted[df_sorted['month'].isin(test_months)]
            
            # Prepare features
            feature_columns = [col for col in df.columns if col not in [
                'driver_id', 'month', 'had_claim_in_period', 'claim_severity', 'claim_probability'
            ]]
            
            X_train = train_data[feature_columns].copy()
            X_test = test_data[feature_columns].copy()
            y_train = train_data['had_claim_in_period']
            y_test = test_data['had_claim_in_period']
            
            # Handle categorical variables
            le = LabelEncoder()
            X_train['data_source'] = le.fit_transform(X_train['data_source'].astype(str))
            X_test['data_source'] = le.transform(X_test['data_source'].astype(str))
            
            # Train model
            scale_pos_weight = (y_train == 0).sum() / max((y_train == 1).sum(), 1)
            
            model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                scale_pos_weight=scale_pos_weight,
                random_state=42
            )
            
            model.fit(X_train, y_train)
            
            # Evaluate
            y_pred_proba = model.predict_proba(X_test)[:, 1]
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            if len(set(y_test)) > 1:  # Need both classes for AUC
                auc = roc_auc_score(y_test, y_pred_proba)
            else:
                auc = 0.5
            
            precision = precision_score(y_test, y_pred, zero_division=0)
            recall = recall_score(y_test, y_pred, zero_division=0)
            
            validation_results.append({
                'test_month': test_months[0],
                'train_size': len(train_data),
                'test_size': len(test_data),
                'auc': auc,
                'precision': precision,
                'recall': recall,
                'claims_in_test': y_test.sum()
            })
        
        # Calculate average performance
        avg_metrics = {
            'avg_auc': np.mean([r['auc'] for r in validation_results]),
            'avg_precision': np.mean([r['precision'] for r in validation_results]),
            'avg_recall': np.mean([r['recall'] for r in validation_results]),
            'std_auc': np.std([r['auc'] for r in validation_results]),
            'validation_splits': len(validation_results)
        }
        
        logger.info(f"   📊 Time-series validation complete:")
        logger.info(f"      • Average AUC: {avg_metrics['avg_auc']:.3f} ± {avg_metrics['std_auc']:.3f}")
        logger.info(f"      • Average Precision: {avg_metrics['avg_precision']:.3f}")
        logger.info(f"      • Average Recall: {avg_metrics['avg_recall']:.3f}")
        
        return {
            'validation_type': 'time_series',
            'results': validation_results,
            'average_metrics': avg_metrics
        }
    
    def _final_evaluation(self, df: pd.DataFrame, frequency_model: Any, severity_model: Any, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final evaluation and risk scoring system."""
        
        logger.info("   🎯 Generating final evaluation...")
        
        # Prepare test data
        feature_columns = [col for col in df.columns if col not in [
            'driver_id', 'month', 'had_claim_in_period', 'claim_severity', 'claim_probability'
        ]]
        
        X = df[feature_columns].copy()
        
        # Handle categorical variables
        from sklearn.preprocessing import LabelEncoder
        le = LabelEncoder()
        X['data_source'] = le.fit_transform(X['data_source'].astype(str))
        
        # Generate predictions
        claim_probabilities = frequency_model.predict_proba(X)[:, 1]
        
        if severity_model and len(df[df['had_claim_in_period']]) > 0:
            # Predict severity for all drivers (expected severity)
            expected_severities = severity_model.predict(X)
            expected_loss = claim_probabilities * expected_severities
        else:
            # Use average claim cost if no severity model
            avg_claim_cost = df[df['claim_severity'] > 0]['claim_severity'].mean() if (df['claim_severity'] > 0).any() else 5000
            expected_loss = claim_probabilities * avg_claim_cost
        
        # Create risk scores
        df['predicted_claim_probability'] = claim_probabilities
        df['expected_annual_loss'] = expected_loss * 12  # Convert monthly to annual
        
        # Risk tiers
        df['risk_tier'] = pd.cut(
            df['expected_annual_loss'], 
            bins=5, 
            labels=['Very Low', 'Low', 'Medium', 'High', 'Very High']
        )
        
        # Save enhanced dataset
        output_path = self.output_dir / "production_training_data.csv"
        df.to_csv(output_path, index=False)
        
        # Generate summary statistics
        summary = {
            'dataset_info': {
                'total_records': len(df),
                'total_drivers': df['driver_id'].nunique(),
                'time_period_months': df['month'].nunique(),
                'claim_rate': df['had_claim_in_period'].mean(),
                'avg_claim_severity': df[df['claim_severity'] > 0]['claim_severity'].mean() if (df['claim_severity'] > 0).any() else 0
            },
            'model_performance': validation_results.get('average_metrics', {}),
            'risk_distribution': df['risk_tier'].value_counts().to_dict(),
            'feature_count': len(feature_columns),
            'output_files': {
                'training_data': str(output_path),
                'frequency_model': str(self.output_dir / "frequency_model.xgb"),
                'severity_model': str(self.output_dir / "severity_model.xgb") if severity_model else None
            }
        }
        
        # Save summary
        summary_path = self.output_dir / "production_pipeline_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        logger.info(f"   ✅ Final evaluation complete")
        logger.info(f"   📄 Enhanced dataset: {output_path}")
        logger.info(f"   📊 Summary: {summary_path}")
        
        return summary


def main():
    """Execute the production-scale pipeline."""
    print("\n" + "="*70)
    print("🏭 PRODUCTION-SCALE TELEMATICS PIPELINE")
    print("📊 2-Day Sprint: From POC to Robust Model")
    print("="*70)
    
    print(f"\n🎯 Mission: Dramatically improve model robustness")
    print(f"📈 Strategy: Scale up data + advanced techniques")
    print(f"🚀 Target: Production-ready model in < 2 hours")
    
    # Configuration options
    print(f"\n🔧 Scale Options:")
    print(f"   1. Full Production Scale (1,000 drivers, 18 months)")
    print(f"   2. Large Test Scale (500 drivers, 12 months)")
    print(f"   3. Medium Test Scale (200 drivers, 6 months)")
    
    choice = input(f"\n🔢 Choose scale (1-3): ").strip()
    
    if choice == '1':
        pipeline = ProductionScalePipeline(full_scale=True)
        scale_name = "Full Production"
    elif choice == '2':
        # Medium scale for testing
        pipeline = ProductionScalePipeline(full_scale=False)
        pipeline.drivers_count = 500
        pipeline.months_count = 12
        scale_name = "Large Test"
    else:
        pipeline = ProductionScalePipeline(full_scale=False)
        scale_name = "Medium Test"
    
    print(f"\n✅ Selected: {scale_name} Scale")
    
    try:
        results = pipeline.execute_production_pipeline()
        
        print(f"\n🎉 PRODUCTION PIPELINE COMPLETED!")
        print(f"\n📊 Results Summary:")
        print(f"   • Dataset: {results['dataset_info']['total_records']:,} records")
        print(f"   • Drivers: {results['dataset_info']['total_drivers']:,}")
        print(f"   • Claim Rate: {results['dataset_info']['claim_rate']:.2%}")
        
        if 'model_performance' in results and results['model_performance']:
            perf = results['model_performance']
            print(f"   • Model AUC: {perf.get('avg_auc', 0):.3f}")
            print(f"   • Precision: {perf.get('avg_precision', 0):.3f}")
            print(f"   • Recall: {perf.get('avg_recall', 0):.3f}")
        
        print(f"\n📁 Output Files:")
        for name, path in results['output_files'].items():
            if path:
                print(f"   • {name}: {path}")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Production pipeline failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
