@echo off
cd /d "%~dp0"
set PYTHONPATH=%~dp0venv\Lib\site-packages;%PYTHONPATH%
echo Starting Notes Sharing Backend...
echo.
echo Configuration:
echo - Storage: Local (USE_S3=false)
echo - Redis: Optional (for caching)
echo - Celery: Optional (for async processing)
echo.
python app.py
pause