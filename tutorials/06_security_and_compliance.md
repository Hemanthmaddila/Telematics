# Security and Compliance for Telematics System

This tutorial covers implementing security best practices and compliance measures for your cloud-based telematics system.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Identity and Access Management](#identity-and-access-management)
3. [Data Encryption](#data-encryption)
4. [Network Security](#network-security)
5. [Compliance Frameworks](#compliance-frameworks)
6. [Security Monitoring](#security-monitoring)
7. [Incident Response](#incident-response)

## Prerequisites

Before starting, ensure you have:
- Completed the previous tutorials
- AWS CLI configured
- Basic understanding of security concepts
- Access to AWS account with appropriate permissions

## Identity and Access Management

### IAM Best Practices

1. **Principle of Least Privilege**: Grant minimum permissions required
2. **Use IAM Roles**: Instead of access keys for services
3. **Enable MFA**: For all users with console access
4. **Regular Review**: Audit permissions regularly

### Create IAM Policies

Create `security/policies/telematics-service-policy.json`:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::telematics-raw-data-*",
                "arn:aws:s3:::telematics-raw-data-*/*",
                "arn:aws:s3:::telematics-processed-data-*",
                "arn:aws:s3:::telematics-processed-data-*/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "rds:DescribeDBInstances",
                "rds:Connect"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage"
            ],
            "Resource": "*"
        }
    ]
}
```

### Implement IAM Roles

```bash
# Create IAM role for ECS tasks
aws iam create-role \
    --role-name TelematicsEcsTaskRole \
    --assume-role-policy-document '{
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
    }'

# Attach custom policy to role
aws iam put-role-policy \
    --role-name TelematicsEcsTaskRole \
    --policy-name TelematicsServicePolicy \
    --policy-document file://security/policies/telematics-service-policy.json

# Attach managed policies
aws iam attach-role-policy \
    --role-name TelematicsEcsTaskRole \
    --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess
```

### User Management

```bash
# Create user groups
aws iam create-group --group-name TelematicsAdmins
aws iam create-group --group-name TelematicsDevelopers
aws iam create-group --group-name TelematicsReadOnly

# Attach policies to groups
aws iam attach-group-policy \
    --group-name TelematicsAdmins \
    --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

aws iam attach-group-policy \
    --group-name TelematicsDevelopers \
    --policy-arn arn:aws:iam::aws:policy/PowerUserAccess

aws iam attach-group-policy \
    --group-name TelematicsReadOnly \
    --policy-arn arn:aws:iam::aws:policy/ReadOnlyAccess

# Create users and add to groups
aws iam create-user --user-name admin-user
aws iam add-user-to-group --user-name admin-user --group-name TelematicsAdmins

aws iam create-user --user-name dev-user
aws iam add-user-to-group --user-name dev-user --group-name TelematicsDevelopers
```

## Data Encryption

### S3 Encryption

```bash
# Enable default encryption for S3 buckets
aws s3api put-bucket-encryption \
    --bucket telematics-raw-data-[account-id] \
    --server-side-encryption-configuration '{
        "Rules": [
            {
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "AES256"
                }
            }
        ]
    }'

aws s3api put-bucket-encryption \
    --bucket telematics-processed-data-[account-id] \
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

### RDS Encryption

```bash
# Note: Encryption must be enabled during database creation
# For existing databases, create encrypted snapshot and restore

# Create encrypted snapshot
aws rds create-db-snapshot \
    --db-instance-identifier telematics-db \
    --db-snapshot-identifier telematics-db-encrypted-snapshot

# Copy snapshot with encryption
aws rds copy-db-snapshot \
    --source-db-snapshot-identifier telematics-db-encrypted-snapshot \
    --target-db-snapshot-identifier telematics-db-encrypted-copy \
    --copy-option-group \
    --kms-key-id [your-kms-key-id] \
    --option-group-name [your-option-group]

# Restore from encrypted snapshot
aws rds restore-db-instance-from-db-snapshot \
    --db-instance-identifier telematics-db-encrypted \
    --db-snapshot-identifier telematics-db-encrypted-copy
```

