import psycopg2
import sys

# Database connection parameters (updated with your actual values)
DB_HOST = "telematics-db.cteio0ogsw3d.us-east-2.rds.amazonaws.com"
DB_PORT = "5432"
DB_NAME = "telematics"
DB_USER = "telematics_admin"
DB_PASSWORD = "Hemanth13"

# SQL commands to create tables
CREATE_TABLES_SQL = """
-- Create drivers table
CREATE TABLE IF NOT EXISTS drivers (
    driver_id VARCHAR(50) PRIMARY KEY,
    persona_type VARCHAR(20),
    driver_age INTEGER,
    years_licensed INTEGER,
    vehicle_age INTEGER,
    vehicle_make VARCHAR(50),
    vehicle_model VARCHAR(50),
    prior_at_fault_accidents INTEGER,
    prior_claims INTEGER,
    prior_violations INTEGER,
    data_source VARCHAR(20),
    account_created_date TIMESTAMP,
    policy_start_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create trips table
CREATE TABLE IF NOT EXISTS trips (
    trip_id VARCHAR(50) PRIMARY KEY,
    driver_id VARCHAR(50),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    total_distance_miles DECIMAL(10, 2),
    avg_speed_mph DECIMAL(10, 2),
    duration_minutes DECIMAL(10, 2),
    data_source VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (driver_id) REFERENCES drivers(driver_id)
);

-- Create monthly_features table
CREATE TABLE IF NOT EXISTS monthly_features (
    driver_id VARCHAR(50),
    month VARCHAR(7),
    total_trips INTEGER,
    total_drive_time_hours DECIMAL(10, 2),
    total_miles_driven DECIMAL(10, 2),
    avg_speed_mph DECIMAL(10, 2),
    max_speed_mph DECIMAL(10, 2),
    avg_jerk_rate DECIMAL(10, 4),
    hard_brake_rate_per_100_miles DECIMAL(10, 4),
    rapid_accel_rate_per_100_miles DECIMAL(10, 4),
    harsh_cornering_rate_per_100_miles DECIMAL(10, 4),
    swerving_events_per_100_miles DECIMAL(10, 4),
    pct_miles_night DECIMAL(10, 4),
    pct_miles_late_night_weekend DECIMAL(10, 4),
    pct_miles_weekday_rush_hour DECIMAL(10, 4),
    pct_trip_time_screen_on DECIMAL(10, 4),
    handheld_events_rate_per_hour DECIMAL(10, 4),
    pct_trip_time_on_call_handheld DECIMAL(10, 4),
    avg_engine_rpm DECIMAL(10, 2),
    has_dtc_codes BOOLEAN,
    airbag_deployment_flag BOOLEAN,
    driver_age INTEGER,
    vehicle_age INTEGER,
    prior_at_fault_accidents INTEGER,
    years_licensed INTEGER,
    data_source VARCHAR(20),
    gps_accuracy_avg_meters DECIMAL(10, 2),
    driver_passenger_confidence_score DECIMAL(10, 4),
    speeding_rate_per_100_miles DECIMAL(10, 4),
    max_speed_over_limit_mph DECIMAL(10, 2),
    pct_miles_highway DECIMAL(10, 4),
    pct_miles_urban DECIMAL(10, 4),
    pct_miles_in_rain_or_snow DECIMAL(10, 4),
    pct_miles_in_heavy_traffic DECIMAL(10, 4),
    had_claim_in_period BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (driver_id, month),
    FOREIGN KEY (driver_id) REFERENCES drivers(driver_id)
);
"""

def create_schema():
    try:
        print("Connecting to database...")
        # Connect to the database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        print("Connected successfully!")
        cursor = conn.cursor()
        
        print("Creating tables...")
        # Execute the SQL commands
        cursor.execute(CREATE_TABLES_SQL)
        conn.commit()
        
        print("✅ Database schema created successfully!")
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        print("📋 Created tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        cursor.close()
        conn.close()
        print("✅ Database connection closed.")
        
    except Exception as e:
        print(f"❌ Error creating database schema: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_schema()