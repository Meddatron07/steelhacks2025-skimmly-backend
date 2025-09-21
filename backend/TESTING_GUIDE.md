# Testing Guide

## 🚀 Quick Start Testing

### 1. Test Basic Setup
```bash
python test_setup.py
```

### 2. Start the Server (Local Storage)
- **Option A**: Double-click `run.bat`
- **Option B**: `python app.py` (with PYTHONPATH set)

Server will start at: `http://localhost:5000`

### 3. Test Endpoints

#### Health Check
```bash
curl http://localhost:5000
```
Expected: `{"status": "healthy", "message": "Notes sharing API is running"}`

#### Register User
```bash
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "password123"}'
```

#### Login
```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}'
```
Copy the `access_token` from response.

#### Upload File (Local Storage)
```bash
curl -X POST http://localhost:5000/api/upload \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@test.pdf" \
  -F "title=My Test Note" \
  -F "description=Testing file upload" \
  -F "tags=test,pdf"
```

#### Get Notes
```bash
curl http://localhost:5000/api/notes
```

## 🔧 Local vs S3 Testing

### Local Storage (Default)
- Files stored in `uploads/` folder
- Thumbnails in `uploads/thumbnails/`
- No AWS setup needed

### S3 Storage
1. Set up AWS account (follow `AWS_SETUP.md`)
2. Update `.env`:
   ```
   USE_S3=true
   AWS_ACCESS_KEY_ID=your-key
   AWS_SECRET_ACCESS_KEY=your-secret
   S3_BUCKET_NAME=your-bucket
   ```
3. Restart server
4. Files will be stored in S3

## 📱 Testing with Postman

### Import this collection:
1. **POST** `/api/register` - Register user
2. **POST** `/api/login` - Get auth token
3. **POST** `/api/upload` - Upload file (form-data)
4. **GET** `/api/notes` - List notes
5. **GET** `/api/notes/:id` - Get specific note
6. **DELETE** `/api/notes/:id` - Delete note

### Headers for authenticated requests:
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

## 🐛 Troubleshooting

### Dependencies Missing
```bash
pip install -r requirements.txt
```

### Import Errors
- Use `run.bat` which sets correct PYTHONPATH
- Or manually set: `set PYTHONPATH=%cd%\venv\Lib\site-packages`

### S3 Errors
- Check AWS credentials in `.env`
- Verify bucket exists and permissions
- Check bucket name format (lowercase, no spaces)

### Database Issues
- Delete `notes_app.db` to reset
- Check file permissions in uploads folder

## 📊 Test Data Structure

### User Registration
```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "password123"
}
```

### File Upload (form-data)
- `file`: File to upload
- `title`: Note title (optional)
- `description`: Description (optional)
- `tags`: Comma-separated tags
- `is_public`: true/false

### Expected Response
```json
{
  "message": "File uploaded successfully",
  "note": {
    "id": 1,
    "title": "My Test Note",
    "file_url": "/api/files/uuid.pdf",
    "thumbnails": {
      "small": "/api/thumbnails/thumb_small_uuid.jpg",
      "medium": "/api/thumbnails/thumb_medium_uuid.jpg",
      "large": "/api/thumbnails/thumb_large_uuid.jpg"
    }
  }
}
```