# Quick Backend Deployment Guide

Your frontend is already live at:
**http://steelhacks2025-frontend.s3-website.us-east-2.amazonaws.com/**

## Option 1: Use ngrok (Requires free account)

1. **Sign up for ngrok**: https://dashboard.ngrok.com/signup (free)
2. **Get auth token**: https://dashboard.ngrok.com/get-started/your-authtoken
3. **Setup ngrok**:
   ```bash
   ./ngrok.exe authtoken YOUR_AUTHTOKEN_HERE
   ./ngrok.exe http 5000
   ```
4. **Get your URL**: Look for something like `https://abc123.ngrok.io`

## Option 2: Use localtunnel (No account needed)

1. **Open new terminal** (keep your backend running)
2. **Run**: `npx localtunnel --port 5000`
3. **Get your URL**: Look for something like `https://random-name.loca.lt`

## Option 3: Use your public IP (if available)

1. **Find your public IP**: https://whatismyipaddress.com/
2. **Configure router**: Forward port 5000 to your computer
3. **Use**: `http://YOUR_PUBLIC_IP:5000`

## Option 4: Keep local for now

**For immediate testing**, update your frontend to use:
- Your local IP instead of localhost
- Example: `http://192.168.1.100:5000` (find your local IP with `ipconfig`)

## Next Steps After Getting Backend URL:

1. **Test your backend URL** in browser
2. **Update frontend files** to use the new URL
3. **Re-upload to S3**

Your website will then be fully functional and accessible to anyone!

## Current Status:
- ✅ Frontend deployed and working
- ✅ Backend running locally on port 5000
- 🔄 Need public URL for backend

Choose whichever option works best for you!