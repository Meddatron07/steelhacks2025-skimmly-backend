# S3 Frontend Deployment Guide

## Prerequisites
1. Install AWS CLI: https://aws.amazon.com/cli/
2. Configure AWS credentials: `aws configure`
3. Use the same AWS account/region as your backend S3 bucket

## Step 1: Install AWS CLI
```bash
# Download from: https://aws.amazon.com/cli/
# Or use chocolatey:
choco install awscli

# Verify installation:
aws --version
```

## Step 2: Configure AWS Credentials
```bash
aws configure
```
Enter your:
- AWS Access Key ID (from your IAM user)
- AWS Secret Access Key
- Default region (e.g., us-east-1)
- Default output format (json)

## Step 3: Update Deployment Script
1. Open `deploy-s3.ps1`
2. Change `$BUCKET_NAME` to your desired bucket name (must be globally unique)
3. Ensure `$REGION` matches your backend region

## Step 4: Deploy Frontend
```powershell
# From the frontend directory:
cd frontend
./deploy-s3.ps1
```

## Step 5: Update Frontend Configuration
After deployment, update your JavaScript files to use your production backend URL instead of localhost:5000

## Your Website URLs
- **S3 Website**: `http://your-bucket-name.s3-website-us-east-1.amazonaws.com`
- **CloudFront** (optional): For better performance and HTTPS

## Cost Estimate
- S3 hosting: ~$0.50-2.00/month for small websites
- Data transfer: First 1GB free per month
- Requests: First 20,000 free per month

## Next Steps
1. Deploy your backend to AWS (EC2/Elastic Beanstalk)
2. Update frontend to use production backend URL
3. Optional: Set up CloudFront for HTTPS and better performance