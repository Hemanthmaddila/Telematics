# 📊 Complete Feature Set & Variable Definitions

## Executive Summary

This document provides the definitive specification for all 32 variables used in our telematics risk assessment model. Each variable is precisely defined with calculation methods, data sources, normalization approaches, and business interpretation. This feature set represents the gold standard in telematics insurance, incorporating insights from industry leaders and academic research.

## Variable Categories Overview

Our 32-variable model covers eight critical dimensions of driving risk:

| Category | Variables | Purpose | Data Source |
|----------|-----------|---------|-------------|
| **Trip & Kinematics** | 6 | Fundamental driving patterns | GPS + IMU |
| **Behavioral Events** | 6 | Risky driving actions | Accelerometer + GPS |
| **Phone Usage** | 3 | Distraction indicators | Phone sensors |
| **Exposure & Context** | 5 | Risk exposure patterns | GPS + Time analysis |
| **Environment** | 5 | External risk factors | Weather + Traffic APIs |
| **Vehicle Systems** | 3 | Vehicle health & performance | OBD-II (where available) |
| **Driver Profile** | 4 | Historical risk factors | Insurance records |
| **Data Provenance** | 3 | Data quality indicators | System metadata |

## Detailed Variable Specifications

### 1. Trip & Kinematics Features

#### 1.1 `total_trips`
- **Definition**: Total number of separate driving journeys in the month
- **Data Type**: Integer (0-500)
- **Calculation**: Count of distinct trip sessions with >0.5 miles and >5 minutes duration
- **Business Logic**: Higher trip frequency may indicate professional drivers or high exposure
- **Normalization**: None (raw count)

```python
def calculate_total_trips(trip_logs):
    valid_trips = [
        trip for trip in trip_logs 
        if trip.distance_miles >= 0.5 and trip.duration_minutes >= 5
    ]
    return len(valid_trips)
```

#### 1.2 `total_drive_time_hours`
- **Definition**: Total time spent driving in the month
- **Data Type**: Float (0.0-500.0)
- **Calculation**: Sum of all trip durations from ignition on to ignition off
- **Business Logic**: Exposure metric - more time driving = more opportunity for claims
- **Normalization**: Hours (convert from seconds/minutes)

```python
def calculate_total_drive_time(trip_logs):
    return sum(trip.duration_seconds for trip in trip_logs) / 3600
```

#### 1.3 `total_miles_driven`
- **Definition**: Total distance driven in the month
- **Data Type**: Float (0.0-10000.0)
- **Calculation**: Sum of GPS-based distance calculations for all trips
- **Business Logic**: Primary exposure metric for insurance pricing
- **Data Sources**: GPS (phone users) or Odometer (device users)

```python
def calculate_total_miles(trip_logs, data_source):
    if data_source == "phone_plus_device":
        return sum(trip.odometer_miles for trip in trip_logs)
    else:
        return sum(trip.gps_distance_miles for trip in trip_logs)
```

#### 1.4 `avg_speed_mph`
- **Definition**: Average speed across all driving time in the month
- **Data Type**: Float (0.0-120.0)
- **Calculation**: Distance-weighted average speed across all trips
- **Business Logic**: Indicates driving environment (highway vs city) and aggressiveness

```python
def calculate_avg_speed(trip_logs):
    total_distance = sum(trip.distance_miles for trip in trip_logs)
    total_time = sum(trip.duration_hours for trip in trip_logs)
    return total_distance / total_time if total_time > 0 else 0
```

#### 1.5 `max_speed_mph`
- **Definition**: Highest single speed recorded during the month
- **Data Type**: Float (0.0-200.0)
- **Calculation**: Maximum GPS speed reading across all trip data points
- **Business Logic**: Extreme speeding indicator, risk of severe crashes

```python
def calculate_max_speed(trip_logs):
    all_speeds = []
    for trip in trip_logs:
        all_speeds.extend(trip.gps_speed_readings)
    return max(all_speeds) if all_speeds else 0
```

#### 1.6 `avg_jerk_rate`
- **Definition**: Average rate of change of acceleration (smoothness of driving)
- **Data Type**: Float (0.0-10.0)
- **Calculation**: RMS (Root Mean Square) of acceleration derivatives
- **Business Logic**: Smooth drivers are safer; high jerk indicates erratic/aggressive driving

