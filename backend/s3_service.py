import os
import logging
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    ClientError = Exception
    NoCredentialsError = Exception
from werkzeug.utils import secure_filename
import io
from urllib.parse import quote

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        self.use_s3 = os.getenv('USE_S3', 'false').lower() == 'true'
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
        self.region = os.getenv('AWS_REGION', 'us-east-1')

        if self.use_s3 and BOTO3_AVAILABLE:
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                    region_name=self.region
                )
                # Test connection
                self.s3_client.head_bucket(Bucket=self.bucket_name)
                logger.info(f"S3 service initialized successfully for bucket: {self.bucket_name}")
            except (ClientError, NoCredentialsError) as e:
                logger.error(f"S3 initialization failed: {e}")
                self.use_s3 = False
                logger.warning("Falling back to local storage")
        elif self.use_s3 and not BOTO3_AVAILABLE:
            logger.warning("boto3 not available, falling back to local storage")
            self.use_s3 = False
        else:
            logger.info("Using local file storage")

    def upload_file(self, file_obj, filename, content_type=None):
        """
        Upload file to S3 or local storage
        Returns: (success: bool, file_url: str, error_message: str)
        """
        try:
            if self.use_s3:
                return self._upload_to_s3(file_obj, filename, content_type)
            else:
                return self._upload_to_local(file_obj, filename)
        except Exception as e:
            logger.error(f"File upload failed: {e}")
            return False, None, str(e)

    def _upload_to_s3(self, file_obj, filename, content_type=None):
        """Upload file to AWS S3"""
        try:
            # Create folder structure in S3
            key = f"uploads/{filename}"

            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type

            # Reset file pointer to beginning
            if hasattr(file_obj, 'seek'):
                file_obj.seek(0)

            # Upload to S3
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                key,
                ExtraArgs=extra_args
            )

            # Generate file URL
            file_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{key}"

            logger.info(f"File uploaded to S3: {key}")
            return True, file_url, None

        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            return False, None, str(e)

    def _upload_to_local(self, file_obj, filename):
        """Upload file to local storage"""
        try:
            upload_folder = os.getenv('UPLOAD_FOLDER', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)

            file_path = os.path.join(upload_folder, filename)

            # Save file locally
            if hasattr(file_obj, 'seek'):
                file_obj.seek(0)

            if hasattr(file_obj, 'save'):
                file_obj.save(file_path)
            else:
                with open(file_path, 'wb') as f:
                    if hasattr(file_obj, 'read'):
                        f.write(file_obj.read())
                    else:
                        f.write(file_obj)

            file_url = f"/api/files/{filename}"
            logger.info(f"File uploaded locally: {file_path}")
            return True, file_url, None

        except Exception as e:
            logger.error(f"Local upload failed: {e}")
            return False, None, str(e)

    def upload_thumbnail(self, image_data, filename, content_type='image/jpeg'):
        """
        Upload thumbnail to S3 or local storage
        """
        try:
            if self.use_s3:
                return self._upload_thumbnail_to_s3(image_data, filename, content_type)
            else:
                return self._upload_thumbnail_to_local(image_data, filename)
        except Exception as e:
            logger.error(f"Thumbnail upload failed: {e}")
            return False, None, str(e)

    def _upload_thumbnail_to_s3(self, image_data, filename, content_type):
        """Upload thumbnail to S3"""
        try:
            key = f"thumbnails/{filename}"

            # Convert image data to bytes if it's a PIL Image
            if hasattr(image_data, 'save'):
                img_buffer = io.BytesIO()
                image_data.save(img_buffer, format='JPEG' if content_type == 'image/jpeg' else 'PNG')
                img_buffer.seek(0)
                image_data = img_buffer

            self.s3_client.upload_fileobj(
                image_data,
                self.bucket_name,
                key,
                ExtraArgs={'ContentType': content_type}
            )

            file_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{key}"
            logger.info(f"Thumbnail uploaded to S3: {key}")
            return True, file_url, None

        except ClientError as e:
            logger.error(f"S3 thumbnail upload failed: {e}")
            return False, None, str(e)

    def _upload_thumbnail_to_local(self, image_data, filename):
        """Upload thumbnail to local storage"""
        try:
            upload_folder = os.getenv('UPLOAD_FOLDER', 'uploads')
            thumbnails_folder = os.path.join(upload_folder, 'thumbnails')
            os.makedirs(thumbnails_folder, exist_ok=True)

            file_path = os.path.join(thumbnails_folder, filename)

            if hasattr(image_data, 'save'):
                image_data.save(file_path)
            else:
                with open(file_path, 'wb') as f:
                    f.write(image_data)

            file_url = f"/api/thumbnails/{filename}"
            logger.info(f"Thumbnail uploaded locally: {file_path}")
            return True, file_url, None

        except Exception as e:
            logger.error(f"Local thumbnail upload failed: {e}")
            return False, None, str(e)

    def delete_file(self, filename):
        """Delete file from S3 or local storage"""
        try:
            if self.use_s3:
                return self._delete_from_s3(f"uploads/{filename}")
            else:
                return self._delete_from_local(filename)
        except Exception as e:
            logger.error(f"File deletion failed: {e}")
            return False, str(e)

    def delete_thumbnail(self, filename):
        """Delete thumbnail from S3 or local storage"""
        try:
            if self.use_s3:
                return self._delete_from_s3(f"thumbnails/{filename}")
            else:
                return self._delete_thumbnail_from_local(filename)
        except Exception as e:
            logger.error(f"Thumbnail deletion failed: {e}")
            return False, str(e)

    def _delete_from_s3(self, key):
        """Delete file from S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            logger.info(f"File deleted from S3: {key}")
            return True, None
        except ClientError as e:
            logger.error(f"S3 deletion failed: {e}")
            return False, str(e)

    def _delete_from_local(self, filename):
        """Delete file from local storage"""
        try:
            upload_folder = os.getenv('UPLOAD_FOLDER', 'uploads')
            file_path = os.path.join(upload_folder, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File deleted locally: {file_path}")
            return True, None
        except Exception as e:
            logger.error(f"Local deletion failed: {e}")
            return False, str(e)

    def _delete_thumbnail_from_local(self, filename):
        """Delete thumbnail from local storage"""
        try:
            upload_folder = os.getenv('UPLOAD_FOLDER', 'uploads')
            file_path = os.path.join(upload_folder, 'thumbnails', filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Thumbnail deleted locally: {file_path}")
            return True, None
        except Exception as e:
            logger.error(f"Local thumbnail deletion failed: {e}")
            return False, str(e)

    def generate_presigned_url(self, filename, expiration=3600):
        """Generate presigned URL for S3 file (for secure access)"""
        if not self.use_s3:
            return None

        try:
            key = f"uploads/{filename}"
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None

# Global instance
s3_service = S3Service()