### Application-Level Encryption

Create `security/encryption.py`:

```python
#!/usr/bin/env python3
"""
Application-level encryption for sensitive data
"""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class DataEncryption:
    def __init__(self):
        # In production, use AWS KMS or similar service
        self.key = self._derive_key(os.environ.get('ENCRYPTION_PASSWORD', 'default-password'))
        self.cipher = Fernet(self.key)
    
    def _derive_key(self, password: str) -> bytes:
        """Derive encryption key from password"""
        salt = b'telematics_salt_12345'  # In production, use random salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        encrypted_data = self.cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted_data = self.cipher.decrypt(decoded_data)
        return decrypted_data.decode()

# Usage example
if __name__ == "__main__":
    encryptor = DataEncryption()
    
    # Encrypt sensitive data
    sensitive_data = "driver_license_number_12345"
    encrypted = encryptor.encrypt_data(sensitive_data)
    print(f"Encrypted: {encrypted}")
    
    # Decrypt data
    decrypted = encryptor.decrypt_data(encrypted)
    print(f"Decrypted: {decrypted}")
```

### Secrets Management

Create `security/secrets_manager.py`:

```python
#!/usr/bin/env python3
"""
Secrets management using AWS Secrets Manager
"""

import boto3
import json
import os

class SecretsManager:
    def __init__(self):
        self.client = boto3.client('secretsmanager')
        self.environment = os.environ.get('ENVIRONMENT', 'dev')
    
    def get_secret(self, secret_name: str) -> dict:
        """Retrieve secret from AWS Secrets Manager"""
        try:
            # Add environment prefix to secret name
            full_secret_name = f"telematics/{self.environment}/{secret_name}"
            
            response = self.client.get_secret_value(SecretId=full_secret_name)
            secret_string = response['SecretString']
            
            return json.loads(secret_string)
        except Exception as e:
            print(f"Error retrieving secret {secret_name}: {e}")
            return {}
    
    def create_secret(self, secret_name: str, secret_value: dict) -> bool:
        """Create a new secret in AWS Secrets Manager"""
        try:
            full_secret_name = f"telematics/{self.environment}/{secret_name}"
            
            self.client.create_secret(
                Name=full_secret_name,
                Description=f"Telematics system secret for {secret_name}",
                SecretString=json.dumps(secret_value)
            )
            
            return True
        except Exception as e:
            print(f"Error creating secret {secret_name}: {e}")
            return False
    
    def update_secret(self, secret_name: str, secret_value: dict) -> bool:
        """Update an existing secret in AWS Secrets Manager"""
        try:
            full_secret_name = f"telematics/{self.environment}/{secret_name}"
            
            self.client.put_secret_value(
                SecretId=full_secret_name,
                SecretString=json.dumps(secret_value)
            )
            
            return True
        except Exception as e:
            print(f"Error updating secret {secret_name}: {e}")
            return False

# Usage example
if __name__ == "__main__":
    secrets_manager = SecretsManager()
    
    # Retrieve database credentials
    db_credentials = secrets_manager.get_secret('database-credentials')
    print(f"Database host: {db_credentials.get('host', 'Not found')}")
    
    # Create a new secret
    new_secret = {
        'api_key': 'your-api-key-here',
        'client_secret': 'your-client-secret-here'
    }
    
    # Only create in development environment
    if os.environ.get('ENVIRONMENT') == 'dev':
        secrets_manager.create_secret('api-credentials', new_secret)
```

## Network Security

### Security Groups Review

```bash
# Review security groups
aws ec2 describe-security-groups \
    --filters "Name=tag:Project,Values=telematics"

# Tighten security group rules
aws ec2 authorize-security-group-ingress \
    --group-id [security-group-id] \
    --protocol tcp \
    --port 22 \
    --cidr [your-ip-address]/32
```

### VPC Flow Logs

