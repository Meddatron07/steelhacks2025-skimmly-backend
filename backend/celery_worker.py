#!/usr/bin/env python3
"""
Celery worker startup script
Run with: python celery_worker.py
"""

from tasks import celery_app

if __name__ == '__main__':
    celery_app.start()