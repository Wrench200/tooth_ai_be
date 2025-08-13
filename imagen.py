from setup import api_token, gemini_api_key
import requests
import time
import cloudinary_utils
import os
import base64






def generate_replicate_image(prompt, aspect_ratio="1:1", max_retries=5, backoff_factor=1):
    retries = 0
    api_url = "https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-preview-06-06:predict"
    api_key = gemini_api_key
    if not api_key:
        print("GEMINI_API_KEY not found in environment variables!")
        return False

    # Prepare local output directory
    images_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
    os.makedirs(images_dir, exist_ok=True)

    while retries < max_retries:
        payload = {
            "instances": [
                {
                    "prompt": prompt
                }
            ],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": aspect_ratio,
                "personGeneration": "allow_all"
            }
        }
        headers = {
            "x-goog-api-key": api_key,
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(api_url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            response_data = response.json()

            # First, handle base64-encoded image bytes returned in predictions
            predictions = response_data.get("predictions")
            if isinstance(predictions, list) and predictions:
                pred = predictions[0]
                b64_data = pred.get("bytesBase64Encoded")
                mime_type = (pred.get("mimeType") or "image/png").lower()
                if b64_data:
                    # Determine file extension from mime type
                    ext = ".png"
                    if "jpeg" in mime_type or mime_type.endswith("/jpg"):
                        ext = ".jpg"
                    elif "webp" in mime_type:
                        ext = ".webp"
                    # Build safe filename
                    safe_prompt = "".join(c if c.isalnum() else "_" for c in prompt).strip("_") or "image"
                    if len(safe_prompt) > 60:
                        safe_prompt = safe_prompt[:60]
                    file_name = f"{safe_prompt}_{int(time.time())}{ext}"
                    file_path = os.path.join(images_dir, file_name)
                    with open(file_path, "wb") as img_file:
                        img_file.write(base64.b64decode(b64_data))
                    return file_path

            # Fallback: handle URL-based responses if present
            images = response_data.get("images", [])
            image_urls = [img.get("url") for img in images if isinstance(img, dict) and img.get("url")]
            if image_urls:
                image_url = image_urls[0]
                img_resp = requests.get(image_url, stream=True, timeout=120)
                img_resp.raise_for_status()
                content_type = (img_resp.headers.get("Content-Type") or "image/png").lower()
                ext = ".png"
                if "jpeg" in content_type or content_type.endswith("/jpg"):
                    ext = ".jpg"
                elif "webp" in content_type:
                    ext = ".webp"
                safe_prompt = "".join(c if c.isalnum() else "_" for c in prompt).strip("_") or "image"
                if len(safe_prompt) > 60:
                    safe_prompt = safe_prompt[:60]
                file_name = f"{safe_prompt}_{int(time.time())}{ext}"
                file_path = os.path.join(images_dir, file_name)
                with open(file_path, "wb") as img_file:
                    for chunk in img_resp.iter_content(chunk_size=8192):
                        if chunk:
                            img_file.write(chunk)
                return file_path

            # If we reach here, nothing useful was returned; retry with backoff
            retries += 1
            sleep_time = backoff_factor * (2 ** (retries - 1))
            print(f"No image data found. Retrying in {sleep_time} seconds... (Attempt {retries}/{max_retries})")
            time.sleep(sleep_time)
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            retries += 1
            sleep_time = backoff_factor * (2 ** (retries - 1))
            print(f"Retrying in {sleep_time} seconds... (Attempt {retries}/{max_retries})")
            time.sleep(sleep_time)
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return False
    print(f"Failed to generate image after {max_retries} attempts.")
    return False


def generate_image(prompt, aspect_ratio="1:1", public_id=None, folder="toothai"):
    """
    Generate an image using Replicate API and upload it to Cloudinary
    
    Args:
        prompt (str): The text prompt for image generation
        aspect_ratio (str): Aspect ratio for the image (default: "1:1")
        public_id (str): Optional custom public ID for Cloudinary
        folder (str): Folder to store the image in Cloudinary
    
    Returns:
        str: Cloudinary URL of the uploaded image, or None if failed
    """
    try:
        print(f"Generating image with prompt: {prompt}")
        
        # Generate image using Replicate
        # image_url = generate_replicate_image(prompt, aspect_ratio)
        
        # if not image_url:
        #     print("Failed to generate image with Replicate")
        #     return None
        
        # print(f"Image generated successfully: {image_url}")
        
        # # Upload to Cloudinary
        # upload_result = cloudinary_utils.upload_image_from_url(
        #     image_url, 
        #     public_id=public_id,
        #     folder=folder
        # )
        image_path = generate_replicate_image(prompt, aspect_ratio)
        
        if not image_path:
            print("Failed to generate image with Replicate")
            return None
        
        # upload to cloudinary
        upload_result = cloudinary_utils.upload_image_from_file(
            image_path,
            public_id=public_id,
            folder=folder
        )
        
        
        if not upload_result:
            print("Failed to upload image to Cloudinary")
            return None
        
        print(f"Image uploaded to Cloudinary: {upload_result['secure_url']}")
        return upload_result['secure_url']
        
    except Exception as e:
        print(f"Error in generate_image: {e}")
        return None



# print(generate_image("A man dancing in a car"))