```bash
# Create CloudWatch log group for flow logs
aws logs create-log-group --log-group-name telematics-vpc-flow-logs

# Create flow logs
aws ec2 create-flow-logs \
    --resource-ids [vpc-id] \
    --resource-type VPC \
    --traffic-type ALL \
    --log-destination-type cloud-watch-logs \
    --log-group-name telematics-vpc-flow-logs
```

### Network ACLs

```bash
# Create network ACL
aws ec2 create-network-acl --vpc-id [vpc-id]

# Add rules to network ACL
aws ec2 create-network-acl-entry \
    --network-acl-id [nacl-id] \
    --rule-number 100 \
    --protocol tcp \
    --rule-action allow \
    --egress false \
    --cidr-block 0.0.0.0/0 \
    --port-range From=80,To=80
```

## Compliance Frameworks

### GDPR Compliance

Create `security/gdpr_compliance.py`:

```python
#!/usr/bin/env python3
"""
GDPR compliance features for telematics system
"""

import json
from datetime import datetime, timedelta
import os

class GDPRCompliance:
    def __init__(self):
        self.data_retention_days = int(os.environ.get('DATA_RETENTION_DAYS', '730'))  # 2 years default
        self.consent_required = os.environ.get('GDPR_CONSENT_REQUIRED', 'true').lower() == 'true'
    
    def check_consent(self, driver_id: str) -> bool:
        """Check if driver has given consent for data processing"""
        if not self.consent_required:
            return True
        
        # In a real implementation, check consent database
        # This is a simplified example
        consent_file = f"data/consent/{driver_id}.json"
        
        try:
            with open(consent_file, 'r') as f:
                consent_data = json.load(f)
                return consent_data.get('consent_given', False)
        except FileNotFoundError:
            return False
    
    def anonymize_data(self, driver_data: dict) -> dict:
        """Anonymize personal data for compliance"""
        anonymized_data = driver_data.copy()
        
        # Remove or obfuscate personal identifiers
        if 'driver_id' in anonymized_data:
            # Keep for internal tracking but obfuscate if needed
            pass
        
        if 'personal_info' in anonymized_data:
            # Remove personal information
            del anonymized_data['personal_info']
        
        # Add anonymization timestamp
        anonymized_data['anonymized_at'] = datetime.utcnow().isoformat()
        
        return anonymized_data
    
    def handle_data_deletion_request(self, driver_id: str) -> bool:
        """Handle GDPR right to be forgotten requests"""
        try:
            # Delete from database
            # This is a simplified example
            data_files = [
                f"data/drivers/{driver_id}.json",
                f"data/trips/{driver_id}_*",
                f"data/features/{driver_id}_*"
            ]
            
            # Delete files (in real implementation, use proper database deletion)
            for file_pattern in data_files:
                # Implementation would delete matching files
                pass
            
            # Log deletion request
            log_entry = {
                'driver_id': driver_id,
                'action': 'data_deletion',
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'completed'
            }
            
            with open(f"data/deletion_log/{driver_id}.json", 'w') as f:
                json.dump(log_entry, f)
            
            return True
        except Exception as e:
            print(f"Error handling data deletion request: {e}")
            return False
    
    def apply_data_retention_policy(self) -> int:
        """Apply data retention policy to remove old data"""
        deleted_count = 0
        cutoff_date = datetime.utcnow() - timedelta(days=self.data_retention_days)
        
        # In real implementation, query database for old records
        # This is a simplified file-based example
        import glob
        
        # Delete old trip data
        old_trip_files = glob.glob("data/trips/*")
        for file_path in old_trip_files:
            try:
                # Check file modification time
                import os
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_time < cutoff_date:
                    os.remove(file_path)
                    deleted_count += 1
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")
        
        return deleted_count

# Usage example
if __name__ == "__main__":
    gdpr = GDPRCompliance()
    
    # Check consent for a driver
    has_consent = gdpr.check_consent("driver_001")
    print(f"Driver has consent: {has_consent}")
    
    # Anonymize data
    driver_data = {
        'driver_id': 'driver_001',
        'personal_info': {'name': 'John Doe', 'email': 'john@example.com'},
        'trip_data': [{'trip_id': 'trip_001', 'distance': 10.5}]
    }
    
    anonymized = gdpr.anonymize_data(driver_data)
    print(f"Anonymized data: {anonymized}")
```

