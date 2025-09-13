# Cloud Infrastructure Setup for Telematics System

This tutorial provides step-by-step instructions for setting up cloud infrastructure for the Telematics Insurance Risk Assessment System.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Cloud Provider Selection](#cloud-provider-selection)
3. [Account Setup](#account-setup)
4. [CLI Tools Installation](#cli-tools-installation)
5. [Basic Infrastructure Setup](#basic-infrastructure-setup)
6. [Container Registry Setup](#container-registry-setup)
7. [Database Setup](#database-setup)
8. [Object Storage Setup](#object-storage-setup)
9. [Monitoring and Logging Setup](#monitoring-and-logging-setup)
10. [Security Configuration](#security-configuration)
11. [Deployment Pipeline Setup](#deployment-pipeline-setup)
12. [Testing and Validation](#testing-and-validation)

## Prerequisites

Before starting, ensure you have:
- A computer with internet access
- Basic knowledge of command-line interfaces
- A credit card for cloud account verification (most providers offer free tiers)
- Git installed on your system
- Docker and Docker Compose installed

## Cloud Provider Selection

We recommend AWS for this tutorial due to its comprehensive free tier and extensive documentation. However, the concepts can be adapted to Azure or GCP.

### Why AWS?
- Generous free tier offerings
- Comprehensive managed services
- Extensive documentation and community support
- Mature ecosystem for containerized applications

## Account Setup

1. Visit [AWS Console](https://aws.amazon.com/)
2. Click "Create an AWS Account"
3. Follow the registration process
4. Verify your email address
5. Provide payment information (required for verification, but you'll stay within free tier limits)
6. Complete the identity verification process
7. Sign in to the AWS Management Console

## CLI Tools Installation

### AWS CLI Installation

#### Windows
```powershell
# Download the MSI installer
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi

# Or using Chocolatey
choco install awscli
```

#### macOS
```bash
# Using curl
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# Or using Homebrew
brew install awscli
```

#### Linux
```bash
# Using curl
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

### Configure AWS CLI
```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, default region (e.g., us-east-1), and output format (json)
```

### Docker Installation
Visit [Docker Installation Guide](https://docs.docker.com/get-docker/) and follow instructions for your operating system.

## Basic Infrastructure Setup

### Create VPC and Networking Components

1. Navigate to the VPC Dashboard in AWS Console
2. Create a new VPC:
   - Name: `telematics-vpc`
   - IPv4 CIDR block: `10.0.0.0/16`
3. Create subnets:
   - Public subnet 1: `10.0.1.0/24` (us-east-1a)
   - Public subnet 2: `10.0.2.0/24` (us-east-1b)
   - Private subnet 1: `10.0.3.0/24` (us-east-1a)
   - Private subnet 2: `10.0.4.0/24` (us-east-1b)
4. Create an Internet Gateway and attach it to your VPC
5. Create a route table for public subnets with a route to the Internet Gateway
6. Associate public subnets with the route table

### Security Groups
Create the following security groups:

1. **Web Security Group**:
   - Allow HTTP (80) from anywhere
   - Allow HTTPS (443) from anywhere
   - Allow SSH (22) from your IP only

2. **App Security Group**:
   - Allow ports 8080-8099 from Web Security Group
   - Allow SSH (22) from your IP only

3. **Database Security Group**:
   - Allow PostgreSQL (5432) from App Security Group only

## Container Registry Setup

### Create ECR Repositories

```bash
# Create repositories for each microservice
aws ecr create-repository --repository-name telematics/risk-service
aws ecr create-repository --repository-name telematics/pricing-service
aws ecr create-repository --repository-name telematics/trip-service
aws ecr create-repository --repository-name telematics/driver-service
aws ecr create-repository --repository-name telematics/analytics-service
aws ecr create-repository --repository-name telematics/api-gateway

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin [your-account-id].dkr.ecr.us-east-1.amazonaws.com
```

## Database Setup

### Create RDS PostgreSQL Instance

1. Navigate to the RDS Dashboard in AWS Console
2. Click "Create database"
3. Choose PostgreSQL
4. Select "Free tier" template
5. Settings:
   - DB instance identifier: `telematics-db`
   - Master username: `telematics_admin`
   - Master password: [secure password]
6. DB instance class: `db.t3.micro`
7. Storage: 20 GB (General Purpose SSD)
8. Storage autoscaling: Disable
9. VPC: Select your `telematics-vpc`
10. Subnet group: Create new, select both private subnets
11. Public access: No
12. VPC security group: Select your Database Security Group
13. Database authentication: Password authentication
14. Initial database name: `telematics`
15. Backup retention period: 0 days (for free tier)
16. Enable deletion protection: No (for development)

### Database Schema Setup

After the database is available, connect and create the required tables:

```sql
-- Connect to your database
-- Create drivers table
CREATE TABLE drivers (
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
CREATE TABLE trips (
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
CREATE TABLE monthly_features (
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
```

## Object Storage Setup

### Create S3 Bucket

```bash
# Create S3 bucket for telematics data
aws s3 mb s3://telematics-data-[your-account-id] --region us-east-1

# Set bucket policy for access
cat > bucket-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "ec2.amazonaws.com"
            },
            "Action": "s3:*",
            "Resource": [
                "arn:aws:s3:::telematics-data-[your-account-id]",
                "arn:aws:s3:::telematics-data-[your-account-id]/*"
            ]
        }
    ]
}
EOF

aws s3api put-bucket-policy --bucket telematics-data-[your-account-id] --policy file://bucket-policy.json
```

## Monitoring and Logging Setup

### CloudWatch Configuration

1. Navigate to CloudWatch in AWS Console
2. Create log groups for each service:
   ```bash
   aws logs create-log-group --log-group-name /telematics/risk-service
   aws logs create-log-group --log-group-name /telematics/pricing-service
   aws logs create-log-group --log-group-name /telematics/trip-service
   aws logs create-log-group --log-group-name /telematics/driver-service
   aws logs create-log-group --log-group-name /telematics/analytics-service
   aws logs create-log-group --log-group-name /telematics/api-gateway
   ```

3. Create basic alarms:
   ```bash
   # High CPU utilization alarm
   aws cloudwatch put-metric-alarm \
       --alarm-name telematics-high-cpu \
       --alarm-description "Alarm when CPU exceeds 70%" \
       --metric-name CPUUtilization \
       --namespace AWS/ECS \
       --statistic Average \
       --period 300 \
       --threshold 70 \
       --comparison-operator GreaterThanThreshold \
       --dimensions Name=ClusterName,Value=telematics-cluster \
       --evaluation-periods 2 \
       --alarm-actions arn:aws:sns:us-east-1:[your-account-id]:telematics-alerts \
       --unit Percent
   ```

## Security Configuration

### IAM Roles and Policies

1. Create IAM role for ECS tasks:
   ```bash
   # Create trust policy
   cat > ecs-trust-policy.json << EOF
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Principal": {
           "Service": "ecs-tasks.amazonaws.com"
         },
         "Action": "sts:AssumeRole"
       }
     ]
   }
   EOF

   # Create role
   aws iam create-role \
       --role-name TelematicsEcsTaskRole \
       --assume-role-policy-document file://ecs-trust-policy.json

   # Attach policies
   aws iam attach-role-policy \
       --role-name TelematicsEcsTaskRole \
       --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess

   aws iam attach-role-policy \
       --role-name TelematicsEcsTaskRole \
       --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess
   ```

## Deployment Pipeline Setup

### GitHub Actions Workflow

Create `.github/workflows/deploy.yml` in your repository:

```yaml
name: Deploy to AWS ECS

on:
  push:
    branches: [ main ]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v2
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v1
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1
    
    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v1
    
    - name: Build, tag, and push image to Amazon ECR
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        ECR_REPOSITORY: telematics/risk-service
        IMAGE_TAG: ${{ github.sha }}
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
    
    - name: Fill in the new image ID in the Amazon ECS task definition
      id: task-def
      uses: aws-actions/amazon-ecs-render-task-definition@v1
      with:
        task-definition: task-definition.json
        container-name: risk-service
        image: ${{ steps.login-ecr.outputs.registry }}/telematics/risk-service:${{ github.sha }}
    
    - name: Deploy Amazon ECS task definition
      uses: aws-actions/amazon-ecs-deploy-task-definition@v1
      with:
        task-definition: ${{ steps.task-def.outputs.task-definition }}
        service: telematics-risk-service
        cluster: telematics-cluster
        wait-for-service-stability: true
```

## Testing and Validation

### Validate Infrastructure

1. Check VPC and subnets:
   ```bash
   aws ec2 describe-vpcs --filters "Name=tag:Name,Values=telematics-vpc"
   aws ec2 describe-subnets --filters "Name=vpc-id,Values=[vpc-id]"
   ```

2. Check security groups:
   ```bash
   aws ec2 describe-security-groups --filters "Name=vpc-id,Values=[vpc-id]"
   ```

3. Check database:
   ```bash
   aws rds describe-db-instances --db-instance-identifier telematics-db
   ```

4. Check container registry:
   ```bash
   aws ecr describe-repositories
   ```

5. Check S3 bucket:
   ```bash
   aws s3 ls s3://telematics-data-[your-account-id]
   ```

## Next Steps

After completing this setup:
1. Proceed with containerizing your services
2. Deploy services to ECS
3. Configure load balancing
4. Set up monitoring dashboards
5. Test end-to-end functionality

This completes the basic cloud infrastructure setup for your telematics system.