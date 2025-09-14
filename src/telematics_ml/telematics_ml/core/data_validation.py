"""Data validation utilities for the telematics system."""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..data.schemas import GPSPoint, IMUReading, TripData


class DataValidator:
    """Validates telematics data for quality and consistency."""
    
    @staticmethod
    def validate_gps_point(point: GPSPoint) -> List[str]:
        """
        Validate a GPS point for reasonable values.
        
        Args:
            point: GPS point to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Latitude validation (-90 to 90)
        if not (-90 <= point.latitude <= 90):
            errors.append(f"Invalid latitude: {point.latitude}")
        
        # Longitude validation (-180 to 180)
        if not (-180 <= point.longitude <= 180):
            errors.append(f"Invalid longitude: {point.longitude}")
        
        # Speed validation (reasonable driving speeds)
        if point.speed_mph is not None and (point.speed_mph < 0 or point.speed_mph > 200):
            errors.append(f"Invalid speed: {point.speed_mph} mph")
        
        # Accuracy validation
        if point.accuracy_meters < 0 or point.accuracy_meters > 1000:
            errors.append(f"Invalid GPS accuracy: {point.accuracy_meters} meters")
        
        return errors
    
    @staticmethod
    def validate_imu_reading(reading: IMUReading) -> List[str]:
        """
        Validate an IMU reading for reasonable values.
        
        Args:
            reading: IMU reading to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Accelerometer validation (reasonable G-force limits)
        for axis, value in [('x', reading.accel_x), ('y', reading.accel_y), ('z', reading.accel_z)]:
            if abs(value) > 20:  # 20G is extreme but possible in crashes
                errors.append(f"Extreme acceleration on {axis}-axis: {value}G")
        
        # Gyroscope validation (reasonable rotation rates)
        for axis, value in [('x', reading.gyro_x), ('y', reading.gyro_y), ('z', reading.gyro_z)]:
            if abs(value) > 2000:  # 2000 deg/s is very high
                errors.append(f"Extreme rotation on {axis}-axis: {value} deg/s")
        
        return errors
    
    @staticmethod
    def validate_trip_data(trip: TripData) -> Dict[str, List[str]]:
        """
        Validate complete trip data.
        
        Args:
            trip: Trip data to validate
            
        Returns:
            Dictionary of validation results by category
        """
        results = {
            'gps_errors': [],
            'imu_errors': [],
            'trip_errors': [],
            'timing_errors': []
        }
        
        # Trip-level validation
        if trip.end_time <= trip.start_time:
            results['trip_errors'].append("End time must be after start time")
        
        if trip.total_distance_miles < 0:
            results['trip_errors'].append(f"Invalid distance: {trip.total_distance_miles}")
        
        if trip.avg_speed_mph < 0 or trip.avg_speed_mph > 200:
            results['trip_errors'].append(f"Invalid average speed: {trip.avg_speed_mph} mph")
        
        if not (0 <= trip.data_completeness_pct <= 100):
            results['trip_errors'].append(f"Invalid data completeness: {trip.data_completeness_pct}%")
        
        # GPS validation
        for i, point in enumerate(trip.gps_points):
            point_errors = DataValidator.validate_gps_point(point)
            if point_errors:
                results['gps_errors'].extend([f"Point {i}: {err}" for err in point_errors])
        
        # IMU validation
        for i, reading in enumerate(trip.imu_readings):
            reading_errors = DataValidator.validate_imu_reading(reading)
            if reading_errors:
                results['imu_errors'].extend([f"Reading {i}: {err}" for err in reading_errors])
        
        # Timing validation
        DataValidator._validate_timing_consistency(trip, results['timing_errors'])
        
        return results
    
    @staticmethod
    def _validate_timing_consistency(trip: TripData, errors: List[str]) -> None:
        """Validate timing consistency across all data streams."""
        all_timestamps = []
        
        # Collect all timestamps
        all_timestamps.extend([p.timestamp for p in trip.gps_points])
        all_timestamps.extend([r.timestamp for r in trip.imu_readings])
        all_timestamps.extend([e.timestamp for e in trip.behavioral_events])
        
        if not all_timestamps:
            errors.append("No timestamp data found")
            return
        
        # Check if timestamps are within trip bounds
        min_timestamp = min(all_timestamps)
        max_timestamp = max(all_timestamps)
        
        if min_timestamp < trip.start_time:
            errors.append(f"Data timestamp before trip start: {min_timestamp}")
        
        if max_timestamp > trip.end_time:
            errors.append(f"Data timestamp after trip end: {max_timestamp}")
    
    @staticmethod
    def validate_monthly_features(features_df: pd.DataFrame) -> Dict[str, List[str]]:
        """
        Validate monthly feature data for ML model input.
        
        Args:
            features_df: DataFrame with monthly features
            
        Returns:
            Dictionary of validation results
        """
        results = {
            'missing_data': [],
            'range_errors': [],
            'consistency_errors': []
        }
        
        # Required columns check
        required_columns = [
            'driver_id', 'month', 'total_trips', 'total_miles_driven',
            'hard_brake_rate', 'speeding_rate', 'driver_age'
        ]
        
        missing_columns = [col for col in required_columns if col not in features_df.columns]
        if missing_columns:
            results['missing_data'].append(f"Missing columns: {missing_columns}")
        
        # Range validation
        if 'total_trips' in features_df.columns:
            invalid_trips = features_df[features_df['total_trips'] < 0]
            if len(invalid_trips) > 0:
                results['range_errors'].append(f"{len(invalid_trips)} records with negative trip count")
        
        if 'total_miles_driven' in features_df.columns:
            invalid_miles = features_df[features_df['total_miles_driven'] < 0]
            if len(invalid_miles) > 0:
                results['range_errors'].append(f"{len(invalid_miles)} records with negative miles")
        
        if 'driver_age' in features_df.columns:
            invalid_age = features_df[(features_df['driver_age'] < 16) | (features_df['driver_age'] > 100)]
            if len(invalid_age) > 0:
                results['range_errors'].append(f"{len(invalid_age)} records with invalid driver age")
        
        # Percentage validation
        percentage_columns = [col for col in features_df.columns if 'pct_' in col]
        for col in percentage_columns:
            if col in features_df.columns:
                invalid_pct = features_df[(features_df[col] < 0) | (features_df[col] > 1)]
                if len(invalid_pct) > 0:
                    results['range_errors'].append(f"{len(invalid_pct)} records with invalid {col}")
        
        # Consistency checks
        if 'total_trips' in features_df.columns and 'total_miles_driven' in features_df.columns:
            # Check for unreasonable trip distances
            features_df['avg_trip_distance'] = features_df['total_miles_driven'] / features_df['total_trips']
            unreasonable = features_df[features_df['avg_trip_distance'] > 500]  # 500+ miles per trip
            if len(unreasonable) > 0:
                results['consistency_errors'].append(f"{len(unreasonable)} records with unreasonable trip distances")
        
        return results
    
    @staticmethod
    def generate_data_quality_report(validation_results: Dict[str, Any]) -> str:
        """
        Generate a human-readable data quality report.
        
        Args:
            validation_results: Results from validation functions
            
        Returns:
            Formatted report string
        """
        report = ["Data Quality Report", "=" * 50]
        
        total_errors = 0
        for category, errors in validation_results.items():
            if errors:
                report.append(f"\n{category.upper()}:")
                for error in errors:
                    report.append(f"  - {error}")
                    total_errors += 1
        
        if total_errors == 0:
            report.append("\n✅ All validations passed - data quality is good!")
        else:
            report.append(f"\n⚠️ Found {total_errors} data quality issues")
        
        return "\n".join(report)
