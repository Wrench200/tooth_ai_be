from setup import api_token
import requests




url = "https://api.replicate.com/v1/models/google/imagen-4/predictions"
headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json",
    "Prefer": "wait"
}


def generate_replicate_image(prompt, aspect_ratio="1:1"):

    data = {
        "input": {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "safety_filter_level": "block_medium_and_above"
        }
    }
    response = requests.post(url, headers=headers, json=data)
    
    # if response.status_code == 200:
    #     return response.json()
    # else:
    #     raise Exception(f"Request failed with status {response.status_code}: {response.text}")
    response = response.json()
    return response['output'] if 'output' in response and response['output'] else False



