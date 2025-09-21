#!/usr/bin/env python3
"""
Simple S3 Frontend Deployment Script
"""

import boto3
import os
from pathlib import Path

# AWS Configuration - Use environment variables or AWS credentials file
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-2')
FRONTEND_BUCKET_NAME = "steelhacks2025-frontend"

def upload_files():
    """Upload frontend files to existing S3 bucket"""
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )

    current_dir = Path(__file__).parent
    uploaded_files = 0

    # Files to include (specific file types for frontend)
    include_files = ['*.html', '*.css', '*.js', '*.jpg', '*.png', '*.gif', '*.svg']

    for pattern in include_files:
        for file_path in current_dir.glob(pattern):
            if file_path.is_file():
                s3_key = file_path.name

                try:
                    # Determine content type
                    if file_path.suffix == '.html':
                        content_type = 'text/html'
                    elif file_path.suffix == '.css':
                        content_type = 'text/css'
                    elif file_path.suffix == '.js':
                        content_type = 'application/javascript'
                    elif file_path.suffix in ['.jpg', '.jpeg']:
                        content_type = 'image/jpeg'
                    elif file_path.suffix == '.png':
                        content_type = 'image/png'
                    elif file_path.suffix == '.gif':
                        content_type = 'image/gif'
                    elif file_path.suffix == '.svg':
                        content_type = 'image/svg+xml'
                    else:
                        content_type = 'binary/octet-stream'

                    # Upload file
                    s3_client.upload_file(
                        str(file_path),
                        FRONTEND_BUCKET_NAME,
                        s3_key,
                        ExtraArgs={'ContentType': content_type}
                    )
                    print(f"[OK] Uploaded: {s3_key}")
                    uploaded_files += 1

                except Exception as e:
                    print(f"[ERROR] Error uploading {file_path.name}: {e}")

    return uploaded_files

def main():
    print("Starting simple frontend upload to S3...")
    print(f"Bucket: {FRONTEND_BUCKET_NAME}")
    print()

    uploaded_count = upload_files()

    print()
    print("Upload complete!")
    print(f"Uploaded {uploaded_count} files")
    print()
    print("To make your website public, you need to:")
    print("1. Go to AWS S3 Console")
    print("2. Select your bucket: steelhacks2025-frontend")
    print("3. Go to 'Permissions' tab")
    print("4. Edit 'Block public access' settings")
    print("5. Uncheck 'Block all public access'")
    print("6. Go to 'Properties' tab")
    print("7. Enable 'Static website hosting'")
    print("8. Set index document to 'landing.html'")

if __name__ == "__main__":
    main()