# Monitoring, Logging, and Observability for Telematics System

This tutorial covers setting up comprehensive monitoring, logging, and observability for your cloud-based telematics system.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [CloudWatch Metrics Setup](#cloudwatch-metrics-setup)
3. [Centralized Logging with CloudWatch Logs](#centralized-logging-with-cloudwatch-logs)
4. [Application Performance Monitoring](#application-performance-monitoring)
5. [Distributed Tracing](#distributed-tracing)
6. [Custom Dashboards and Alerts](#custom-dashboards-and-alerts)
7. [Health Checks and Service Discovery](#health-checks-and-service-discovery)
8. [Security Monitoring](#security-monitoring)
9. [Cost Monitoring and Optimization](#cost-monitoring-and-optimization)

## Prerequisites

Before starting, ensure you have:
- Completed the previous tutorials
- AWS CLI configured
- Services deployed to ECS
- CloudWatch Logs groups created
- Basic understanding of monitoring concepts

## CloudWatch Metrics Setup

### Container Metrics Collection

Enable detailed monitoring for ECS services:

```bash
# Update ECS service to enable detailed monitoring
aws ecs update-service \
    --cluster telematics-cluster \
    --service telematics-risk-service \
    --enable-execute-command
```

### Custom Metrics Implementation

Create `monitoring/metrics_collector.py`:

```python
#!/usr/bin/env python3
"""
Metrics collector for telematics services
"""

import boto3
import psutil
import time
import logging
from datetime import datetime
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetricsCollector:
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
        self.service_name = os.environ.get('SERVICE_NAME', 'unknown-service')
        self.namespace = 'Telematics/Application'
    
    def collect_system_metrics(self):
        """Collect system-level metrics"""
        metrics = []
        
        # CPU utilization
        cpu_percent = psutil.cpu_percent(interval=1)
        metrics.append({
            'MetricName': 'CPUUtilization',
            'Value': cpu_percent,
            'Unit': 'Percent'
        })
        
        # Memory utilization
        memory = psutil.virtual_memory()
        metrics.append({
            'MetricName': 'MemoryUtilization',
            'Value': memory.percent,
            'Unit': 'Percent'
        })
        
        # Disk utilization
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        metrics.append({
            'MetricName': 'DiskUtilization',
            'Value': disk_percent,
            'Unit': 'Percent'
        })
        
        return metrics
    
    def collect_application_metrics(self):
        """Collect application-specific metrics"""
        metrics = []
        
        # Request rate (simulated)
        request_count = int(os.environ.get('REQUEST_COUNT', 0))
        metrics.append({
            'MetricName': 'RequestCount',
            'Value': request_count,
            'Unit': 'Count'
        })
        
        # Error rate (simulated)
        error_count = int(os.environ.get('ERROR_COUNT', 0))
        if request_count > 0:
            error_rate = (error_count / request_count) * 100
        else:
            error_rate = 0
            
        metrics.append({
            'MetricName': 'ErrorRate',
            'Value': error_rate,
            'Unit': 'Percent'
        })
        
        # Latency (simulated)
        avg_latency = float(os.environ.get('AVG_LATENCY', 0))
        metrics.append({
            'MetricName': 'Latency',
            'Value': avg_latency,
            'Unit': 'Milliseconds'
        })
        
        return metrics
    
    def publish_metrics(self):
        """Publish metrics to CloudWatch"""
        try:
            # Collect all metrics
            system_metrics = self.collect_system_metrics()
            app_metrics = self.collect_application_metrics()
            all_metrics = system_metrics + app_metrics
            
            # Add common dimensions
            timestamp = datetime.utcnow()
            metric_data = []
            
            for metric in all_metrics:
                metric_data.append({
                    'MetricName': metric['MetricName'],
                    'Dimensions': [
                        {
                            'Name': 'ServiceName',
                            'Value': self.service_name
                        },
                        {
                            'Name': 'Environment',
                            'Value': os.environ.get('ENVIRONMENT', 'production')
                        }
                    ],
                    'Timestamp': timestamp,
                    'Value': metric['Value'],
                    'Unit': metric['Unit']
                })
            
            # Publish to CloudWatch
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=metric_data
            )
            
            logger.info(f"Published {len(metric_data)} metrics to CloudWatch")
            return True
            
        except Exception as e:
            logger.error(f"Error publishing metrics: {e}")
            return False

# Run metrics collection
if __name__ == "__main__":
    collector = MetricsCollector()
    
    # Collect and publish metrics every 60 seconds
    while True:
        collector.publish_metrics()
        time.sleep(60)
```

### Docker Health Check Integration

Update your Dockerfiles to include health check metrics:

```dockerfile
# Add to your service Dockerfiles
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Add metrics collection to startup
CMD ["sh", "-c", "python monitoring/metrics_collector.py & python app.py"]
```

## Centralized Logging with CloudWatch Logs

### Structured Logging Implementation

Create `monitoring/logger.py`:

```python
#!/usr/bin/env python3
"""
Structured logging for telematics services
"""

import logging
import json
import boto3
from datetime import datetime
import os

class StructuredLogger:
    def __init__(self, service_name):
        self.service_name = service_name
        self.environment = os.environ.get('ENVIRONMENT', 'production')
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def _create_log_record(self, level, message, **kwargs):
        """Create a structured log record"""
        record = {
            'timestamp': datetime.utcnow().isoformat(),
            'service': self.service_name,
            'environment': self.environment,
            'level': level,
            'message': message,
            **kwargs
        }
        return json.dumps(record)
    
    def info(self, message, **kwargs):
        """Log info message"""
        log_record = self._create_log_record('INFO', message, **kwargs)
        self.logger.info(log_record)
    
    def warning(self, message, **kwargs):
        """Log warning message"""
        log_record = self._create_log_record('WARNING', message, **kwargs)
        self.logger.warning(log_record)
    
    def error(self, message, **kwargs):
        """Log error message"""
        log_record = self._create_log_record('ERROR', message, **kwargs)
        self.logger.error(log_record)
    
    def debug(self, message, **kwargs):
        """Log debug message"""
        log_record = self._create_log_record('DEBUG', message, **kwargs)
        self.logger.debug(log_record)

# Usage example
logger = StructuredLogger('risk-service')

# Log structured events
logger.info('Risk assessment completed', 
           driver_id='driver_001',
           risk_score=0.45,
           processing_time_ms=125)

logger.error('Database connection failed',
            error_code='DB_CONN_ERROR',
            retry_count=3)
```

### CloudWatch Logs Configuration

```bash
# Create log groups with retention policies
aws logs create-log-group --log-group-name /telematics/risk-service
aws logs create-log-group --log-group-name /telematics/pricing-service
aws logs create-log-group --log-group-name /telematics/trip-service
aws logs create-log-group --log-group-name /telematics/api-gateway

# Set retention policies (7 days)
aws logs put-retention-policy --log-group-name /telematics/risk-service --retention-in-days 7
aws logs put-retention-policy --log-group-name /telematics/pricing-service --retention-in-days 7
aws logs put-retention-policy --log-group-name /telematics/trip-service --retention-in-days 7
aws logs put-retention-policy --log-group-name /telematics/api-gateway --retention-in-days 7
```

### Log Aggregation and Analysis

Create `monitoring/log_analyzer.py`:

```python
#!/usr/bin/env python3
"""
Log analyzer for telematics system
"""

import boto3
import json
from datetime import datetime, timedelta
import re

class LogAnalyzer:
    def __init__(self):
        self.logs_client = boto3.client('logs')
        self.log_groups = [
            '/telematics/risk-service',
            '/telematics/pricing-service',
            '/telematics/trip-service',
            '/telematics/api-gateway'
        ]
    
    def analyze_error_patterns(self, hours_back=24):
        """Analyze error patterns in logs"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours_back)
        
        error_patterns = {}
        
        for log_group in self.log_groups:
            try:
                # Get log events
                response = self.logs_client.filter_log_events(
                    logGroupName=log_group,
                    startTime=int(start_time.timestamp() * 1000),
                    endTime=int(end_time.timestamp() * 1000),
                    filterPattern='ERROR'
                )
                
                # Analyze error patterns
                for event in response.get('events', []):
                    message = event['message']
                    timestamp = event['timestamp']
                    
                    # Extract error codes or patterns
                    error_match = re.search(r'error_code["\']?:["\']?([A-Z_]+)', message, re.IGNORECASE)
                    if error_match:
                        error_code = error_match.group(1)
                        if error_code not in error_patterns:
                            error_patterns[error_code] = {
                                'count': 0,
                                'services': set(),
                                'first_occurrence': timestamp,
                                'last_occurrence': timestamp
                            }
                        error_patterns[error_code]['count'] += 1
                        error_patterns[error_code]['services'].add(log_group)
                        if timestamp < error_patterns[error_code]['first_occurrence']:
                            error_patterns[error_code]['first_occurrence'] = timestamp
                        if timestamp > error_patterns[error_code]['last_occurrence']:
                            error_patterns[error_code]['last_occurrence'] = timestamp
                
            except Exception as e:
                print(f"Error analyzing {log_group}: {e}")
        
        # Convert sets to lists for JSON serialization
        for pattern in error_patterns.values():
            pattern['services'] = list(pattern['services'])
        
        return error_patterns
    
    def get_service_metrics(self, hours_back=1):
        """Get service-level metrics"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours_back)
        
        metrics = {}
        
        for log_group in self.log_groups:
            try:
                # Count log events by level
                levels = ['ERROR', 'WARNING', 'INFO']
                level_counts = {}
                
                for level in levels:
                    response = self.logs_client.filter_log_events(
                        logGroupName=log_group,
                        startTime=int(start_time.timestamp() * 1000),
                        endTime=int(end_time.timestamp() * 1000),
                        filterPattern=level
                    )
                    level_counts[level] = len(response.get('events', []))
                
                metrics[log_group] = level_counts
                
            except Exception as e:
                print(f"Error getting metrics for {log_group}: {e}")
        
        return metrics
    
    def generate_report(self, hours_back=24):
        """Generate monitoring report"""
        print(f"Telematics System Monitoring Report - Last {hours_back} hours")
        print("=" * 60)
        
        # Error analysis
        print("\nError Patterns:")
        error_patterns = self.analyze_error_patterns(hours_back)
        if error_patterns:
            for error_code, details in error_patterns.items():
                print(f"  {error_code}: {details['count']} occurrences")
                print(f"    Services: {', '.join(details['services'])}")
                print(f"    First: {datetime.fromtimestamp(details['first_occurrence']/1000)}")
                print(f"    Last: {datetime.fromtimestamp(details['last_occurrence']/1000)}")
        else:
            print("  No significant error patterns detected")
        
        # Service metrics
        print("\nService Metrics (Last 1 hour):")
        service_metrics = self.get_service_metrics(1)
        for service, metrics in service_metrics.items():
            print(f"  {service}:")
            for level, count in metrics.items():
                print(f"    {level}: {count}")

# Run analysis
if __name__ == "__main__":
    analyzer = LogAnalyzer()
    analyzer.generate_report()
```

## Application Performance Monitoring

### Response Time Monitoring

Create `monitoring/apm.py`:

```python
#!/usr/bin/env python3
"""
Application Performance Monitoring for telematics services
"""

import time
import functools
import logging
from datetime import datetime
import boto3

logger = logging.getLogger(__name__)

class APM:
    def __init__(self, service_name):
        self.service_name = service_name
        self.cloudwatch = boto3.client('cloudwatch')
        self.namespace = 'Telematics/APM'
    
    def monitor_endpoint(self, endpoint_name):
        """Decorator to monitor endpoint performance"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    success = True
                    error = None
                except Exception as e:
                    success = False
                    error = str(e)
                    raise
                finally:
                    end_time = time.time()
                    duration = (end_time - start_time) * 1000  # Convert to milliseconds
                    
                    # Log the request
                    logger.info(f"Endpoint {endpoint_name} - Duration: {duration:.2f}ms, Success: {success}")
                    
                    # Publish metrics
                    self._publish_metrics(endpoint_name, duration, success)
                    
                    if not success:
                        logger.error(f"Endpoint {endpoint_name} failed: {error}")
                
                return result
            return wrapper
        return decorator
    
    def _publish_metrics(self, endpoint_name, duration, success):
        """Publish APM metrics to CloudWatch"""
        timestamp = datetime.utcnow()
        
        metric_data = [
            {
                'MetricName': 'ResponseTime',
                'Dimensions': [
                    {'Name': 'ServiceName', 'Value': self.service_name},
                    {'Name': 'Endpoint', 'Value': endpoint_name}
                ],
                'Timestamp': timestamp,
                'Value': duration,
                'Unit': 'Milliseconds'
            },
            {
                'MetricName': 'RequestCount',
                'Dimensions': [
                    {'Name': 'ServiceName', 'Value': self.service_name},
                    {'Name': 'Endpoint', 'Value': endpoint_name},
                    {'Name': 'Status', 'Value': 'Success' if success else 'Error'}
                ],
                'Timestamp': timestamp,
                'Value': 1,
                'Unit': 'Count'
            }
        ]
        
        try:
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=metric_data
            )
        except Exception as e:
            logger.error(f"Failed to publish APM metrics: {e}")

# Usage example
apm = APM('risk-service')

@apm.monitor_endpoint('assess_risk')
def assess_risk(driver_id, features):
    """Example endpoint to monitor"""
    # Simulate processing time
    time.sleep(0.1)
    
    # Simulate occasional errors
    if driver_id == 'error_driver':
        raise Exception("Simulated error")
    
    return {'risk_score': 0.5, 'driver_id': driver_id}

# Test the monitoring
if __name__ == "__main__":
    # Test successful request
    try:
        result = assess_risk('driver_001', {})
        print(f"Success: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test failed request
    try:
        result = assess_risk('error_driver', {})
        print(f"Success: {result}")
    except Exception as e:
        print(f"Expected error: {e}")
```

## Distributed Tracing

### X-Ray Integration

Install X-Ray SDK:
```bash
pip install aws-xray-sdk
```

Create `monitoring/tracer.py`:

```python
#!/usr/bin/env python3
"""
Distributed tracing with AWS X-Ray for telematics services
"""

from aws_xray_sdk.core import xray_recorder, patch_all
from aws_xray_sdk.core.context import Context
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware
import boto3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Tracer:
    def __init__(self, service_name):
        self.service_name = service_name
        
        # Configure X-Ray
        xray_recorder.configure(
            service=self.service_name,
            context=Context(),
            plugins=('EC2Plugin', 'ECSPlugin')
        )
        
        # Patch libraries for automatic tracing
        patch_all()
    
    def trace_function(self, name):
        """Decorator to trace function execution"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                segment = xray_recorder.begin_subsegment(name)
                try:
                    result = func(*args, **kwargs)
                    segment.put_annotation('status', 'success')
                    return result
                except Exception as e:
                    segment.put_annotation('status', 'error')
                    segment.add_exception(e)
                    raise
                finally:
                    xray_recorder.end_subsegment()
            return wrapper
        return decorator
    
    def trace_database_query(self, query_name, query_text):
        """Trace database query execution"""
        segment = xray_recorder.current_segment()
        if segment:
            subsegment = segment.put_subsegment(query_name)
            subsegment.put_annotation('query', query_text[:100])  # Limit query text length
            return subsegment
        return None
    
    def trace_external_call(self, service_name, operation):
        """Trace external service calls"""
        segment = xray_recorder.current_segment()
        if segment:
            subsegment = segment.put_subsegment(f"{service_name}.{operation}")
            subsegment.put_annotation('service', service_name)
            subsegment.put_annotation('operation', operation)
            return subsegment
        return None

# Initialize tracer
tracer = Tracer('telematics-service')

# Usage example
@tracer.trace_function('process_driver_data')
def process_driver_data(driver_id):
    """Process driver data with tracing"""
    # Simulate database query
    db_segment = tracer.trace_database_query('get_driver_profile', 'SELECT * FROM drivers WHERE driver_id = ?')
    # ... database operations ...
    if db_segment:
        db_segment.close()
    
    # Simulate external API call
    api_segment = tracer.trace_external_call('weather_service', 'get_conditions')
    # ... API call ...
    if api_segment:
        api_segment.close()
    
    return {'driver_id': driver_id, 'processed': True}

# Flask integration
def setup_flask_tracing(app):
    """Setup X-Ray tracing for Flask app"""
    XRayMiddleware(app, xray_recorder)
```

## Custom Dashboards and Alerts

### CloudWatch Dashboard Creation

Create `monitoring/dashboard.json`:

```json
{
    "widgets": [
        {
            "type": "metric",
            "x": 0,
            "y": 0,
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    ["Telematics/Application", "CPUUtilization", "ServiceName", "risk-service"],
                    ["Telematics/Application", "CPUUtilization", "ServiceName", "pricing-service"],
                    ["Telematics/Application", "CPUUtilization", "ServiceName", "trip-service"]
                ],
                "view": "timeSeries",
                "stacked": false,
                "region": "us-east-1",
                "title": "CPU Utilization by Service",
                "period": 300,
                "stat": "Average"
            }
        },
        {
            "type": "metric",
            "x": 12,
            "y": 0,
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    ["Telematics/Application", "MemoryUtilization", "ServiceName", "risk-service"],
                    ["Telematics/Application", "MemoryUtilization", "ServiceName", "pricing-service"],
                    ["Telematics/Application", "MemoryUtilization", "ServiceName", "trip-service"]
                ],
                "view": "timeSeries",
                "stacked": false,
                "region": "us-east-1",
                "title": "Memory Utilization by Service",
                "period": 300,
                "stat": "Average"
            }
        },
        {
            "type": "metric",
            "x": 0,
            "y": 6,
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    ["Telematics/APM", "ResponseTime", "ServiceName", "risk-service", "Endpoint", "assess_risk"],
                    ["Telematics/APM", "ResponseTime", "ServiceName", "pricing-service", "Endpoint", "calculate_premium"]
                ],
                "view": "timeSeries",
                "stacked": false,
                "region": "us-east-1",
                "title": "Endpoint Response Times",
                "period": 300,
                "stat": "Average"
            }
        },
        {
            "type": "metric",
            "x": 12,
            "y": 6,
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    ["Telematics/APM", "RequestCount", "ServiceName", "risk-service", "Endpoint", "assess_risk", "Status", "Success"],
                    ["Telematics/APM", "RequestCount", "ServiceName", "risk-service", "Endpoint", "assess_risk", "Status", "Error"]
                ],
                "view": "timeSeries",
                "stacked": true,
                "region": "us-east-1",
                "title": "Risk Service Request Volume",
                "period": 300,
                "stat": "Sum"
            }
        },
        {
            "type": "log",
            "x": 0,
            "y": 12,
            "width": 24,
            "height": 6,
            "properties": {
                "query": "SOURCE '/telematics/risk-service' | fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 20",
                "region": "us-east-1",
                "title": "Recent Error Logs",
                "view": "table"
            }
        }
    ]
}
```

Deploy the dashboard:
```bash
aws cloudwatch put-dashboard --dashboard-name Telematics-Dashboard --dashboard-body file://monitoring/dashboard.json
```

### Alert Creation

Create monitoring alerts:

```bash
# High CPU utilization alert
aws cloudwatch put-metric-alarm \
    --alarm-name telematics-high-cpu \
    --alarm-description "Alert when CPU utilization exceeds 70%" \
    --metric-name CPUUtilization \
    --namespace Telematics/Application \
    --statistic Average \
    --period 300 \
    --threshold 70 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=ServiceName,Value=risk-service \
    --evaluation-periods 2 \
    --alarm-actions arn:aws:sns:us-east-1:[account-id]:telematics-alerts \
    --unit Percent

# High error rate alert
aws cloudwatch put-metric-alarm \
    --alarm-name telematics-high-error-rate \
    --alarm-description "Alert when error rate exceeds 5%" \
    --metric-name ErrorRate \
    --namespace Telematics/Application \
    --statistic Average \
    --period 300 \
    --threshold 5 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=ServiceName,Value=risk-service \
    --evaluation-periods 2 \
    --alarm-actions arn:aws:sns:us-east-1:[account-id]:telematics-alerts \
    --unit Percent

# High latency alert
aws cloudwatch put-metric-alarm \
    --alarm-name telematics-high-latency \
    --alarm-description "Alert when average latency exceeds 1000ms" \
    --metric-name Latency \
    --namespace Telematics/APM \
    --statistic Average \
    --period 300 \
    --threshold 1000 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=ServiceName,Value=risk-service,Name=Endpoint,Value=assess_risk \
    --evaluation-periods 2 \
    --alarm-actions arn:aws:sns:us-east-1:[account-id]:telematics-alerts \
    --unit Milliseconds
```

## Health Checks and Service Discovery

### Enhanced Health Check Endpoint

Update your service health check endpoints:

```python
# In your service app.py files
from flask import Flask, jsonify
import psutil
import boto3
from datetime import datetime

app = Flask(__name__)

@app.route('/health')
def health_check():
    """Comprehensive health check endpoint"""
    try:
        # Check system resources
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Check database connectivity (if applicable)
        db_healthy = check_database_connection()
        
        # Check external service connectivity
        external_services_healthy = check_external_services()
        
        # Overall health status
        healthy = (
            cpu_percent < 80 and 
            memory.percent < 80 and 
            (disk.used / disk.total) < 0.85 and
            db_healthy and
            external_services_healthy
        )
        
        return jsonify({
            'status': 'healthy' if healthy else 'unhealthy',
            'service': 'risk-service',  # Update for each service
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'checks': {
                'cpu': {
                    'status': 'healthy' if cpu_percent < 80 else 'unhealthy',
                    'value': cpu_percent,
                    'threshold': 80
                },
                'memory': {
                    'status': 'healthy' if memory.percent < 80 else 'unhealthy',
                    'value': memory.percent,
                    'threshold': 80
                },
                'disk': {
                    'status': 'healthy' if (disk.used / disk.total) < 0.85 else 'unhealthy',
                    'value': (disk.used / disk.total) * 100,
                    'threshold': 85
                },
                'database': {
                    'status': 'healthy' if db_healthy else 'unhealthy'
                },
                'external_services': {
                    'status': 'healthy' if external_services_healthy else 'unhealthy'
                }
            }
        }), 200 if healthy else 503
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': 'risk-service',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 503

def check_database_connection():
    """Check database connectivity"""
    try:
        # Add your database connection check logic here
        # Return True if healthy, False otherwise
        return True
    except:
        return False

def check_external_services():
    """Check external service connectivity"""
    try:
        # Add your external service checks here
        # Return True if all services are healthy, False otherwise
        return True
    except:
        return False
```

## Security Monitoring

### CloudTrail Integration

```bash
# Create CloudTrail trail for security monitoring
aws cloudtrail create-trail \
    --name telematics-security-trail \
    --s3-bucket-name telematics-logs-[your-account-id] \
    --is-multi-region-trail

# Start logging
aws cloudtrail start-logging --name telematics-security-trail
```

### Security Alerts

```bash
# Alert on unauthorized API calls
aws cloudtrail put-event-selectors \
    --trail-name telematics-security-trail \
    --event-selectors '[
        {
            "ReadWriteType": "All",
            "IncludeManagementEvents": true,
            "DataResources": []
        }
    ]'

# Create CloudWatch alarm for security events
aws logs put-metric-filter \
    --log-group-name CloudTrail/DefaultLogGroup \
    --filter-name UnauthorizedAPICalls \
    --filter-pattern '{ ($.errorCode = "*UnauthorizedOperation") || ($.errorCode = "AccessDenied*") }' \
    --metric-transformations '[
        {
            "metricName": "UnauthorizedAPICalls",
            "metricNamespace": "CloudTrailMetrics",
            "metricValue": "1"
        }
    ]'
```

## Cost Monitoring and Optimization

### Cost Allocation Tags

```bash
# Tag resources for cost allocation
aws ec2 create-tags \
    --resources [instance-id] \
    --tags Key=Project,Value=Telematics Key=Environment,Value=Production

aws rds add-tags-to-resource \
    --resource-name arn:aws:rds:us-east-1:[account-id]:db:telematics-db \
    --tags Key=Project,Value=Telematics Key=Environment,Value=Production
```

### Budget Setup

```bash
# Create monthly budget
aws budgets create-budget \
    --account-id [account-id] \
    --budget '{
        "BudgetName": "TelematicsMonthlyBudget",
        "BudgetLimit": {
            "Amount": "500",
            "Unit": "USD"
        },
        "CostFilters": {
            "TagKeyValue": ["Project$Telematics"]
        },
        "CostTypes": {
            "IncludeTax": true,
            "IncludeSubscription": true,
            "UseBlended": false,
            "IncludeRefund": false,
            "IncludeCredit": false
        },
        "TimeUnit": "MONTHLY",
        "TimePeriod": {
            "Start": "2024-01-01T00:00:00Z",
            "End": "2025-01-01T00:00:00Z"
        },
        "BudgetType": "COST"
    }' \
    --notifications-with-subscribers '[
        {
            "Notification": {
                "NotificationType": "ACTUAL",
                "ComparisonOperator": "GREATER_THAN",
                "Threshold": 80,
                "ThresholdType": "PERCENTAGE"
            },
            "Subscribers": [
                {
                    "SubscriptionType": "EMAIL",
                    "Address": "admin@yourcompany.com"
                }
            ]
        }
    ]'
```

## Testing and Validation

### Monitoring System Testing

```bash
# Test metrics collection
python monitoring/metrics_collector.py

# Test log analysis
python monitoring/log_analyzer.py

# Test APM decorators
python monitoring/apm.py

# Verify CloudWatch dashboard
aws cloudwatch get-dashboard --dashboard-name Telematics-Dashboard

# Test alerts
aws cloudwatch describe-alarms --alarm-names telematics-high-cpu
```

### Load Testing with Monitoring

```python
# Create load_test.py
import requests
import threading
import time
from concurrent.futures import ThreadPoolExecutor

def send_request(url, duration_seconds=60):
    """Send requests for specified duration"""
    end_time = time.time() + duration_seconds
    request_count = 0
    
    while time.time() < end_time:
        try:
            response = requests.get(url, timeout=5)
            request_count += 1
            if request_count % 10 == 0:
                print(f"Sent {request_count} requests")
        except Exception as e:
            print(f"Request failed: {e}")
        time.sleep(0.1)  # 100ms delay between requests
    
    return request_count

def run_load_test():
    """Run load test and monitor metrics"""
    url = "http://your-service-url/health"  # Update with your service URL
    
    # Run load test with 10 concurrent users
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(send_request, url, 60) for _ in range(10)]
        results = [future.result() for future in futures]
    
    total_requests = sum(results)
    print(f"Load test completed: {total_requests} total requests")

if __name__ == "__main__":
    run_load_test()
```

This completes the monitoring, logging, and observability setup for your telematics system.