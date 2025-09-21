# Comments API Documentation

The note-sharing backend now includes a comprehensive commenting system that allows users to comment on notes and reply to other comments.

## Features

- **Nested Comments**: Support for replies to comments (one level deep)
- **User Authentication**: Comments require authentication
- **Access Control**: Respects note privacy settings
- **Edit & Delete**: Comment authors can edit/delete their comments
- **Note Owner Control**: Note owners can delete any comment on their notes
- **Pagination**: Comments are paginated for performance
- **Validation**: Comment content is validated for length and spam patterns

## API Endpoints

### 1. Get Comments for a Note

**GET** `/api/notes/{note_id}/comments`

Retrieves all top-level comments for a note with pagination.

**Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 20)

**Response:**
```json
{
    "comments": [
        {
            "id": 1,
            "content": "Great note!",
            "user_id": 123,
            "username": "john_doe",
            "note_id": 456,
            "parent_id": null,
            "created_at": "2025-01-15T10:30:00",
            "updated_at": "2025-01-15T10:30:00",
            "is_edited": false,
            "replies_count": 2,
            "replies": [
                {
                    "id": 2,
                    "content": "Thanks!",
                    "user_id": 789,
                    "username": "jane_smith",
                    "note_id": 456,
                    "parent_id": 1,
                    "created_at": "2025-01-15T11:00:00",
                    "updated_at": "2025-01-15T11:00:00",
                    "is_edited": false,
                    "replies_count": 0
                }
            ]
        }
    ],
    "total": 15,
    "pages": 2,
    "current_page": 1,
    "note_id": 456
}
```

### 2. Add a Comment

**POST** `/api/notes/{note_id}/comments`

**Authentication:** Required (JWT token)

**Request Body:**
```json
{
    "content": "This is a great note!",
    "parent_id": null  // Optional: ID of parent comment for replies
}
```

**Response:**
```json
{
    "message": "Comment added successfully",
    "comment": {
        "id": 1,
        "content": "This is a great note!",
        "user_id": 123,
        "username": "john_doe",
        "note_id": 456,
        "parent_id": null,
        "created_at": "2025-01-15T10:30:00",
        "updated_at": "2025-01-15T10:30:00",
        "is_edited": false,
        "replies_count": 0
    }
}
```

### 3. Edit a Comment

**PUT** `/api/comments/{comment_id}`

**Authentication:** Required (JWT token - must be comment author)

**Request Body:**
```json
{
    "content": "Updated comment content"
}
```

**Response:**
```json
{
    "message": "Comment updated successfully",
    "comment": {
        "id": 1,
        "content": "Updated comment content",
        "user_id": 123,
        "username": "john_doe",
        "note_id": 456,
        "parent_id": null,
        "created_at": "2025-01-15T10:30:00",
        "updated_at": "2025-01-15T12:00:00",
        "is_edited": true,
        "replies_count": 0
    }
}
```

### 4. Delete a Comment

**DELETE** `/api/comments/{comment_id}`

**Authentication:** Required (JWT token - must be comment author or note owner)

**Response:**
```json
{
    "message": "Comment deleted successfully",
    "deleted": true
}
```

**Note:** If a comment has replies, it will be marked as "[Comment deleted]" instead of being completely removed to preserve the conversation structure.

### 5. Get Replies to a Comment

**GET** `/api/comments/{comment_id}/replies`

**Response:**
```json
{
    "replies": [
        {
            "id": 2,
            "content": "Thanks!",
            "user_id": 789,
            "username": "jane_smith",
            "note_id": 456,
            "parent_id": 1,
            "created_at": "2025-01-15T11:00:00",
            "updated_at": "2025-01-15T11:00:00",
            "is_edited": false,
            "replies_count": 0
        }
    ],
    "total": 1,
    "parent_comment_id": 1
}
```

## Access Control

- **Public Notes**: Anyone can read comments, authenticated users can add comments
- **Private Notes**: Only the note owner can read and add comments
- **Comment Editing**: Only the comment author can edit their comments
- **Comment Deletion**: Comment author or note owner can delete comments

## Validation Rules

- Comment content must be 1-1000 characters
- Comments cannot be empty or contain only whitespace
- Basic spam detection prevents comments with too many links
- HTML tags are not allowed in comment content

## Database Schema

The `Comment` model includes:
- `id`: Primary key
- `content`: Comment text (max 1000 chars)
- `user_id`: Foreign key to User
- `note_id`: Foreign key to Note
- `parent_id`: Foreign key to Comment (for replies)
- `created_at`: Timestamp
- `updated_at`: Timestamp
- `is_edited`: Boolean flag

## Usage Examples

### Adding a comment:
```bash
curl -X POST http://localhost:5000/api/notes/123/comments \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Great explanation of the concepts!"}'
```

### Replying to a comment:
```bash
curl -X POST http://localhost:5000/api/notes/123/comments \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "I agree!", "parent_id": 456}'
```

### Getting comments:
```bash
curl http://localhost:5000/api/notes/123/comments?page=1&per_page=10
```

The commenting system is now fully integrated into your note-sharing backend and ready for use!