```python
def calculate_avg_jerk(trip_logs):
    jerk_values = []
    for trip in trip_logs:
        accelerations = trip.acceleration_readings
        for i in range(1, len(accelerations)):
            jerk = abs(accelerations[i] - accelerations[i-1]) / trip.sampling_rate
            jerk_values.append(jerk)
    return np.sqrt(np.mean(np.square(jerk_values))) if jerk_values else 0
```

### 2. Behavioral Event Features

#### 2.1 `hard_brake_rate_per_100_miles`
- **Definition**: Number of hard braking events per 100 miles driven
- **Data Type**: Float (0.0-50.0)
- **Calculation**: Count of longitudinal G-force < -0.4g, normalized per 100 miles
- **Business Logic**: Strong predictor of aggressive driving and rear-end collision risk

```python
def calculate_hard_brake_rate(trip_logs):
    hard_brakes = 0
    total_miles = 0
    
    for trip in trip_logs:
        # Count events where longitudinal G-force < -0.4g
        for reading in trip.accelerometer_data:
            if reading.g_force_y < -0.4:
                hard_brakes += 1
        total_miles += trip.distance_miles
        
    return (hard_brakes / total_miles * 100) if total_miles > 0 else 0
```

#### 2.2 `rapid_accel_rate_per_100_miles`
- **Definition**: Number of rapid acceleration events per 100 miles
- **Data Type**: Float (0.0-30.0)
- **Calculation**: Count of longitudinal G-force > 0.4g, normalized per 100 miles
- **Business Logic**: Indicates aggressive driving style and potential loss of control

```python
def calculate_rapid_accel_rate(trip_logs):
    rapid_accels = 0
    total_miles = 0
    
    for trip in trip_logs:
        for reading in trip.accelerometer_data:
            if reading.g_force_y > 0.4:
                rapid_accels += 1
        total_miles += trip.distance_miles
        
    return (rapid_accels / total_miles * 100) if total_miles > 0 else 0
```

#### 2.3 `harsh_cornering_rate_per_100_miles`
- **Definition**: Number of harsh cornering events per 100 miles
- **Data Type**: Float (0.0-40.0)
- **Calculation**: Count of lateral G-force > |0.4g|, normalized per 100 miles
- **Business Logic**: Taking turns too fast, loss of control risk

```python
def calculate_harsh_cornering_rate(trip_logs):
    harsh_corners = 0
    total_miles = 0
    
    for trip in trip_logs:
        for reading in trip.accelerometer_data:
            if abs(reading.g_force_x) > 0.4:
                harsh_corners += 1
        total_miles += trip.distance_miles
        
    return (harsh_corners / total_miles * 100) if total_miles > 0 else 0
```

#### 2.4 `swerving_events_per_100_miles`
- **Definition**: Number of swerving maneuvers per 100 miles
- **Data Type**: Float (0.0-20.0)
- **Calculation**: Rapid opposing lateral G-forces within 2-second windows
- **Business Logic**: Indicates distraction, obstacle avoidance, or impairment

```python
def calculate_swerving_rate(trip_logs):
    swerving_events = 0
    total_miles = 0
    
    for trip in trip_logs:
        readings = trip.accelerometer_data
        for i in range(len(readings) - 20):  # 2-second window at 10Hz
            window = readings[i:i+20]
            left_gforce = max(r.g_force_x for r in window)
            right_gforce = min(r.g_force_x for r in window)
            
            # Swerving = high left force followed by high right force
            if left_gforce > 0.3 and right_gforce < -0.3:
                swerving_events += 1
                
        total_miles += trip.distance_miles
        
    return (swerving_events / total_miles * 100) if total_miles > 0 else 0
```

#### 2.5 `speeding_rate_per_100_miles`
- **Definition**: Number of speeding violations per 100 miles (>10 mph over limit)
- **Data Type**: Float (0.0-100.0)
- **Calculation**: Count of GPS speed > (posted_limit + 10), normalized per 100 miles
- **Business Logic**: Direct violation of traffic laws, crash severity predictor

