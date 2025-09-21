#!/usr/bin/env python3
"""
Check S3 bucket status and configuration
"""

import boto3
import json
import os

# AWS Configuration - Use environment variables or AWS credentials file
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-2')
FRONTEND_BUCKET_NAME = "steelhacks2025-frontend"

def check_bucket_status():
    """Check S3 bucket configuration and status"""
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )

    print(f"Checking bucket: {FRONTEND_BUCKET_NAME}")
    print()

    # Check if bucket exists
    try:
        s3_client.head_bucket(Bucket=FRONTEND_BUCKET_NAME)
        print("[OK] Bucket exists")
    except Exception as e:
        print(f"[ERROR] Bucket check: {e}")
        return

    # Check bucket location
    try:
        response = s3_client.get_bucket_location(Bucket=FRONTEND_BUCKET_NAME)
        location = response.get('LocationConstraint', 'us-east-1')
        print(f"[INFO] Bucket region: {location}")
    except Exception as e:
        print(f"[ERROR] Getting bucket location: {e}")

    # Check website configuration
    try:
        response = s3_client.get_bucket_website(Bucket=FRONTEND_BUCKET_NAME)
        print("[OK] Website hosting is enabled")
        print(f"[INFO] Index document: {response.get('IndexDocument', {}).get('Suffix', 'None')}")
    except Exception as e:
        print(f"[ERROR] Website configuration: {e}")

    # Check public access block
    try:
        response = s3_client.get_public_access_block(Bucket=FRONTEND_BUCKET_NAME)
        pab = response['PublicAccessBlockConfiguration']
        print(f"[INFO] Public access block status:")
        print(f"  - BlockPublicAcls: {pab.get('BlockPublicAcls', False)}")
        print(f"  - IgnorePublicAcls: {pab.get('IgnorePublicAcls', False)}")
        print(f"  - BlockPublicPolicy: {pab.get('BlockPublicPolicy', False)}")
        print(f"  - RestrictPublicBuckets: {pab.get('RestrictPublicBuckets', False)}")
    except Exception as e:
        print("[OK] No public access block (good for website hosting)")

    # Check bucket policy
    try:
        response = s3_client.get_bucket_policy(Bucket=FRONTEND_BUCKET_NAME)
        print("[OK] Bucket policy exists")
    except Exception as e:
        print(f"[ERROR] Bucket policy: {e}")

    # List files in bucket
    try:
        response = s3_client.list_objects_v2(Bucket=FRONTEND_BUCKET_NAME, MaxKeys=10)
        if 'Contents' in response:
            print(f"[OK] Bucket contains {len(response['Contents'])} files")
            print("[INFO] Sample files:")
            for obj in response['Contents'][:5]:
                print(f"  - {obj['Key']}")
        else:
            print("[ERROR] Bucket is empty")
    except Exception as e:
        print(f"[ERROR] Listing files: {e}")

    # Generate correct website URLs
    print()
    print("Website URLs to try:")
    print(f"1. http://{FRONTEND_BUCKET_NAME}.s3-website-{AWS_REGION}.amazonaws.com")
    print(f"2. http://{FRONTEND_BUCKET_NAME}.s3-website.{AWS_REGION}.amazonaws.com")
    print(f"3. Direct S3 URL: https://{FRONTEND_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/landing.html")

def main():
    print("Checking S3 bucket status...")
    print()
    check_bucket_status()

if __name__ == "__main__":
    main()