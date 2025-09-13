"""Data schemas and models for the telematics system."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum


class DataSource(Enum):
    """Data source type for distinguishing user categories."""
    PHONE_ONLY = "phone_only"
    PHONE_PLUS_DEVICE = "phone_plus_device"


class EventType(Enum):
    """Types of behavioral events that can be detected."""
    HARD_BRAKE = "hard_brake"
    RAPID_ACCEL = "rapid_accel"
    HARSH_CORNER = "harsh_corner"
    SWERVING = "swerving"
    SPEEDING = "speeding"
    PHONE_HANDLING = "phone_handling"


class WeatherCondition(Enum):
    """Weather conditions for contextual analysis."""
    CLEAR = "clear"
    RAIN = "rain"
    SNOW = "snow"
    FOG = "fog"
    CLOUDY = "cloudy"


@dataclass
class GPSPoint:
    """Individual GPS coordinate with timestamp and accuracy."""
    timestamp: datetime
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    accuracy_meters: float = 0.0
    speed_mph: Optional[float] = None
    heading: Optional[float] = None


@dataclass
class IMUReading:
    """Inertial Measurement Unit reading for motion analysis."""
    timestamp: datetime
    accel_x: float  # Forward/backward acceleration (G-force)
    accel_y: float  # Left/right acceleration (G-force)
    accel_z: float  # Up/down acceleration (G-force)
    gyro_x: float   # Roll rate (degrees/second)
    gyro_y: float   # Pitch rate (degrees/second)
    gyro_z: float   # Yaw rate (degrees/second)


@dataclass
class BehavioralEvent:
    """A detected behavioral event during driving."""
    timestamp: datetime
    event_type: EventType
    severity: float  # 0.0 to 1.0, where 1.0 is most severe
    duration_seconds: float
    speed_at_event_mph: Optional[float] = None
    location: Optional[GPSPoint] = None
    
    # Event-specific details
    g_force: Optional[float] = None  # For acceleration/braking events
    speed_over_limit_mph: Optional[float] = None  # For speeding events


@dataclass
class ContextualData:
    """Environmental and road context for a trip segment."""
    timestamp: datetime
    location: GPSPoint
    
    # Road information
    posted_speed_limit_mph: Optional[int] = None
    road_type: Optional[str] = None  # highway, urban, residential
    
    # Weather conditions
    weather_condition: Optional[WeatherCondition] = None
    temperature_f: Optional[float] = None
    visibility_miles: Optional[float] = None
    
    # Traffic conditions
    traffic_level: Optional[str] = None  # light, moderate, heavy
    congestion_factor: Optional[float] = None  # 0.0 to 1.0


@dataclass
class VehicleSystemData:
    """Data from OBD-II or vehicle systems (when available)."""
    timestamp: datetime
    
    # Engine metrics
    engine_rpm: Optional[float] = None
    engine_load_pct: Optional[float] = None
    throttle_position_pct: Optional[float] = None
    
    # Diagnostic information
    dtc_codes: List[str] = None  # Diagnostic Trouble Codes
    mil_status: Optional[bool] = None  # Malfunction Indicator Lamp
    
    # Safety systems
    airbag_deployment: Optional[bool] = None
    abs_active: Optional[bool] = None
    
    def __post_init__(self):
        if self.dtc_codes is None:
            self.dtc_codes = []


@dataclass
class TripData:
    """Complete data for a single trip."""
    trip_id: str
    driver_id: str
    start_time: datetime
    end_time: datetime
    
    # Raw sensor data
    gps_points: List[GPSPoint]
    imu_readings: List[IMUReading]
    
    # Processed events and context
    behavioral_events: List[BehavioralEvent]
    contextual_data: List[ContextualData]
    vehicle_data: List[VehicleSystemData]
    
    # Trip-level metadata
    data_source: DataSource
    total_distance_miles: float
    avg_speed_mph: float
    duration_minutes: float
    
    # Phone usage during trip
    screen_on_duration_minutes: float = 0.0
    call_duration_minutes: float = 0.0
    handheld_duration_minutes: float = 0.0
    
    # Data quality metrics
    gps_accuracy_avg_meters: float = 0.0
    data_completeness_pct: float = 100.0
    driver_passenger_confidence: float = 1.0


@dataclass
class DriverProfile:
    """Static profile information for a driver."""
    driver_id: str
    
    # Demographics
    age: int
    years_licensed: int
    
    # Vehicle information
    vehicle_age: int
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    
    # Historical risk factors
    prior_at_fault_accidents: int = 0
    prior_claims: int = 0
    prior_violations: int = 0
    
    # Account information
    data_source: DataSource = DataSource.PHONE_ONLY
    account_created_date: Optional[datetime] = None


@dataclass
class MonthlyFeatures:
    """
    The complete 32-feature set calculated monthly for each driver.
    This is the actual input to the machine learning model.
    """
    driver_id: str
    month: str  # YYYY-MM format
    
    # Category 1: Data Derived from Simulated Sensor Logs (13 features)
    total_trips: int
    total_drive_time_hours: float
    total_miles_driven: float
    avg_speed_mph: float
    max_speed_mph: float
    avg_jerk_rate: float
    hard_brake_rate_per_100_miles: float
    rapid_accel_rate_per_100_miles: float
    harsh_cornering_rate_per_100_miles: float
    swerving_events_per_100_miles: float
    pct_miles_night: float
    pct_miles_late_night_weekend: float
    pct_miles_weekday_rush_hour: float
    
    # Category 2: Data That Is Directly Simulated (13 features)
    pct_trip_time_screen_on: float
    handheld_events_rate_per_hour: float
    pct_trip_time_on_call_handheld: float
    avg_engine_rpm: float
    has_dtc_codes: bool
    airbag_deployment_flag: bool
    driver_age: int
    vehicle_age: int
    prior_at_fault_accidents: int
    years_licensed: int
    data_source: DataSource
    gps_accuracy_avg_meters: float
    driver_passenger_confidence_score: float
    
    # Category 3: Data from Simulated Trips + Real API Data (6 features)
    speeding_rate_per_100_miles: float
    max_speed_over_limit_mph: float
    pct_miles_highway: float
    pct_miles_urban: float
    pct_miles_in_rain_or_snow: float
    pct_miles_in_heavy_traffic: float
    
    # Target Variable
    had_claim_in_period: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for ML model input."""
        result = {}
        for field_name, field_value in self.__dict__.items():
            if isinstance(field_value, Enum):
                result[field_name] = field_value.value
            else:
                result[field_name] = field_value
        return result
    
    @classmethod
    def get_feature_names(cls) -> List[str]:
        """Get list of all 32 feature names for ML model."""
        return [
            # Category 1: Data Derived from Simulated Sensor Logs (13 features)
            'total_trips', 'total_drive_time_hours', 'total_miles_driven',
            'avg_speed_mph', 'max_speed_mph', 'avg_jerk_rate',
            'hard_brake_rate_per_100_miles', 'rapid_accel_rate_per_100_miles', 
            'harsh_cornering_rate_per_100_miles', 'swerving_events_per_100_miles',
            'pct_miles_night', 'pct_miles_late_night_weekend', 'pct_miles_weekday_rush_hour',
            
            # Category 2: Data That Is Directly Simulated (13 features)
            'pct_trip_time_screen_on', 'handheld_events_rate_per_hour',
            'pct_trip_time_on_call_handheld', 'avg_engine_rpm', 'has_dtc_codes',
            'airbag_deployment_flag', 'driver_age', 'vehicle_age',
            'prior_at_fault_accidents', 'years_licensed', 'data_source',
            'gps_accuracy_avg_meters', 'driver_passenger_confidence_score',
            
            # Category 3: Data from Simulated Trips + Real API Data (6 features)
            'speeding_rate_per_100_miles', 'max_speed_over_limit_mph',
            'pct_miles_highway', 'pct_miles_urban', 'pct_miles_in_rain_or_snow',
            'pct_miles_in_heavy_traffic'
        ]
    
    @classmethod
    def get_target_name(cls) -> str:
        """Get the target variable name."""
        return 'had_claim_in_period'
