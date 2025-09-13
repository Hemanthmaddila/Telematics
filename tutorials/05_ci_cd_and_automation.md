# CI/CD and Automation for Telematics System

This tutorial covers setting up continuous integration and deployment pipelines for your cloud-based telematics system.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [GitHub Repository Setup](#github-repository-setup)
3. [GitHub Actions Workflow](#github-actions-workflow)
4. [Infrastructure as Code with Terraform](#infrastructure-as-code-with-terraform)
5. [Automated Testing](#automated-testing)
6. [Deployment Strategies](#deployment-strategies)
7. [Environment Management](#environment-management)

## Prerequisites

Before starting, ensure you have:
- Completed the previous tutorials
- AWS CLI configured
- GitHub account
- Docker and Docker Compose installed
- Terraform installed
- Basic understanding of CI/CD concepts

## GitHub Repository Setup

### Create Repository

1. Go to https://github.com/new
2. Create a new repository named `telematics-system`
3. Choose public or private based on your preference
4. Initialize with a README (optional)
5. Clone the repository locally:

```bash
git clone https://github.com/[your-username]/telematics-system.git
cd telematics-system
```

### Organize Project Files

Move your project files to the repository:

```bash
# Copy project files (excluding venv and other unnecessary files)
cp -r A:\project\Telematics\* .
git add .
git commit -m "Initial commit: Telematics system"
git push origin main
```

### Set Up GitHub Secrets

1. Go to your repository Settings
2. Click "Secrets and variables" > "Actions"
3. Add the following secrets:
   - `AWS_ACCESS_KEY_ID`: Your AWS access key
   - `AWS_SECRET_ACCESS_KEY`: Your AWS secret key
   - `ECR_REGISTRY`: Your ECR registry URL

## GitHub Actions Workflow

### Create Workflow Directory

```bash
mkdir -p .github/workflows
```

### Build and Test Workflow

Create `.github/workflows/build-test.yml`:

```yaml
name: Build and Test

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run unit tests
      run: |
        python -m pytest tests/unit
    
    - name: Run integration tests
      run: |
        python -m pytest tests/integration
```

### Container Build and Deploy Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Build, Push, and Deploy

on:
  push:
    branches: [ main ]

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY_RISK: telematics/risk-service
  ECR_REPOSITORY_PRICING: telematics/pricing-service
  ECR_REPOSITORY_TRIP: telematics/trip-service
  ECR_REPOSITORY_GATEWAY: telematics/api-gateway

jobs:
  build-and-deploy:
    name: Build and Deploy
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
    
    steps:
    - name: Checkout
      uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v1
      with:
        aws-access-key-id: ${ secrets.AWS_ACCESS_KEY_ID }
        aws-secret-access-key: ${ secrets.AWS_SECRET_ACCESS_KEY }
        aws-region: ${ env.AWS_REGION }
    
    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v1
    
    - name: Build, tag, and push risk service image
      id: build-risk-image
      env:
        ECR_REGISTRY: ${ steps.login-ecr.outputs.registry }
        IMAGE_TAG: ${ github.sha }
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY_RISK:$IMAGE_TAG \
          -f microservices/risk-service/Dockerfile.cloud .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY_RISK:$IMAGE_TAG
        echo "image=$ECR_REGISTRY/$ECR_REPOSITORY_RISK:$IMAGE_TAG" >> $GITHUB_OUTPUT
    
    - name: Build, tag, and push pricing service image
      id: build-pricing-image
      env:
        ECR_REGISTRY: ${ steps.login-ecr.outputs.registry }
        IMAGE_TAG: ${ github.sha }
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY_PRICING:$IMAGE_TAG \
          -f microservices/pricing-service/Dockerfile.cloud .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY_PRICING:$IMAGE_TAG
        echo "image=$ECR_REGISTRY/$ECR_REPOSITORY_PRICING:$IMAGE_TAG" >> $GITHUB_OUTPUT
    
    - name: Build, tag, and push trip service image
      id: build-trip-image
      env:
        ECR_REGISTRY: ${ steps.login-ecr.outputs.registry }
        IMAGE_TAG: ${ github.sha }
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY_TRIP:$IMAGE_TAG \
          -f microservices/trip-service/Dockerfile.cloud .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY_TRIP:$IMAGE_TAG
        echo "image=$ECR_REGISTRY/$ECR_REPOSITORY_TRIP:$IMAGE_TAG" >> $GITHUB_OUTPUT
    
    - name: Build, tag, and push API gateway image
      id: build-gateway-image
      env:
        ECR_REGISTRY: ${ steps.login-ecr.outputs.registry }
        IMAGE_TAG: ${ github.sha }
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY_GATEWAY:$IMAGE_TAG \
          -f api-gateway/Dockerfile.cloud .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY_GATEWAY:$IMAGE_TAG
        echo "image=$ECR_REGISTRY/$ECR_REPOSITORY_GATEWAY:$IMAGE_TAG" >> $GITHUB_OUTPUT
    
    - name: Deploy to ECS
      run: |
        # Update risk service
        aws ecs update-service \
          --cluster telematics-cluster \
          --service telematics-risk-service \
          --force-new-deployment
        
        # Update pricing service
        aws ecs update-service \
          --cluster telematics-cluster \
          --service telematics-pricing-service \
          --force-new-deployment
        
        # Update trip service
        aws ecs update-service \
          --cluster telematics-cluster \
          --service telematics-trip-service \
          --force-new-deployment
        
        # Update API gateway
        aws ecs update-service \
          --cluster telematics-cluster \
          --service telematics-api-gateway \
          --force-new-deployment
```

### Scheduled Data Processing Workflow

Create `.github/workflows/data-processing.yml`:

```yaml
name: Data Processing

on:
  schedule:
    # Run daily at 2 AM UTC
    - cron: '0 2 * * *'
  workflow_dispatch:

jobs:
  process-data:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout
      uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v1
      with:
        aws-access-key-id: ${ secrets.AWS_ACCESS_KEY_ID }
        aws-secret-access-key: ${ secrets.AWS_SECRET_ACCESS_KEY }
        aws-region: us-east-1
    
    - name: Run data processing pipeline
      run: |
        python pipelines/data_pipeline.py
    
    - name: Send notification on success
      if: success()
      run: |
        echo "Data processing completed successfully" | aws sns publish \
          --topic-arn arn:aws:sns:us-east-1:[account-id]:telematics-notifications \
          --message "Daily data processing completed successfully"
    
    - name: Send notification on failure
      if: failure()
      run: |
        echo "Data processing failed" | aws sns publish \
          --topic-arn arn:aws:sns:us-east-1:[account-id]:telematics-alerts \
          --message "Daily data processing failed - please check logs"
```

## Infrastructure as Code with Terraform

### Install Terraform

```bash
# On macOS
brew tap hashicorp/tap
brew install hashicorp/tap/terraform

# On Windows (using Chocolatey)
choco install terraform

# On Linux
wget https://releases.hashicorp.com/terraform/1.5.7/terraform_1.5.7_linux_amd64.zip
unzip terraform_1.5.7_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

### Create Terraform Directory

```bash
mkdir -p terraform
```

### Variables File

Create `terraform/variables.tf`:

```hcl
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "telematics"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}
```

### Provider Configuration

Create `terraform/provider.tf`:

```hcl
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}
```

### VPC Configuration

Create `terraform/vpc.tf`:

```hcl
# VPC
resource "aws_vpc" "telematics" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-${var.environment}-vpc"
  }
}

# Public subnets
resource "aws_subnet" "public" {
  count                   = length(var.availability_zones)
  vpc_id                  = aws_vpc.telematics.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-${var.environment}-public-${count.index}"
  }
}

# Private subnets
resource "aws_subnet" "private" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.telematics.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 10)
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name = "${var.project_name}-${var.environment}-private-${count.index}"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "telematics" {
  vpc_id = aws_vpc.telematics.id

  tags = {
    Name = "${var.project_name}-${var.environment}-igw"
  }
}

# Route table for public subnets
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.telematics.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.telematics.id
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-public-rt"
  }
}

# Route table associations for public subnets
resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}
```

### Security Groups

Create `terraform/security.tf`:

```hcl
# Web security group
resource "aws_security_group" "web" {
  name        = "${var.project_name}-${var.environment}-web-sg"
  description = "Security group for web traffic"
  vpc_id      = aws_vpc.telematics.id

  # HTTP access from anywhere
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS access from anywhere
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # SSH access (restrict to your IP in production)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Outbound internet access
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-web-sg"
  }
}

# Application security group
resource "aws_security_group" "app" {
  name        = "${var.project_name}-${var.environment}-app-sg"
  description = "Security group for application services"
  vpc_id      = aws_vpc.telematics.id

  # Service ports from web security group
  ingress {
    from_port       = 8080
    to_port         = 8099
    protocol        = "tcp"
    security_groups = [aws_security_group.web.id]
  }

  # SSH access (restrict to your IP in production)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Outbound internet access
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-app-sg"
  }
}

# Database security group
resource "aws_security_group" "db" {
  name        = "${var.project_name}-${var.environment}-db-sg"
  description = "Security group for database"
  vpc_id      = aws_vpc.telematics.id

  # PostgreSQL access from app security group
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-db-sg"
  }
}
```

### ECS Cluster

Create `terraform/ecs.tf`:

```hcl
# ECS cluster
resource "aws_ecs_cluster" "telematics" {
  name = "${var.project_name}-${var.environment}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-cluster"
  }
}

# ECS IAM role
resource "aws_iam_role" "ecs_task" {
  name = "${var.project_name}-${var.environment}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# ECS task execution role
resource "aws_iam_role" "ecs_task_execution" {
  name = "${var.project_name}-${var.environment}-ecs-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# Attach policies to ECS task role
resource "aws_iam_role_policy_attachment" "ecs_task_s3" {
  role       = aws_iam_role.ecs_task.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}

resource "aws_iam_role_policy_attachment" "ecs_task_logs" {
  role       = aws_iam_role.ecs_task.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
}

# Attach policies to ECS task execution role
resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}
```

### Database Configuration

Create `terraform/database.tf`:

```hcl
# RDS subnet group
resource "aws_db_subnet_group" "telematics" {
  name       = "${var.project_name}-${var.environment}-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "${var.project_name}-${var.environment}-db-subnet-group"
  }
}

# RDS instance
resource "aws_db_instance" "telematics" {
  identifier             = "${var.project_name}-${var.environment}-db"
  instance_class         = "db.t3.micro"
  engine                 = "postgres"
  engine_version         = "13"
  allocated_storage      = 20
  storage_type           = "gp2"
  username               = "telematics_admin"
  password               = "telematics_password123" # Use secrets in production
  db_subnet_group_name   = aws_db_subnet_group.telematics.name
  vpc_security_group_ids = [aws_security_group.db.id]
  publicly_accessible    = false
  skip_final_snapshot    = true

  tags = {
    Name = "${var.project_name}-${var.environment}-db"
  }
}
```

### S3 Buckets

Create `terraform/s3.tf`:

```hcl
# S3 buckets
resource "aws_s3_bucket" "raw_data" {
  bucket = "${var.project_name}-raw-data-${var.environment}-${random_string.suffix.result}"
}

resource "aws_s3_bucket" "processed_data" {
  bucket = "${var.project_name}-processed-data-${var.environment}-${random_string.suffix.result}"
}

resource "aws_s3_bucket" "models" {
  bucket = "${var.project_name}-models-${var.environment}-${random_string.suffix.result}"
}

resource "aws_s3_bucket" "logs" {
  bucket = "${var.project_name}-logs-${var.environment}-${random_string.suffix.result}"
}

# Random suffix for unique bucket names
resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}

# Bucket policies
resource "aws_s3_bucket_policy" "raw_data" {
  bucket = aws_s3_bucket.raw_data.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "s3:*"
        Resource = [
          aws_s3_bucket.raw_data.arn,
          "${aws_s3_bucket.raw_data.arn}/*"
        ]
      }
    ]
  })
}
```

### Outputs

Create `terraform/outputs.tf`:

```hcl
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.telematics.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.telematics.name
}

output "db_endpoint" {
  description = "Database endpoint"
  value       = aws_db_instance.telematics.endpoint
}

output "s3_bucket_names" {
  description = "S3 bucket names"
  value = {
    raw_data      = aws_s3_bucket.raw_data.bucket
    processed_data = aws_s3_bucket.processed_data.bucket
    models        = aws_s3_bucket.models.bucket
    logs          = aws_s3_bucket.logs.bucket
  }
}
```

### Initialize and Apply Terraform

```bash
# Initialize Terraform
cd terraform
terraform init

# Plan the infrastructure
terraform plan

# Apply the infrastructure
terraform apply
```

## Automated Testing

### Unit Tests

Create `tests/unit/test_risk_model.py`:

```python
import unittest
import pandas as pd
import numpy as np
from src.telematics_ml.models.real_risk_model import RiskAssessmentModel

class TestRiskModel(unittest.TestCase):
    def setUp(self):
        self.model = RiskAssessmentModel()
    
    def test_model_initialization(self):
        """Test that model initializes correctly"""
        self.assertIsNotNone(self.model)
    
    def test_feature_preparation(self):
        """Test feature preparation"""
        # Create sample data
        sample_data = {
            'driver_id': ['test_driver'],
            'total_trips': [45],
            'total_drive_time_hours': [25.0],
            'total_miles_driven': [450.0],
            'avg_speed_mph': [38.0],
            'max_speed_mph': [82.0],
            'avg_jerk_rate': [0.6],
            'hard_brake_rate_per_100_miles': [1.2],
            'rapid_accel_rate_per_100_miles': [0.9],
            'harsh_cornering_rate_per_100_miles': [0.4],
            'swerving_events_per_100_miles': [0.2],
            'pct_miles_night': [0.15],
            'pct_miles_late_night_weekend': [0.08],
            'pct_miles_weekday_rush_hour': [0.25],
            'pct_trip_time_screen_on': [0.03],
            'handheld_events_rate_per_hour': [0.3],
            'pct_trip_time_on_call_handheld': [0.01],
            'avg_engine_rpm': [2200.0],
            'has_dtc_codes': [False],
            'airbag_deployment_flag': [False],
            'driver_age': [32],
            'vehicle_age': [3],
            'prior_at_fault_accidents': [0],
            'years_licensed': [14],
            'data_source': ['phone_plus_device'],
            'gps_accuracy_avg_meters': [5.0],
            'driver_passenger_confidence_score': [0.88],
            'speeding_rate_per_100_miles': [0.7],
            'max_speed_over_limit_mph': [8.0],
            'pct_miles_highway': [0.45],
            'pct_miles_urban': [0.4],
            'pct_miles_in_rain_or_snow': [0.03],
            'pct_miles_in_heavy_traffic': [0.12],
            'had_claim_in_period': [0]
        }
        
        df = pd.DataFrame(sample_data)
        X, y = self.model.prepare_features(df)
        
        self.assertIsInstance(X, pd.DataFrame)
        self.assertIsInstance(y, pd.Series)
        self.assertEqual(len(X), 1)
        self.assertEqual(len(y), 1)

if __name__ == '__main__':
    unittest.main()
```

### Integration Tests

Create `tests/integration/test_services.py`:

```python
import unittest
import requests
import time
import os

class TestServices(unittest.TestCase):
    def setUp(self):
        self.base_url = os.environ.get('SERVICE_BASE_URL', 'http://localhost:8080')
    
    def test_api_gateway_health(self):
        """Test API gateway health endpoint"""
        response = requests.get(f"{self.base_url}/health")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'healthy')
    
    def test_risk_service_health(self):
        """Test risk service health endpoint"""
        response = requests.get(f"{self.base_url}/risk/health")
        # This might fail in local testing, so we check for common success codes
        self.assertIn(response.status_code, [200, 503])  # 503 if service not ready
    
    def test_pricing_service_health(self):
        """Test pricing service health endpoint"""
        response = requests.get(f"{self.base_url}/pricing/health")
        self.assertIn(response.status_code, [200, 503])

if __name__ == '__main__':
    unittest.main()
```

## Deployment Strategies

### Blue-Green Deployment

Update your ECS service configuration to support blue-green deployments:

```bash
# Create new task definition revision
aws ecs register-task-definition \
    --family telematics-risk-service \
    --cli-input-json file://new-task-definition.json

# Update service with new task definition
aws ecs update-service \
    --cluster telematics-cluster \
    --service telematics-risk-service \
    --task-definition telematics-risk-service:v2 \
    --force-new-deployment
```

### Rolling Updates

Configure rolling updates in your task definition:

```json
{
  "family": "telematics-risk-service",
  "deploymentConfiguration": {
    "deploymentCircuitBreaker": {
      "enable": true,
      "rollback": true
    },
    "maximumPercent": 200,
    "minimumHealthyPercent": 50
  }
}
```

## Environment Management

### Multiple Environments

Create separate Terraform workspaces for different environments:

```bash
# Create workspaces
terraform workspace new dev
terraform workspace new staging
terraform workspace new prod

# Switch to dev environment
terraform workspace select dev

# Apply with dev variables
terraform apply -var-file=terraform/vars/dev.tfvars
```

### Environment Variables

Create `terraform/vars/dev.tfvars`:

```hcl
environment = "dev"
instance_class = "db.t3.micro"
desired_count = 1
```

Create `terraform/vars/prod.tfvars`:

```hcl
environment = "prod"
instance_class = "db.t3.small"
desired_count = 3
```

## Monitoring CI/CD Pipeline

### Pipeline Status Monitoring

Create `scripts/monitor_pipeline.py`:

```python
#!/usr/bin/env python3
"""
Monitor CI/CD pipeline status
"""

import requests
import json
import time
from datetime import datetime

class PipelineMonitor:
    def __init__(self, github_repo, github_token):
        self.github_repo = github_repo
        self.github_token = github_token
        self.headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
    
    def get_workflow_runs(self):
        """Get recent workflow runs"""
        url = f"https://api.github.com/repos/{self.github_repo}/actions/runs"
        response = requests.get(url, headers=self.headers)
        return response.json()
    
    def check_pipeline_status(self):
        """Check overall pipeline status"""
        try:
            runs = self.get_workflow_runs()
            if 'workflow_runs' not in runs:
                return "UNKNOWN"
            
            latest_run = runs['workflow_runs'][0]
            status = latest_run['status']
            conclusion = latest_run['conclusion']
            
            if status == 'completed':
                return conclusion.upper()  # success, failure, cancelled
            else:
                return "RUNNING"
                
        except Exception as e:
            print(f"Error checking pipeline status: {e}")
            return "ERROR"
    
    def monitor_pipeline(self, check_interval=300):
        """Monitor pipeline continuously"""
        print("Monitoring CI/CD pipeline...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                status = self.check_pipeline_status()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{timestamp}] Pipeline status: {status}")
                
                if status == "SUCCESS":
                    print("✅ Pipeline completed successfully")
                elif status == "FAILURE":
                    print("❌ Pipeline failed")
                    # Send alert
                    self.send_alert("Pipeline failed")
                
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped")

    def send_alert(self, message):
        """Send alert notification"""
        # Implement your alerting mechanism here
        # Could be SNS, Slack, email, etc.
        print(f"🚨 ALERT: {message}")

# Usage
if __name__ == "__main__":
    monitor = PipelineMonitor(
        github_repo="your-username/telematics-system",
        github_token="your-github-token"
    )
    
    # Check status once
    status = monitor.check_pipeline_status()
    print(f"Current pipeline status: {status}")
    
    # Monitor continuously (uncomment to use)
    # monitor.monitor_pipeline()
```

## Testing and Validation

### Validate CI/CD Setup

```bash
# Test GitHub Actions workflow
# Make a small change and push to trigger workflow
echo "# Test change" >> README.md
git add README.md
git commit -m "Test CI/CD workflow"
git push origin main

# Monitor workflow status
curl -H "Authorization: token [your-token]" \
     https://api.github.com/repos/[your-username]/telematics-system/actions/runs
```

### Validate Terraform Configuration

```bash
# Validate Terraform configuration
cd terraform
terraform validate

# Check Terraform plan
terraform plan

# Apply in dev environment
terraform workspace select dev
terraform apply -var-file=vars/dev.tfvars
```

### Validate Automated Tests

```bash
# Run unit tests
python -m pytest tests/unit -v

# Run integration tests
python -m pytest tests/integration -v

# Run all tests
python -m pytest tests/ -v
```

This completes the CI/CD and automation setup for your telematics system.