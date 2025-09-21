#!/usr/bin/env python3
"""
S3 Frontend Deployment Script
Deploys static frontend files to S3 for website hosting
"""

import boto3
import os
import mimetypes
from pathlib import Path

# AWS Configuration - Use environment variables or AWS credentials file
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-2')
FRONTEND_BUCKET_NAME = "steelhacks2025-frontend"  # Separate bucket for frontend

def create_s3_client():
    """Create and return S3 client"""
    return boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )

def create_bucket_if_not_exists(s3_client, bucket_name):
    """Create S3 bucket if it doesn't exist"""
    try:
        # Check if bucket exists
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"[OK] Bucket '{bucket_name}' already exists")
    except:
        try:
            # Create bucket
            if AWS_REGION == 'us-east-1':
                s3_client.create_bucket(Bucket=bucket_name)
            else:
                s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': AWS_REGION}
                )
            print(f"[OK] Created bucket '{bucket_name}'")
        except Exception as e:
            print(f"[ERROR] Error creating bucket: {e}")
            return False
    return True

def configure_website_hosting(s3_client, bucket_name):
    """Configure S3 bucket for static website hosting"""
    try:
        # Configure website hosting
        s3_client.put_bucket_website(
            Bucket=bucket_name,
            WebsiteConfiguration={
                'IndexDocument': {'Suffix': 'landing.html'},
                'ErrorDocument': {'Key': 'landing.html'}
            }
        )
        print("[OK] Configured static website hosting")

        # Set bucket policy for public read access
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{bucket_name}/*"
                }
            ]
        }

        s3_client.put_bucket_policy(
            Bucket=bucket_name,
            Policy=str(bucket_policy).replace("'", '"')
        )
        print("[OK] Set bucket policy for public access")
        return True

    except Exception as e:
        print(f"[ERROR] Error configuring website hosting: {e}")
        return False

def upload_files(s3_client, bucket_name, local_directory):
    """Upload all files from local directory to S3"""
    uploaded_files = 0
    local_path = Path(local_directory)

    # Files to exclude from upload
    exclude_extensions = {'.py', '.ps1', '.md', '.git'}
    exclude_files = {'deploy_frontend.py', 'deploy-s3.ps1', 'S3_DEPLOYMENT_GUIDE.md'}

    for file_path in local_path.rglob('*'):
        if file_path.is_file():
            # Skip excluded files
            if (file_path.suffix.lower() in exclude_extensions or
                file_path.name in exclude_files):
                continue

            # Calculate relative path for S3 key
            relative_path = file_path.relative_to(local_path)
            s3_key = str(relative_path).replace('\\', '/')

            # Determine content type
            content_type, _ = mimetypes.guess_type(str(file_path))
            if not content_type:
                content_type = 'binary/octet-stream'

            try:
                # Upload file
                s3_client.upload_file(
                    str(file_path),
                    bucket_name,
                    s3_key,
                    ExtraArgs={'ContentType': content_type}
                )
                print(f"[OK] Uploaded: {s3_key}")
                uploaded_files += 1

            except Exception as e:
                print(f"[ERROR] Error uploading {file_path}: {e}")

    return uploaded_files

def main():
    """Main deployment function"""
    print("Starting frontend deployment to S3...")
    print(f"Region: {AWS_REGION}")
    print(f"Bucket: {FRONTEND_BUCKET_NAME}")
    print()

    # Create S3 client
    s3_client = create_s3_client()

    # Create bucket
    if not create_bucket_if_not_exists(s3_client, FRONTEND_BUCKET_NAME):
        return

    # Configure website hosting
    if not configure_website_hosting(s3_client, FRONTEND_BUCKET_NAME):
        return

    # Upload files
    current_dir = os.path.dirname(os.path.abspath(__file__))
    uploaded_count = upload_files(s3_client, FRONTEND_BUCKET_NAME, current_dir)

    # Generate website URL
    website_url = f"http://{FRONTEND_BUCKET_NAME}.s3-website-{AWS_REGION}.amazonaws.com"

    print()
    print("Deployment complete!")
    print(f"Uploaded {uploaded_count} files")
    print(f"Website URL: {website_url}")
    print()
    print("Next steps:")
    print("1. Test your website at the URL above")
    print("2. Deploy your backend to AWS")
    print("3. Update frontend to use production backend URL")

if __name__ == "__main__":
    main()