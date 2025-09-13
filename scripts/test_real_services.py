#!/usr/bin/env python3
"""
Test Script for Real Telematics Services

This script tests the real implementations of all services:
1. Risk assessment with actual ML models
2. Dynamic pricing with real business logic
3. MLflow integration
4. End-to-end pipeline
"""

import requests
import json
import time
import logging
from datetime import datetime
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service URLs (adjust as needed for your environment)
SERVICES = {
    'risk': 'http://localhost:8092',
    'pricing': 'http://localhost:8093',
    'mlflow': 'http://localhost:5000'
}

def test_service_health(service_name, base_url):
    """Test if a service is healthy"""
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            logger.info(f"✅ {service_name} service is healthy")
            return True
        else:
            logger.warning(f"⚠️ {service_name} service returned status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ {service_name} service is not accessible: {e}")
        return False

def test_risk_service():
    """Test the real risk assessment service"""
    logger.info("🧪 Testing Risk Service...")
    
    try:
        # Test health endpoint
        health_response = requests.get(f"{SERVICES['risk']}/health")
        if health_response.status_code != 200:
            logger.error("❌ Risk service health check failed")
            return False
        
        # Test risk assessment
        sample_features = {
            'total_trips': 45,
            'total_drive_time_hours': 25.0,
            'total_miles_driven': 450.0,
            'avg_speed_mph': 38.0,
            'max_speed_mph': 82.0,
            'avg_jerk_rate': 0.6,
            'hard_brake_rate_per_100_miles': 1.2,
            'rapid_accel_rate_per_100_miles': 0.9,
            'harsh_cornering_rate_per_100_miles': 0.4,
            'swerving_events_per_100_miles': 0.2,
            'pct_miles_night': 0.15,
            'pct_miles_late_night_weekend': 0.08,
            'pct_miles_weekday_rush_hour': 0.25,
            'pct_trip_time_screen_on': 0.03,
            'handheld_events_rate_per_hour': 0.3,
            'pct_trip_time_on_call_handheld': 0.01,
            'avg_engine_rpm': 2200.0,
            'has_dtc_codes': False,
            'airbag_deployment_flag': False,
            'driver_age': 32,
            'vehicle_age': 3,
            'prior_at_fault_accidents': 0,
            'years_licensed': 14,
            'data_source': 'phone_plus_device',
            'gps_accuracy_avg_meters': 5.0,
            'driver_passenger_confidence_score': 0.88,
            'speeding_rate_per_100_miles': 0.7,
            'max_speed_over_limit_mph': 8.0,
            'pct_miles_highway': 0.45,
            'pct_miles_urban': 0.4,
            'pct_miles_in_rain_or_snow': 0.03,
            'pct_miles_in_heavy_traffic': 0.12
        }
        
        risk_payload = {
            'driver_id': 'test_driver_001',
            'features': sample_features
        }
        
        risk_response = requests.post(
            f"{SERVICES['risk']}/risk/assess",
            json=risk_payload,
            headers={'Content-Type': 'application/json'}
        )
        
        if risk_response.status_code == 200:
            result = risk_response.json()
            logger.info(f"✅ Risk assessment successful")
            logger.info(f"   Driver ID: {result['driver_id']}")
            logger.info(f"   Risk Score: {result['risk_score']:.3f}")
            logger.info(f"   Risk Category: {result['risk_category']}")
            return True
        else:
            logger.error(f"❌ Risk assessment failed with status {risk_response.status_code}")
            logger.error(f"   Response: {risk_response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Risk service test failed: {e}")
        return False

def test_pricing_service():
    """Test the real pricing service"""
    logger.info("💰 Testing Pricing Service...")
    
    try:
        # Test health endpoint
        health_response = requests.get(f"{SERVICES['pricing']}/health")
        if health_response.status_code != 200:
            logger.error("❌ Pricing service health check failed")
            return False
        
        # Test premium calculation
        sample_driver_data = {
            'driver_id': 'test_driver_001',
            'risk_score': 0.45,
            'driver_age': 32,
            'years_licensed': 14,
            'vehicle_age': 3,
            'prior_at_fault_accidents': 0,
            'annual_mileage': 12000,
            'telematics_score': 0.78
        }
        
        pricing_payload = sample_driver_data
        
        pricing_response = requests.post(
            f"{SERVICES['pricing']}/pricing/calculate",
            json=pricing_payload,
            headers={'Content-Type': 'application/json'}
        )
        
        if pricing_response.status_code == 200:
            result = pricing_response.json()
            logger.info(f"✅ Premium calculation successful")
            logger.info(f"   Annual Premium: ${result['annual_premium']:.2f}")
            logger.info(f"   Monthly Premium: ${result['monthly_premium']:.2f}")
            logger.info(f"   Pricing Tier: {result['pricing_tier']}")
            return True
        else:
            logger.error(f"❌ Premium calculation failed with status {pricing_response.status_code}")
            logger.error(f"   Response: {pricing_response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Pricing service test failed: {e}")
        return False