### SOC2 Compliance

Create `security/soc2_compliance.py`:

```python
#!/usr/bin/env python3
"""
SOC2 compliance monitoring and reporting
"""

import json
import logging
from datetime import datetime
import boto3

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SOC2Compliance:
    def __init__(self):
        self.cloudtrail = boto3.client('cloudtrail')
        self.cloudwatch = boto3.client('cloudwatch')
        self.logs = boto3.client('logs')
    
    def monitor_security_events(self) -> dict:
        """Monitor security-related events for SOC2 compliance"""
        security_events = {
            'unauthorized_access_attempts': 0,
            'failed_authentications': 0,
            'data_access_violations': 0,
            'configuration_changes': 0,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            # Check CloudTrail for security events
            response = self.cloudtrail.lookup_events(
                LookupAttributes=[
                    {
                        'AttributeKey': 'EventName',
                        'AttributeValue': 'ConsoleLogin'
                    }
                ],
                MaxResults=50
            )
            
            for event in response.get('Events', []):
                # Check for failed login attempts
                if 'errorMessage' in event:
                    security_events['failed_authentications'] += 1
            
            # Check for unauthorized API calls
            response = self.cloudtrail.lookup_events(
                LookupAttributes=[
                    {
                        'AttributeKey': 'ErrorCode',
                        'AttributeValue': 'AccessDenied'
                    }
                ],
                MaxResults=50
            )
            
            security_events['unauthorized_access_attempts'] = len(response.get('Events', []))
            
        except Exception as e:
            logger.error(f"Error monitoring security events: {e}")
        
        return security_events
    
    def generate_compliance_report(self) -> dict:
        """Generate SOC2 compliance report"""
        report = {
            'report_date': datetime.utcnow().isoformat(),
            'compliance_status': 'COMPLIANT',
            'security_events': self.monitor_security_events(),
            'data_protection': self.check_data_protection(),
            'access_controls': self.check_access_controls(),
            'audit_logging': self.check_audit_logging()
        }
        
        # Determine overall compliance status
        if (report['security_events']['unauthorized_access_attempts'] > 10 or
            report['security_events']['failed_authentications'] > 50):
            report['compliance_status'] = 'NON_COMPLIANT'
        
        return report
    
    def check_data_protection(self) -> dict:
        """Check data protection measures"""
        data_protection = {
            'encryption_at_rest': True,
            'encryption_in_transit': True,
            'backup_enabled': True,
            'backup_encrypted': True
        }
        
        # In real implementation, check actual AWS service configurations
        # This is a simplified example
        return data_protection
    
    def check_access_controls(self) -> dict:
        """Check access control measures"""
        access_controls = {
            'mfa_enabled': True,
            'least_privilege': True,
            'role_based_access': True,
            'regular_audits': True
        }
        
        # In real implementation, check IAM configurations
        # This is a simplified example
        return access_controls
    
    def check_audit_logging(self) -> dict:
        """Check audit logging configuration"""
        audit_logging = {
            'cloudtrail_enabled': True,
            'log_retention_days': 365,
            'log_encryption': True,
            'alerting_configured': True
        }
        
        # In real implementation, check actual logging configurations
        # This is a simplified example
        return audit_logging
    
    def save_compliance_report(self, report: dict) -> bool:
        """Save compliance report to S3"""
        try:
            import boto3
            s3 = boto3.client('s3')
            
            report_json = json.dumps(report, indent=2)
            report_key = f"compliance/soc2_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            
            s3.put_object(
                Bucket='telematics-compliance-reports',
                Key=report_key,
                Body=report_json,
                ServerSideEncryption='AES256'
            )
            
            logger.info(f"Compliance report saved: {report_key}")
            return True
        except Exception as e:
            logger.error(f"Error saving compliance report: {e}")
            return False

# Usage example
if __name__ == "__main__":
    soc2 = SOC2Compliance()
    
    # Generate compliance report
    report = soc2.generate_compliance_report()
    print(f"Compliance Status: {report['compliance_status']}")
    
    # Save report
    soc2.save_compliance_report(report)
```

