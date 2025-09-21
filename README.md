# Skimmly - Study Notes Sharing Platform

A full-stack web application for sharing and discovering study notes, built for SteelHacks 2025.

## 🚀 Features

- **User Authentication** - Firebase-based user registration and login
- **Profile Management** - Customizable user profiles with education level and pronouns
- **Note Upload** - Upload and share study notes as images
- **Note Discovery** - Browse and search through shared notes
- **Comments & Likes** - Interactive engagement with study materials
- **Real-time Notifications** - Stay updated on interactions
- **Responsive Design** - Works on desktop and mobile devices

## 🏗️ Architecture

### Frontend
- **HTML5/CSS3/JavaScript** - Modern responsive web interface
- **Firebase Auth** - User authentication and session management
- **File Upload** - Drag-and-drop note uploading

### Backend
- **Flask** - Python web framework
- **SQLAlchemy** - Database ORM
- **JWT** - Token-based authentication
- **AWS S3** - File storage and serving
- **Redis** - Caching and rate limiting
- **Celery** - Background task processing

### Database Schema
- **Users** - Profile information, authentication
- **Notes** - Study material metadata and files
- **Comments** - User interactions and discussions
- **Likes** - Note popularity tracking
- **Notifications** - User activity updates

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.8+
- Node.js (for frontend tools)
- Redis server
- AWS S3 bucket (for file storage)
- Firebase project (for authentication)

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Meddatron07/steelhacks2025-skimmly-backend.git
   cd steelhacks2025-skimmly-backend
   ```

2. **Create virtual environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Create a `.env` file in the backend directory:
   ```env
   # Flask Configuration
   SECRET_KEY=your-super-secret-key-change-this
   JWT_SECRET_KEY=your-jwt-secret-key-change-this

   # Database
   DATABASE_URL=sqlite:///notes_app.db

   # AWS S3 Configuration
   AWS_ACCESS_KEY_ID=your-aws-access-key
   AWS_SECRET_ACCESS_KEY=your-aws-secret-key
   AWS_REGION=us-east-2
   S3_BUCKET_NAME=your-s3-bucket-name
   USE_S3=true

   # Redis (Optional)
   REDIS_URL=redis://localhost:6379/0

   # Environment
   FLASK_ENV=development
   FLASK_DEBUG=True
   ```

5. **Initialize the database**
   ```bash
   python app.py
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Configure Firebase**
   Update the Firebase configuration in the HTML files with your project details.

3. **Serve the files**
   You can serve the frontend files using any web server or upload them to S3 for static hosting.

## 🚀 Deployment

### Backend Deployment (Render)

1. **Connect GitHub repository** to Render
2. **Set environment variables** in Render dashboard
3. **Deploy** - Render will automatically install dependencies and start the application

### Frontend Deployment (AWS S3)

1. **Configure S3 bucket** for static website hosting
2. **Upload frontend files** using the provided deployment scripts
3. **Configure CloudFront** (optional) for CDN

## 📱 API Endpoints

### Authentication
- `POST /api/register` - User registration
- `POST /api/login` - User login
- `POST /api/firebase-sync` - Firebase user synchronization

### Profile Management
- `GET /api/profile` - Get user profile
- `PUT /api/profile` - Update user profile

### Notes
- `GET /api/notes` - Get all notes
- `POST /api/notes` - Upload new note
- `GET /api/notes/<id>` - Get specific note
- `PUT /api/notes/<id>` - Update note
- `DELETE /api/notes/<id>` - Delete note

### Interactions
- `POST /api/notes/<id>/like` - Like/unlike note
- `POST /api/notes/<id>/comments` - Add comment
- `GET /api/notifications` - Get user notifications

## 🧪 Testing

Run the test suite:
```bash
cd backend
python -m pytest tests/
```

## 🔧 Configuration

### Rate Limiting
The application includes rate limiting on sensitive endpoints:
- Registration: 5 per minute
- Login: 10 per minute
- Profile updates: 10 per minute

### File Upload Limits
- Maximum file size: 16MB
- Supported formats: JPG, PNG, GIF
- Automatic thumbnail generation

### Security Features
- CORS protection
- SQL injection prevention
- Input validation and sanitization
- JWT token authentication
- Password hashing with bcrypt

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏆 SteelHacks 2025

Built with ❤️ for SteelHacks 2025 hackathon at the University of Pittsburgh.

### Team
- Full-stack development and deployment
- UI/UX design and implementation
- Backend architecture and API design
- Database design and optimization

## 🐛 Known Issues & Fixes

### Recent Bug Fixes
- ✅ **Profile Save Button**: Fixed username handling in backend API
- ✅ **Deployment Failure**: Added missing `pyperclip` dependency
- ✅ **Security**: Removed hardcoded AWS credentials
- ✅ **CORS Issues**: Configured proper cross-origin headers

### Troubleshooting

**Deployment Issues:**
- Ensure all environment variables are set in your deployment platform
- Check that AWS credentials have proper S3 permissions
- Verify Redis connection for rate limiting features

**Authentication Issues:**
- Confirm Firebase configuration matches your project
- Check JWT secret keys are properly set
- Verify CORS settings allow your frontend domain

**File Upload Issues:**
- Check S3 bucket permissions and CORS configuration
- Verify file size limits and supported formats
- Ensure proper AWS credentials are configured

## 📞 Support

If you encounter any issues or have questions, please:
1. Check the troubleshooting section above
2. Search existing GitHub issues
3. Create a new issue with detailed information about the problem

---

**Happy studying! 📚✨**