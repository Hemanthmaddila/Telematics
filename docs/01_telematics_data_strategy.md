# 📊 Telematics Data Strategy & Master Feature Set

## Executive Summary

This document defines the comprehensive data strategy for building a production-grade telematics insurance risk assessment system. Based on extensive industry research and analysis of leading insurance carriers (Progressive, State Farm, GEICO, USAA), we've designed a unified approach that handles both smartphone-only and device-augmented users through a single, sophisticated machine learning model.

## Core Principle: Unified Data Architecture

Our system operates on the principle of **"One App, Two Data Sources"** - the smartphone app serves as the universal hub for all users, with optional augmentation from OBD-II devices for enhanced data quality.

### User Types Supported

#### Type 1: Phone-Only Users
- **Data Source**: Smartphone app using internal sensors (GPS, accelerometer, gyroscope)
- **Coverage**: All behavioral features, phone usage patterns, contextual data
- **Limitations**: No vehicle system data, slightly lower GPS accuracy
- **Market Share**: ~60-70% of telematics users

#### Type 2: Phone + Device Users  
- **Data Source**: Smartphone app + OBD-II device via Bluetooth
- **Coverage**: All features with enhanced vehicle system data
- **Advantages**: Higher accuracy, vehicle health data, fraud prevention
- **Market Share**: ~30-40% of telematics users (growing)

## The Master Feature Set (32 Variables)

Our machine learning model uses 32 carefully selected features that represent the gold standard in telematics risk assessment:

### 1. Trip & Kinematics Features (6 variables)
```
total_trips                 - Number of journeys in the month
total_drive_time_hours     - Total driving duration 
total_miles_driven         - Total distance covered
avg_speed_mph              - Average speed across all trips
max_speed_mph              - Highest speed recorded
avg_jerk_rate              - Smoothness of driving (rate of acceleration change)
```

### 2. Behavioral Event Features (6 variables)
```
hard_brake_rate_per_100_miles      - Hard braking events (< -0.4g) per 100 miles
rapid_accel_rate_per_100_miles     - Rapid acceleration (> 0.4g) per 100 miles  
harsh_cornering_rate_per_100_miles - Sharp turns (> 0.4g lateral) per 100 miles
swerving_events_per_100_miles      - Opposing lateral G-forces per 100 miles
speeding_rate_per_100_miles        - Speed >10mph over limit per 100 miles
max_speed_over_limit_mph           - Worst speeding violation of the month
```

### 3. Phone Usage Features (3 variables)
```
pct_trip_time_screen_on           - % of driving time with screen active
handheld_events_rate_per_hour     - Phone handling events per hour
pct_trip_time_on_call_handheld    - % time on non-hands-free calls
```

### 4. Usage & Exposure Features (3 variables)
```
pct_miles_night                   - % miles driven 9PM-5AM
pct_miles_late_night_weekend      - % miles driven Fri/Sat 11PM-4AM  
pct_miles_weekday_rush_hour       - % miles driven peak commute times
```

### 5. Context & Environment Features (5 variables)
```
pct_miles_highway                 - % miles on highways/interstates
pct_miles_urban                   - % miles in dense urban areas
pct_miles_in_rain                 - % miles driven in rain
pct_miles_in_snow                 - % miles driven in snow
pct_miles_in_heavy_traffic        - % miles in heavy traffic conditions
```

### 6. Vehicle & Diagnostics Features (3 variables)
```
avg_engine_rpm                    - Average engine RPM (device users)
has_dtc_codes                     - Binary flag for diagnostic trouble codes
airbag_deployment_flag            - Binary flag for severe crash events
```

### 7. Driver Profile Features (4 variables)
```
driver_age                        - Driver's age in years
vehicle_age                       - Vehicle's age in years  
prior_at_fault_accidents          - At-fault accidents in last 3 years
years_licensed                    - Years holding driver's license
```

### 8. Data Provenance Features (3 variables)
```
data_source                       - "phone_only" or "phone_plus_device"
gps_accuracy_avg_meters           - Average GPS accuracy (quality indicator)
driver_passenger_confidence_score - Confidence user was driving (0.0-1.0)
```

## Smart Defaults Strategy

The key to our unified model is the **Smart Defaults** approach for handling missing data:

### For Phone-Only Users:
```python
# Vehicle system features are imputed with neutral defaults
avg_engine_rpm = 2200                    # Population average for safe drivers
has_dtc_codes = 0                        # Assume no diagnostic codes
airbag_deployment_flag = 0               # No crash detection available
data_source = "phone_only"              # Flag for model interpretation
```

### For Phone + Device Users:
```python
# All features populated with real device data
avg_engine_rpm = actual_rpm_from_obd     # Real engine data
has_dtc_codes = obd_diagnostic_status    # Actual vehicle health
airbag_deployment_flag = crash_sensor    # Real crash detection
data_source = "phone_plus_device"       # Flag for enhanced data
```

## Data Sources & Collection Strategy

### Primary Data Sources

#### 1. Smartphone Sensors (Universal)
- **GPS/GNSS**: Location, speed, heading, altitude
- **Accelerometer**: 3-axis G-force measurements
- **Gyroscope**: Rotational velocity and orientation
- **Magnetometer**: Compass/heading validation (advanced systems)
- **Barometer**: Altitude precision (USAA, advanced carriers)
- **Phone State**: Screen activity, call status, app usage

