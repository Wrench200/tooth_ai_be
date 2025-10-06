import os
import cloudinary
import cloudinary.uploader
import cloudinary.api
import requests
from dotenv import load_dotenv

load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

def upload_image_from_url(image_url, public_id=None, folder="toothai"):
    """
    Upload an image from a URL to Cloudinary
    
    Args:
        image_url (str): URL of the image to upload
        public_id (str): Optional custom public ID for the image
        folder (str): Folder to store the image in Cloudinary
    
    Returns:
        dict: Cloudinary upload response with URL and other details
    """
    try:
        # Download the image temporarily
        response = requests.get(image_url)
        response.raise_for_status()
        
        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            response.content,
            public_id=public_id,
            folder=folder,
            resource_type="image"
        )
        
        print(f"Image uploaded successfully: {upload_result['secure_url']}")
        return upload_result
        
    except Exception as e:
        print(f"Error uploading image to Cloudinary: {e}")
        return None

def upload_image_from_file(file_path, public_id=None, folder="toothai"):
    """
    Upload an image file to Cloudinary
    
    Args:
        file_path (str): Path to the image file
        public_id (str): Optional custom public ID for the image
        folder (str): Folder to store the image in Cloudinary
    
    Returns:
        dict: Cloudinary upload response with URL and other details
    """
    try:
        upload_result = cloudinary.uploader.upload(
            file_path,
            public_id=public_id,
            folder=folder,
            resource_type="image"
        )
        
        print(f"Image uploaded successfully: {upload_result['secure_url']}")
        return upload_result
        
    except Exception as e:
        print(f"Error uploading image to Cloudinary: {e}")
        return None

def delete_image(public_id):
    """
    Delete an image from Cloudinary
    
    Args:
        public_id (str): Public ID of the image to delete
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        result = cloudinary.uploader.destroy(public_id)
        print(f"Image deleted successfully: {public_id}")
        return True
    except Exception as e:
        print(f"Error deleting image from Cloudinary: {e}")
        return False

def get_image_url(public_id, transformation=None):
    """
    Get the URL for an image with optional transformations
    
    Args:
        public_id (str): Public ID of the image
        transformation (dict): Optional transformation parameters
    
    Returns:
        str: Image URL
    """
    try:
        if transformation:
            url = cloudinary.CloudinaryImage(public_id).build_url(**transformation)
        else:
            url = cloudinary.CloudinaryImage(public_id).build_url()
        return url
    except Exception as e:
        print(f"Error generating image URL: {e}")
        return None 
    
    
    
# print(upload_image_from_file("newLogo.jpeg"))