#!/usr/bin/env python3
"""
REAL MODEL ANALYSIS: Show Actual Working Models on Real Data

This demonstrates the actual trained models working on real data,
showing concrete results, predictions, and performance metrics.
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
from sklearn.preprocessing import LabelEncoder
import matplotlib.pyplot as plt
# import seaborn as sns
from pathlib import Path

def load_and_analyze_real_models():
    """Load and analyze the actual trained models with real data."""
    
    print("=" * 60)
    print("🔍 REAL MODEL ANALYSIS: ACTUAL RESULTS")
    print("=" * 60)
    print()
    
    # Load the actual production dataset
    print("📊 Loading Production Dataset...")
    df = pd.read_csv('data/production/production_training_data.csv')
    print(f"   Records: {len(df):,}")
    print(f"   Features: {df.shape[1]} columns")
    print(f"   Actual claims: {df['had_claim_in_period'].sum():,}")
    print(f"   Claim rate: {df['had_claim_in_period'].mean():.2%}")
    print()
    
    # Load the trained model
    print("🤖 Loading Trained Model...")
    model = xgb.XGBClassifier()
    model.load_model('data/production/frequency_model.xgb')
    print("   ✅ Production XGBoost model loaded")
    print(f"   Features in model: {model.n_features_in_}")
    print()
    
    # Prepare features
    feature_columns = [col for col in df.columns if col not in [
        'driver_id', 'month', 'had_claim_in_period', 'claim_severity', 
        'claim_probability', 'predicted_claim_probability', 'expected_annual_loss', 'risk_tier'
    ]]
    
    X = df[feature_columns].copy()
    
    # Handle categorical variables
    le = LabelEncoder()
    if 'data_source' in X.columns:
        X['data_source'] = le.fit_transform(X['data_source'].astype(str))
    
    y_true = df['had_claim_in_period']
    
    print("🎯 Getting Real Model Predictions...")
    
    # Get actual predictions
    predictions = model.predict(X)
    probabilities = model.predict_proba(X)[:, 1]
    
    print(f"   Processed {len(X):,} real driver records")
    print()
    
    # Calculate performance metrics
    print("📈 ACTUAL MODEL PERFORMANCE")
    print("-" * 40)
    
    auc = roc_auc_score(y_true, probabilities)
    accuracy = (predictions == y_true).mean()
    
    print(f"AUC-ROC Score: {auc:.3f}")
    print(f"Accuracy: {accuracy:.3f}")
    print()
    
    # Confusion matrix
    tn, fp, fn, tp = confusion_matrix(y_true, predictions).ravel()
    
    print("Confusion Matrix (Actual Results):")
    print(f"   True Negatives:  {tn:,} (correct no-claim predictions)")
    print(f"   False Positives: {fp:,} (predicted claim, but no claim)")
    print(f"   False Negatives: {fn:,} (predicted no claim, but had claim)")
    print(f"   True Positives:  {tp:,} (correct claim predictions)")
    print()
    
    if tp + fp > 0:
        precision = tp / (tp + fp)
        print(f"Precision: {precision:.3f} (when model predicts claim, it's right {precision:.1%} of time)")
    
    if tp + fn > 0:
        recall = tp / (tp + fn)
        print(f"Recall: {recall:.3f} (model catches {recall:.1%} of actual claims)")
    print()
    
    # Risk score distribution
    print("📊 REAL RISK SCORE DISTRIBUTION")
    print("-" * 40)
    
    very_low = (probabilities < 0.02).sum()
    low = ((probabilities >= 0.02) & (probabilities < 0.05)).sum()
    medium = ((probabilities >= 0.05) & (probabilities < 0.10)).sum()
    high = ((probabilities >= 0.10) & (probabilities < 0.20)).sum()
    very_high = (probabilities >= 0.20).sum()
    
    total = len(probabilities)
    
    print(f"Very Low Risk (0-2%):   {very_low:5,} drivers ({very_low/total:.1%})")
    print(f"Low Risk (2-5%):        {low:5,} drivers ({low/total:.1%})")
    print(f"Medium Risk (5-10%):    {medium:5,} drivers ({medium/total:.1%})")
    print(f"High Risk (10-20%):     {high:5,} drivers ({high/total:.1%})")
    print(f"Very High Risk (20%+):  {very_high:5,} drivers ({very_high/total:.1%})")
    print()
    
    # Feature importance
    print("🔝 TOP 10 MOST IMPORTANT FEATURES")
    print("-" * 40)
    
    feature_importance = model.feature_importances_
    importance_df = pd.DataFrame({
        'feature': feature_columns,
        'importance': feature_importance
    }).sort_values('importance', ascending=False)
    
    for i, (_, row) in enumerate(importance_df.head(10).iterrows()):
        print(f"{i+1:2d}. {row['feature']:<35} {row['importance']:.4f}")
    print()
    
    # Analyze actual high-risk vs low-risk drivers
    print("⚖️  HIGH RISK vs LOW RISK DRIVER COMPARISON")
    print("-" * 40)
    
    high_risk_drivers = df[probabilities >= 0.10]  # Top 10%+ risk
    low_risk_drivers = df[probabilities < 0.02]   # Bottom 2% risk
    
    print(f"High Risk Drivers: {len(high_risk_drivers):,}")
    print(f"Low Risk Drivers: {len(low_risk_drivers):,}")
    print()
    
    # Compare key metrics
    comparisons = [
        ('hard_brake_rate_per_100_miles', 'Hard Braking Rate'),
        ('speeding_rate_per_100_miles', 'Speeding Rate'),
        ('pct_trip_time_screen_on', 'Phone Usage %'),
        ('driver_age', 'Driver Age'),
        ('total_miles_driven', 'Monthly Miles')
    ]
    
    for col, label in comparisons:
        if col in df.columns:
            high_avg = high_risk_drivers[col].mean()
            low_avg = low_risk_drivers[col].mean()
            diff = high_avg - low_avg
            
            print(f"{label:<25}: High={high_avg:6.1f}, Low={low_avg:6.1f}, Diff={diff:+6.1f}")
    print()
    
    # Show actual claim rates by risk tier
    print("💰 ACTUAL CLAIM RATES BY PREDICTED RISK")
    print("-" * 40)
    
    risk_bins = [
        (probabilities < 0.02, "Very Low (0-2%)"),
        ((probabilities >= 0.02) & (probabilities < 0.05), "Low (2-5%)"),
        ((probabilities >= 0.05) & (probabilities < 0.10), "Medium (5-10%)"),
        ((probabilities >= 0.10) & (probabilities < 0.20), "High (10-20%)"),
        (probabilities >= 0.20, "Very High (20%+)")
    ]
    
    for mask, label in risk_bins:
        if mask.sum() > 0:
            actual_rate = df[mask]['had_claim_in_period'].mean()
            count = mask.sum()
            print(f"{label:<20}: {actual_rate:.1%} actual claims ({count:,} drivers)")
    print()
    
    # Test on specific real drivers
    print("👥 REAL DRIVER EXAMPLES")
    print("-" * 40)
    
    # Get some actual drivers with different risk levels
    examples = []
    
    # Find a low-risk driver
    low_risk_idx = np.where(probabilities < 0.02)[0]
    if len(low_risk_idx) > 0:
        idx = low_risk_idx[0]
        examples.append(("Low Risk", idx, probabilities[idx]))
    
    # Find a medium-risk driver
    med_risk_idx = np.where((probabilities >= 0.05) & (probabilities < 0.10))[0]
    if len(med_risk_idx) > 0:
        idx = med_risk_idx[0]
        examples.append(("Medium Risk", idx, probabilities[idx]))
    
    # Find a high-risk driver
    high_risk_idx = np.where(probabilities >= 0.10)[0]
    if len(high_risk_idx) > 0:
        idx = high_risk_idx[0]
        examples.append(("High Risk", idx, probabilities[idx]))
    
    for risk_level, idx, prob in examples:
        driver_data = df.iloc[idx]
        print(f"\n{risk_level} Driver ({driver_data['driver_id']}):")
        print(f"   Predicted Risk: {prob:.1%}")
        print(f"   Actual Claim: {'YES' if driver_data['had_claim_in_period'] else 'NO'}")
        print(f"   Hard Braking: {driver_data['hard_brake_rate_per_100_miles']:.1f}/100mi")
        print(f"   Speeding: {driver_data['speeding_rate_per_100_miles']:.1f}/100mi")
        print(f"   Phone Usage: {driver_data['pct_trip_time_screen_on']:.1f}%")
        print(f"   Driver Age: {driver_data['driver_age']}")
        
        if 'expected_annual_loss' in driver_data:
            print(f"   Expected Loss: ${driver_data['expected_annual_loss']:,.0f}/year")
    
    print()
    print("✅ Real model analysis complete!")
    print("📊 All results above are from actual trained models on real data")
    
    return {
        'model': model,
        'predictions': predictions,
        'probabilities': probabilities,
        'performance': {'auc': auc, 'accuracy': accuracy},
        'feature_importance': importance_df
    }


if __name__ == "__main__":
    results = load_and_analyze_real_models()
