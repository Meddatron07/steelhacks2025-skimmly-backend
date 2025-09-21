#!/usr/bin/env python3
"""
Simple EC2 Backend Deployment Guide
Since EB requires additional IAM permissions, let's use EC2
"""

print("""
===============================================
EC2 Backend Deployment Instructions
===============================================

Since your IAM user needs additional permissions for Elastic Beanstalk,
here's how to deploy using EC2 (which you can do manually):

1. LAUNCH EC2 INSTANCE:
   - Go to AWS EC2 Console
   - Launch new instance: t3.micro (free tier)
   - Choose: Amazon Linux 2023
   - Create/use existing key pair
   - Security group: Allow HTTP (80), HTTPS (443), SSH (22)

2. CONNECT TO INSTANCE:
   ssh -i your-key.pem ec2-user@your-instance-ip

3. SETUP ON EC2:
   sudo yum update -y
   sudo yum install python3 python3-pip git -y

4. DEPLOY YOUR CODE:
   # Upload your backend files or clone from git
   # Install dependencies:
   pip3 install -r requirements.txt

5. RUN YOUR APP:
   # For testing:
   python3 app.py

   # For production (with gunicorn):
   pip3 install gunicorn
   gunicorn -w 4 -b 0.0.0.0:80 app:app

===============================================
ALTERNATIVE: Use your existing hosting
===============================================

If you already have hosting (like your current setup), you can:
1. Use your local backend URL temporarily
2. Set up port forwarding with ngrok:

   npm install -g ngrok
   ngrok http 5000

   This gives you a public URL for your backend.

===============================================
""")

# Let's create a simple deployment package anyway
import zipfile
import os

def create_simple_package():
    """Create deployment package for manual upload"""
    files_to_include = [
        'app.py',
        'requirements.txt',
        's3_service.py',
        'url_manager.py',
        'validators.py',
        'firebase_auth.py',
        'firebase-service-account.json.json'
    ]

    with zipfile.ZipFile('backend_package.zip', 'w') as zipf:
        for file in files_to_include:
            if os.path.exists(file):
                zipf.write(file)
                print(f"Added to package: {file}")

    print("\nCreated: backend_package.zip")
    print("You can upload this to your EC2 instance or hosting provider")

if __name__ == "__main__":
    create_simple_package()