"""
Firebase Authentication module for Flask backend
Provides Firebase token verification and user management
"""
import firebase_admin
from firebase_admin import credentials, auth
from flask import request, jsonify
from functools import wraps
import logging
import os

logger = logging.getLogger(__name__)

class FirebaseAuth:
    def __init__(self):
        self.initialized = False
        self.init_firebase()

    def init_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            if not firebase_admin._apps:
                # Try to use service account file first
                service_account_path = os.path.join(os.path.dirname(__file__), 'firebase-service-account.json')

                if os.path.exists(service_account_path):
                    # Use service account file
                    cred = credentials.Certificate(service_account_path)
                    firebase_admin.initialize_app(cred, {
                        'projectId': 'skimmly-c09f7'
                    })
                    logger.info("Firebase Admin SDK initialized with service account")
                else:
                    # Fallback to application default credentials
                    firebase_admin.initialize_app(credentials.ApplicationDefault(), {
                        'projectId': 'skimmly-c09f7'
                    })
                    logger.info("Firebase Admin SDK initialized with application default credentials")

            self.initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            logger.warning("Firebase authentication will not be available")
            logger.info("To fix this, download firebase-service-account.json from Firebase Console")
            self.initialized = False

    def verify_token(self, id_token):
        """Verify Firebase ID token and return user info"""
        if not self.initialized:
            raise Exception("Firebase not initialized")

        try:
            # Verify the ID token
            decoded_token = auth.verify_id_token(id_token)
            user_id = decoded_token['uid']
            email = decoded_token.get('email')

            return {
                'uid': user_id,
                'email': email,
                'firebase_user': decoded_token
            }
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise Exception(f"Invalid token: {e}")

# Global Firebase auth instance
firebase_auth = FirebaseAuth()

def firebase_required(f):
    """Decorator to require Firebase authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization header missing'}), 401

        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Invalid authorization header format'}), 401

        token = auth_header[7:]  # Remove 'Bearer ' prefix

        try:
            user_info = firebase_auth.verify_token(token)
            # Add user info to request context
            request.firebase_user = user_info
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': str(e)}), 401

    return decorated_function

def get_firebase_user():
    """Get current Firebase user from request context"""
    return getattr(request, 'firebase_user', None)