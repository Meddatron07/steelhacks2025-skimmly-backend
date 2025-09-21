# Notes Sharing Backend

A Flask-based backend for a Pinterest-style note-sharing platform where users can upload, share, and discover notes and documents.

## Features

- **User Authentication**: Register, login, and JWT-based authentication
- **File Upload**: Support for multiple file types (txt, pdf, images, doc, docx)
- **Note Management**: Create, view, delete, and like notes
- **Search & Discovery**: Search by title, description, or tags
- **Thumbnails**: Automatic thumbnail generation for images
- **Privacy Controls**: Public/private note visibility
- **Pagination**: Efficient browsing of large note collections

## API Endpoints

### Authentication
- `POST /api/register` - Register new user
- `POST /api/login` - User login
- `GET /api/profile` - Get user profile (requires auth)

### Notes Management
- `POST /api/upload` - Upload a new note (requires auth)
- `GET /api/notes` - Get public notes with pagination
- `GET /api/notes/<id>` - Get specific note details
- `DELETE /api/notes/<id>` - Delete note (requires auth, owner only)
- `GET /api/my-notes` - Get user's notes (requires auth)

### Interactions
- `POST /api/notes/<id>/like` - Toggle like on note (requires auth)

### Search & Discovery
- `GET /api/search` - Search notes by query or tags
- `GET /api/tags` - Get popular tags

### File Serving
- `GET /api/files/<filename>` - Serve uploaded files
- `GET /api/thumbnails/<filename>` - Serve image thumbnails

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

The server will start on `http://localhost:5000`

## Configuration

Update these configuration values in `app.py`:
- `SECRET_KEY`: Change to a secure random string
- `JWT_SECRET_KEY`: Change to a secure random string for JWT tokens
- `SQLALCHEMY_DATABASE_URI`: Database connection string (defaults to SQLite)

## File Structure

```
backend/
├── app.py              # Main Flask application
├── models.py           # Database models
├── requirements.txt    # Python dependencies
├── uploads/           # Directory for uploaded files
│   └── thumbnails/    # Directory for image thumbnails
└── notes_app.db       # SQLite database (created automatically)
```

## Database Models

- **User**: User accounts with authentication
- **Note**: Uploaded notes/files with metadata
- **Like**: User likes on notes

## Security Features

- Password hashing using Werkzeug
- JWT token-based authentication
- File type validation
- File size limits (16MB max)
- Access control for private notes