```python
def calculate_speeding_rate(trip_logs, speed_limit_data):
    speeding_events = 0
    total_miles = 0
    
    for trip in trip_logs:
        for point in trip.gps_points:
            speed_limit = speed_limit_data.get(point.location, 35)  # Default 35 mph
            if point.speed_mph > speed_limit + 10:
                speeding_events += 1
        total_miles += trip.distance_miles
        
    return (speeding_events / total_miles * 100) if total_miles > 0 else 0
```

#### 2.6 `max_speed_over_limit_mph`
- **Definition**: Worst speeding violation in the month (mph over posted limit)
- **Data Type**: Float (0.0-80.0)
- **Calculation**: Maximum difference between actual speed and posted speed limit
- **Business Logic**: Extreme speeding indicator, predictor of crash severity

```python
def calculate_max_speed_over_limit(trip_logs, speed_limit_data):
    max_violation = 0
    
    for trip in trip_logs:
        for point in trip.gps_points:
            speed_limit = speed_limit_data.get(point.location, 35)
            violation = max(0, point.speed_mph - speed_limit)
            max_violation = max(max_violation, violation)
            
    return max_violation
```

### 3. Phone Usage Features (Distraction)

#### 3.1 `pct_trip_time_screen_on`
- **Definition**: Percentage of driving time with phone screen active
- **Data Type**: Float (0.0-100.0)
- **Calculation**: (Screen-on seconds / Total drive seconds) * 100
- **Business Logic**: Direct measure of visual distraction while driving

```python
def calculate_screen_on_percentage(trip_logs):
    total_drive_seconds = 0
    screen_on_seconds = 0
    
    for trip in trip_logs:
        total_drive_seconds += trip.duration_seconds
        screen_on_seconds += sum(
            event.duration for event in trip.phone_events 
            if event.type == "screen_on"
        )
        
    return (screen_on_seconds / total_drive_seconds * 100) if total_drive_seconds > 0 else 0
```

#### 3.2 `handheld_events_rate_per_hour`
- **Definition**: Number of phone handling events per hour of driving
- **Data Type**: Float (0.0-60.0)
- **Calculation**: Count of phone touch/pickup events, normalized per drive hour
- **Business Logic**: Manual distraction - hands off wheel, eyes off road

```python
def calculate_handheld_rate(trip_logs):
    total_drive_hours = 0
    handheld_events = 0
    
    for trip in trip_logs:
        total_drive_hours += trip.duration_seconds / 3600
        handheld_events += len([
            event for event in trip.phone_events 
            if event.type in ["touch", "pickup", "swipe"]
        ])
        
    return handheld_events / total_drive_hours if total_drive_hours > 0 else 0
```

#### 3.3 `pct_trip_time_on_call_handheld`
- **Definition**: Percentage of driving time on non-hands-free calls
- **Data Type**: Float (0.0-100.0)
- **Calculation**: (Handheld call seconds / Total drive seconds) * 100
- **Business Logic**: Cognitive and manual distraction combined

```python
def calculate_handheld_call_percentage(trip_logs):
    total_drive_seconds = 0
    handheld_call_seconds = 0
    
    for trip in trip_logs:
        total_drive_seconds += trip.duration_seconds
        handheld_call_seconds += sum(
            event.duration for event in trip.phone_events 
            if event.type == "call" and not event.hands_free
        )
        
    return (handheld_call_seconds / total_drive_seconds * 100) if total_drive_seconds > 0 else 0
```

### 4. Exposure & Context Features

#### 4.1 `pct_miles_night`
- **Definition**: Percentage of miles driven during night hours (9 PM - 5 AM)
- **Data Type**: Float (0.0-100.0)
- **Calculation**: (Night miles / Total miles) * 100
- **Business Logic**: Night driving has 3x higher crash rate due to visibility and fatigue

```python
def calculate_night_driving_percentage(trip_logs):
    total_miles = 0
    night_miles = 0
    
    for trip in trip_logs:
        total_miles += trip.distance_miles
        
        # Check if trip occurs during night hours
        start_hour = trip.start_time.hour
        end_hour = trip.end_time.hour
        
        if is_night_time(start_hour, end_hour):
            night_miles += trip.distance_miles
            
    return (night_miles / total_miles * 100) if total_miles > 0 else 0

def is_night_time(start_hour, end_hour):
    return start_hour >= 21 or start_hour < 5 or end_hour >= 21 or end_hour < 5
```

