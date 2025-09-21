import re
from werkzeug.datastructures import FileStorage

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username):
    if not username or len(username.strip()) < 3:
        return False, "Username must be at least 3 characters long"
    if len(username) > 50:
        return False, "Username must be less than 50 characters"
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Username can only contain letters, numbers, underscores, and hyphens"
    return True, ""

def validate_password(password):
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters long"
    if len(password) > 128:
        return False, "Password must be less than 128 characters"
    return True, ""

def validate_note_title(title):
    if not title or len(title.strip()) < 1:
        return False, "Title is required"
    if len(title) > 200:
        return False, "Title must be less than 200 characters"
    return True, ""

def validate_note_description(description):
    if description and len(description) > 1000:
        return False, "Description must be less than 1000 characters"
    return True, ""

def validate_tags(tags):
    if tags and len(tags) > 500:
        return False, "Tags must be less than 500 characters"
    return True, ""

def validate_file_upload(file):
    if not file:
        return False, "No file provided"

    if not isinstance(file, FileStorage):
        return False, "Invalid file format"

    if file.filename == '':
        return False, "No file selected"

    if not file.filename:
        return False, "Invalid filename"

    allowed_extensions = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
    if '.' not in file.filename:
        return False, "File must have an extension"

    extension = file.filename.rsplit('.', 1)[1].lower()
    if extension not in allowed_extensions:
        return False, f"File type '{extension}' not allowed. Allowed types: {', '.join(allowed_extensions)}"

    return True, ""

def sanitize_search_query(query):
    if not query:
        return ""

    query = query.strip()
    if len(query) > 100:
        query = query[:100]

    query = re.sub(r'[<>"\']', '', query)
    return query

def validate_comment_content(content):
    """Validate comment content"""
    if not content or not content.strip():
        return False, "Comment content cannot be empty"

    content = content.strip()

    if len(content) < 1:
        return False, "Comment content is too short"

    if len(content) > 1000:
        return False, "Comment content is too long (max 1000 characters)"

    # Check for basic spam patterns
    if content.count('http') > 3:
        return False, "Too many links in comment"

    return True, ""