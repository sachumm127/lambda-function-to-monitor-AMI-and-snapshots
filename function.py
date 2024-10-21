import json
import os
import boto3
from datetime import datetime, timezone

def lambda_handler(event, context):
    Ami = []
    Snapshot = []
    n_days_threshold = int(os.getenv('days', 30))  # Default to 30 days if not provided

    utc_timezone = timezone.utc
    ec2 = boto3.client('ec2')
    rds = boto3.client('rds')

    current_time = datetime.now(utc_timezone)

    # Include EC2 AMIs
    try:
        amis = ec2.describe_images(Owners=['self'])['Images']
        for ami in amis:
            creation_time = ami['CreationDate']
            creation_datetime = datetime.strptime(creation_time, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=utc_timezone)
            age = current_time - creation_datetime

            if age.days > n_days_threshold:
                print(f"EC2 AMI {ami['ImageId']} created more than {n_days_threshold} days ago.")
                Ami.append({'ImageId': ami['ImageId']})
    except Exception as e:
        print(f"Error fetching EC2 AMIs: {e}")

    # Include EC2 snapshots
    try:
        snapshots = ec2.describe_snapshots(OwnerIds=['self'])['Snapshots']
        for snapshot in snapshots:
            start_time = snapshot['StartTime'].astimezone(utc_timezone)
            age = current_time - start_time

            if age.days > n_days_threshold:
                print(f"EC2 Snapshot ID: {snapshot['SnapshotId']} is older than {n_days_threshold} days.")
                Snapshot.append({'snapshot': snapshot['SnapshotId']})
    except Exception as e:
        print(f"Error fetching EC2 Snapshots: {e}")

    # Include RDS snapshots
    try:
        rds_snapshots = rds.describe_db_snapshots()['DBSnapshots']
        for rds_snapshot in rds_snapshots:
            snapshot_time = rds_snapshot['SnapshotCreateTime']
            snapshot_datetime = snapshot_time if snapshot_time.tzinfo else snapshot_time.replace(tzinfo=utc_timezone)
            age = current_time - snapshot_datetime

            if age.days > n_days_threshold:
                print(f"RDS Snapshot ID: {rds_snapshot['DBSnapshotIdentifier']} is older than {n_days_threshold} days.")
                Snapshot.append({'snapshot': rds_snapshot['DBSnapshotIdentifier']})
    except Exception as e:
        print(f"Error fetching RDS Snapshots: {e}")

    # Message creation
    ami_message = f"EC2 AMI {'/'.join(item['ImageId'] for item in Ami)} created more than {n_days_threshold} days ago.\n" if Ami else "No EC2 AMIs are older than the threshold.\n"
    snapshot_message = f"EC2/RDS Snapshot ID(s): {'/'.join(item['snapshot'] for item in Snapshot)} older than {n_days_threshold} days." if Snapshot else "No EC2 or RDS snapshots are older than the threshold."
    message = ami_message + snapshot_message
    print(message)

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Function executed successfully!',
            'old_amis': Ami,
            'old_snapshots': Snapshot
        })
    }