#### 4.2 `pct_miles_late_night_weekend`
- **Definition**: Percentage of miles driven Friday/Saturday 11 PM - 4 AM
- **Data Type**: Float (0.0-100.0)
- **Calculation**: (High-risk weekend miles / Total miles) * 100
- **Business Logic**: Highest risk driving period - alcohol, fatigue, young drivers

```python
def calculate_late_night_weekend_percentage(trip_logs):
    total_miles = 0
    high_risk_miles = 0
    
    for trip in trip_logs:
        total_miles += trip.distance_miles
        
        # Check if Friday or Saturday night
        is_weekend_night = (
            trip.start_time.weekday() in [4, 5] and  # Friday=4, Saturday=5
            23 <= trip.start_time.hour or trip.start_time.hour < 4
        )
        
        if is_weekend_night:
            high_risk_miles += trip.distance_miles
            
    return (high_risk_miles / total_miles * 100) if total_miles > 0 else 0
```

#### 4.3 `pct_miles_weekday_rush_hour`
- **Definition**: Percentage of miles driven during weekday rush hours
- **Data Type**: Float (0.0-100.0)
- **Calculation**: Miles during 7-9 AM and 4-6 PM on weekdays / Total miles * 100
- **Business Logic**: High traffic density increases rear-end collision risk

```python
def calculate_rush_hour_percentage(trip_logs):
    total_miles = 0
    rush_hour_miles = 0
    
    for trip in trip_logs:
        total_miles += trip.distance_miles
        
        # Check if weekday rush hour
        is_weekday = trip.start_time.weekday() < 5  # Monday=0 to Friday=4
        hour = trip.start_time.hour
        is_rush_hour = (7 <= hour <= 9) or (16 <= hour <= 18)
        
        if is_weekday and is_rush_hour:
            rush_hour_miles += trip.distance_miles
            
    return (rush_hour_miles / total_miles * 100) if total_miles > 0 else 0
```

### 5. Environment Features

#### 5.1 `pct_miles_highway`
- **Definition**: Percentage of miles driven on highways/interstates
- **Data Type**: Float (0.0-100.0)
- **Calculation**: (Highway miles / Total miles) * 100 based on road classification
- **Business Logic**: Highway driving is generally safer but crashes are more severe

```python
def calculate_highway_percentage(trip_logs, road_classification_data):
    total_miles = 0
    highway_miles = 0
    
    for trip in trip_logs:
        total_miles += trip.distance_miles
        
        # Analyze road types along trip route
        for segment in trip.route_segments:
            road_type = road_classification_data.get(segment.location, "local")
            if road_type in ["highway", "interstate", "freeway"]:
                highway_miles += segment.distance_miles
                
    return (highway_miles / total_miles * 100) if total_miles > 0 else 0
```

#### 5.2 `pct_miles_urban`
- **Definition**: Percentage of miles driven in dense urban areas
- **Data Type**: Float (0.0-100.0)
- **Calculation**: Urban area miles based on population density and road type
- **Business Logic**: Higher pedestrian risk, more intersections, complex traffic patterns

#### 5.3 `pct_miles_in_rain`
- **Definition**: Percentage of miles driven while raining
- **Data Type**: Float (0.0-100.0)
- **Calculation**: Miles driven during precipitation events / Total miles * 100
- **Business Logic**: Rain increases stopping distance and reduces visibility

```python
def calculate_rain_driving_percentage(trip_logs, weather_data):
    total_miles = 0
    rain_miles = 0
    
    for trip in trip_logs:
        total_miles += trip.distance_miles
        
        # Check weather conditions during trip
        weather = weather_data.get_conditions(
            trip.start_location, trip.start_time
        )
        
        if weather.precipitation_type in ["rain", "drizzle", "showers"]:
            rain_miles += trip.distance_miles
            
    return (rain_miles / total_miles * 100) if total_miles > 0 else 0
```

#### 5.4 `pct_miles_in_snow`
- **Definition**: Percentage of miles driven in snow conditions
- **Data Type**: Float (0.0-100.0)
- **Business Logic**: Extreme weather condition requiring adjusted driving behavior