## Security Monitoring

### CloudTrail Configuration

```bash
# Create CloudTrail trail
aws cloudtrail create-trail \
    --name telematics-security-trail \
    --s3-bucket-name telematics-logs-[account-id] \
    --is-multi-region-trail \
    --enable-log-file-validation

# Start logging
aws cloudtrail start-logging --name telematics-security-trail

# Create event selectors for detailed logging
aws cloudtrail put-event-selectors \
    --trail-name telematics-security-trail \
    --event-selectors '[
        {
            "ReadWriteType": "All",
            "IncludeManagementEvents": true,
            "DataResources": [
                {
                    "Type": "AWS::S3::Object",
                    "Values": ["arn:aws:s3:::telematics-raw-data-*/"]
                },
                {
                    "Type": "AWS::S3::Object",
                    "Values": ["arn:aws:s3:::telematics-processed-data-*/"]
                }
            ]
        }
    ]'
```

### Security Hub Integration

```bash
# Enable Security Hub
aws securityhub enable-security-hub

# Enable standards
aws securityhub batch-enable-standards \
    --standards-subscription-requests '[
        {
            "StandardsArn": "arn:aws:securityhub:::ruleset/cis-aws-foundations-benchmark/v/1.2.0"
        }
    ]'
```

### GuardDuty Setup

```bash
# Enable GuardDuty
aws guardduty create-detector --enable

# List detectors
aws guardduty list-detectors
```

## Incident Response

### Create Incident Response Plan

Create `security/incident_response_plan.md`:

```markdown
# Telematics System Incident Response Plan

## 1. Incident Classification

### Severity Levels
- **Critical**: Data breach, system compromise, service outage > 4 hours
- **High**: Unauthorized access, significant data loss, service outage 1-4 hours
- **Medium**: Suspicious activity, minor data exposure, service degradation
- **Low**: Failed login attempts, minor configuration issues

## 2. Response Team

### Primary Contacts
- Security Lead: [security-lead-email]
- System Administrator: [admin-email]
- Compliance Officer: [compliance-email]

### Escalation Path
1. Security Lead
2. System Administrator
3. Compliance Officer
4. Executive Management

## 3. Incident Response Procedures

### Step 1: Detection and Analysis
- Monitor security alerts and logs
- Analyze suspicious activity
- Determine incident severity

### Step 2: Containment
- Isolate affected systems
- Block malicious IP addresses
- Disable compromised accounts

### Step 3: Eradication
- Remove malware or unauthorized access
- Patch vulnerabilities
- Reset compromised credentials

### Step 4: Recovery
- Restore systems from clean backups
- Validate system integrity
- Monitor for recurrence

### Step 5: Post-Incident Activities
- Document incident details
- Conduct root cause analysis
- Update security measures
- Report to stakeholders

## 4. Communication Plan

### Internal Communication
- Security team via Slack channel #security-alerts
- Status updates every 2 hours during active incidents

### External Communication
- Customers: Only if personally identifiable data is compromised
- Regulators: As required by law (e.g., GDPR data breach notifications)
- Media: Only through designated spokesperson

## 5. Tools and Resources

### Monitoring Tools
- AWS CloudTrail for audit logs
- AWS CloudWatch for metrics
- AWS GuardDuty for threat detection

### Response Tools
- AWS Systems Manager for remote access
- AWS Backup for data recovery
- AWS Security Hub for consolidated security findings

## 6. Testing and Training

### Quarterly Drills
- Simulated security incidents
- Response time measurements
- Procedure improvements

### Annual Training
- Security awareness training for all staff
- Incident response procedure refresh
- New threat landscape updates
```

### Automated Incident Response

Create `security/incident_response.py`:

