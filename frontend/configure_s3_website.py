#!/usr/bin/env python3
"""
S3 Bucket Website Configuration Script
Configures S3 bucket for public static website hosting
"""

import boto3
import json

# AWS Configuration
AWS_ACCESS_KEY_ID = "AKIAQX3CDY3P2AK7XMSW"
AWS_SECRET_ACCESS_KEY = "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"
AWS_REGION = "us-east-2"
FRONTEND_BUCKET_NAME = "steelhacks2025-frontend"

def configure_bucket():
    """Configure S3 bucket for static website hosting"""
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )

    print(f"Configuring bucket: {FRONTEND_BUCKET_NAME}")
    print()

    # Step 1: Remove public access block
    try:
        print("1. Removing public access block...")
        s3_client.delete_public_access_block(Bucket=FRONTEND_BUCKET_NAME)
        print("[OK] Public access block removed")
    except Exception as e:
        print(f"[INFO] Public access block: {e}")

    # Step 2: Configure website hosting
    try:
        print("2. Configuring static website hosting...")
        s3_client.put_bucket_website(
            Bucket=FRONTEND_BUCKET_NAME,
            WebsiteConfiguration={
                'IndexDocument': {'Suffix': 'landing.html'},
                'ErrorDocument': {'Key': 'landing.html'}
            }
        )
        print("[OK] Static website hosting configured")
    except Exception as e:
        print(f"[ERROR] Website hosting configuration: {e}")
        return False

    # Step 3: Set bucket policy for public read access
    try:
        print("3. Setting bucket policy for public read access...")
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{FRONTEND_BUCKET_NAME}/*"
                }
            ]
        }

        s3_client.put_bucket_policy(
            Bucket=FRONTEND_BUCKET_NAME,
            Policy=json.dumps(bucket_policy)
        )
        print("[OK] Bucket policy set for public access")
    except Exception as e:
        print(f"[ERROR] Bucket policy: {e}")
        print("[INFO] You may need to manually configure public access in AWS Console")

    # Step 4: Get website URL
    website_url = f"http://{FRONTEND_BUCKET_NAME}.s3-website-{AWS_REGION}.amazonaws.com"

    print()
    print("Configuration complete!")
    print(f"Website URL: {website_url}")
    print()
    print("Your website should now be accessible at the URL above.")
    print("It may take a few minutes for changes to propagate.")

    return True

def main():
    print("Configuring S3 bucket for static website hosting...")
    print()
    configure_bucket()

if __name__ == "__main__":
    main()