#### 2. OBD-II Device Data (Enhanced Users)
- **Vehicle Identification**: VIN for fraud prevention
- **Odometer**: Exact mileage vs GPS estimates
- **Engine Data**: RPM, throttle position, fuel consumption
- **Diagnostics**: Trouble codes, maintenance alerts
- **Safety Systems**: Airbag deployment, ABS activation

#### 3. External API Data (Contextual Enhancement)
- **Mapping APIs**: Posted speed limits, road classification
- **Weather APIs**: Real-time/historical weather conditions
- **Traffic APIs**: Congestion levels, incident data

### Data Collection Workflow

```
1. Raw Trip Collection
   ├── Smartphone sensors capture motion/location data
   ├── OBD-II device streams vehicle data (if available)
   └── App fuses data streams in real-time

2. Contextual Enrichment  
   ├── Map API lookup for speed limits and road types
   ├── Weather API lookup for conditions during trip
   └── Traffic API lookup for congestion levels

3. Event Detection
   ├── Apply G-force thresholds for behavioral events
   ├── Speed limit comparison for speeding detection
   └── Phone state analysis for distraction events

4. Monthly Aggregation
   ├── Normalize event counts per 100 miles driven
   ├── Calculate exposure percentages by context
   └── Apply smart defaults for missing vehicle data

5. Model Input Preparation
   ├── Create unified 32-feature vector
   ├── Validate data quality and completeness
   └── Generate risk score and pricing recommendation
```

## Industry Validation

Our feature set aligns with industry leaders:

### Progressive Snapshot
- ✅ Mileage, speed, braking patterns
- ✅ Time-of-day and location context
- ✅ Phone app-based collection

### State Farm Drive Safe & Save
- ✅ Acceleration, braking, cornering
- ✅ Phone usage detection
- ✅ Connected car integration

### GEICO DriveEasy
- ✅ GPS, Bluetooth, sensor fusion
- ✅ Weather and road condition context
- ✅ Crash detection capabilities

### USAA SafePilot
- ✅ Advanced sensor suite (barometer, magnetometer)
- ✅ Comprehensive behavioral tracking
- ✅ Swerving and cornering analysis

## Target Variable Definition

Our model predicts the **probability of filing an at-fault claim** in the next month:

```python
target_variable = "had_claim_in_period"  # Binary: 0 or 1

# Claim probability simulation logic:
def calculate_claim_probability(features):
    base_risk = 0.02  # 2% baseline monthly claim rate
    
    # Behavioral risk multipliers
    base_risk += features['hard_brake_rate'] * 0.005
    base_risk += features['speeding_rate'] * 0.003  
    base_risk += features['phone_usage_pct'] * 0.004
    base_risk += features['night_driving_pct'] * 0.002
    
    # Contextual adjustments
    if features['rain_driving_pct'] > 0.3:
        base_risk *= 1.2  # 20% increase for weather exposure
        
    # Experience factors
    base_risk += features['prior_accidents'] * 0.01
    
    return min(0.5, base_risk)  # Cap at 50% monthly probability
```

## Data Quality & Provenance

### Quality Indicators
- **GPS Accuracy**: Track signal quality for reliability scoring
- **Sensor Calibration**: Validate accelerometer readings
- **Driver Detection**: Confidence scoring for driver vs passenger
- **Trip Validation**: Minimum distance/duration thresholds

### Privacy & Compliance
- **Data Minimization**: Collect only necessary features
- **Anonymization**: Hash personally identifiable information
- **Consent Management**: Granular permissions for data collection
- **Retention Policies**: Automatic data deletion after retention period

## Technical Implementation

### Data Pipeline Architecture
```
Mobile App → API Gateway → Trip Service → Feature Engineering → ML Model
     ↓              ↓            ↓              ↓              ↓
Phone Sensors  Load Balancer  Data Storage  Context APIs  Risk Score
OBD Device     Rate Limiting  Event Detect  Smart Defaults Pricing Tier
```

### Storage Strategy
- **Raw Trip Data**: Time-series database for sensor streams
- **Processed Features**: Relational database for monthly aggregations
- **Model Artifacts**: Object storage for trained models
- **Real-time Cache**: In-memory storage for active scoring

## Success Metrics

### Model Performance Targets
- **AUC Score**: > 0.80 for claim prediction
- **Precision**: > 0.75 for high-risk identification
- **Recall**: > 0.70 for claim detection
- **Inference Time**: < 100ms for real-time scoring

### Business Impact Goals
- **Risk Segmentation**: 5-tier pricing with 25% spread
- **Customer Retention**: 20% improvement vs traditional pricing
- **Loss Ratio**: 15-20% improvement through better risk selection
- **Fraud Detection**: 95% accuracy for device-based validation

## Future Enhancements

### Advanced Features (Roadmap)
- **Connected Car Integration**: OEM telematics partnerships
- **Computer Vision**: Dash cam analysis for road rage, distraction
- **Predictive Maintenance**: Vehicle health scoring
- **Route Optimization**: Safer path recommendations
- **Gamification**: Achievement systems for safer driving

### Emerging Data Sources
- **V2X Communication**: Vehicle-to-everything connectivity
- **Weather Radar**: Granular weather condition tracking
- **Traffic Incidents**: Real-time crash and hazard data
- **Road Quality**: Pothole detection and surface conditions

---

*This data strategy provides the foundation for building a best-in-class telematics insurance platform that can compete with industry leaders while providing superior accuracy, fairness, and customer value.*
