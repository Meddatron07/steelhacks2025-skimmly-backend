from url_manager import ImageURLManager
from flask import Flask, request, jsonify, send_file, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from firebase_auth import firebase_required, get_firebase_user
import os
import uuid
import logging
from datetime import datetime, timedelta
from PIL import Image
import io
from dotenv import load_dotenv
from validators import validate_email, validate_username, validate_password, validate_note_title, validate_note_description, validate_tags, validate_file_upload, sanitize_search_query
from s3_service import s3_service
import redis
from functools import wraps
import json
# Image Preview System
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import json
import uuid
import requests
import base64
from io import BytesIO
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from urllib.parse import urlparse
import os

class ImagePreviewManager:
    """Manager for image previews with metadata"""
    
    def __init__(self, db_path: str = "saved_images.db"):
        self.db_path = db_path
        self.init_database()
        self.cache_dir = "image_cache"
        self.create_cache_dir()
    
    def init_database(self):
        """Initialize database with preview-related fields"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS saved_images (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                image_url TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                tags TEXT,
                is_pinned BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                pinned_at TIMESTAMP,
                category TEXT,
                file_size INTEGER,
                dimensions TEXT,
                thumbnail_path TEXT,
                preview_generated BOOLEAN DEFAULT 0
            )
        ''')
        
        # Create preview_metadata table for additional info
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS preview_metadata (
                image_id TEXT PRIMARY KEY,
                original_filename TEXT,
                mime_type TEXT,
                color_palette TEXT,
                dominant_colors TEXT,
                brightness REAL,
                contrast REAL,
                preview_created_at TIMESTAMP,
                FOREIGN KEY (image_id) REFERENCES saved_images (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_cache_dir(self):
        """Create cache directory for thumbnails"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def download_image(self, url: str) -> Optional[bytes]:
        """Download image from URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"Error downloading image: {str(e)}")
            return None
    
    def generate_thumbnail(self, image_data: bytes, size: Tuple[int, int] = (200, 200)) -> Optional[str]:
        """Generate thumbnail and save to cache"""
        try:
            image = Image.open(BytesIO(image_data))
            
            # Convert RGBA to RGB if necessary
            if image.mode == 'RGBA':
                image = image.convert('RGB')
            
            # Generate thumbnail
            image.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Save thumbnail
            thumbnail_filename = f"thumb_{uuid.uuid4().hex}.jpg"
            thumbnail_path = os.path.join(self.cache_dir, thumbnail_filename)
            image.save(thumbnail_path, "JPEG", quality=85)
            
            return thumbnail_path
        except Exception as e:
            print(f"Error generating thumbnail: {str(e)}")
            return None
    
    def extract_image_metadata(self, image_data: bytes, url: str) -> Dict:
        """Extract metadata from image"""
        try:
            image = Image.open(BytesIO(image_data))
            
            # Basic metadata
            metadata = {
                'dimensions': f"{image.width}x{image.height}",
                'mode': image.mode,
                'format': image.format,
                'file_size': len(image_data),
                'mime_type': f"image/{image.format.lower()}" if image.format else None
            }
            
            # Extract filename from URL
            parsed_url = urlparse(url)
            metadata['original_filename'] = os.path.basename(parsed_url.path) or 'unknown'
            
            # Color analysis (simplified)
            try:
                # Get dominant colors
                image_rgb = image.convert('RGB')
                image_small = image_rgb.resize((50, 50))
                pixels = list(image_small.getdata())
                
                # Calculate average color (simplified dominant color)
                avg_color = [
                    sum(p[0] for p in pixels) // len(pixels),
                    sum(p[1] for p in pixels) // len(pixels),
                    sum(p[2] for p in pixels) // len(pixels)
                ]
                metadata['dominant_color'] = f"rgb({avg_color[0]}, {avg_color[1]}, {avg_color[2]})"
                
                # Calculate brightness
                brightness = sum(avg_color) / 3 / 255
                metadata['brightness'] = round(brightness, 2)
                
            except Exception:
                metadata['dominant_color'] = None
                metadata['brightness'] = None
            
            return metadata
        except Exception as e:
            print(f"Error extracting metadata: {str(e)}")
            return {}
    
    def save_image_with_preview(self, user_id: str, image_url: str, title: str,
                               description: str = None, tags: List[str] = None,
                               category: str = None) -> Dict:
        """Save image and generate preview"""
        try:
            # Download image
            print(f"Downloading image from: {image_url}")
            image_data = self.download_image(image_url)
            if not image_data:
                return {"success": False, "message": "Failed to download image"}
            
            # Generate thumbnail
            print("Generating thumbnail...")
            thumbnail_path = self.generate_thumbnail(image_data)
            
            # Extract metadata
            print("Extracting metadata...")
            metadata = self.extract_image_metadata(image_data, image_url)
            
            # Save to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            image_id = str(uuid.uuid4())
            tags_json = json.dumps(tags or [])
            created_at = datetime.now().isoformat()
            
            # Save main image record
            cursor.execute('''
                INSERT INTO saved_images 
                (id, user_id, image_url, title, description, tags, created_at, category,
                 file_size, dimensions, thumbnail_path, preview_generated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (image_id, user_id, image_url, title, description, tags_json, 
                  created_at, category, metadata.get('file_size'), 
                  metadata.get('dimensions'), thumbnail_path, 1))
            
            # Save preview metadata
            cursor.execute('''
                INSERT INTO preview_metadata
                (image_id, original_filename, mime_type, dominant_colors, brightness, preview_created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (image_id, metadata.get('original_filename'), metadata.get('mime_type'),
                  metadata.get('dominant_color'), metadata.get('brightness'), created_at))
            
            conn.commit()
            conn.close()
            
            print(f"✓ Image saved with preview! ID: {image_id}")
            return {
                "success": True,
                "message": "Image saved with preview successfully",
                "image_id": image_id,
                "thumbnail_path": thumbnail_path,
                "metadata": metadata
            }
            
        except Exception as e:
            print(f"✗ Error saving image with preview: {str(e)}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def get_images_with_previews(self, user_id: str, pinned_only: bool = False) -> List[Dict]:
        """Get images with preview information"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = '''
                SELECT s.*, p.original_filename, p.mime_type, p.dominant_colors, p.brightness
                FROM saved_images s
                LEFT JOIN preview_metadata p ON s.id = p.image_id
                WHERE s.user_id = ?
            '''
            params = [user_id]
            
            if pinned_only:
                query += ' AND s.is_pinned = 1'
            
            query += ' ORDER BY s.created_at DESC'
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert to dictionaries
            columns = [desc[0] for desc in cursor.description]
            images = []
            
            for row in rows:
                image_dict = dict(zip(columns, row))
                image_dict['tags'] = json.loads(image_dict['tags'] or '[]')
                images.append(image_dict)
            
            conn.close()
            return images
            
        except Exception as e:
            print(f"Error getting images with previews: {str(e)}")
            return []

class ImagePreviewGUI:
    """GUI for previewing saved images"""
    
    def __init__(self):
        self.preview_manager = ImagePreviewManager()
        self.root = tk.Tk()
        self.root.title("Image Preview Manager")
        self.root.geometry("1200x800")
        
        # Current user (in real app, this would come from authentication)
        self.current_user = "user123"
        
        self.setup_gui()
        self.load_images()
    
    def setup_gui(self):
        """Setup the GUI components"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Top controls
        controls_frame = ttk.Frame(main_frame)
        controls_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(controls_frame, text="Add Image", command=self.add_image_dialog).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(controls_frame, text="Refresh", command=self.load_images).grid(row=0, column=1, padx=(0, 10))
        
        # Filter options
        ttk.Label(controls_frame, text="Filter:").grid(row=0, column=2, padx=(20, 5))
        self.filter_var = tk.StringVar(value="all")
        filter_combo = ttk.Combobox(controls_frame, textvariable=self.filter_var, 
                                   values=["all", "pinned", "unpinned"], state="readonly")
        filter_combo.grid(row=0, column=3, padx=(0, 10))
        filter_combo.bind('<<ComboboxSelected>>', lambda e: self.load_images())
        
        # Search
        ttk.Label(controls_frame, text="Search:").grid(row=0, column=4, padx=(20, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(controls_frame, textvariable=self.search_var, width=20)
        search_entry.grid(row=0, column=5, padx=(0, 10))
        search_entry.bind('<KeyRelease>', lambda e: self.load_images())
        
        # Main content area with scrollbar
        self.setup_scrollable_frame(main_frame)
    
    def setup_scrollable_frame(self, parent):
        """Setup scrollable frame for image grid"""
        # Create canvas and scrollbar
        canvas = tk.Canvas(parent, bg='white')
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        
        # Configure grid weights
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)
        
        self.canvas = canvas
    
    def add_image_dialog(self):
        """Dialog to add new image"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Image")
        dialog.geometry("400x300")
        
        # URL
        ttk.Label(dialog, text="Image URL:").pack(pady=5)
        url_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=url_var, width=50).pack(pady=5)
        
        # Title
        ttk.Label(dialog, text="Title:").pack(pady=5)
        title_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=title_var, width=50).pack(pady=5)
        
        # Description
        ttk.Label(dialog, text="Description:").pack(pady=5)
        desc_text = tk.Text(dialog, height=4, width=50)
        desc_text.pack(pady=5)
        
        # Tags
        ttk.Label(dialog, text="Tags (comma separated):").pack(pady=5)
        tags_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=tags_var, width=50).pack(pady=5)
        
        # Category
        ttk.Label(dialog, text="Category:").pack(pady=5)
        category_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=category_var, width=50).pack(pady=5)
        
        def save_image():
            url = url_var.get().strip()
            title = title_var.get().strip()
            
            if not url or not title:
                messagebox.showerror("Error", "URL and Title are required!")
                return
            
            # Show progress
            progress = tk.Toplevel(dialog)
            progress.title("Processing...")
            progress.geometry("300x100")
            ttk.Label(progress, text="Downloading and processing image...").pack(pady=20)
            progress_bar = ttk.Progressbar(progress, mode='indeterminate')
            progress_bar.pack(pady=10)
            progress_bar.start()
            
            def process_image():
                try:
                    description = desc_text.get("1.0", tk.END).strip()
                    tags = [tag.strip() for tag in tags_var.get().split(',') if tag.strip()]
                    category = category_var.get().strip()
                    
                    result = self.preview_manager.save_image_with_preview(
                        user_id=self.current_user,
                        image_url=url,
                        title=title,
                        description=description or None,
                        tags=tags,
                        category=category or None
                    )
                    
                    progress.destroy()
                    
                    if result['success']:
                        messagebox.showinfo("Success", "Image saved successfully!")
                        dialog.destroy()
                        self.load_images()
                    else:
                        messagebox.showerror("Error", result['message'])
                        
                except Exception as e:
                    progress.destroy()
                    messagebox.showerror("Error", f"Failed to save image: {str(e)}")
            
            # Run in thread to prevent GUI freezing
            threading.Thread(target=process_image, daemon=True).start()
        
        ttk.Button(dialog, text="Save Image", command=save_image).pack(pady=20)
    
    def load_images(self):
        """Load and display images"""
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Get filter settings
        filter_type = self.filter_var.get()
        search_term = self.search_var.get().strip().lower()
        
        # Load images
        pinned_only = filter_type == "pinned"
        images = self.preview_manager.get_images_with_previews(self.current_user, pinned_only)
        
        # Apply search filter
        if search_term:
            images = [img for img in images if 
                     search_term in img['title'].lower() or 
                     search_term in (img['description'] or '').lower() or
                     any(search_term in tag.lower() for tag in img['tags'])]
        
        # Apply unpinned filter
        if filter_type == "unpinned":
            images = [img for img in images if not img['is_pinned']]
        
        # Display images in grid
        self.display_image_grid(images)
    
    def display_image_grid(self, images):
        """Display images in a grid layout"""
        cols = 4
        
        for i, image in enumerate(images):
            row = i // cols
            col = i % cols
            
            # Create image frame
            img_frame = ttk.LabelFrame(self.scrollable_frame, text=image['title'], padding="10")
            img_frame.grid(row=row, column=col, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # Load and display thumbnail
            self.display_thumbnail(img_frame, image)
            
            # Image info
            info_frame = ttk.Frame(img_frame)
            info_frame.pack(fill=tk.X, pady=(5, 0))
            
            # Dimensions and size
            if image['dimensions']:
                ttk.Label(info_frame, text=f"Size: {image['dimensions']}", 
                         font=('Arial', 8)).pack(anchor=tk.W)
            
            # Tags
            if image['tags']:
                tags_text = ', '.join(image['tags'][:3])  # Show first 3 tags
                if len(image['tags']) > 3:
                    tags_text += f" (+{len(image['tags'])-3} more)"
                ttk.Label(info_frame, text=f"Tags: {tags_text}", 
                         font=('Arial', 8), foreground='blue').pack(anchor=tk.W)
            
            # Buttons
            btn_frame = ttk.Frame(img_frame)
            btn_frame.pack(fill=tk.X, pady=(5, 0))
            
            # Pin/Unpin button
            pin_text = "Unpin" if image['is_pinned'] else "Pin"
            pin_btn = ttk.Button(btn_frame, text=pin_text, width=8,
                               command=lambda img_id=image['id'], pinned=image['is_pinned']: 
                               self.toggle_pin(img_id, pinned))
            pin_btn.pack(side=tk.LEFT, padx=(0, 5))
            
            # View full button
            ttk.Button(btn_frame, text="View", width=8,
                      command=lambda url=image['image_url']: self.view_full_image(url)).pack(side=tk.LEFT)
    
    def display_thumbnail(self, parent, image):
        """Display thumbnail image"""
        try:
            if image['thumbnail_path'] and os.path.exists(image['thumbnail_path']):
                # Load thumbnail
                pil_image = Image.open(image['thumbnail_path'])
                # Resize to fit display
                pil_image.thumbnail((150, 150), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(pil_image)
                
                label = ttk.Label(parent, image=photo)
                label.image = photo  # Keep a reference
                label.pack()
            else:
                # Placeholder
                ttk.Label(parent, text="No Preview\nAvailable", 
                         background='lightgray', width=20, anchor=tk.CENTER).pack()
        except Exception as e:
            print(f"Error displaying thumbnail: {str(e)}")
            ttk.Label(parent, text="Preview\nError", 
                     background='lightcoral', width=20, anchor=tk.CENTER).pack()
    
    def toggle_pin(self, image_id, is_pinned):
        """Toggle pin status of image"""
        conn = sqlite3.connect(self.preview_manager.db_path)
        cursor = conn.cursor()
        
        if is_pinned:
            # Unpin
            cursor.execute('UPDATE saved_images SET is_pinned = 0, pinned_at = NULL WHERE id = ?', (image_id,))
        else:
            # Pin
            pinned_at = datetime.now().isoformat()
            cursor.execute('UPDATE saved_images SET is_pinned = 1, pinned_at = ? WHERE id = ?', (pinned_at, image_id))
        
        conn.commit()
        conn.close()
        
        # Reload images
        self.load_images()
    
    def view_full_image(self, image_url):
        """Open full image in new window"""
        try:
            import webbrowser
            webbrowser.open(image_url)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open image: {str(e)}")
    
    def run(self):
        """Start the GUI"""
        self.root.mainloop()

# Command line interface for testing
def cli_interface():
    """Command line interface for image preview system"""
    manager = ImagePreviewManager()
    
    while True:
        print("\n=== Image Preview System ===")
        print("1. Add image with preview")
        print("2. View saved images")
        print("3. View pinned images")
        print("4. Start GUI")
        print("5. Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == '1':
            url = input("Enter image URL: ").strip()
            title = input("Enter title: ").strip()
            description = input("Enter description (optional): ").strip() or None
            tags_input = input("Enter tags (comma separated, optional): ").strip()
            tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()] if tags_input else None
            category = input("Enter category (optional): ").strip() or None
            
            print("\nProcessing image...")
            result = manager.save_image_with_preview("user123", url, title, description, tags, category)
            
            if result['success']:
                print(f"✓ {result['message']}")
                print(f"Image ID: {result['image_id']}")
                if 'metadata' in result:
                    meta = result['metadata']
                    print(f"Dimensions: {meta.get('dimensions', 'Unknown')}")
                    print(f"File size: {meta.get('file_size', 'Unknown')} bytes")
            else:
                print(f"✗ {result['message']}")
        
        elif choice == '2':
            images = manager.get_images_with_previews("user123")
            print(f"\n=== All Images ({len(images)}) ===")
            for img in images:
                pin_status = "📌" if img['is_pinned'] else "  "
                print(f"{pin_status} {img['title']} ({img['dimensions'] or 'Unknown size'})")
                print(f"   URL: {img['image_url'][:60]}...")
                if img['tags']:
                    print(f"   Tags: {', '.join(img['tags'])}")
                print()
        
        elif choice == '3':
            images = manager.get_images_with_previews("user123", pinned_only=True)
            print(f"\n=== Pinned Images ({len(images)}) ===")
            for img in images:
                print(f"📌 {img['title']} ({img['dimensions'] or 'Unknown size'})")
                print(f"   URL: {img['image_url'][:60]}...")
                print()
        
        elif choice == '4':
            print("Starting GUI...")
            gui = ImagePreviewGUI()
            gui.run()
        
        elif choice == '5':
            print("Goodbye!")
            break
        
        else:
            print("Invalid option. Please try again.")

# Commented out CLI interface to avoid conflicts
# if __name__ == "__main__":
#     # Check if PIL is available for GUI
#     try:
#         from PIL import Image, ImageTk
#         import tkinter as tk
#         from tkinter import ttk, messagebox, filedialog
#
#         print("GUI components available. You can use both CLI and GUI.")
#         print("Run with: python image_preview_system.py")
#
#         # Start CLI interface
#         cli_interface()
#
#     except ImportError as e:
#         print(f"Some GUI components not available: {e}")
#         print("You can still use the basic preview manager.")
#         print("To install missing components: pip install pillow")
#
#         # Provide basic CLI without GUI
#         cli_interface()


from flask import Flask, render_template, send_from_directory
import os

app = Flask(__name__)

@app.route('/')
def preview_page():
    """Serve the image preview page"""
    return send_from_directory('.', 'image_preview.html')

@app.route('/preview')
def image_preview():
    """Alternative route for preview page"""
    return send_from_directory('.', 'image_preview.html')

# Your existing image management routes
# (save-image, pin-image, user-images, etc.)

load_dotenv()
# Add this near the top of your Flask app file
url_manager = ImageURLManager()

# Set up logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

try:
    from tasks import process_image_thumbnails, update_note_thumbnails, cleanup_old_files
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    logger.warning("Celery not available, async processing disabled")

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///notes_app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 20,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
    'max_overflow': 30
}
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-change-this')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}

CORS(app, origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://steelhacks2025-frontend.s3-website.us-east-2.amazonaws.com",
    "https://steelhacks2025-frontend.s3-website.us-east-2.amazonaws.com"
],
supports_credentials=True,
methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'])

# Handle preflight OPTIONS requests
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=os.getenv('REDIS_URL', 'memory://')
)

try:
    redis_client = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'), decode_responses=True)
    redis_client.ping()
    logger.info("Redis connected successfully")
except:
    redis_client = None
    logger.warning("Redis not available, caching disabled")

db = SQLAlchemy(app)
jwt = JWTManager(app)

# Association table for user followers/following relationship
follows = db.Table('follows',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails'), exist_ok=True)

def get_current_user_id():
    """Get current user ID from Firebase auth or JWT"""
    firebase_user = get_firebase_user()
    if firebase_user:
        # Get user from database by Firebase UID
        user = User.query.filter_by(firebase_uid=firebase_user['uid']).first()
        return user.id if user else None
    else:
        # Fallback to JWT
        try:
            return int(get_jwt_identity())
        except:
            return None

@app.route('/api/copy-image-url', methods=['POST'])
@jwt_required()
@limiter.limit("30 per minute")
def copy_image_url():
    """Copy image URL endpoint with enhanced functionality"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'URL is required'}), 400

        url = data['url']
        note_id = data.get('note_id')

        # If note_id provided, verify user has access
        if note_id:
            note = Note.query.get_or_404(note_id)
            user_id = get_jwt_identity()

            if not note.is_public and note.user_id != user_id:
                return jsonify({'error': 'Access denied'}), 403

        copied_url = url_manager.copy_url(url)

        # Log the copy action
        user_id = get_jwt_identity()
        logger.info(f"URL copied by user {user_id}: {url}")

        return jsonify({
            'copied_url': copied_url,
            'original_url': url,
            'message': 'URL copied successfully'
        }), 200
    except Exception as e:
        logger.error(f"Error copying image URL: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/notes/<int:note_id>/share-url', methods=['GET'])
def get_shareable_url(note_id):
    """Get shareable URL for a note"""
    try:
        note = Note.query.get_or_404(note_id)

        # Check if note is public or user has access
        if not note.is_public:
            token = request.headers.get('Authorization')
            if not token:
                return jsonify({'error': 'Note is private'}), 403

            try:
                from flask_jwt_extended import decode_token
                decoded = decode_token(token.replace('Bearer ', ''))
                if decoded['sub'] != note.user_id:
                    return jsonify({'error': 'Access denied'}), 403
            except:
                return jsonify({'error': 'Invalid token'}), 401

        # Generate different types of shareable URLs
        base_url = request.host_url.rstrip('/')

        share_urls = {
            'note_page': f"{base_url}/notes/{note_id}",
            'direct_file': f"{base_url}/api/files/{note.filename}",
            'download': f"{base_url}/api/notes/{note_id}/download"
        }

        # Add thumbnail URLs if available
        if note.thumbnail_medium:
            share_urls['thumbnail'] = note.thumbnail_medium

        return jsonify({
            'share_urls': share_urls,
            'note': {
                'id': note.id,
                'title': note.title,
                'description': note.description
            }
        })

    except Exception as e:
        logger.error(f"Error getting shareable URL for note {note_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

def cache_result(key_prefix, timeout=300):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not redis_client:
                return f(*args, **kwargs)

            cache_key = f"{key_prefix}:{hash(str(args) + str(sorted(kwargs.items())))}"

            try:
                cached = redis_client.get(cache_key)
                if cached:
                    logger.debug(f"Cache hit for {cache_key}")
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Cache read error: {e}")

            result = f(*args, **kwargs)

            try:
                redis_client.setex(cache_key, timeout, json.dumps(result, default=str))
                logger.debug(f"Cached result for {cache_key}")
            except Exception as e:
                logger.warning(f"Cache write error: {e}")

            return result
        return decorated_function
    return decorator

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firebase_uid = db.Column(db.String(128), unique=True, nullable=True)  # Firebase UID
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=True)  # Make optional for Firebase users
    bio = db.Column(db.Text)
    avatar_url = db.Column(db.String(500))
    website = db.Column(db.String(200))
    location = db.Column(db.String(100))
    education_level = db.Column(db.String(100))  # e.g., "High School", "Bachelor's", "Master's", "PhD"
    pronouns = db.Column(db.String(50))  # e.g., "she/her", "he/him", "they/them"
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    notes = db.relationship('Note', backref='author', lazy=True, cascade='all, delete-orphan')

    # Self-referential many-to-many relationship for followers
    followed = db.relationship(
        'User', secondary='follows',
        primaryjoin='User.id == follows.c.follower_id',
        secondaryjoin='User.id == follows.c.followed_id',
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic'
    )

    def to_dict(self, include_private=False):
        data = {
            'id': self.id,
            'username': self.username,
            'bio': self.bio,
            'avatar_url': self.avatar_url,
            'website': self.website,
            'location': self.location,
            'education_level': self.education_level,
            'pronouns': self.pronouns,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'notes_count': len([note for note in self.notes if note.is_public]),
            'followers_count': self.followers.count(),
            'following_count': self.followed.count()
        }

        if include_private:
            data.update({
                'email': self.email,
                'is_active': self.is_active,
                'total_notes_count': len(self.notes)
            })

        return data

    def follow(self, user):
        """Follow a user"""
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        """Unfollow a user"""
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        """Check if following a user"""
        return self.followed.filter(follows.c.followed_id == user.id).count() > 0

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text)
    filename = db.Column(db.String(255), nullable=False, unique=True)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)
    file_type = db.Column(db.String(50), index=True)
    file_url = db.Column(db.String(500))  # S3 URL or local path
    thumbnail_small = db.Column(db.String(500))  # S3 URL or local path
    thumbnail_medium = db.Column(db.String(500))  # S3 URL or local path
    thumbnail_large = db.Column(db.String(500))  # S3 URL or local path
    tags = db.Column(db.String(500), index=True)
    is_public = db.Column(db.Boolean, default=True, index=True)
    allow_comments = db.Column(db.Boolean, default=True)
    allow_downloads = db.Column(db.Boolean, default=True)
    expiry_date = db.Column(db.DateTime, nullable=True, index=True)
    views_count = db.Column(db.Integer, default=0)
    downloads_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)

    likes = db.relationship('Like', backref='note', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'file_url': self.file_url,
            'thumbnails': {
                'small': self.thumbnail_small,
                'medium': self.thumbnail_medium,
                'large': self.thumbnail_large
            },
            'tags': self.tags.split(',') if self.tags else [],
            'is_public': self.is_public,
            'allow_comments': self.allow_comments,
            'allow_downloads': self.allow_downloads,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'is_expired': self.expiry_date and datetime.utcnow() > self.expiry_date,
            'views_count': self.views_count,
            'downloads_count': self.downloads_count,
            'likes_count': self.likes.count(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'author': {
                'id': self.author.id,
                'username': self.author.username
            }
        }

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    note_id = db.Column(db.Integer, db.ForeignKey('note.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'note_id', name='unique_user_note_like'),)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    note_id = db.Column(db.Integer, db.ForeignKey('note.id'), nullable=False, index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True, index=True)  # For replies
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)

    author = db.relationship('User', backref='comments')
    note = db.relationship('Note', backref='comments')
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content if not self.is_deleted else '[Comment deleted]',
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_deleted': self.is_deleted,
            'author': {
                'id': self.author.id,
                'username': self.author.username
            } if not self.is_deleted else None,
            'parent_id': self.parent_id,
            'replies_count': self.replies.filter_by(is_deleted=False).count()
        }

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    type = db.Column(db.String(50), nullable=False, index=True)  # 'like', 'comment', 'reply', 'follow'
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    related_note_id = db.Column(db.Integer, db.ForeignKey('note.id'), nullable=True)
    related_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    related_comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    recipient = db.relationship('User', foreign_keys=[user_id], backref='notifications')
    related_user = db.relationship('User', foreign_keys=[related_user_id])
    related_note = db.relationship('Note', foreign_keys=[related_note_id])
    related_comment = db.relationship('Comment', foreign_keys=[related_comment_id])

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat(),
            'related_note': self.related_note.to_dict() if self.related_note else None,
            'related_user': self.related_user.to_dict() if self.related_user else None
        }


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_notification(user_id, notification_type, title, message, related_note_id=None, related_user_id=None, related_comment_id=None):
    """Helper function to create notifications"""
    try:
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            related_note_id=related_note_id,
            related_user_id=related_user_id,
            related_comment_id=related_comment_id
        )
        db.session.add(notification)
        db.session.commit()
        logger.debug(f"Notification created for user {user_id}: {notification_type}")
    except Exception as e:
        logger.error(f"Error creating notification: {e}")
        db.session.rollback()

def create_thumbnails_s3(file_obj, filename):
    """Create thumbnails and upload to S3 or local storage"""
    thumbnails = {}
    sizes = {
        'small': (150, 150),
        'medium': (300, 300),
        'large': (600, 600)
    }

    try:
        # Ensure file is at beginning
        file_obj.seek(0)

        with Image.open(file_obj) as img:
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')

            for size_name, dimensions in sizes.items():
                thumb_filename = f"thumb_{size_name}_{filename}"

                thumb_img = img.copy()
                thumb_img.thumbnail(dimensions, Image.Resampling.LANCZOS)

                # Upload thumbnail
                success, thumb_url, error = s3_service.upload_thumbnail(
                    thumb_img,
                    thumb_filename,
                    'image/jpeg'
                )

                if success:
                    thumbnails[size_name] = thumb_url
                else:
                    logger.warning(f"Failed to upload thumbnail {thumb_filename}: {error}")

            logger.info(f"Created {len(thumbnails)} thumbnails for {filename}")
            return thumbnails

    except Exception as e:
        logger.error(f"Error creating thumbnails: {e}")
        return {}

def create_thumbnails(file_path, filename):
    """Legacy function for local thumbnail creation"""
    thumbnails = {}
    sizes = {
        'small': (150, 150),
        'medium': (300, 300),
        'large': (600, 600)
    }

    try:
        with Image.open(file_path) as img:
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')

            for size_name, dimensions in sizes.items():
                thumb_filename = f"thumb_{size_name}_{filename}"
                thumb_path = os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails', thumb_filename)

                thumb_img = img.copy()
                thumb_img.thumbnail(dimensions, Image.Resampling.LANCZOS)

                if thumb_img.format == 'JPEG' or file_path.lower().endswith(('.jpg', '.jpeg')):
                    thumb_img.save(thumb_path, 'JPEG', quality=85, optimize=True)
                else:
                    thumb_img.save(thumb_path, 'PNG', optimize=True)

                thumbnails[size_name] = thumb_filename

            logger.info(f"Created {len(thumbnails)} thumbnails for {filename}")
            return thumbnails

    except Exception as e:
        logger.error(f"Error creating thumbnails: {e}")
        return {}

@app.route('/')
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Notes sharing API is running'})

@app.route('/api/upload', methods=['POST'])
@firebase_required
@limiter.limit("10 per minute")
def upload_note():
    try:
        if 'file' not in request.files:
            logger.warning("Upload attempt without file")
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        tags = request.form.get('tags', '').strip()
        is_public = request.form.get('is_public', 'true').lower() == 'true'
        allow_comments = request.form.get('allow_comments', 'true').lower() == 'true'
        allow_downloads = request.form.get('allow_downloads', 'true').lower() == 'true'
        expiry_days = request.form.get('expiry_days', type=int)

        expiry_date = None
        if expiry_days and expiry_days > 0:
            expiry_date = datetime.utcnow() + timedelta(days=expiry_days)

        valid_file, file_error = validate_file_upload(file)
        if not valid_file:
            logger.warning(f"Invalid file upload: {file_error}")
            return jsonify({'error': file_error}), 400

        if title:
            valid_title, title_error = validate_note_title(title)
            if not valid_title:
                return jsonify({'error': title_error}), 400
        else:
            title = file.filename

        valid_desc, desc_error = validate_note_description(description)
        if not valid_desc:
            return jsonify({'error': desc_error}), 400

        valid_tags, tags_error = validate_tags(tags)
        if not valid_tags:
            return jsonify({'error': tags_error}), 400

        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not found'}), 404

        filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
        file_type = file.filename.rsplit('.', 1)[1].lower()

        # Get content type for S3
        content_type = file.content_type or f"application/{file_type}"
        if file_type in ['jpg', 'jpeg']:
            content_type = 'image/jpeg'
        elif file_type == 'png':
            content_type = 'image/png'
        elif file_type == 'pdf':
            content_type = 'application/pdf'

        # Upload main file
        success, file_url, error = s3_service.upload_file(file, filename, content_type)
        if not success:
            logger.error(f"File upload failed: {error}")
            return jsonify({'error': f'File upload failed: {error}'}), 500

        # Get file size (for local files, read from disk; for S3, use content length)
        if s3_service.use_s3:
            file_size = file.content_length or len(file.read())
            file.seek(0)  # Reset file pointer
        else:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file_size = os.path.getsize(file_path)

        note = Note(
            title=title,
            description=description,
            filename=filename,
            original_filename=file.filename,
            file_size=file_size,
            file_type=file_type,
            file_url=file_url,
            tags=tags,
            is_public=is_public,
            allow_comments=allow_comments,
            allow_downloads=allow_downloads,
            expiry_date=expiry_date,
            user_id=user_id
        )

        db.session.add(note)
        db.session.commit()

        # Process thumbnails for images
        if file_type in ['png', 'jpg', 'jpeg', 'gif']:
            try:
                # Reset file pointer and create thumbnails
                file.seek(0)
                thumbnails = create_thumbnails_s3(file, filename)
                if thumbnails:
                    note.thumbnail_small = thumbnails.get('small')
                    note.thumbnail_medium = thumbnails.get('medium')
                    note.thumbnail_large = thumbnails.get('large')
                    db.session.commit()
                    logger.info(f"Created thumbnails for {filename}")
            except Exception as e:
                logger.warning(f"Thumbnail creation failed for {filename}: {e}")

        logger.info(f"File uploaded successfully by user {user_id}: {filename}")
        return jsonify({'message': 'File uploaded successfully', 'note': note.to_dict()}), 201

    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/files/<filename>')
def serve_file(filename):
    """Serve files - for S3, redirect to S3 URL; for local, serve directly"""
    try:
        if s3_service.use_s3:
            # Generate presigned URL for secure access
            presigned_url = s3_service.generate_presigned_url(filename, expiration=3600)
            if presigned_url:
                return jsonify({'file_url': presigned_url})
            else:
                return jsonify({'error': 'File not found'}), 404
        else:
            # Serve from local storage
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(file_path):
                return send_file(file_path)
            else:
                return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        logger.error(f"Error serving file {filename}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/thumbnails/<filename>')
def serve_thumbnail(filename):
    """Serve thumbnails - for S3, redirect to S3 URL; for local, serve directly"""
    try:
        if s3_service.use_s3:
            # For S3, return direct URL (thumbnails can be public)
            bucket_name = os.getenv('S3_BUCKET_NAME')
            region = os.getenv('AWS_REGION', 'us-east-1')
            thumbnail_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/thumbnails/{filename}"
            return jsonify({'thumbnail_url': thumbnail_url})
        else:
            # Serve from local storage
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails', filename)
            if os.path.exists(file_path):
                return send_file(file_path)
            else:
                return jsonify({'error': 'Thumbnail not found'}), 404
    except Exception as e:
        logger.error(f"Error serving thumbnail {filename}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/notes/<int:note_id>/download')
def download_file(note_id):
    """Download file with proper headers"""
    try:
        note = Note.query.get_or_404(note_id)

        # Check if note is expired
        if note.expiry_date and datetime.utcnow() > note.expiry_date:
            return jsonify({'error': 'Note has expired'}), 410

        # Check if note is public or user has access
        if not note.is_public:
            token = request.headers.get('Authorization')
            if not token:
                return jsonify({'error': 'Access denied'}), 403

            try:
                from flask_jwt_extended import decode_token
                decoded = decode_token(token.replace('Bearer ', ''))
                if decoded['sub'] != note.user_id:
                    return jsonify({'error': 'Access denied'}), 403
            except:
                return jsonify({'error': 'Invalid token'}), 401

        # Check if downloads are allowed
        if not note.allow_downloads:
            # Only allow owner to download
            token = request.headers.get('Authorization')
            if not token:
                return jsonify({'error': 'Downloads not allowed for this note'}), 403

            try:
                from flask_jwt_extended import decode_token
                decoded = decode_token(token.replace('Bearer ', ''))
                if decoded['sub'] != note.user_id:
                    return jsonify({'error': 'Downloads not allowed for this note'}), 403
            except:
                return jsonify({'error': 'Invalid token'}), 401

        # Increment view count and download count
        note.views_count += 1
        note.downloads_count += 1
        db.session.commit()

        if s3_service.use_s3:
            # Generate presigned URL for download
            presigned_url = s3_service.generate_presigned_url(note.filename, expiration=300)  # 5 minutes
            if presigned_url:
                return jsonify({
                    'download_url': presigned_url,
                    'filename': note.original_filename,
                    'content_type': f"application/{note.file_type}"
                })
            else:
                return jsonify({'error': 'File not found'}), 404
        else:
            # Serve from local storage with download headers
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], note.filename)
            if os.path.exists(file_path):
                return send_file(
                    file_path,
                    as_attachment=True,
                    download_name=note.original_filename
                )
            else:
                return jsonify({'error': 'File not found'}), 404

    except Exception as e:
        logger.error(f"Error downloading file for note {note_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/notes', methods=['GET'])
@cache_result('notes', 300)
def get_notes():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    search = request.args.get('search', '')
    tag = request.args.get('tag', '')

    query = Note.query.filter_by(is_public=True)

    if search:
        query = query.filter(Note.title.contains(search) | Note.description.contains(search))

    if tag:
        query = query.filter(Note.tags.contains(tag))

    notes = query.order_by(Note.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return {
        'notes': [note.to_dict() for note in notes.items],
        'total': notes.total,
        'pages': notes.pages,
        'current_page': page
    }

@app.route('/api/notes/<int:note_id>', methods=['GET'])
def get_note(note_id):
    note = Note.query.get_or_404(note_id)

    if not note.is_public:
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Note is private'}), 403

        try:
            from flask_jwt_extended import decode_token
            decoded = decode_token(token.replace('Bearer ', ''))
            if decoded['sub'] != note.user_id:
                return jsonify({'error': 'Access denied'}), 403
        except:
            return jsonify({'error': 'Invalid token'}), 401

    note.views_count += 1
    db.session.commit()

    return jsonify(note.to_dict())

@app.route('/api/notes/<int:note_id>/like', methods=['POST'])
@jwt_required()
def toggle_like(note_id):
    user_id = get_jwt_identity()
    note = Note.query.get_or_404(note_id)

    existing_like = Like.query.filter_by(user_id=user_id, note_id=note_id).first()

    if existing_like:
        db.session.delete(existing_like)
        message = 'Note unliked'
        liked = False
    else:
        like = Like(user_id=user_id, note_id=note_id)
        db.session.add(like)
        message = 'Note liked'
        liked = True

        # Create notification for note owner (if not liking own note)
        if note.user_id != user_id:
            liker = User.query.get(user_id)
            create_notification(
                user_id=note.user_id,
                notification_type='like',
                title='New Like',
                message=f'{liker.username} liked your note "{note.title}"',
                related_note_id=note_id,
                related_user_id=user_id
            )

    db.session.commit()

    return jsonify({
        'message': message,
        'liked': liked,
        'likes_count': len(note.likes)
    })

@app.route('/api/my-notes', methods=['GET'])
@jwt_required()
def get_my_notes():
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)

    notes = Note.query.filter_by(user_id=user_id).order_by(Note.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'notes': [note.to_dict() for note in notes.items],
        'total': notes.total,
        'pages': notes.pages,
        'current_page': page
    })

@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
@jwt_required()
def delete_note(note_id):
    user_id = get_jwt_identity()
    note = Note.query.get_or_404(note_id)

    if note.user_id != user_id:
        return jsonify({'error': 'Access denied'}), 403

    # Delete from S3 or local storage
    try:
        # Delete main file
        success, error = s3_service.delete_file(note.filename)
        if not success:
            logger.warning(f"Failed to delete main file {note.filename}: {error}")

        # Delete thumbnails
        if note.thumbnail_small:
            # Extract filename from URL if it's an S3 URL
            thumb_filename = note.thumbnail_small.split('/')[-1] if '/' in note.thumbnail_small else note.thumbnail_small
            success, error = s3_service.delete_thumbnail(thumb_filename)
            if not success:
                logger.warning(f"Failed to delete small thumbnail: {error}")

        if note.thumbnail_medium:
            thumb_filename = note.thumbnail_medium.split('/')[-1] if '/' in note.thumbnail_medium else note.thumbnail_medium
            success, error = s3_service.delete_thumbnail(thumb_filename)
            if not success:
                logger.warning(f"Failed to delete medium thumbnail: {error}")

        if note.thumbnail_large:
            thumb_filename = note.thumbnail_large.split('/')[-1] if '/' in note.thumbnail_large else note.thumbnail_large
            success, error = s3_service.delete_thumbnail(thumb_filename)
            if not success:
                logger.warning(f"Failed to delete large thumbnail: {error}")

    except Exception as e:
        logger.error(f"Error during file cleanup for note {note_id}: {e}")

    # Delete from database
    db.session.delete(note)
    db.session.commit()

    logger.info(f"Note {note_id} deleted successfully")
    return jsonify({'message': 'Note deleted successfully'})

@app.route('/api/notes/<int:note_id>/permissions', methods=['PUT'])
@jwt_required()
def update_note_permissions(note_id):
    """Update note permissions and privacy settings"""
    try:
        user_id = get_jwt_identity()
        note = Note.query.get_or_404(note_id)

        if note.user_id != user_id:
            return jsonify({'error': 'Access denied'}), 403

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        # Update permissions
        if 'is_public' in data:
            note.is_public = bool(data['is_public'])

        if 'allow_comments' in data:
            note.allow_comments = bool(data['allow_comments'])

        if 'allow_downloads' in data:
            note.allow_downloads = bool(data['allow_downloads'])

        if 'expiry_days' in data:
            expiry_days = data['expiry_days']
            if expiry_days is None or expiry_days == 0:
                note.expiry_date = None
            elif expiry_days > 0:
                note.expiry_date = datetime.utcnow() + timedelta(days=expiry_days)
            else:
                return jsonify({'error': 'Invalid expiry_days value'}), 400

        note.updated_at = datetime.utcnow()
        db.session.commit()

        logger.info(f"Permissions updated for note {note_id} by user {user_id}")
        return jsonify({
            'message': 'Permissions updated successfully',
            'note': note.to_dict()
        })

    except Exception as e:
        logger.error(f"Error updating permissions for note {note_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/firebase-sync', methods=['POST'])
@firebase_required
@limiter.limit("10 per minute")
def firebase_sync():
    """Sync Firebase user with Flask database"""
    try:
        data = request.get_json()
        firebase_user = get_firebase_user()

        firebase_uid = firebase_user['uid']
        email = firebase_user['email']

        # Get additional user data from request
        first_name = data.get('firstName', '').strip()
        last_name = data.get('lastName', '').strip()
        username = data.get('username', f"{first_name}_{last_name}").strip().lower()

        # Check if user already exists
        existing_user = User.query.filter_by(firebase_uid=firebase_uid).first()
        if existing_user:
            return jsonify({
                'message': 'User already synced',
                'user': existing_user.to_dict()
            }), 200

        # Check if username is taken
        counter = 1
        original_username = username
        while User.query.filter_by(username=username).first():
            username = f"{original_username}_{counter}"
            counter += 1

        # Create new user
        new_user = User(
            firebase_uid=firebase_uid,
            username=username,
            email=email,
            bio=f"{first_name} {last_name}".strip() if first_name or last_name else ""
        )

        db.session.add(new_user)
        db.session.commit()

        logger.info(f"Firebase user synced: {email}")

        return jsonify({
            'message': 'User synced successfully',
            'user': new_user.to_dict()
        }), 201

    except Exception as e:
        logger.error(f"Error syncing Firebase user: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')

        if not username or not email or not password:
            return jsonify({'error': 'Username, email, and password are required'}), 400

        valid_username, username_error = validate_username(username)
        if not valid_username:
            return jsonify({'error': username_error}), 400

        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400

        valid_password, password_error = validate_password(password)
        if not valid_password:
            return jsonify({'error': password_error}), 400

        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already exists'}), 400

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )

        db.session.add(user)
        db.session.commit()

        access_token = create_access_token(identity=user.id)

        logger.info(f"New user registered: {username}")
        return jsonify({
            'message': 'User registered successfully',
            'access_token': access_token,
            'user': user.to_dict(include_private=True)
        }), 201

    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400

        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password_hash, password):
            logger.warning(f"Failed login attempt for username: {username}")
            return jsonify({'error': 'Invalid credentials'}), 401

        access_token = create_access_token(identity=user.id)

        logger.info(f"Successful login for user: {username}")
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': user.to_dict(include_private=True)
        })

    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict(include_private=True))

@app.route('/api/profile', methods=['PUT'])
@jwt_required()
@limiter.limit("10 per minute")
def update_profile():
    """Update user profile"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        # Update allowed fields
        if 'bio' in data:
            bio = data['bio']
            if bio and len(bio) > 500:
                return jsonify({'error': 'Bio too long (max 500 characters)'}), 400
            user.bio = bio

        if 'website' in data:
            website = data['website']
            if website and len(website) > 200:
                return jsonify({'error': 'Website URL too long'}), 400
            user.website = website

        if 'location' in data:
            location = data['location']
            if location and len(location) > 100:
                return jsonify({'error': 'Location too long'}), 400
            user.location = location

        if 'education_level' in data:
            education_level = data['education_level']
            if education_level and len(education_level) > 100:
                return jsonify({'error': 'Education level too long'}), 400
            user.education_level = education_level

        if 'pronouns' in data:
            pronouns = data['pronouns']
            if pronouns and len(pronouns) > 50:
                return jsonify({'error': 'Pronouns too long'}), 400
            user.pronouns = pronouns

        # Username update with validation
        if 'username' in data:
            new_username = data['username'].strip()
            if not new_username:
                return jsonify({'error': 'Username cannot be empty'}), 400

            valid_username, username_error = validate_username(new_username)
            if not valid_username:
                return jsonify({'error': username_error}), 400

            # Check if username is already taken by another user
            existing_user = User.query.filter_by(username=new_username).filter(User.id != user_id).first()
            if existing_user:
                return jsonify({'error': 'Username already exists'}), 400

            user.username = new_username

        # Email update with validation
        if 'email' in data:
            new_email = data['email'].strip()
            if not validate_email(new_email):
                return jsonify({'error': 'Invalid email format'}), 400

            if User.query.filter_by(email=new_email).filter(User.id != user_id).first():
                return jsonify({'error': 'Email already exists'}), 400

            user.email = new_email

        user.updated_at = datetime.utcnow()
        db.session.commit()

        logger.info(f"Profile updated for user {user_id}")
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict(include_private=True)
        })

    except Exception as e:
        logger.error(f"Error updating profile for user {user_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    """Get public user profile"""
    try:
        user = User.query.filter_by(id=user_id, is_active=True).first_or_404()
        return jsonify(user.to_dict())

    except Exception as e:
        logger.error(f"Error getting user profile {user_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/users/<int:user_id>/follow', methods=['POST'])
@jwt_required()
@limiter.limit("20 per minute")
def follow_user(user_id):
    """Follow a user"""
    try:
        current_user_id = get_jwt_identity()

        if current_user_id == user_id:
            return jsonify({'error': 'Cannot follow yourself'}), 400

        current_user = User.query.get_or_404(current_user_id)
        user_to_follow = User.query.filter_by(id=user_id, is_active=True).first_or_404()

        if current_user.is_following(user_to_follow):
            return jsonify({'error': 'Already following this user'}), 400

        current_user.follow(user_to_follow)
        db.session.commit()

        logger.info(f"User {current_user_id} followed user {user_id}")
        return jsonify({
            'message': 'Successfully followed user',
            'following': True,
            'followers_count': user_to_follow.followers.count()
        })

    except Exception as e:
        logger.error(f"Error following user {user_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/users/<int:user_id>/unfollow', methods=['POST'])
@jwt_required()
@limiter.limit("20 per minute")
def unfollow_user(user_id):
    """Unfollow a user"""
    try:
        current_user_id = get_jwt_identity()

        if current_user_id == user_id:
            return jsonify({'error': 'Cannot unfollow yourself'}), 400

        current_user = User.query.get_or_404(current_user_id)
        user_to_unfollow = User.query.filter_by(id=user_id, is_active=True).first_or_404()

        if not current_user.is_following(user_to_unfollow):
            return jsonify({'error': 'Not following this user'}), 400

        current_user.unfollow(user_to_unfollow)
        db.session.commit()

        logger.info(f"User {current_user_id} unfollowed user {user_id}")
        return jsonify({
            'message': 'Successfully unfollowed user',
            'following': False,
            'followers_count': user_to_unfollow.followers.count()
        })

    except Exception as e:
        logger.error(f"Error unfollowing user {user_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/users/<int:user_id>/follow-status', methods=['GET'])
@jwt_required()
def get_follow_status(user_id):
    """Check if current user is following another user"""
    try:
        current_user_id = get_jwt_identity()

        if current_user_id == user_id:
            return jsonify({'following': False, 'is_self': True})

        current_user = User.query.get_or_404(current_user_id)
        target_user = User.query.filter_by(id=user_id, is_active=True).first_or_404()

        return jsonify({
            'following': current_user.is_following(target_user),
            'is_self': False
        })

    except Exception as e:
        logger.error(f"Error checking follow status for user {user_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/users/<int:user_id>/notes', methods=['GET'])
def get_user_notes(user_id):
    """Get public notes from a specific user"""
    try:
        user = User.query.filter_by(id=user_id, is_active=True).first_or_404()

        page = request.args.get('page', 1, type=int)
        per_page = min(50, request.args.get('per_page', 12, type=int))

        notes = Note.query.filter_by(user_id=user_id, is_public=True).filter(
            db.or_(Note.expiry_date.is_(None), Note.expiry_date > datetime.utcnow())
        ).order_by(Note.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'user': user.to_dict(),
            'notes': [note.to_dict() for note in notes.items],
            'total': notes.total,
            'pages': notes.pages,
            'current_page': page
        })

    except Exception as e:
        logger.error(f"Error getting notes for user {user_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/upload-avatar', methods=['POST'])
@jwt_required()
@limiter.limit("5 per minute")
def upload_avatar():
    """Upload user avatar"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)

        if 'avatar' not in request.files:
            return jsonify({'error': 'No avatar file provided'}), 400

        file = request.files['avatar']
        if not file or file.filename == '':
            return jsonify({'error': 'No avatar file selected'}), 400

        # Validate file type
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            return jsonify({'error': 'Invalid file type. Only PNG, JPG, JPEG, and GIF are allowed'}), 400

        # Generate filename
        filename = f"avatar_{user_id}_{uuid.uuid4()}.{file.filename.rsplit('.', 1)[1].lower()}"

        # Upload to S3 or local storage
        success, avatar_url, error = s3_service.upload_file(file, f"avatars/{filename}", file.content_type)
        if not success:
            logger.error(f"Avatar upload failed: {error}")
            return jsonify({'error': f'Avatar upload failed: {error}'}), 500

        # Update user avatar URL
        user.avatar_url = avatar_url
        user.updated_at = datetime.utcnow()
        db.session.commit()

        logger.info(f"Avatar uploaded for user {user_id}")
        return jsonify({
            'message': 'Avatar uploaded successfully',
            'avatar_url': avatar_url
        }), 201

    except Exception as e:
        logger.error(f"Error uploading avatar for user {user_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            user_id = get_jwt_identity()
            user = User.query.get_or_404(user_id)
            if not user.is_admin or not user.is_active:
                return jsonify({'error': 'Admin access required'}), 403
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Authentication failed'}), 401
    return decorated_function

@app.route('/api/admin/users', methods=['GET'])
@jwt_required()
@admin_required
@limiter.limit("100 per minute")
def admin_get_users():
    """Get all users (admin only)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(100, request.args.get('per_page', 20, type=int))
        search = request.args.get('search', '')

        query = User.query

        if search:
            query = query.filter(
                db.or_(
                    User.username.contains(search),
                    User.email.contains(search)
                )
            )

        users = query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'users': [user.to_dict(include_private=True) for user in users.items],
            'total': users.total,
            'pages': users.pages,
            'current_page': page
        })

    except Exception as e:
        logger.error(f"Error getting users for admin: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/users/<int:user_id>/toggle-status', methods=['POST'])
@jwt_required()
@admin_required
def admin_toggle_user_status(user_id):
    """Toggle user active status (admin only)"""
    try:
        current_user_id = get_jwt_identity()
        if current_user_id == user_id:
            return jsonify({'error': 'Cannot modify your own status'}), 400

        user = User.query.get_or_404(user_id)
        user.is_active = not user.is_active
        user.updated_at = datetime.utcnow()
        db.session.commit()

        action = 'activated' if user.is_active else 'deactivated'
        logger.info(f"User {user_id} {action} by admin {current_user_id}")

        return jsonify({
            'message': f'User {action} successfully',
            'user': user.to_dict(include_private=True)
        })

    except Exception as e:
        logger.error(f"Error toggling user status: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/notes', methods=['GET'])
@jwt_required()
@admin_required
@limiter.limit("100 per minute")
def admin_get_notes():
    """Get all notes (admin only)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(100, request.args.get('per_page', 20, type=int))
        search = request.args.get('search', '')
        user_id = request.args.get('user_id', type=int)

        query = Note.query

        if search:
            query = query.filter(
                db.or_(
                    Note.title.contains(search),
                    Note.description.contains(search)
                )
            )

        if user_id:
            query = query.filter_by(user_id=user_id)

        notes = query.order_by(Note.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'notes': [note.to_dict() for note in notes.items],
            'total': notes.total,
            'pages': notes.pages,
            'current_page': page
        })

    except Exception as e:
        logger.error(f"Error getting notes for admin: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/notes/<int:note_id>/delete', methods=['DELETE'])
@jwt_required()
@admin_required
def admin_delete_note(note_id):
    """Delete note (admin only)"""
    try:
        admin_user_id = get_jwt_identity()
        note = Note.query.get_or_404(note_id)

        # Delete files from storage
        try:
            success, error = s3_service.delete_file(note.filename)
            if not success:
                logger.warning(f"Failed to delete main file {note.filename}: {error}")

            # Delete thumbnails
            for thumb_url in [note.thumbnail_small, note.thumbnail_medium, note.thumbnail_large]:
                if thumb_url:
                    thumb_filename = thumb_url.split('/')[-1] if '/' in thumb_url else thumb_url
                    success, error = s3_service.delete_thumbnail(thumb_filename)
                    if not success:
                        logger.warning(f"Failed to delete thumbnail: {error}")

        except Exception as e:
            logger.error(f"Error during file cleanup for note {note_id}: {e}")

        # Delete from database
        db.session.delete(note)
        db.session.commit()

        logger.info(f"Note {note_id} deleted by admin {admin_user_id}")
        return jsonify({'message': 'Note deleted successfully'})

    except Exception as e:
        logger.error(f"Error deleting note {note_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/stats', methods=['GET'])
@jwt_required()
@admin_required
@cache_result('admin_stats', 300)
def admin_get_stats():
    """Get platform statistics (admin only)"""
    try:
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        total_notes = Note.query.count()
        public_notes = Note.query.filter_by(is_public=True).count()
        total_comments = Comment.query.filter_by(is_deleted=False).count()
        total_likes = Like.query.count()

        # Recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        new_users_week = User.query.filter(User.created_at >= week_ago).count()
        new_notes_week = Note.query.filter(Note.created_at >= week_ago).count()

        return {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': total_users - active_users,
            'total_notes': total_notes,
            'public_notes': public_notes,
            'private_notes': total_notes - public_notes,
            'total_comments': total_comments,
            'total_likes': total_likes,
            'new_users_this_week': new_users_week,
            'new_notes_this_week': new_notes_week
        }

    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """Get user notifications"""
    try:
        user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = min(50, request.args.get('per_page', 20, type=int))
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'

        query = Notification.query.filter_by(user_id=user_id)

        if unread_only:
            query = query.filter_by(is_read=False)

        notifications = query.order_by(Notification.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'notifications': [notification.to_dict() for notification in notifications.items],
            'total': notifications.total,
            'pages': notifications.pages,
            'current_page': page,
            'unread_count': Notification.query.filter_by(user_id=user_id, is_read=False).count()
        })

    except Exception as e:
        logger.error(f"Error getting notifications for user {user_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@jwt_required()
def mark_notification_read(notification_id):
    """Mark notification as read"""
    try:
        user_id = get_jwt_identity()
        notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first_or_404()

        notification.is_read = True
        db.session.commit()

        return jsonify({'message': 'Notification marked as read'})

    except Exception as e:
        logger.error(f"Error marking notification {notification_id} as read: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/notifications/mark-all-read', methods=['POST'])
@jwt_required()
def mark_all_notifications_read():
    """Mark all notifications as read"""
    try:
        user_id = get_jwt_identity()

        Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
        db.session.commit()

        return jsonify({'message': 'All notifications marked as read'})

    except Exception as e:
        logger.error(f"Error marking all notifications as read for user {user_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/notifications/unread-count', methods=['GET'])
@jwt_required()
def get_unread_notifications_count():
    """Get count of unread notifications"""
    try:
        user_id = get_jwt_identity()
        count = Notification.query.filter_by(user_id=user_id, is_read=False).count()

        return jsonify({'unread_count': count})

    except Exception as e:
        logger.error(f"Error getting unread notifications count for user {user_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/search', methods=['GET'])
@limiter.limit("30 per minute")
def search_notes():
    try:
        query = sanitize_search_query(request.args.get('q', ''))
        tag = sanitize_search_query(request.args.get('tag', ''))
        page = max(1, request.args.get('page', 1, type=int))
        per_page = min(50, max(1, request.args.get('per_page', 12, type=int)))

        if not query and not tag:
            return jsonify({'error': 'Search query or tag is required'}), 400

        notes_query = Note.query.filter_by(is_public=True)

        if query:
            notes_query = notes_query.filter(
                Note.title.contains(query) |
                Note.description.contains(query) |
                Note.tags.contains(query)
            )

        if tag:
            notes_query = notes_query.filter(Note.tags.contains(tag))

        notes = notes_query.order_by(Note.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        logger.info(f"Search performed: query='{query}', tag='{tag}', results={notes.total}")
        return jsonify({
            'notes': [note.to_dict() for note in notes.items],
            'total': notes.total,
            'pages': notes.pages,
            'current_page': page,
            'search_query': query,
            'tag_filter': tag
        })

    except Exception as e:
        logger.error(f"Error during search: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/tags', methods=['GET'])
@cache_result('popular_tags', 600)
def get_popular_tags():
    notes = Note.query.filter_by(is_public=True).all()
    tag_counts = {}

    for note in notes:
        if note.tags:
            tags = [tag.strip() for tag in note.tags.split(',')]
            for tag in tags:
                if tag:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

    popular_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:20]

    return {
        'tags': [{'name': tag, 'count': count} for tag, count in popular_tags]
    }

@app.route('/api/notes/<int:note_id>/comments', methods=['GET'])
def get_comments(note_id):
    """Get comments for a specific note"""
    try:
        note = Note.query.get_or_404(note_id)

        # Check if note is accessible
        if not note.is_public:
            token = request.headers.get('Authorization')
            if not token:
                return jsonify({'error': 'Note is private'}), 403

            try:
                from flask_jwt_extended import decode_token
                decoded = decode_token(token.replace('Bearer ', ''))
                if decoded['sub'] != note.user_id:
                    return jsonify({'error': 'Access denied'}), 403
            except:
                return jsonify({'error': 'Invalid token'}), 401

        page = request.args.get('page', 1, type=int)
        per_page = min(50, request.args.get('per_page', 20, type=int))

        # Get top-level comments (no parent)
        comments = Comment.query.filter_by(
            note_id=note_id,
            parent_id=None,
            is_deleted=False
        ).order_by(Comment.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'comments': [comment.to_dict() for comment in comments.items],
            'total': comments.total,
            'pages': comments.pages,
            'current_page': page
        })

    except Exception as e:
        logger.error(f"Error getting comments for note {note_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/notes/<int:note_id>/comments', methods=['POST'])
@jwt_required()
@limiter.limit("20 per minute")
def add_comment(note_id):
    """Add a comment to a note"""
    try:
        user_id = get_jwt_identity()
        note = Note.query.get_or_404(note_id)

        # Check if note is accessible
        if not note.is_public and note.user_id != user_id:
            return jsonify({'error': 'Access denied'}), 403

        # Check if note is expired
        if note.expiry_date and datetime.utcnow() > note.expiry_date:
            return jsonify({'error': 'Note has expired'}), 410

        # Check if comments are allowed
        if not note.allow_comments and note.user_id != user_id:
            return jsonify({'error': 'Comments are not allowed on this note'}), 403

        data = request.get_json()
        if not data or not data.get('content'):
            return jsonify({'error': 'Comment content is required'}), 400

        content = data.get('content', '').strip()
        parent_id = data.get('parent_id')

        if len(content) > 1000:
            return jsonify({'error': 'Comment too long (max 1000 characters)'}), 400

        # Validate parent comment if replying
        if parent_id:
            parent_comment = Comment.query.filter_by(
                id=parent_id,
                note_id=note_id,
                is_deleted=False
            ).first()
            if not parent_comment:
                return jsonify({'error': 'Parent comment not found'}), 404

        comment = Comment(
            content=content,
            user_id=user_id,
            note_id=note_id,
            parent_id=parent_id
        )

        db.session.add(comment)
        db.session.commit()

        # Create notification for note owner (if not commenting on own note)
        if note.user_id != user_id:
            commenter = User.query.get(user_id)
            if parent_id:
                create_notification(
                    user_id=note.user_id,
                    notification_type='reply',
                    title='New Reply',
                    message=f'{commenter.username} replied to a comment on your note "{note.title}"',
                    related_note_id=note_id,
                    related_user_id=user_id,
                    related_comment_id=comment.id
                )
            else:
                create_notification(
                    user_id=note.user_id,
                    notification_type='comment',
                    title='New Comment',
                    message=f'{commenter.username} commented on your note "{note.title}"',
                    related_note_id=note_id,
                    related_user_id=user_id,
                    related_comment_id=comment.id
                )

        # Also notify parent comment author if replying
        if parent_id:
            parent_comment = Comment.query.get(parent_id)
            if parent_comment and parent_comment.user_id != user_id and parent_comment.user_id != note.user_id:
                commenter = User.query.get(user_id)
                create_notification(
                    user_id=parent_comment.user_id,
                    notification_type='reply',
                    title='New Reply',
                    message=f'{commenter.username} replied to your comment on "{note.title}"',
                    related_note_id=note_id,
                    related_user_id=user_id,
                    related_comment_id=comment.id
                )

        logger.info(f"Comment added by user {user_id} on note {note_id}")
        return jsonify({
            'message': 'Comment added successfully',
            'comment': comment.to_dict()
        }), 201

    except Exception as e:
        logger.error(f"Error adding comment to note {note_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/comments/<int:comment_id>/replies', methods=['GET'])
def get_comment_replies(comment_id):
    """Get replies to a specific comment"""
    try:
        parent_comment = Comment.query.get_or_404(comment_id)

        # Check note access
        if not parent_comment.note.is_public:
            token = request.headers.get('Authorization')
            if not token:
                return jsonify({'error': 'Access denied'}), 403

            try:
                from flask_jwt_extended import decode_token
                decoded = decode_token(token.replace('Bearer ', ''))
                if decoded['sub'] != parent_comment.note.user_id:
                    return jsonify({'error': 'Access denied'}), 403
            except:
                return jsonify({'error': 'Invalid token'}), 401

        replies = Comment.query.filter_by(
            parent_id=comment_id,
            is_deleted=False
        ).order_by(Comment.created_at.asc()).all()

        return jsonify({
            'replies': [reply.to_dict() for reply in replies]
        })

    except Exception as e:
        logger.error(f"Error getting replies for comment {comment_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(comment_id):
    """Delete a comment (soft delete)"""
    try:
        user_id = get_jwt_identity()
        comment = Comment.query.get_or_404(comment_id)

        # Check if user owns the comment or the note
        if comment.user_id != user_id and comment.note.user_id != user_id:
            return jsonify({'error': 'Access denied'}), 403

        # Soft delete
        comment.is_deleted = True
        comment.content = '[Comment deleted]'
        db.session.commit()

        logger.info(f"Comment {comment_id} deleted by user {user_id}")
        return jsonify({'message': 'Comment deleted successfully'})

    except Exception as e:
        logger.error(f"Error deleting comment {comment_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)

    