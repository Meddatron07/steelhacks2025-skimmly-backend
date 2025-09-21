from celery import Celery
import os
from PIL import Image
import logging

logger = logging.getLogger(__name__)

celery_app = Celery('notes_app')
celery_app.conf.broker_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
celery_app.conf.result_backend = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

@celery_app.task
def process_image_thumbnails(file_path, filename, upload_folder):
    """
    Background task to create thumbnails for uploaded images
    """
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
                thumb_path = os.path.join(upload_folder, 'thumbnails', thumb_filename)

                thumb_img = img.copy()
                thumb_img.thumbnail(dimensions, Image.Resampling.LANCZOS)

                if thumb_img.format == 'JPEG' or file_path.lower().endswith(('.jpg', '.jpeg')):
                    thumb_img.save(thumb_path, 'JPEG', quality=85, optimize=True)
                else:
                    thumb_img.save(thumb_path, 'PNG', optimize=True)

                thumbnails[size_name] = thumb_filename

            logger.info(f"Background processing: Created {len(thumbnails)} thumbnails for {filename}")
            return thumbnails

    except Exception as e:
        logger.error(f"Error in background thumbnail processing: {e}")
        return {}

@celery_app.task
def update_note_thumbnails(note_id, thumbnails):
    """
    Update note record with generated thumbnail paths
    """
    try:
        from app import db, Note
        with db.session.begin():
            note = Note.query.get(note_id)
            if note:
                note.thumbnail_small = thumbnails.get('small')
                note.thumbnail_medium = thumbnails.get('medium')
                note.thumbnail_large = thumbnails.get('large')
                db.session.commit()
                logger.info(f"Updated thumbnails for note {note_id}")
            else:
                logger.warning(f"Note {note_id} not found for thumbnail update")
    except Exception as e:
        logger.error(f"Error updating note thumbnails: {e}")

@celery_app.task
def cleanup_old_files(file_paths):
    """
    Background task to clean up old files when notes are deleted
    """
    cleaned = 0
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                cleaned += 1
        except Exception as e:
            logger.error(f"Error cleaning up file {file_path}: {e}")

    logger.info(f"Cleaned up {cleaned} files")
    return cleaned