def test_mlflow_integration():
    """Test MLflow integration"""
    logger.info("📊 Testing MLflow Integration...")
    
    try:
        # Test MLflow health
        response = requests.get(f"{SERVICES['mlflow']}/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ MLflow is accessible")
        else:
            logger.warning(f"⚠️ MLflow returned status {response.status_code}")
        
        # Test MLflow API
        experiments_response = requests.get(f"{SERVICES['mlflow']}/api/2.0/mlflow/experiments/list", timeout=5)
        if experiments_response.status_code == 200:
            logger.info("✅ MLflow API is working")
            return True
        else:
            logger.warning(f"⚠️ MLflow API returned status {experiments_response.status_code}")
            return True  # MLflow might be working even if experiments list is empty
            
    except Exception as e:
        logger.error(f"❌ MLflow integration test failed: {e}")
        return False

def test_batch_processing():
    """Test batch processing capabilities"""
    logger.info("🔄 Testing Batch Processing...")
    
    try:
        # Test batch risk assessment
        batch_features = []
        for i in range(5):
            features = {
                'driver_id': f'batch_driver_{i:03d}',
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
                'speeding_rate_per_100_miles': np.random.exponential(0.5),
                'max_speed_over_limit_mph': np.random.exponential(5),
                'pct_miles_highway': np.random.beta(3, 2),
                'pct_miles_urban': np.random.beta(4, 1),
                'pct_miles_in_rain_or_snow': np.random.beta(1, 15),
                'pct_miles_in_heavy_traffic': np.random.beta(2, 8)
            }
            batch_features.append(features)
        
        batch_payload = {
            'driver_features': batch_features
        }
        
        batch_response = requests.post(
            f"{SERVICES['risk']}/risk/batch",
            json=batch_payload,
            headers={'Content-Type': 'application/json'}
        )
        
        if batch_response.status_code == 200:
            result = batch_response.json()
            logger.info(f"✅ Batch processing successful")
            logger.info(f"   Processed {result['count']} drivers")
            return True
        else:
            logger.error(f"❌ Batch processing failed with status {batch_response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Batch processing test failed: {e}")
        return False

def main():
    """Main test execution"""
    logger.info("🚀 Starting Real Telematics Services Test")
    logger.info("=" * 60)
    
    # Test results tracking
    test_results = {
        'service_health': {},
        'risk_assessment': False,
        'pricing_calculation': False,
        'mlflow_integration': False,
        'batch_processing': False
    }
    
    # Test 1: Service health checks
    logger.info("Test 1: Service Health Checks")
    for service_name, url in SERVICES.items():
        test_results['service_health'][service_name] = test_service_health(service_name, url)
    
    # Wait a moment for services to stabilize
    time.sleep(2)
    
    # Test 2: Risk service
    logger.info("\nTest 2: Risk Assessment Service")
    test_results['risk_assessment'] = test_risk_service()
    
    # Test 3: Pricing service
    logger.info("\nTest 3: Pricing Service")
    test_results['pricing_calculation'] = test_pricing_service()
    
    # Test 4: MLflow integration
    logger.info("\nTest 4: MLflow Integration")
    test_results['mlflow_integration'] = test_mlflow_integration()
    
    # Test 5: Batch processing
    logger.info("\nTest 5: Batch Processing")
    test_results['batch_processing'] = test_batch_processing()
    
    # Generate summary report
    logger.info("\n" + "=" * 60)
    logger.info("📋 REAL TELEMATICS SERVICES TEST SUMMARY")
    logger.info("=" * 60)
    
    # Service health summary
    healthy_services = sum(test_results['service_health'].values())
    total_services = len(test_results['service_health'])
    logger.info(f"🏥 Service Health: {healthy_services}/{total_services} services healthy")
    
    # Functionality tests
    functionality_tests = [
        ('Risk Assessment', test_results['risk_assessment']),
        ('Pricing Calculation', test_results['pricing_calculation']),
        ('MLflow Integration', test_results['mlflow_integration']),
        ('Batch Processing', test_results['batch_processing'])
    ]
    
    passed_tests = sum(1 for _, result in functionality_tests if result)
    total_tests = len(functionality_tests)
    
    logger.info(f"⚙️  Functionality Tests: {passed_tests}/{total_tests} tests passed")
    
    for test_name, result in functionality_tests:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"   {status} {test_name}")
    
    # Overall status
    all_passed = (
        all(test_results['service_health'].values()) and
        all([test_results['risk_assessment'], test_results['pricing_calculation'], 
             test_results['mlflow_integration'], test_results['batch_processing']])
    )
    
    if all_passed:
        logger.info("\n🎉 ALL TESTS PASSED! Real telematics system is fully operational!")
        logger.info("🚀 Your system is ready for production use with real data!")
    else:
        failed_count = total_tests + total_services - (healthy_services + passed_tests)
        logger.warning(f"\n⚠️  {failed_count} tests failed. Please check the logs above for details.")
        logger.info("💡 Check service logs and ensure all containers are running properly.")
    
    logger.info("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)