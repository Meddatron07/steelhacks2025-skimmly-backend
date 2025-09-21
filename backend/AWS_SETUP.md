# AWS S3 Setup Guide

## 1. Create AWS Account
1. Go to [aws.amazon.com](https://aws.amazon.com)
2. Sign up for free tier account
3. Verify email and add payment method (won't be charged for free tier usage)

## 2. Create S3 Bucket
1. Login to AWS Console
2. Go to S3 service
3. Click "Create bucket"
4. Choose a unique bucket name (e.g., `your-name-notes-app-bucket`)
5. Select region (recommend `us-east-1`)
6. **Important**: Uncheck "Block all public access" for thumbnails to work
7. Click "Create bucket"

## 3. Create IAM User
1. Go to IAM service in AWS Console
2. Click "Users" → "Add users"
3. Username: `notes-app-user`
4. Select "Programmatic access"
5. Click "Next: Permissions"
6. Click "Attach existing policies directly"
7. Search and select `AmazonS3FullAccess`
8. Click "Next: Tags" → "Next: Review" → "Create user"
9. **IMPORTANT**: Copy the Access Key ID and Secret Access Key

## 4. Configure Your App
1. Update `.env` file:
```env
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your-access-key-here
AWS_SECRET_ACCESS_KEY=your-secret-key-here
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name-here
USE_S3=true
```

## 5. Test the Integration
1. Start your Flask app
2. Try uploading a file
3. Check your S3 bucket - files should appear in `uploads/` folder
4. Thumbnails should appear in `thumbnails/` folder

## Free Tier Limits
- **5GB** of Amazon S3 standard storage
- **20,000 GET** requests
- **2,000 PUT** requests per month
- Valid for 12 months

## Bucket Structure
```
your-bucket-name/
├── uploads/
│   ├── abc123-def456.pdf
│   ├── xyz789-abc123.jpg
│   └── ...
└── thumbnails/
    ├── thumb_small_xyz789.jpg
    ├── thumb_medium_xyz789.jpg
    ├── thumb_large_xyz789.jpg
    └── ...
```

## Switch Between Local and S3
- Set `USE_S3=false` in `.env` to use local storage
- Set `USE_S3=true` in `.env` to use S3 storage
- App automatically handles both modes

## Security Notes
- Keep your AWS keys secret
- Never commit `.env` file to git
- Consider using IAM roles for production
- Enable S3 bucket versioning for backup