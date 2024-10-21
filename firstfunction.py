import json
import boto3
from datetime import datetime, timedelta, timezone

import json
import os
import boto3
from datetime import datetime, timedelta, timezone

def lambda_handler(event, context):
    Ami = []
    Snapshot = []
    n_days_threshold = int(os.environ['days'])

    utc_timezone = timezone.utc

    ec2 = boto3.client('ec2')
    rds = boto3.client('rds')

    current_time = datetime.now(utc_timezone)

    # Include EC2 AMIs
    amis = ec2.describe_images(Owners=['self'])['Images']

    for ami in amis:
        creation_time = ami['CreationDate']
        creation_datetime = datetime.strptime(creation_time, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=utc_timezone)
        age = current_time - creation_datetime

        if age.days > n_days_threshold:
            print(f"EC2 AMI {ami['ImageId']} created more than {n_days_threshold} days ago.")
            Ami.append({'ImageId': ami['ImageId']})

    # Include EC2 snapshots
    snapshots = ec2.describe_snapshots(OwnerIds=['self'])['Snapshots']

    for snapshot in snapshots:
        start_time = snapshot['StartTime'].astimezone(utc_timezone)
        age = current_time - start_time

        if age.days > n_days_threshold:
            print(f"EC2 Snapshot ID: {snapshot['SnapshotId']} is older than {n_days_threshold} days.")
            print(f"Snapshot Start Time: {start_time}")
            Snapshot.append({'snapshot': snapshot['SnapshotId']})

    # Include RDS snapshots
    rds_snapshots = rds.describe_db_snapshots()['DBSnapshots']

    for rds_snapshot in rds_snapshots:
        snapshot_time = rds_snapshot['SnapshotCreateTime']
        snapshot_datetime = snapshot_time.replace(tzinfo=utc_timezone)
        age = current_time - snapshot_datetime

        if age.days > n_days_threshold:
            print(f"RDS Snapshot ID: {rds_snapshot['DBSnapshotIdentifier']} is older than {n_days_threshold} days.")
            print(f"RDS Snapshot Create Time: {snapshot_datetime}")
            Snapshot.append({'snapshot': rds_snapshot['DBSnapshotIdentifier']})

    # Correct the message generation part
    message = f"EC2 AMI {'/'.join(item['ImageId'] for item in Ami)} created more than {n_days_threshold} days ago.\n"
    message += f"EC2 Snapshot ID: {'/'.join(item['snapshot'] for item in Snapshot)} is older than {n_days_threshold} days."

    print(message)

    # You can further modify the function based on your use case, e.g., sending notifications, deleting snapshots, etc.

    return {
        'statusCode': 200,
        'body': json.dumps('Function executed successfully!')
    }
