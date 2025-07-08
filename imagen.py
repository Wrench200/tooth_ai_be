from setup import api_token
import requests
import time




url = "https://api.replicate.com/v1/models/google/imagen-4/predictions"
headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json",
    "Prefer": "wait"
}


def generate_replicate_image(prompt, aspect_ratio="1:1", max_retries=5, backoff_factor=1):
    retries = 0
    while retries < max_retries:
        data = {
            "input": {
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "safety_filter_level": "block_medium_and_above"
            }
        }
        try:
            response = requests.post(url, headers=headers, json=data, timeout=120) # Increased timeout for image generation
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            
            result = response.json()
            return result["output"] if "output" in result and result["output"] else False
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





