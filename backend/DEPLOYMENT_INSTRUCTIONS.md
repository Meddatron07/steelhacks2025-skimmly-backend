# Deployment Instructions for Render.com

## Environment Variables to Set in Render.com

When deploying to Render.com, set these environment variables in the dashboard:

```
AWS_ACCESS_KEY_ID=[YOUR_AWS_ACCESS_KEY_FROM_ENV_FILE]
AWS_SECRET_ACCESS_KEY=[YOUR_AWS_SECRET_KEY_FROM_ENV_FILE]
AWS_REGION=us-east-2
S3_BUCKET_NAME=steelhacks2025-skimmly
USE_S3=true
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=[GENERATE_RANDOM_SECRET_KEY]
JWT_SECRET_KEY=[GENERATE_RANDOM_JWT_KEY]
```

## Deployment Steps

1. Connect GitHub repository to Render.com
2. Create new Web Service
3. Set environment variables above with actual values
4. Deploy automatically

Your app will be live at: https://steelhacks2025-backend.onrender.com