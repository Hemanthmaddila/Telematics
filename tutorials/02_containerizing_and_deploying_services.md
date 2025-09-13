# Containerizing and Deploying Telematics Services

This tutorial covers containerizing your telematics microservices and deploying them to cloud infrastructure.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Containerizing Services](#containerizing-services)
3. [Building Docker Images](#building-docker-images)
4. [Pushing Images to Container Registry](#pushing-images-to-container-registry)
5. [Setting up ECS Cluster](#setting-up-ecs-cluster)
6. [Deploying Services to ECS](#deploying-services-to-ecs)
7. [Configuring Load Balancer](#configuring-load-balancer)
8. [Service Communication](#service-communication)
9. [Testing Deployed Services](#testing-deployed-services)

## Prerequisites

Before starting, ensure you have:
- Completed the Cloud Infrastructure Setup tutorial
- AWS CLI configured
- Docker installed and running
- Access to ECR repositories created in previous tutorial
- Your telematics project code ready

## Containerizing Services

### Risk Service Containerization

Create `microservices/risk-service/Dockerfile.cloud`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional ML dependencies
RUN pip install mlflow psycopg2-binary

# Copy application code
COPY src/telematics_ml src/telematics_ml
COPY microservices/risk-service/app_real.py ./app.py

# Create directories
RUN mkdir -p models data

# Expose port
EXPOSE 8082

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8082/health || exit 1

# Run the application
CMD ["python", "app.py"]
```

### Pricing Service Containerization

Create `microservices/pricing-service/Dockerfile.cloud`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY microservices/pricing-service ./pricing-service
COPY src/telematics_ml ./telematics_ml

# Expose port
EXPOSE 8083

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8083/health || exit 1

# Run the application
CMD ["python", "pricing-service/app.py"]
```

### Trip Service Containerization

Create `microservices/trip-service/Dockerfile.cloud`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY microservices/trip-service ./trip-service
COPY src/telematics_ml ./telematics_ml

# Expose port
EXPOSE 8081

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8081/health || exit 1

# Run the application
CMD ["python", "trip-service/app.py"]
```

### API Gateway Containerization

Create `api-gateway/Dockerfile.cloud`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api-gateway/gateway_complete.py ./gateway.py

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["python", "gateway.py"]
```

## Building Docker Images

### Build All Services

```bash
# Navigate to project root
cd A:\project\Telematics

# Build risk service
docker build -t telematics/risk-service -f microservices/risk-service/Dockerfile.cloud .

# Build pricing service
docker build -t telematics/pricing-service -f microservices/pricing-service/Dockerfile.cloud .

# Build trip service
docker build -t telematics/trip-service -f microservices/trip-service/Dockerfile.cloud .

# Build API gateway
docker build -t telematics/api-gateway -f api-gateway/Dockerfile.cloud .
```

## Pushing Images to Container Registry

### Tag and Push Images to ECR

```bash
# Get ECR login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin [your-account-id].dkr.ecr.us-east-1.amazonaws.com

# Tag images
docker tag telematics/risk-service:latest [your-account-id].dkr.ecr.us-east-1.amazonaws.com/telematics/risk-service:latest
docker tag telematics/pricing-service:latest [your-account-id].dkr.ecr.us-east-1.amazonaws.com/telematics/pricing-service:latest
docker tag telematics/trip-service:latest [your-account-id].dkr.ecr.us-east-1.amazonaws.com/telematics/trip-service:latest
docker tag telematics/api-gateway:latest [your-account-id].dkr.ecr.us-east-1.amazonaws.com/telematics/api-gateway:latest

# Push images
docker push [your-account-id].dkr.ecr.us-east-1.amazonaws.com/telematics/risk-service:latest
docker push [your-account-id].dkr.ecr.us-east-1.amazonaws.com/telematics/pricing-service:latest
docker push [your-account-id].dkr.ecr.us-east-1.amazonaws.com/telematics/trip-service:latest
docker push [your-account-id].dkr.ecr.us-east-1.amazonaws.com/telematics/api-gateway:latest
```

## Setting up ECS Cluster

### Create ECS Cluster

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name telematics-cluster

# Create IAM role for ECS instance
cat > ecs-instance-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

aws iam create-role \
    --role-name TelematicsEcsInstanceRole \
    --assume-role-policy-document file://ecs-instance-trust-policy.json

aws iam attach-role-policy \
    --role-name TelematicsEcsInstanceRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role

# Create ECS instance profile
aws iam create-instance-profile --instance-profile-name TelematicsEcsInstanceProfile
aws iam add-role-to-instance-profile --instance-profile-name TelematicsEcsInstanceProfile --role-name TelematicsEcsInstanceRole
```

## Deploying Services to ECS

### Create Task Definitions

Create `task-definitions/risk-service.json`:

```json
{
  "family": "telematics-risk-service",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::[your-account-id]:role/TelematicsEcsTaskRole",
  "containerDefinitions": [
    {
      "name": "risk-service",
      "image": "[your-account-id].dkr.ecr.us-east-1.amazonaws.com/telematics/risk-service:latest",
      "portMappings": [
        {
          "containerPort": 8082,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "environment": [
        {
          "name": "PORT",
          "value": "8082"
        },
        {
          "name": "DATABASE_URL",
          "value": "postgresql://telematics_admin:[password]@telematics-db.[region].rds.amazonaws.com:5432/telematics"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/telematics/risk-service",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

Register the task definition:

```bash
aws ecs register-task-definition --cli-input-json file://task-definitions/risk-service.json
```

### Create ECS Service

```bash
# Create security group for service
aws ec2 create-security-group \
    --group-name telematics-service-sg \
    --description "Security group for telematics services" \
    --vpc-id [vpc-id]

# Allow traffic on service ports
aws ec2 authorize-security-group-ingress \
    --group-id [security-group-id] \
    --protocol tcp \
    --port 8082 \
    --source-group [web-sg-id]

# Create ECS service
aws ecs create-service \
    --cluster telematics-cluster \
    --service-name telematics-risk-service \
    --task-definition telematics-risk-service \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-1,subnet-2],securityGroups=[sg-id],assignPublicIp=ENABLED}"
```

## Configuring Load Balancer

### Create Application Load Balancer

```bash
# Create load balancer
aws elbv2 create-load-balancer \
    --name telematics-alb \
    --subnets [subnet-1] [subnet-2] \
    --security-groups [web-sg-id] \
    --scheme internet-facing \
    --type application

# Create target group
aws elbv2 create-target-group \
    --name telematics-risk-tg \
    --protocol HTTP \
    --port 8082 \
    --vpc-id [vpc-id] \
    --target-type ip

# Register targets
aws elbv2 register-targets \
    --target-group-arn [target-group-arn] \
    --targets Id=[ecs-task-ip],Port=8082

# Create listener
aws elbv2 create-listener \
    --load-balancer-arn [load-balancer-arn] \
    --protocol HTTP \
    --port 80 \
    --default-actions Type=forward,TargetGroupArn=[target-group-arn]
```

## Service Communication

### Environment Variables for Service Discovery

Update your services to use environment variables for service discovery:

```python
# In your service code
import os

RISK_SERVICE_URL = os.environ.get('RISK_SERVICE_URL', 'http://localhost:8082')
PRICING_SERVICE_URL = os.environ.get('PRICING_SERVICE_URL', 'http://localhost:8083')
TRIP_SERVICE_URL = os.environ.get('TRIP_SERVICE_URL', 'http://localhost:8081')
```

### Docker Compose for Local Testing

Create `docker-compose.cloud.yml` for local testing:

```yaml
version: '3.8'

services:
  risk-service:
    build:
      context: .
      dockerfile: microservices/risk-service/Dockerfile.cloud
    ports:
      - "8082:8082"
    environment:
      - DATABASE_URL=postgresql://telematics_admin:password@host.docker.internal:5432/telematics
      - AWS_REGION=us-east-1

  pricing-service:
    build:
      context: .
      dockerfile: microservices/pricing-service/Dockerfile.cloud
    ports:
      - "8083:8083"
    environment:
      - RISK_SERVICE_URL=http://risk-service:8082
      - DATABASE_URL=postgresql://telematics_admin:password@host.docker.internal:5432/telematics

  trip-service:
    build:
      context: .
      dockerfile: microservices/trip-service/Dockerfile.cloud
    ports:
      - "8081:8081"
    environment:
      - DATABASE_URL=postgresql://telematics_admin:password@host.docker.internal:5432/telematics

  api-gateway:
    build:
      context: .
      dockerfile: api-gateway/Dockerfile.cloud
    ports:
      - "8080:8080"
    environment:
      - RISK_SERVICE_URL=http://risk-service:8082
      - PRICING_SERVICE_URL=http://pricing-service:8083
      - TRIP_SERVICE_URL=http://trip-service:8081
```

## Testing Deployed Services

### Health Check Testing

```bash
# Test risk service health
curl http://[alb-dns-name]/risk/health

# Test pricing service health
curl http://[alb-dns-name]/pricing/health

# Test trip service health
curl http://[alb-dns-name]/trip/health

# Test API gateway health
curl http://[alb-dns-name]/health
```

### Functional Testing

```bash
# Test risk assessment
curl -X POST http://[alb-dns-name]/risk/assess \
  -H "Content-Type: application/json" \
  -d '{
    "driver_id": "test_driver_001",
    "features": {
      "total_trips": 45,
      "total_drive_time_hours": 25.0,
      "total_miles_driven": 450.0,
      "avg_speed_mph": 38.0,
      "max_speed_mph": 82.0,
      "avg_jerk_rate": 0.6,
      "hard_brake_rate_per_100_miles": 1.2,
      "rapid_accel_rate_per_100_miles": 0.9,
      "harsh_cornering_rate_per_100_miles": 0.4,
      "swerving_events_per_100_miles": 0.2,
      "pct_miles_night": 0.15,
      "pct_miles_late_night_weekend": 0.08,
      "pct_miles_weekday_rush_hour": 0.25,
      "pct_trip_time_screen_on": 0.03,
      "handheld_events_rate_per_hour": 0.3,
      "pct_trip_time_on_call_handheld": 0.01,
      "avg_engine_rpm": 2200.0,
      "has_dtc_codes": false,
      "airbag_deployment_flag": false,
      "driver_age": 32,
      "vehicle_age": 3,
      "prior_at_fault_accidents": 0,
      "years_licensed": 14,
      "data_source": "phone_plus_device",
      "gps_accuracy_avg_meters": 5.0,
      "driver_passenger_confidence_score": 0.88,
      "speeding_rate_per_100_miles": 0.7,
      "max_speed_over_limit_mph": 8.0,
      "pct_miles_highway": 0.45,
      "pct_miles_urban": 0.4,
      "pct_miles_in_rain_or_snow": 0.03,
      "pct_miles_in_heavy_traffic": 0.12
    }
  }'
```

## Monitoring Deployed Services

### View Service Logs

```bash
# View risk service logs
aws logs tail /telematics/risk-service --follow

# View pricing service logs
aws logs tail /telematics/pricing-service --follow
```

### Check Service Status

```bash
# Check ECS service status
aws ecs describe-services --cluster telematics-cluster --services telematics-risk-service

# Check running tasks
aws ecs list-tasks --cluster telematics-cluster
```

## Troubleshooting

### Common Issues and Solutions

1. **Service won't start**:
   - Check CloudWatch logs for error messages
   - Verify environment variables are correctly set
   - Ensure security groups allow required traffic

2. **Database connection issues**:
   - Verify database endpoint and credentials
   - Check that database security group allows connections
   - Ensure VPC and subnet configuration is correct

3. **Load balancer health checks failing**:
   - Verify service is listening on correct port
   - Check security group rules
   - Ensure health check path returns 200 status

4. **Container image not found**:
   - Verify ECR repository name and region
   - Check that images were pushed successfully
   - Ensure task definition references correct image URI

This completes the containerization and deployment of your telematics services to the cloud.