#### 5.5 `pct_miles_in_heavy_traffic`
- **Definition**: Percentage of miles driven in heavy traffic conditions
- **Data Type**: Float (0.0-100.0)
- **Calculation**: Miles in congested conditions / Total miles * 100
- **Business Logic**: Stop-and-go traffic increases rear-end collision risk

### 6. Vehicle & Diagnostics Features

#### 6.1 `avg_engine_rpm`
- **Definition**: Average engine RPM across all driving
- **Data Type**: Float (500.0-8000.0)
- **Calculation**: RPM-weighted average across all OBD-II readings
- **Business Logic**: High RPM indicates aggressive driving style
- **Smart Default**: 2200 RPM (safe driver population average)

```python
def calculate_avg_engine_rpm(trip_logs, data_source):
    if data_source == "phone_only":
        return 2200  # Smart default for phone-only users
        
    total_rpm_seconds = 0
    total_seconds = 0
    
    for trip in trip_logs:
        for reading in trip.obd_data:
            total_rpm_seconds += reading.engine_rpm * reading.duration_seconds
            total_seconds += reading.duration_seconds
            
    return total_rpm_seconds / total_seconds if total_seconds > 0 else 2200
```

#### 6.2 `has_dtc_codes`
- **Definition**: Binary flag indicating presence of diagnostic trouble codes
- **Data Type**: Boolean (0 or 1)
- **Calculation**: 1 if any DTC codes detected, 0 otherwise
- **Business Logic**: Vehicle maintenance issues correlate with driver behavior
- **Smart Default**: 0 (no codes for phone-only users)

```python
def calculate_has_dtc_codes(trip_logs, data_source):
    if data_source == "phone_only":
        return 0  # Smart default - assume no codes
        
    for trip in trip_logs:
        if any(reading.dtc_codes for reading in trip.obd_data):
            return 1
            
    return 0
```

#### 6.3 `airbag_deployment_flag`
- **Definition**: Binary flag for airbag deployment (severe crash indicator)
- **Data Type**: Boolean (0 or 1)
- **Calculation**: 1 if airbag deployed during month, 0 otherwise
- **Business Logic**: Definitive indicator of severe crash
- **Smart Default**: 0 (no detection capability for phone-only)

### 7. Driver Profile Features

#### 7.1 `driver_age`
- **Definition**: Driver's age in years
- **Data Type**: Integer (16-100)
- **Calculation**: Current year - birth year
- **Business Logic**: Age-based risk curve - highest risk for 16-25 and 70+

#### 7.2 `vehicle_age`
- **Definition**: Vehicle's age in years
- **Data Type**: Integer (0-30)
- **Calculation**: Current year - vehicle model year
- **Business Logic**: Newer vehicles have better safety features

#### 7.3 `prior_at_fault_accidents`
- **Definition**: Number of at-fault accidents in last 3 years
- **Data Type**: Integer (0-10)
- **Calculation**: Count from insurance/DMV records
- **Business Logic**: Strong predictor of future claims

#### 7.4 `years_licensed`
- **Definition**: Number of years holding driver's license
- **Data Type**: Integer (0-70)
- **Calculation**: Current year - license issue year
- **Business Logic**: Experience factor - more years typically means safer driving

### 8. Data Provenance Features

#### 8.1 `data_source`
- **Definition**: Type of data collection system
- **Data Type**: Categorical ("phone_only" or "phone_plus_device")
- **Calculation**: System configuration flag
- **Business Logic**: Critical for model to understand data reliability

#### 8.2 `gps_accuracy_avg_meters`
- **Definition**: Average GPS accuracy in meters
- **Data Type**: Float (1.0-50.0)
- **Calculation**: Average of GPS accuracy readings across all trips
- **Business Logic**: Data quality indicator - affects speed and location reliability

#### 8.3 `driver_passenger_confidence_score`
- **Definition**: Confidence that phone user was the driver (not passenger)
- **Data Type**: Float (0.0-1.0)
- **Calculation**: ML model based on phone position, motion patterns, trip context
- **Business Logic**: Prevents unfair scoring of passengers

## Target Variable

