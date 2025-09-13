# Cloud Data Storage and Processing for Telematics

This tutorial covers setting up cloud-native data storage and processing for your telematics system.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Database Migration to Cloud](#database-migration-to-cloud)
3. [Object Storage Configuration](#object-storage-configuration)
4. [Data Pipeline Setup](#data-pipeline-setup)
5. [Real-time Data Processing](#real-time-data-processing)
6. [Batch Processing with Spark](#batch-processing-with-spark)
7. [Data Security and Compliance](#data-security-and-compliance)
8. [Backup and Disaster Recovery](#backup-and-disaster-recovery)

## Prerequisites

Before starting, ensure you have:
- Completed the previous tutorials
- AWS CLI configured
- Access to RDS database and S3 bucket
- Docker and Docker Compose installed
- Basic understanding of data processing concepts

## Database Migration to Cloud

### Connecting Services to Cloud Database

Update your service configuration files to use the cloud database:

Create `config/database.yml`:

```yaml
development:
  adapter: postgresql
  host: localhost
  port: 5432
  database: telematics
  username: telematics_admin
  password: [local_password]

production:
  adapter: postgresql
  host: telematics-db.[region].rds.amazonaws.com
  port: 5432
  database: telematics
  username: telematics_admin
  password: [cloud_password]
  sslmode: require
```

### Database Connection in Services

Update your service code to use environment-specific database connections:

```python
# In your database connection module
import os
import yaml
from sqlalchemy import create_engine

def get_database_connection():
    env = os.environ.get('ENVIRONMENT', 'development')
    
    with open('config/database.yml', 'r') as f:
        config = yaml.safe_load(f)
    
    db_config = config[env]
    
    connection_string = f"postgresql://{db_config['username']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    
    if env == 'production':
        connection_string += "?sslmode=require"
    
    return create_engine(connection_string)
```

### Database Schema Migration

Create database migration scripts:

Create `scripts/migrate_database.py`:

```python
#!/usr/bin/env python3
"""
Database migration script for telematics system
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def migrate_database():
    # Database connection parameters
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_port = os.environ.get('DB_PORT', '5432')
    db_name = os.environ.get('DB_NAME', 'telematics')
    db_user = os.environ.get('DB_USER', 'telematics_admin')
    db_password = os.environ.get('DB_PASSWORD', '')
    
    # Connect to PostgreSQL server
    conn = psycopg2.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    # Create database if it doesn't exist
    try:
        cursor.execute(f"CREATE DATABASE {db_name}")
        print(f"Database {db_name} created successfully")
    except psycopg2.errors.DuplicateDatabase:
        print(f"Database {db_name} already exists")
    
    cursor.close()
    conn.close()
    
    # Connect to the specific database
    conn = psycopg2.connect(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_password
    )
    cursor = conn.cursor()
    
    # Create tables
    create_tables_sql = """
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
    
    -- Create indexes for better query performance
    CREATE INDEX IF NOT EXISTS idx_trips_driver ON trips(driver_id);
    CREATE INDEX IF NOT EXISTS idx_trips_time ON trips(start_time);
    CREATE INDEX IF NOT EXISTS idx_features_driver ON monthly_features(driver_id);
    CREATE INDEX IF NOT EXISTS idx_features_month ON monthly_features(month);
    """
    
    cursor.execute(create_tables_sql)
    conn.commit()
    
    print("Database schema created/updated successfully")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    migrate_database()
```

## Object Storage Configuration

### S3 Bucket Setup for Telematics Data

```bash
# Create S3 bucket for different data types
aws s3 mb s3://telematics-raw-data-[your-account-id] --region us-east-1
aws s3 mb s3://telematics-processed-data-[your-account-id] --region us-east-1
aws s3 mb s3://telematics-models-[your-account-id] --region us-east-1
aws s3 mb s3://telematics-logs-[your-account-id] --region us-east-1

# Set lifecycle policies
cat > lifecycle-policy.json << EOF
{
    "Rules": [
        {
            "ID": "MoveToIA",
            "Status": "Enabled",
            "Filter": {
                "Prefix": "processed/"
            },
            "Transitions": [
                {
                    "Days": 30,
                    "StorageClass": "STANDARD_IA"
                }
            ]
        },
        {
            "ID": "DeleteOldLogs",
            "Status": "Enabled",
            "Filter": {
                "Prefix": "logs/"
            },
            "Expiration": {
                "Days": 90
            }
        }
    ]
}
EOF

aws s3api put-bucket-lifecycle-configuration \
    --bucket telematics-raw-data-[your-account-id] \
    --lifecycle-configuration file://lifecycle-policy.json
```

### Data Organization in S3

Organize your data in S3 with a clear structure:

```
telematics-raw-data-[your-account-id]/
├── trips/
│   ├── 2024/
│   │   ├── 01/
│   │   ├── 02/
│   │   └── ...
│   └── 2025/
├── drivers/
├── features/
└── models/

telematics-processed-data-[your-account-id]/
├── aggregated_features/
├── risk_scores/
├── analytics/
└── reports/
```

### S3 Access from Services

Update your services to access S3:

```python
# In your data processing module
import boto3
import os
from botocore.exceptions import ClientError

class S3DataManager:
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.raw_bucket = os.environ.get('S3_RAW_BUCKET', 'telematics-raw-data-[your-account-id]')
        self.processed_bucket = os.environ.get('S3_PROCESSED_BUCKET', 'telematics-processed-data-[your-account-id]')
    
    def upload_file(self, file_path, s3_key, bucket_type='raw'):
        """Upload a file to S3"""
        bucket = self.raw_bucket if bucket_type == 'raw' else self.processed_bucket
        
        try:
            self.s3_client.upload_file(file_path, bucket, s3_key)
            print(f"File {file_path} uploaded to {bucket}/{s3_key}")
            return True
        except ClientError as e:
            print(f"Error uploading file: {e}")
            return False
    
    def download_file(self, s3_key, local_path, bucket_type='raw'):
        """Download a file from S3"""
        bucket = self.raw_bucket if bucket_type == 'raw' else self.processed_bucket
        
        try:
            self.s3_client.download_file(bucket, s3_key, local_path)
            print(f"File {bucket}/{s3_key} downloaded to {local_path}")
            return True
        except ClientError as e:
            print(f"Error downloading file: {e}")
            return False
    
    def list_files(self, prefix='', bucket_type='raw'):
        """List files in S3 with a given prefix"""
        bucket = self.raw_bucket if bucket_type == 'raw' else self.processed_bucket
        
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents']]
            return []
        except ClientError as e:
            print(f"Error listing files: {e}")
            return []
```

## Data Pipeline Setup

### Create Data Processing Pipeline

Create `pipelines/data_pipeline.py`:

```python
#!/usr/bin/env python3
"""
Data processing pipeline for telematics system
"""

import os
import boto3
import pandas as pd
from datetime import datetime
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelematicsDataPipeline:
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.raw_bucket = os.environ.get('S3_RAW_BUCKET', 'telematics-raw-data-[your-account-id]')
        self.processed_bucket = os.environ.get('S3_PROCESSED_BUCKET', 'telematics-processed-data-[your-account-id]')
        
    def process_trip_data(self, trip_file_key):
        """Process raw trip data and extract features"""
        logger.info(f"Processing trip data: {trip_file_key}")
        
        # Download raw trip data
        local_file = f"/tmp/{os.path.basename(trip_file_key)}"
        try:
            self.s3_client.download_file(self.raw_bucket, trip_file_key, local_file)
        except Exception as e:
            logger.error(f"Error downloading trip data: {e}")
            return False
        
        # Load and process data (simplified example)
        try:
            # For parquet files
            if trip_file_key.endswith('.parquet'):
                df = pd.read_parquet(local_file)
            # For CSV files
            elif trip_file_key.endswith('.csv'):
                df = pd.read_csv(local_file)
            else:
                logger.warning(f"Unsupported file format: {trip_file_key}")
                return False
            
            # Extract features (simplified)
            features = self.extract_trip_features(df, trip_file_key)
            
            # Save processed features
            processed_key = trip_file_key.replace('trips/', 'features/').replace('.parquet', '.json').replace('.csv', '.json')
            processed_file = f"/tmp/{os.path.basename(processed_key)}"
            
            with open(processed_file, 'w') as f:
                json.dump(features, f)
            
            # Upload processed data
            self.s3_client.upload_file(processed_file, self.processed_bucket, processed_key)
            logger.info(f"Processed features uploaded to {self.processed_bucket}/{processed_key}")
            
            # Clean up local files
            os.remove(local_file)
            os.remove(processed_file)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing trip data: {e}")
            return False
    
    def extract_trip_features(self, df, trip_file_key):
        """Extract features from trip data"""
        # Extract driver_id from file path (simplified)
        driver_id = trip_file_key.split('/')[-1].split('_')[0]
        
        # Calculate basic features
        features = {
            'driver_id': driver_id,
            'trip_id': trip_file_key,
            'total_points': len(df),
            'start_time': df['timestamp'].min() if 'timestamp' in df.columns else None,
            'end_time': df['timestamp'].max() if 'timestamp' in df.columns else None,
            'duration_minutes': None,
            'total_distance_miles': None,
            'avg_speed_mph': df['speed_mph'].mean() if 'speed_mph' in df.columns else 0,
            'max_speed_mph': df['speed_mph'].max() if 'speed_mph' in df.columns else 0,
            'avg_acceleration': df['accel_x'].mean() if 'accel_x' in df.columns else 0,
            'harsh_braking_events': len(df[df['accel_x'] < -0.3]) if 'accel_x' in df.columns else 0,
            'rapid_acceleration_events': len(df[df['accel_x'] > 0.3]) if 'accel_x' in df.columns else 0,
            'processed_at': datetime.now().isoformat()
        }
        
        # Calculate duration if we have timestamps
        if features['start_time'] and features['end_time']:
            duration = pd.to_datetime(features['end_time']) - pd.to_datetime(features['start_time'])
            features['duration_minutes'] = duration.total_seconds() / 60
        
        return features
    
    def aggregate_monthly_features(self, year, month):
        """Aggregate daily features into monthly features"""
        logger.info(f"Aggregating monthly features for {year}-{month}")
        
        # List daily feature files for the month
        prefix = f"features/{year}/{month:02d}/"
        feature_files = self.list_s3_files(prefix, self.processed_bucket)
        
        if not feature_files:
            logger.warning(f"No feature files found for {year}-{month:02d}")
            return False
        
        # Load all feature files
        all_features = []
        for file_key in feature_files:
            try:
                response = self.s3_client.get_object(Bucket=self.processed_bucket, Key=file_key)
                content = response['Body'].read().decode('utf-8')
                features = json.loads(content)
                all_features.append(features)
            except Exception as e:
                logger.error(f"Error loading feature file {file_key}: {e}")
                continue
        
        if not all_features:
            logger.warning("No valid feature data to aggregate")
            return False
        
        # Convert to DataFrame for aggregation
        df = pd.DataFrame(all_features)
        
        # Group by driver and aggregate
        monthly_features = df.groupby('driver_id').agg({
            'total_points': ['sum', 'count'],
            'avg_speed_mph': 'mean',
            'max_speed_mph': 'max',
            'avg_acceleration': 'mean',
            'harsh_braking_events': 'sum',
            'rapid_acceleration_events': 'sum'
        }).reset_index()
        
        # Flatten column names
        monthly_features.columns = ['_'.join(col).strip() if col[1] else col[0] for col in monthly_features.columns]
        
        # Add metadata
        monthly_features['month'] = f"{year}-{month:02d}"
        monthly_features['processed_at'] = datetime.now().isoformat()
        
        # Save aggregated features
        monthly_file = f"/tmp/monthly_features_{year}_{month:02d}.parquet"
        monthly_features.to_parquet(monthly_file, index=False)
        
        # Upload to S3
        s3_key = f"aggregated_features/{year}/{month:02d}/monthly_features.parquet"
        self.s3_client.upload_file(monthly_file, self.processed_bucket, s3_key)
        
        logger.info(f"Monthly features aggregated and uploaded to {self.processed_bucket}/{s3_key}")
        
        # Clean up
        os.remove(monthly_file)
        
        return True
    
    def list_s3_files(self, prefix, bucket):
        """List files in S3 with a given prefix"""
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents']]
            return []
        except Exception as e:
            logger.error(f"Error listing S3 files: {e}")
            return []

# Run the pipeline
if __name__ == "__main__":
    pipeline = TelematicsDataPipeline()
    
    # Process a specific trip file (example)
    # pipeline.process_trip_data("trips/2024/01/driver_001_trip_001.parquet")
    
    # Aggregate monthly features (example)
    # pipeline.aggregate_monthly_features(2024, 1)
```

## Real-time Data Processing

### Kinesis Data Stream Setup

```bash
# Create Kinesis data stream for real-time telematics data
aws kinesis create-stream --stream-name telematics-real-time-data --shard-count 2

# Create IAM role for Kinesis access
cat > kinesis-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "kinesis.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

aws iam create-role \
    --role-name TelematicsKinesisRole \
    --assume-role-policy-document file://kinesis-trust-policy.json

# Attach policies
aws iam attach-role-policy \
    --role-name TelematicsKinesisRole \
    --policy-arn arn:aws:iam::aws:policy/AmazonKinesisFullAccess
```

### Real-time Data Processor

Create `processors/real_time_processor.py`:

```python
#!/usr/bin/env python3
"""
Real-time data processor for telematics system
"""

import boto3
import json
import logging
from datetime import datetime
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealTimeDataProcessor:
    def __init__(self):
        self.kinesis_client = boto3.client('kinesis')
        self.stream_name = 'telematics-real-time-data'
        self.s3_client = boto3.client('s3')
        self.processed_bucket = 'telematics-processed-data-[your-account-id]'
    
    def process_stream_data(self):
        """Process data from Kinesis stream"""
        # Get shard iterator
        response = self.kinesis_client.describe_stream(StreamName=self.stream_name)
        shard_id = response['StreamDescription']['Shards'][0]['ShardId']
        
        shard_iterator = self.kinesis_client.get_shard_iterator(
            StreamName=self.stream_name,
            ShardId=shard_id,
            ShardIteratorType='LATEST'
        )['ShardIterator']
        
        # Process records
        while True:
            try:
                response = self.kinesis_client.get_records(ShardIterator=shard_iterator, Limit=100)
                records = response['Records']
                
                for record in records:
                    # Parse the data
                    data = json.loads(record['Data'])
                    self.process_record(data)
                
                # Update shard iterator
                shard_iterator = response['NextShardIterator']
                
                # Sleep briefly to avoid excessive API calls
                import time
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing stream data: {e}")
                break
    
    def process_record(self, data):
        """Process individual record"""
        try:
            # Extract driver and trip information
            driver_id = data.get('driver_id')
            trip_id = data.get('trip_id')
            timestamp = data.get('timestamp')
            
            # Perform real-time risk scoring
            risk_score = self.calculate_real_time_risk(data)
            
            # Create result record
            result = {
                'driver_id': driver_id,
                'trip_id': trip_id,
                'timestamp': timestamp,
                'risk_score': risk_score,
                'processed_at': datetime.now().isoformat()
            }
            
            # Save to S3
            result_key = f"real_time_scores/{driver_id}/{trip_id}/{timestamp}.json"
            result_json = json.dumps(result)
            
            self.s3_client.put_object(
                Bucket=self.processed_bucket,
                Key=result_key,
                Body=result_json
            )
            
            logger.info(f"Processed real-time data for driver {driver_id}, trip {trip_id}")
            
        except Exception as e:
            logger.error(f"Error processing record: {e}")
    
    def calculate_real_time_risk(self, data):
        """Calculate real-time risk score"""
        # Simplified risk calculation
        risk_score = 0.1  # Base score
        
        # Add risk factors
        if 'speed_mph' in data:
            speed = data['speed_mph']
            if speed > 80:
                risk_score += 0.2
            elif speed > 65:
                risk_score += 0.1
        
        if 'acceleration' in data:
            accel = data['acceleration']
            if accel > 0.5:  # Rapid acceleration
                risk_score += 0.15
            elif accel < -0.5:  # Harsh braking
                risk_score += 0.2
        
        if 'phone_usage' in data and data['phone_usage']:
            risk_score += 0.25
        
        # Clamp to 0-1 range
        return max(0.0, min(1.0, risk_score))

# Run the processor
if __name__ == "__main__":
    processor = RealTimeDataProcessor()
    processor.process_stream_data()
```

## Batch Processing with Spark

### EMR Cluster Setup

```bash
# Create EMR cluster for batch processing
aws emr create-cluster \
    --name "TelematicsBatchProcessing" \
    --release-label emr-6.4.0 \
    --instance-type m5.xlarge \
    --instance-count 3 \
    --applications Name=Spark Name=Hadoop \
    --ec2-attributes KeyName=[your-key-pair] \
    --service-role EMR_DefaultRole \
    --ec2-attributes InstanceProfile=EMR_EC2_DefaultRole
```

### Spark Batch Processing Job

Create `spark_jobs/feature_aggregation.py`:

```python
#!/usr/bin/env python3
"""
Spark job for batch feature aggregation
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import argparse

def create_spark_session():
    """Create Spark session"""
    spark = SparkSession.builder \
        .appName("TelematicsFeatureAggregation") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .getOrCreate()
    return spark

def process_trip_features(spark, input_path, output_path):
    """Process trip features and aggregate them"""
    
    # Read trip data
    df = spark.read.parquet(input_path)
    
    # Extract date from timestamp for grouping
    df_with_date = df.withColumn("trip_date", to_date(col("timestamp")))
    
    # Aggregate features by driver and date
    aggregated = df_with_date.groupBy("driver_id", "trip_date").agg(
        count("*").alias("trip_count"),
        sum("total_distance_miles").alias("total_miles"),
        avg("avg_speed_mph").alias("avg_speed"),
        max("max_speed_mph").alias("max_speed"),
        sum("harsh_braking_events").alias("total_hard_brakes"),
        sum("rapid_acceleration_events").alias("total_rapid_accels"),
        avg("phone_usage_duration").alias("avg_phone_usage")
    )
    
    # Calculate derived features
    result = aggregated.withColumn(
        "avg_miles_per_trip",
        col("total_miles") / col("trip_count")
    ).withColumn(
        "hard_brake_rate",
        col("total_hard_brakes") / col("total_miles") * 100
    ).withColumn(
        "rapid_accel_rate",
        col("total_rapid_accels") / col("total_miles") * 100
    )
    
    # Save results
    result.write.mode("overwrite").parquet(output_path)
    
    print(f"Processed {result.count()} records")
    return result

def main():
    parser = argparse.ArgumentParser(description="Process telematics data with Spark")
    parser.add_argument("--input", required=True, help="Input S3 path")
    parser.add_argument("--output", required=True, help="Output S3 path")
    
    args = parser.parse_args()
    
    spark = create_spark_session()
    
    try:
        result = process_trip_features(spark, args.input, args.output)
        result.show(5)
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
```

### Submit Spark Job to EMR

```bash
# Submit Spark job to EMR cluster
aws emr add-steps --cluster-id [cluster-id] --steps '[
  {
    "Name": "Telematics Feature Aggregation",
    "ActionOnFailure": "CONTINUE",
    "HadoopJarStep": {
      "Jar": "command-runner.jar",
      "Args": [
        "spark-submit",
        "--deploy-mode", "cluster",
        "s3://telematics-scripts/feature_aggregation.py",
        "--input", "s3://telematics-raw-data/trips/",
        "--output", "s3://telematics-processed-data/aggregated_features/"
      ]
    }
  }
]'
```

## Data Security and Compliance

### Encryption at Rest

```bash
# Enable default encryption for S3 buckets
aws s3api put-bucket-encryption \
    --bucket telematics-raw-data-[your-account-id] \
    --server-side-encryption-configuration '{
        "Rules": [
            {
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "AES256"
                }
            }
        ]
    }'
```

### Data Access Logging

```bash
# Enable S3 server access logging
aws s3api put-bucket-logging \
    --bucket telematics-raw-data-[your-account-id] \
    --bucket-logging-status '{
        "LoggingEnabled": {
            "TargetBucket": "telematics-logs-[your-account-id]",
            "TargetPrefix": "s3-access-logs/"
        }
    }'
```

### Database Security

```bash
# Enable RDS encryption
# Note: This must be done during database creation
# For existing databases, you'll need to create a snapshot and restore with encryption

# Enable enhanced monitoring
aws rds modify-db-instance \
    --db-instance-identifier telematics-db \
    --monitoring-interval 60 \
    --monitoring-role-arn arn:aws:iam::[account-id]:role/rds-monitoring-role
```

## Backup and Disaster Recovery

### Automated Backups

```bash
# Enable automated backups for RDS
aws rds modify-db-instance \
    --db-instance-identifier telematics-db \
    --backup-retention-period 7 \
    --preferred-backup-window "03:00-04:00"

# Create manual snapshot
aws rds create-db-snapshot \
    --db-instance-identifier telematics-db \
    --db-snapshot-identifier telematics-db-snapshot-$(date +%Y%m%d)
```

### Cross-Region Replication

```bash
# Enable cross-region replication for critical S3 buckets
aws s3api put-bucket-replication \
    --bucket telematics-processed-data-[your-account-id] \
    --replication-configuration '{
        "Role": "arn:aws:iam::[account-id]:role/s3-replication-role",
        "Rules": [
            {
                "ID": "ReplicateToUsWest",
                "Status": "Enabled",
                "Destination": {
                    "Bucket": "arn:aws:s3:::telematics-backup-us-west-[your-account-id]"
                }
            }
        ]
    }'
```

## Testing and Validation

### Data Pipeline Testing

```bash
# Test database connection
python -c "
import os
from scripts.migrate_database import migrate_database
migrate_database()
print('Database migration completed successfully')
"

# Test S3 access
python -c "
from pipelines.data_pipeline import S3DataManager
s3_manager = S3DataManager()
files = s3_manager.list_files('trips/2024/01/')
print(f'Found {len(files)} trip files')
"

# Test data processing
python pipelines/data_pipeline.py
```

### Monitoring Data Pipeline

```bash
# Check S3 bucket sizes
aws s3 ls s3://telematics-raw-data-[your-account-id] --recursive --human-readable --summarize

# Check RDS performance
aws rds describe-db-instances --db-instance-identifier telematics-db

# Check EMR cluster status
aws emr list-clusters --cluster-states WAITING RUNNING
```

This completes the cloud data storage and processing setup for your telematics system.