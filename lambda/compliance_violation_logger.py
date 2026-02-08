import json
import os
from datetime import datetime
import boto3

SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']

def lambda_handler(event, context):
    """
    Log compliance violations and send notifications
    """
    # Extract violation details from the event
    violation_type = event.get('detail', {}).get('configRuleName', 'unknown')
    resource_id = event.get('detail', {}).get('resourceId', 'unknown')
    account_id = event.get('detail', {}).get('awsAccountId', 'unknown')
    
    # Create detailed log entry
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'violation_type': violation_type,
        'resource_id': resource_id,
        'account_id': account_id,
        'severity': determine_severity(violation_type),
        'function_name': context.function_name,
        'request_id': context.aws_request_id
    }
    
    # Log the violation (appears in CloudWatch Logs)
    print(f"COMPLIANCE VIOLATION: {json.dumps(log_entry)}")
    
    # Send notification for high-severity violations
    if log_entry['severity'] == 'HIGH':
        send_notification(log_entry)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Compliance violation processed successfully')
    }

def determine_severity(violation_type):
    """Determine violation severity based on rule type"""
    high_severity_rules = [
        's3-bucket-public-access-prohibited',
        'iam-root-access-key-check',
        'encrypted-volumes',
        's3-bucket-server-side-encryption-enabled',
        'ec2-security-group-attached-to-eni-periodic',
        'iam-password-policy',
    ]

    if violation_type in high_severity_rules:
        return 'HIGH'
    return 'MEDIUM'

def send_notification(log_entry):
    """Send SNS notification for high-severity violations"""
    sns = boto3.client('sns')
    
    message = f"""
    URGENT: High-severity compliance violation detected
    
    Rule: {log_entry['violation_type']}
    Resource: {log_entry['resource_id']}
    Account: {log_entry['account_id']}
    Time: {log_entry['timestamp']}
    """
    
    # Note: You will need to replace this ARN with the ARN of your SNS topic.
    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Message=message,
        Subject="AWS Compliance Alert - Immediate Action Required"
    )
