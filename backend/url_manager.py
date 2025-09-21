# Image URL Copy Functionality for Backend App

import pyperclip  # pip install pyperclip
import requests
from typing import List, Optional
import json

class ImageURLManager:
    def __init__(self):
        """Initialize the ImageURLManager"""
        pass
    
    def copy_single_url(self, image_url: str) -> bool:
        """
        Copy a single image URL to clipboard
        
        Args:
            image_url (str): The URL of the image to copy
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            pyperclip.copy(image_url)
            print(f"✓ URL copied to clipboard: {image_url}")
            return True
        except Exception as e:
            print(f"✗ Error copying URL: {str(e)}")
            return False
    
    def copy_multiple_urls(self, image_urls: List[str], separator: str = "\n") -> bool:
        """
        Copy multiple image URLs to clipboard
        
        Args:
            image_urls (List[str]): List of image URLs
            separator (str): Separator between URLs (default: newline)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            urls_text = separator.join(image_urls)
            pyperclip.copy(urls_text)
            print(f"✓ {len(image_urls)} URLs copied to clipboard")
            return True
        except Exception as e:
            print(f"✗ Error copying URLs: {str(e)}")
            return False
    
    def get_clipboard_content(self) -> str:
        """
        Get current clipboard content
        
        Returns:
            str: Current clipboard content
        """
        try:
            return pyperclip.paste()
        except Exception as e:
            print(f"✗ Error getting clipboard content: {str(e)}")
            return ""
    
    def validate_url(self, url: str) -> bool:
        """
        Validate if URL is accessible
        
        Args:
            url (str): URL to validate
            
        Returns:
            bool: True if URL is valid and accessible
        """
        try:
            response = requests.head(url, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def copy_url_with_validation(self, image_url: str) -> bool:
        """
        Copy URL to clipboard after validation
        
        Args:
            image_url (str): The URL to validate and copy
            
        Returns:
            bool: True if URL is valid and copied successfully
        """
        if self.validate_url(image_url):
            return self.copy_single_url(image_url)
        else:
            print(f"✗ URL is not accessible: {image_url}")
            return False

# Flask API endpoint example
from flask import Flask, request, jsonify

app = Flask(__name__)
url_manager = ImageURLManager()

@app.route('/copy-image-url', methods=['POST'])
def copy_image_url():
    """
    API endpoint to copy image URL to clipboard
    Expected JSON: {"url": "https://example.com/image.jpg"}
    """
    try:
        data = request.get_json()
        image_url = data.get('url')
        
        if not image_url:
            return jsonify({"error": "URL is required"}), 400
        
        success = url_manager.copy_single_url(image_url)
        
        if success:
            return jsonify({
                "success": True, 
                "message": "URL copied to clipboard",
                "url": image_url
            })
        else:
            return jsonify({"error": "Failed to copy URL"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/copy-multiple-urls', methods=['POST'])
def copy_multiple_urls():
    """
    API endpoint to copy multiple image URLs
    Expected JSON: {"urls": ["url1", "url2"], "separator": "\n"}
    """
    try:
        data = request.get_json()
        urls = data.get('urls', [])
        separator = data.get('separator', '\n')
        
        if not urls:
            return jsonify({"error": "URLs list is required"}), 400
        
        success = url_manager.copy_multiple_urls(urls, separator)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"{len(urls)} URLs copied to clipboard",
                "count": len(urls)
            })
        else:
            return jsonify({"error": "Failed to copy URLs"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Command line interface
def cli_interface():
    """Command line interface for URL copying"""
    url_manager = ImageURLManager()
    
    while True:
        print("\n--- Image URL Copy Tool ---")
        print("1. Copy single URL")
        print("2. Copy multiple URLs") 
        print("3. View clipboard content")
        print("4. Copy with validation")
        print("5. Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == '1':
            url = input("Enter image URL: ").strip()
            url_manager.copy_single_url(url)
            
        elif choice == '2':
            print("Enter URLs (one per line, empty line to finish):")
            urls = []
            while True:
                url = input().strip()
                if not url:
                    break
                urls.append(url)
            
            if urls:
                separator = input("Enter separator (default: newline): ") or "\n"
                url_manager.copy_multiple_urls(urls, separator)
            else:
                print("No URLs entered.")
                
        elif choice == '3':
            content = url_manager.get_clipboard_content()
            print(f"Clipboard content:\n{content}")
            
        elif choice == '4':
            url = input("Enter image URL to validate and copy: ").strip()
            url_manager.copy_url_with_validation(url)
            
        elif choice == '5':
            print("Goodbye!")
            break
            
        else:
            print("Invalid option. Please try again.")

# Example usage with cloud storage URLs
def example_usage():
    """Example usage with different cloud providers"""
    url_manager = ImageURLManager()
    
    # Example AWS S3 URLs
    s3_urls = [
        "https://mybucket.s3.amazonaws.com/images/photo1.jpg",
        "https://mybucket.s3.amazonaws.com/images/photo2.png"
    ]
    
    # Example Google Cloud Storage URLs
    gcs_urls = [
        "https://storage.googleapis.com/mybucket/images/photo1.jpg"
    ]
    
    # Example Azure Blob Storage URLs
    azure_urls = [
        "https://myaccount.blob.core.windows.net/container/photo1.jpg"
    ]
    
    # Copy single URL
    url_manager.copy_single_url(s3_urls[0])
    
    # Copy multiple URLs with comma separator
    all_urls = s3_urls + gcs_urls + azure_urls
    url_manager.copy_multiple_urls(all_urls, separator=", ")

if __name__ == "__main__":
    # Uncomment the interface you want to use:
    
    # For command line interface
    # cli_interface()
    
    # For Flask API (run with: python filename.py)
    # app.run(debug=True, host='0.0.0.0', port=5000)
    
    # For example usage
    example_usage()