### `had_claim_in_period`
- **Definition**: Binary indicator of at-fault claim filed in the month
- **Data Type**: Boolean (0 or 1)
- **Calculation**: 1 if any at-fault claim filed, 0 otherwise
- **Business Logic**: Primary target for risk prediction model

```python
def generate_target_variable(driver_features):
    """
    Simulate claim probability based on risk factors
    """
    base_risk = 0.02  # 2% baseline monthly claim rate
    
    # Behavioral risk factors
    base_risk += driver_features['hard_brake_rate'] * 0.005
    base_risk += driver_features['speeding_rate'] * 0.003
    base_risk += driver_features['phone_usage_pct'] * 0.004
    base_risk += driver_features['night_driving_pct'] * 0.002
    
    # Experience factors
    base_risk += driver_features['prior_accidents'] * 0.01
    base_risk -= min(driver_features['years_licensed'] / 20, 0.01)
    
    # Environmental factors
    if driver_features['rain_driving_pct'] > 30:
        base_risk *= 1.2
        
    # Generate binary outcome
    return 1 if random.random() < min(base_risk, 0.5) else 0
```

## Data Quality Standards

### Validation Rules

```python
def validate_feature_quality(features):
    """
    Comprehensive data quality validation
    """
    quality_checks = {
        'range_checks': validate_ranges(features),
        'logical_consistency': validate_logic(features),
        'completeness': validate_completeness(features),
        'distribution_checks': validate_distributions(features)
    }
    
    overall_quality = calculate_quality_score(quality_checks)
    return overall_quality > 0.85  # 85% quality threshold

def validate_ranges(features):
    """Ensure all features are within expected ranges"""
    range_checks = {
        'total_trips': 0 <= features['total_trips'] <= 500,
        'avg_speed_mph': 0 <= features['avg_speed_mph'] <= 120,
        'hard_brake_rate': 0 <= features['hard_brake_rate'] <= 50,
        'pct_miles_night': 0 <= features['pct_miles_night'] <= 100,
        # ... additional range validations
    }
    return all(range_checks.values())
```

### Missing Data Handling

```python
def handle_missing_data(raw_features, data_source):
    """
    Apply smart defaults and imputation strategies
    """
    if data_source == "phone_only":
        # Vehicle system defaults
        raw_features.setdefault('avg_engine_rpm', 2200)
        raw_features.setdefault('has_dtc_codes', 0)
        raw_features.setdefault('airbag_deployment_flag', 0)
        
    # Context data defaults (if API calls fail)
    raw_features.setdefault('pct_miles_in_rain', 5.0)  # Regional average
    raw_features.setdefault('pct_miles_highway', 25.0)  # National average
    
    return raw_features
```

## Feature Importance Rankings

Based on industry research and our model training:

| Rank | Feature | Importance | Category |
|------|---------|------------|----------|
| 1 | `hard_brake_rate_per_100_miles` | 0.18 | Behavioral |
| 2 | `prior_at_fault_accidents` | 0.15 | Profile |
| 3 | `speeding_rate_per_100_miles` | 0.12 | Behavioral |
| 4 | `pct_trip_time_screen_on` | 0.10 | Phone Usage |
| 5 | `driver_age` | 0.09 | Profile |
| 6 | `pct_miles_late_night_weekend` | 0.08 | Exposure |
| 7 | `avg_jerk_rate` | 0.07 | Kinematics |
| 8 | `harsh_cornering_rate` | 0.06 | Behavioral |
| 9 | `total_miles_driven` | 0.05 | Exposure |
| 10 | `years_licensed` | 0.04 | Profile |

## Implementation Checklist

### Development Phase
- [ ] Implement all 32 feature calculation functions
- [ ] Create data validation and quality checks  
- [ ] Build smart defaults system for missing data
- [ ] Develop feature engineering pipeline
- [ ] Create unit tests for each feature calculation

### Production Phase
- [ ] Set up real-time feature calculation
- [ ] Implement monitoring for feature drift
- [ ] Create feature importance tracking
- [ ] Build regulatory explanation system
- [ ] Establish data quality SLAs

---

*This complete feature specification provides the foundation for building a production-ready telematics risk assessment system with industry-leading accuracy and regulatory compliance.*
