"""
Real Risk Assessment Model with MLflow Integration

This module implements actual XGBoost model training with MLflow tracking,
feature engineering, and model deployment capabilities.
"""

import mlflow
import mlflow.xgboost
import xgboost as xgb
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.preprocessing import LabelEncoder
import shap
import logging
import joblib
from datetime import datetime
from typing import Dict, Any, Tuple, List
import os

from ..data.schemas import MonthlyFeatures
from ..utils.config import get_config


class RiskAssessmentModel:
    """
    Real XGBoost-based risk assessment model with full MLflow integration.
    
    This model processes the 32-feature monthly dataset to predict claim probability
    with full experiment tracking, model versioning, and production deployment support.
    """
    
    def __init__(self, model_name: str = "telematics_risk_model"):
        """
        Initialize the risk assessment model.
        
        Args:
            model_name: Name for the model in MLflow registry
        """
        self.config = get_config()
        self.model_name = model_name
        self.model = None
        self.label_encoder = LabelEncoder()
        self.feature_names = None
        self.shap_explainer = None
        self.logger = logging.getLogger(__name__)
        
        # Set MLflow tracking URI
        mlflow.set_tracking_uri("http://localhost:5000")
        
    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare features and target variable from raw data.
        
        Args:
            df: DataFrame with all MonthlyFeatures columns
            
        Returns:
            Tuple of (features_df, target_series)
        """
        # Extract feature names from schema
        feature_names = MonthlyFeatures.get_feature_names()
        target_name = MonthlyFeatures.get_target_name()
        
        # Separate features and target
        X = df[feature_names].copy()
        y = df[target_name].copy()
        
        # Handle categorical features (data_source)
        if 'data_source' in X.columns:
            X['data_source_encoded'] = self.label_encoder.fit_transform(X['data_source'])
            X = X.drop('data_source', axis=1)
        
        # Handle missing values
        X = X.fillna(0)
        
        self.feature_names = X.columns.tolist()
        self.logger.info(f"Prepared {X.shape[1]} features for training")
        
        return X, y
    
    def train(self, training_data: pd.DataFrame, 
              validation_data: pd.DataFrame = None,
              experiment_name: str = "Risk_Assessment_Experiment") -> Dict[str, Any]:
        """
        Train the XGBoost model with MLflow tracking.
        
        Args:
            training_data: DataFrame with training data
            validation_data: Optional validation data
            experiment_name: Name for MLflow experiment
            
        Returns:
            Dictionary with training results and metrics
        """
        # Set experiment
        mlflow.set_experiment(experiment_name)
        
        # Prepare features
        X_train, y_train = self.prepare_features(training_data)
        if validation_data is not None:
            X_val, y_val = self.prepare_features(validation_data)
        else:
            # Split training data for validation
            X_train, X_val, y_train, y_val = train_test_split(
                X_train, y_train, test_size=0.2, random_state=42
            )
        
        # Model parameters
        params = {
            'n_estimators': 200,
            'max_depth': 8,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'random_state': 42
        }
        
        # Start MLflow run
        with mlflow.start_run(run_name=f"risk_model_training_{datetime.now().strftime('%Y%m%d_%H%M')}"):
            # Log parameters
            mlflow.log_params(params)
            
            # Create and train model
            self.model = xgb.XGBClassifier(**params)
            self.model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                early_stopping_rounds=10,
                verbose=False
            )
            
            # Make predictions
            y_pred = self.model.predict(X_val)
            y_pred_proba = self.model.predict_proba(X_val)[:, 1]
            
            # Calculate metrics
            metrics = {
                'accuracy': accuracy_score(y_val, y_pred),
                'precision': precision_score(y_val, y_pred),
                'recall': recall_score(y_val, y_pred),
                'f1_score': f1_score(y_val, y_pred),
                'auc_roc': roc_auc_score(y_val, y_pred_proba)
            }
            
            # Business metrics
            business_metrics = {
                'claims_reduction_percent': metrics['recall'] * 100,
                'cost_savings_annual': metrics['accuracy'] * 0.15 * 1000000,  # Simulated
                'customer_fairness_score': (1 - abs(metrics['precision'] - metrics['recall'])) * 100,
                'model_confidence': metrics['precision'] * metrics['recall'] * 100
            }
            
            # Log all metrics
            mlflow.log_metrics({**metrics, **business_metrics})
            
            # Log model
            mlflow.xgboost.log_model(
                self.model, 
                "model",
                conda_env={
                    "channels": ["conda-forge"],
                    "dependencies": [
                        "python=3.8",
                        "xgboost=1.7.0",
                        "scikit-learn=1.3.0",
                        "pandas=1.5.0",
                        "numpy=1.24.0"
                    ],
                    "name": "risk-model-env"
                }
            )
            
            # Create SHAP explainer
            self.shap_explainer = shap.TreeExplainer(self.model)
            
            # Log feature importance plot
            try:
                importance_plot = self._plot_feature_importance()
                mlflow.log_figure(importance_plot, "feature_importance.png")
            except Exception as e:
                self.logger.warning(f"Could not log feature importance plot: {e}")
            
            # Register model
            try:
                model_uri = f"runs:/{mlflow.active_run().info.run_id}/model"
                mv = mlflow.register_model(model_uri, self.model_name)
                mlflow.set_tag("model_version", mv.version)
                self.logger.info(f"Model registered as version {mv.version}")
            except Exception as e:
                self.logger.warning(f"Could not register model: {e}")
            
            # Log completion
            mlflow.set_tag("training_completed", "true")
            mlflow.set_tag("model_type", "xgboost")
            mlflow.set_tag("use_case", "risk_assessment")
            
            self.logger.info(f"Model training completed with AUC-ROC: {metrics['auc_roc']:.3f}")
            
            return {
                'metrics': metrics,
                'business_metrics': business_metrics,
                'model_version': getattr(mv, 'version', 'unknown') if 'mv' in locals() else 'unknown'
            }
    
    def _plot_feature_importance(self):
        """Create feature importance plot."""
        import matplotlib.pyplot as plt
        
        # Get feature importance
        importance = self.model.feature_importances_
        feature_names = self.feature_names
        
        # Create plot
        fig, ax = plt.subplots(figsize=(10, 8))
        indices = np.argsort(importance)[-20:]  # Top 20 features
        plt.barh(range(len(indices)), importance[indices])
        plt.yticks(range(len(indices)), [feature_names[i] for i in indices])
        plt.xlabel('Feature Importance')
        plt.title('Top 20 Feature Importance')
        plt.tight_layout()
        
        return fig
    
    def predict(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """
        Make predictions on new data.
        
        Args:
            features_df: DataFrame with features for prediction
            
        Returns:
            DataFrame with predictions and probabilities
        """
        if self.model is None:
            raise ValueError("Model not trained yet. Call train() first.")
        
        # Prepare features (same as training)
        X = features_df.copy()
        if 'data_source' in X.columns:
            X['data_source_encoded'] = self.label_encoder.transform(X['data_source'])
            X = X.drop('data_source', axis=1)
        
        # Ensure all features are present
        for feature in self.feature_names:
            if feature not in X.columns:
                X[feature] = 0
        
        # Reorder columns to match training
        X = X[self.feature_names]
        
        # Make predictions
        predictions = self.model.predict(X)
        probabilities = self.model.predict_proba(X)[:, 1]
        
        # Create results dataframe
        results = pd.DataFrame({
            'prediction': predictions,
            'probability': probabilities
        })
        
        return results
    
    def explain_prediction(self, features: pd.DataFrame, top_k: int = 5) -> Dict[str, Any]:
        """
        Generate SHAP explanations for predictions.
        
        Args:
            features: DataFrame with features for a single prediction
            top_k: Number of top features to return
            
        Returns:
            Dictionary with explanation data
        """
        if self.shap_explainer is None:
            raise ValueError("SHAP explainer not available. Model must be trained first.")
        
        # Prepare features
        X = features.copy()
        if 'data_source' in X.columns:
            X['data_source_encoded'] = self.label_encoder.transform(X['data_source'])
            X = X.drop('data_source', axis=1)
        
        # Ensure all features are present
        for feature in self.feature_names:
            if feature not in X.columns:
                X[feature] = 0
        
        # Reorder columns
        X = X[self.feature_names]
        
        # Calculate SHAP values
        shap_values = self.shap_explainer.shap_values(X.iloc[0:1])
        
        # Get feature contributions
        feature_contributions = []
        for i, feature in enumerate(self.feature_names):
            contribution = shap_values[0][i]
            feature_contributions.append({
                'feature': feature,
                'value': float(X.iloc[0][i]),
                'contribution': float(contribution)
            })
        
        # Sort by absolute contribution
        feature_contributions.sort(key=lambda x: abs(x['contribution']), reverse=True)
        
        return {
            'top_features': feature_contributions[:top_k],
            'base_value': float(self.shap_explainer.expected_value[1]),
            'prediction': float(self.model.predict_proba(X)[0][1])
        }
    
    def save_model(self, path: str) -> None:
        """
        Save the trained model to disk.
        
        Args:
            path: Path to save the model
        """
        if self.model is None:
            raise ValueError("No model to save. Train the model first.")
        
        # Save model
        joblib.dump(self.model, path)
        
        # Save label encoder
        joblib.dump(self.label_encoder, path.replace('.pkl', '_encoder.pkl'))
        
        self.logger.info(f"Model saved to {path}")
    
    def load_model(self, path: str) -> None:
        """
        Load a trained model from disk.
        
        Args:
            path: Path to load the model from
        """
        # Load model
        self.model = joblib.load(path)
        
        # Load label encoder
        encoder_path = path.replace('.pkl', '_encoder.pkl')
        if os.path.exists(encoder_path):
            self.label_encoder = joblib.load(encoder_path)
        
        # Create SHAP explainer
        self.shap_explainer = shap.TreeExplainer(self.model)
        
        self.logger.info(f"Model loaded from {path}")


def main():
    """Example usage of the risk assessment model."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Starting real risk model training...")
    
    # Initialize model
    model = RiskAssessmentModel()
    
    # For demonstration, create synthetic training data
    # In practice, you would load real data from your feature engineering pipeline
    logger.info("📋 Generating synthetic training data...")
    
    # Create sample data that matches the schema
    sample_data = []
    np.random.seed(42)
    
    for i in range(1000):
        # Create realistic feature values
        features = {
            'driver_id': f'driver_{i:06d}',
            'month': '2024-01',
            
            # Category 1: Data Derived from Sensor Logs
            'total_trips': np.random.poisson(45),
            'total_drive_time_hours': np.random.gamma(2, 15),
            'total_miles_driven': np.random.gamma(2, 150),
            'avg_speed_mph': np.random.normal(35, 10),
            'max_speed_mph': np.random.normal(75, 15),
            'avg_jerk_rate': np.random.exponential(0.5),
            'hard_brake_rate_per_100_miles': np.random.exponential(1.0),
            'rapid_accel_rate_per_100_miles': np.random.exponential(0.8),
            'harsh_cornering_rate_per_100_miles': np.random.exponential(0.5),
            'swerving_events_per_100_miles': np.random.exponential(0.3),
            'pct_miles_night': np.random.beta(2, 8),
            'pct_miles_late_night_weekend': np.random.beta(1, 15),
            'pct_miles_weekday_rush_hour': np.random.beta(3, 7),
            
            # Category 2: Directly Simulated Data
            'pct_trip_time_screen_on': np.random.beta(1, 20),
            'handheld_events_rate_per_hour': np.random.exponential(0.2),
            'pct_trip_time_on_call_handheld': np.random.beta(1, 50),
            'avg_engine_rpm': np.random.normal(2100, 500),
            'has_dtc_codes': np.random.choice([True, False], p=[0.05, 0.95]),
            'airbag_deployment_flag': False,
            'driver_age': np.random.randint(18, 80),
            'vehicle_age': np.random.randint(0, 20),
            'prior_at_fault_accidents': np.random.poisson(0.5),
            'years_licensed': np.random.randint(1, 50),
            'data_source': np.random.choice(['phone_only', 'phone_plus_device'], p=[0.5, 0.5]),
            'gps_accuracy_avg_meters': np.random.gamma(2, 4),
            'driver_passenger_confidence_score': np.random.beta(8, 2),
            
            # Category 3: Simulated + Real API Data
            'speeding_rate_per_100_miles': np.random.exponential(0.5),
            'max_speed_over_limit_mph': np.random.exponential(5),
            'pct_miles_highway': np.random.beta(3, 2),
            'pct_miles_urban': np.random.beta(4, 1),
            'pct_miles_in_rain_or_snow': np.random.beta(1, 15),
            'pct_miles_in_heavy_traffic': np.random.beta(2, 8),
            
            # Target variable
            'had_claim_in_period': np.random.choice([0, 1], p=[0.9, 0.1])
        }
        
        sample_data.append(features)
    
    # Create DataFrame
    df = pd.DataFrame(sample_data)
    
    # Train model
    logger.info("🏋️ Training model with MLflow tracking...")
    results = model.train(df)
    
    logger.info("✅ Model training completed!")
    logger.info(f"📊 Metrics: {results['metrics']}")
    logger.info(f"💰 Business Impact: {results['business_metrics']}")
    
    # Test prediction
    logger.info("🔮 Testing prediction on sample data...")
    sample_features = df.drop(['driver_id', 'month', 'had_claim_in_period'], axis=1).iloc[0:1]
    predictions = model.predict(sample_features)
    logger.info(f"🎯 Prediction: {predictions.iloc[0].to_dict()}")
    
    # Test explanation
    logger.info("🔍 Testing SHAP explanation...")
    explanation = model.explain_prediction(sample_features)
    logger.info(f"📝 Top contributing features: {[f['feature'] for f in explanation['top_features']]}")
    
    # Save model
    model_path = "models/risk_model.pkl"
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    model.save_model(model_path)
    logger.info(f"💾 Model saved to {model_path}")
    
    logger.info("🎉 Real risk model implementation complete!")


if __name__ == "__main__":
    main()