```python
#!/usr/bin/env python3
"""
Automated incident response system
"""

import boto3
import json
import logging
from datetime import datetime
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IncidentResponse:
    def __init__(self):
        self.securityhub = boto3.client('securityhub')
        self.cloudtrail = boto3.client('cloudtrail')
        self.sns = boto3.client('sns')
        self.s3 = boto3.client('s3')
        
        # Configuration
        self.alert_topic_arn = 'arn:aws:sns:us-east-1:[account-id]:telematics-security-alerts'
        self.incident_bucket = 'telematics-incident-reports'
    
    def handle_security_alert(self, alert_data: dict):
        """Handle security alert and initiate response"""
        try:
            # Classify incident severity
            severity = self.classify_incident(alert_data)
            
            # Log incident
            incident_id = self.log_incident(alert_data, severity)
            
            # Take automated actions based on severity
            self.automated_response(alert_data, severity, incident_id)
            
            # Notify response team
            self.notify_team(alert_data, severity, incident_id)
            
            # Update stakeholders if necessary
            if severity in ['CRITICAL', 'HIGH']:
                self.notify_stakeholders(alert_data, severity, incident_id)
            
            logger.info(f"Incident {incident_id} handled with severity {severity}")
            
        except Exception as e:
            logger.error(f"Error handling security alert: {e}")
    
    def classify_incident(self, alert_data: dict) -> str:
        """Classify incident severity"""
        # Extract key information
        alert_type = alert_data.get('alert_type', 'UNKNOWN')
        resource_arn = alert_data.get('resource_arn', '')
        threat_level = alert_data.get('threat_level', 0)
        
        # Classification rules
        if alert_type == 'UNAUTHORIZED_ACCESS' or threat_level >= 9:
            return 'CRITICAL'
        elif alert_type in ['DATA_EXFILTRATION', 'SYSTEM_COMPROMISE'] or threat_level >= 7:
            return 'HIGH'
        elif alert_type in ['SUSPICIOUS_ACTIVITY', 'FAILED_LOGIN'] or threat_level >= 5:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def log_incident(self, alert_data: dict, severity: str) -> str:
        """Log incident details"""
        incident_id = f"INC-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        
        incident_record = {
            'incident_id': incident_id,
            'timestamp': datetime.utcnow().isoformat(),
            'severity': severity,
            'alert_data': alert_data,
            'status': 'OPEN',
            'response_actions': []
        }
        
        # Save to S3
        try:
            self.s3.put_object(
                Bucket=self.incident_bucket,
                Key=f"incidents/{incident_id}.json",
                Body=json.dumps(incident_record, indent=2)
            )
        except Exception as e:
            logger.error(f"Error saving incident log: {e}")
        
        return incident_id
    
    def automated_response(self, alert_data: dict, severity: str, incident_id: str):
        """Take automated response actions"""
        actions_taken = []
        
        if severity == 'CRITICAL':
            # Block IP addresses
            if 'source_ip' in alert_data:
                self.block_ip(alert_data['source_ip'])
                actions_taken.append(f"Blocked IP: {alert_data['source_ip']}")
            
            # Disable compromised accounts
            if 'user_name' in alert_data:
                self.disable_account(alert_data['user_name'])
                actions_taken.append(f"Disabled account: {alert_data['user_name']}")
        
        elif severity == 'HIGH':
            # Isolate affected resources
            if 'resource_arn' in alert_data:
                self.isolate_resource(alert_data['resource_arn'])
                actions_taken.append(f"Isolated resource: {alert_data['resource_arn']}")
        
        elif severity == 'MEDIUM':
            # Increase monitoring
            self.increase_monitoring(alert_data)
            actions_taken.append("Increased monitoring on affected resources")
        
        # Update incident record with actions taken
        self.update_incident_record(incident_id, actions_taken)
    
    def block_ip(self, ip_address: str):
        """Block malicious IP address"""
        try:
            # In real implementation, update security groups or NACLs
            # This is a simplified example
            logger.info(f"Blocking IP address: {ip_address}")
        except Exception as e:
            logger.error(f"Error blocking IP {ip_address}: {e}")
    
    def disable_account(self, user_name: str):
        """Disable compromised user account"""
        try:
            iam = boto3.client('iam')
            iam.delete_access_key(UserName=user_name)
            logger.info(f"Disabled access for user: {user_name}")
        except Exception as e:
            logger.error(f"Error disabling user {user_name}: {e}")
    
    def isolate_resource(self, resource_arn: str):
        """Isolate compromised resource"""
        try:
            # In real implementation, update security groups or network ACLs
            # This is a simplified example
            logger.info(f"Isolating resource: {resource_arn}")
        except Exception as e:
            logger.error(f"Error isolating resource {resource_arn}: {e}")
    
    def increase_monitoring(self, alert_data: dict):
        """Increase monitoring on affected resources"""
        try:
            # In real implementation, adjust CloudWatch metrics and alarms
            # This is a simplified example
            logger.info("Increasing monitoring frequency for affected resources")
        except Exception as e:
            logger.error(f"Error increasing monitoring: {e}")
    
    def update_incident_record(self, incident_id: str, actions: list):
        """Update incident record with actions taken"""
        try:
            # Read existing record
            response = self.s3.get_object(
                Bucket=self.incident_bucket,
                Key=f"incidents/{incident_id}.json"
            )
            incident_record = json.loads(response['Body'].read())
            
            # Update actions
            incident_record['response_actions'].extend(actions)
            
            # Save updated record
            self.s3.put_object(
                Bucket=self.incident_bucket,
                Key=f"incidents/{incident_id}.json",
                Body=json.dumps(incident_record, indent=2)
            )
        except Exception as e:
            logger.error(f"Error updating incident record: {e}")
    
    def notify_team(self, alert_data: dict, severity: str, incident_id: str):
        """Notify response team"""
        message = f"""
        Security Alert - Incident {incident_id}
        
        Severity: {severity}
        Time: {datetime.utcnow().isoformat()}
        
        Alert Details:
        {json.dumps(alert_data, indent=2)}
        
        Please review and take appropriate action.
        """
        
        try:
            self.sns.publish(
                TopicArn=self.alert_topic_arn,
                Subject=f"Security Alert - {severity} Severity",
                Message=message
            )
        except Exception as e:
            logger.error(f"Error notifying team: {e}")
    
    def notify_stakeholders(self, alert_data: dict, severity: str, incident_id: str):
        """Notify stakeholders for critical incidents"""
        # In real implementation, send emails to stakeholders
        # This is a simplified example
        logger.info(f"Stakeholder notification sent for incident {incident_id}")

# Usage example
if __name__ == "__main__":
    incident_response = IncidentResponse()
    
    # Example alert data
    alert = {
        'alert_type': 'UNAUTHORIZED_ACCESS',
        'source_ip': '192.168.1.100',
        'user_name': 'compromised_user',
        'resource_arn': 'arn:aws:s3:::telematics-sensitive-data',
        'threat_level': 9,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Handle the alert
    incident_response.handle_security_alert(alert)
```

## Testing and Validation

### Security Testing

```bash
# Test IAM policies
aws iam simulate-principal-policy \
    --policy-source-arn arn:aws:iam::[account-id]:role/TelematicsEcsTaskRole \
    --action-names s3:GetObject s3:PutObject \
    --resource-arns arn:aws:s3:::telematics-raw-data-*

# Test encryption
python security/encryption.py

# Test secrets management
python security/secrets_manager.py

# Test GDPR compliance functions
python security/gdpr_compliance.py

# Test SOC2 compliance monitoring
python security/soc2_compliance.py

# Test incident response
python security/incident_response.py
```

### Compliance Validation

```bash
# Check IAM policy attachments
aws iam list-attached-role-policies --role-name TelematicsEcsTaskRole

# Verify S3 encryption
aws s3api get-bucket-encryption --bucket telematics-raw-data-[account-id]

# Check CloudTrail configuration
aws cloudtrail describe-trails

# Verify Security Hub standards
aws securityhub get-enabled-standards
```

This completes the security and compliance setup for your telematics system.