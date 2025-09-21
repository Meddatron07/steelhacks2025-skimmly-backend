# S3 Frontend Deployment Script
# Run this script from the frontend directory

# Configuration - UPDATE THESE VALUES
$BUCKET_NAME = "your-website-bucket-name"  # Change this to your desired bucket name
$REGION = "us-east-1"
$PROFILE = "default"  # AWS CLI profile name

Write-Host "Deploying frontend to S3..." -ForegroundColor Green

# Create S3 bucket if it doesn't exist
Write-Host "Creating S3 bucket: $BUCKET_NAME" -ForegroundColor Yellow
aws s3 mb s3://$BUCKET_NAME --region $REGION --profile $PROFILE

# Configure bucket for static website hosting
Write-Host "Configuring static website hosting..." -ForegroundColor Yellow
aws s3 website s3://$BUCKET_NAME --index-document landing.html --error-document landing.html --profile $PROFILE

# Set bucket policy for public read access
$BUCKET_POLICY = @"
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::$BUCKET_NAME/*"
        }
    ]
}
"@

$BUCKET_POLICY | Out-File -FilePath "bucket-policy.json" -Encoding UTF8
aws s3api put-bucket-policy --bucket $BUCKET_NAME --policy file://bucket-policy.json --profile $PROFILE

# Upload all frontend files
Write-Host "Uploading files to S3..." -ForegroundColor Yellow
aws s3 sync . s3://$BUCKET_NAME --exclude "*.ps1" --exclude "*.json" --exclude "*.md" --profile $PROFILE

# Set correct content types
aws s3 cp s3://$BUCKET_NAME --recursive --exclude "*" --include "*.html" --content-type "text/html" --metadata-directive REPLACE --profile $PROFILE
aws s3 cp s3://$BUCKET_NAME --recursive --exclude "*" --include "*.css" --content-type "text/css" --metadata-directive REPLACE --profile $PROFILE
aws s3 cp s3://$BUCKET_NAME --recursive --exclude "*" --include "*.js" --content-type "application/javascript" --metadata-directive REPLACE --profile $PROFILE

# Clean up temporary files
Remove-Item "bucket-policy.json" -ErrorAction SilentlyContinue

$WEBSITE_URL = "http://$BUCKET_NAME.s3-website-$REGION.amazonaws.com"
Write-Host "Deployment complete!" -ForegroundColor Green
Write-Host "Website URL: $WEBSITE_URL" -ForegroundColor Cyan
Write-Host "Make sure to update your frontend code to use your production backend URL" -ForegroundColor Yellow