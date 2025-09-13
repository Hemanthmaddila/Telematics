"""Configuration management for the telematics system."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class FeatureConfig:
    """Configuration for feature engineering parameters."""
    trip_gap_threshold_minutes: int
    min_trip_duration_minutes: int
    min_trip_distance_miles: float
    hard_brake_threshold_g: float
    rapid_accel_threshold_g: float
    harsh_corner_threshold_g: float
    speeding_threshold_mph: int


@dataclass
class ModelConfig:
    """Configuration for machine learning model parameters."""
    algorithm: str
    hyperparameters: Dict[str, Any]
    shap_min_feature_importance: float


@dataclass
class SimulationConfig:
    """Configuration for data simulation parameters."""
    num_drivers: int
    months_per_driver: int
    avg_trips_per_month: int
    personas: Dict[str, Dict[str, Any]]


class ConfigManager:
    """Manages configuration loading and validation for the telematics system."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration YAML file.
                        If None, looks for config.yaml in standard locations.
        """
        self.config_path = self._find_config_path(config_path)
        self._config = self._load_config()
        
    def _find_config_path(self, config_path: Optional[str]) -> Path:
        """Find the configuration file in standard locations."""
        if config_path:
            return Path(config_path)
        
        # Standard search locations
        search_paths = [
            Path("config/config.yaml"),
            Path("config.yaml"),
            Path("../config/config.yaml"),
            Path("../../config/config.yaml"),
        ]
        
        for path in search_paths:
            if path.exists():
                return path.resolve()
        
        raise FileNotFoundError(
            f"Configuration file not found. Searched: {[str(p) for p in search_paths]}"
        )
    
    def _load_config(self) -> Dict[str, Any]:
        """Load and validate the configuration file."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file {self.config_path}: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load config file {self.config_path}: {e}")
    
    @property
    def features(self) -> FeatureConfig:
        """Get feature engineering configuration."""
        config = self._config["features"]
        return FeatureConfig(
            trip_gap_threshold_minutes=config["trip_gap_threshold_minutes"],
            min_trip_duration_minutes=config["min_trip_duration_minutes"],
            min_trip_distance_miles=config["min_trip_distance_miles"],
            hard_brake_threshold_g=config["hard_brake_threshold_g"],
            rapid_accel_threshold_g=config["rapid_accel_threshold_g"],
            harsh_corner_threshold_g=config["harsh_corner_threshold_g"],
            speeding_threshold_mph=config["speeding_threshold_mph"]
        )
    
    @property
    def model(self) -> ModelConfig:
        """Get model configuration."""
        config = self._config["model"]
        return ModelConfig(
            algorithm=config["algorithm"],
            hyperparameters=config["hyperparameters"],
            shap_min_feature_importance=config["shap_min_feature_importance"]
        )
    
    @property
    def simulation(self) -> SimulationConfig:
        """Get simulation configuration."""
        config = self._config["simulation"]
        return SimulationConfig(
            num_drivers=config["num_drivers"],
            months_per_driver=config["months_per_driver"],
            avg_trips_per_month=config["avg_trips_per_month"],
            personas=config["personas"]
        )
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key using dot notation.
        
        Args:
            key: Configuration key (e.g., 'apis.weather.timeout_seconds')
            default: Default value if key is not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_data_path(self, dataset_name: str) -> Path:
        """Get the path for a specific dataset."""
        base_path = Path(self.get("data.raw_data_path", "./data/raw"))
        dataset_path = self.get(f"data.datasets.{dataset_name}")
        
        if dataset_path:
            return Path(dataset_path)
        else:
            return base_path / dataset_name
    
    def get_api_config(self, api_name: str) -> Dict[str, Any]:
        """Get configuration for a specific API."""
        return self.get(f"apis.{api_name}", {})
    
    def reload(self) -> None:
        """Reload the configuration from file."""
        self._config = self._load_config()


# Global configuration instance
_config_manager: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def set_config_path(config_path: str) -> None:
    """Set a custom configuration file path."""
    global _config_manager
    _config_manager = ConfigManager(config_path)
