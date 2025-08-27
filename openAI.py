import requests
import os
import json
import time
from setup import api_token, openai_api_key, gemini_api_key
import functions
import uuid



def get_text_prediction(system_prompt, prompt, max_retries=5, backoff_factor=1, image_input=[]):
    answer = None
    retries = 0

    from setup import gemini_api_key
    import base64
    import mimetypes

    api_key = gemini_api_key
    if not api_key:
        print("GEMINI_API_KEY not set in environment.")
        return None

    model = "gemini-2.5-flash"
    # model = "gemini-2.5-pro"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    while (answer is None or answer == "") and retries < max_retries:
        try:
            parts = []
            parts.append({"text": prompt})

            # Prepare image inputs as inline_data (supports file paths, data URIs, or URLs)
            inputs = image_input
            if isinstance(inputs, str):
                inputs = [inputs]
            if isinstance(inputs, list):
                for item in inputs:
                    try:
                        if isinstance(item, str) and os.path.isfile(item):
                            mime_type = mimetypes.guess_type(item)[0] or "image/jpeg"
                            with open(item, "rb") as f:
                                raw = f.read()
                            b64_data = base64.b64encode(raw).decode("ascii")
                            parts.append({"inline_data": {"mime_type": mime_type, "data": b64_data}})
                        elif isinstance(item, str) and item.startswith("data:") and "," in item:
                            header, b64 = item.split(",", 1)
                            mime_type = header.split(";")[0][5:] if header.startswith("data:") else "image/jpeg"
                            parts.append({"inline_data": {"mime_type": mime_type, "data": b64}})
                        elif isinstance(item, str) and item.startswith("http"):
                            resp = requests.get(item, timeout=30)
                            resp.raise_for_status()
                            mime_type = resp.headers.get("Content-Type") or "image/jpeg"
                            b64_data = base64.b64encode(resp.content).decode("ascii")
                            parts.append({"inline_data": {"mime_type": mime_type, "data": b64_data}})
                    except Exception as _:
                        continue

            payload = {
                "system_instruction": {
                    "parts": [{"text": system_prompt}]
                },
                "contents": [
                    {
                        "parts": parts
                    }
                ],
                "generationConfig": {
                    "temperature": 1,
                    "topP": 1,
                    "maxOutputTokens": 4096,
                    # "thinkingConfig": {
                    #     "thinkingBudget": 0
                    # }
                }
            }

            headers_local = {
                "x-goog-api-key": api_key,
                "Content-Type": "application/json",
            }

            response = requests.post(url, headers=headers_local, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            answer = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            answer = None
        except json.JSONDecodeError:
            print("Failed to decode JSON response.")
            answer = None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            answer = None

        if answer is None or answer == "":
            retries += 1
            sleep_time = backoff_factor * (2 ** (retries - 1))
            print(f"Retrying in {sleep_time} seconds... (Attempt {retries}/{max_retries})")
            time.sleep(sleep_time)

    return answer




def validate_answer(question, answer):
    systemPrompt = 'You are a question and answer validation bot, all you do is validate the answer against the question. You are supposed to check if the answer is relevant for the question. If the answer is relevant even in any way, just respond with a json {"error": false, "message": "passed"}, if the answer is absolutely not relevant to the question, output a json in the format {"error": true, "message": "explanation"} Make sure to add an explanation in the place of explanation. The explanation should be very brief and straigth forward, as to what the issue with the answer is, only add small suggestions when necessary. Make sure to not over write. Make sure to only give simple easy to understand and brief explanations. Your explanation is addressed to the user, so make sure to use a friendly tone. Do not paraphrase the question or the answer in your response. We need the answers to at least answer the question and give us some information. We need the information that we are requesting from the user. Make sure to explain exactly how the answer is not relevant to the question, and provide a small guide when necessary'
    
    prompt = f"Here's the question >>> {question} <<<, and here is the users answer >>> {answer} <<<, validate it"
    print(f"Prompt: {prompt}")
    validation = get_text_prediction(systemPrompt, prompt)
    
    # Try to extract JSON from the response
    if isinstance(validation, str):
        start = validation.find('{')
        end = validation.rfind('}') + 1
        if start != -1 and end != -1:
            json_str = validation[start:end]
            try:
                result = json.loads(json_str)
                # Ensure required keys
                if not isinstance(result, dict):
                    print(f"validate_answer: Parsed JSON is not a dict: {result}")
                    return {"error": True, "message": "Validation response was not a JSON object.", "raw": validation}
                if "error" not in result or "message" not in result:
                    print(f"validate_answer: Missing keys in result: {result}")
                    return {"error": True, "message": "Validation response missing required keys.", "raw": result}
                return result
            except json.JSONDecodeError as e:
                print(f"validate_answer: JSON decode error: {e}")
                print(f"validate_answer: String that failed to parse: {json_str}")
                return {"error": True, "message": "Validation response was not valid JSON.", "raw": json_str}
        else:
            print("validate_answer: No JSON found in validation response")
            return {"error": True, "message": "No JSON found in validation response.", "raw": validation}
    else:
        print(f"validate_answer: Unexpected type for validation: {type(validation)}")
        return {"error": True, "message": "Validation response was not a string.", "raw": str(validation)}




def generate_image(prompt, images = [], max_retries=5, backoff_factor=1):
    """
    Generate an edited image using Google's image edits API with multiple input images.
    Args:
        prompt (str): The prompt describing the desired edit.
        images (list): List of file paths to images to upload as references.
    Returns:
        str: Path to the saved output image, or error message.
    """
    answer = None
    retries = 0

    from setup import gemini_api_key
    import base64
    import mimetypes

    api_key = gemini_api_key
    if not api_key:
        print("GEMINI_API_KEY not set in environment.")
        return None

    model = "gemini-2.5-flash-image-preview"
    # model = "gemini-2.5-pro"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    while (answer is None or answer == "") and retries < max_retries:
        try:
            parts = []
            parts.append({"text": prompt})

            # Prepare image inputs as inline_data (supports file paths, data URIs, or URLs)
            inputs = images
            if isinstance(inputs, str):
                inputs = [inputs]
            if isinstance(inputs, list):
                for item in inputs:
                    try:
                        if isinstance(item, str) and os.path.isfile(item):
                            mime_type = mimetypes.guess_type(item)[0] or "image/jpeg"
                            with open(item, "rb") as f:
                                raw = f.read()
                            b64_data = base64.b64encode(raw).decode("ascii")
                            parts.append({"inline_data": {"mime_type": mime_type, "data": b64_data}})
                        elif isinstance(item, str) and item.startswith("data:") and "," in item:
                            header, b64 = item.split(",", 1)
                            mime_type = header.split(";")[0][5:] if header.startswith("data:") else "image/jpeg"
                            parts.append({"inline_data": {"mime_type": mime_type, "data": b64}})
                        elif isinstance(item, str) and item.startswith("http"):
                            resp = requests.get(item, timeout=30)
                            resp.raise_for_status()
                            mime_type = resp.headers.get("Content-Type") or "image/jpeg"
                            b64_data = base64.b64encode(resp.content).decode("ascii")
                            parts.append({"inline_data": {"mime_type": mime_type, "data": b64_data}})
                    except Exception as _:
                        continue

            payload = {
                # "system_instruction": {
                #     "parts": [{"text": system_prompt}]
                # },
                "contents": [
                    {
                        "parts": parts
                    }
                ],
                # "generationConfig": {
                #     "temperature": 1,
                #     "topP": 1,
                #     "maxOutputTokens": 4096,
                #     "thinkingConfig": {
                #         "thinkingBudget": 0
                #     }
                # }
            }

            headers_local = {
                "x-goog-api-key": api_key,
                "Content-Type": "application/json",
            }

            response = requests.post(url, headers=headers_local, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            # answer = data
            # Extract image data from response
            parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            image_b64 = None
            for part in parts:
                if isinstance(part, dict) and "inlineData" in part:
                    image_b64 = part["inlineData"].get("data")
                    break
            if image_b64:
                images_dir = "images"
                if not os.path.exists(images_dir):
                    os.makedirs(images_dir)
                out_path = f"{images_dir}/{uuid.uuid4()}.png"
                with open(out_path, "wb") as f:
                    f.write(base64.b64decode(image_b64))
                answer = out_path
            else:
                print("No image data found in response.")
                answer = None
            
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            answer = None
        except json.JSONDecodeError:
            print("Failed to decode JSON response.")
            answer = None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            answer = None

        if answer is None or answer == "":
            retries += 1
            sleep_time = backoff_factor * (2 ** (retries - 1))
            print(f"Retrying in {sleep_time} seconds... (Attempt {retries}/{max_retries})")
            time.sleep(sleep_time)

    return answer




# def generate_image(prompt, images = []):
#     """
#     Generate an edited image using OpenAI's image edits API with multiple input images.
#     Args:
#         prompt (str): The prompt describing the desired edit.
#         images (list): List of file paths to images to upload as references.
#     Returns:
#         str: Path to the saved output image, or error message.
#     """
#     import requests
#     from requests_toolbelt.multipart.encoder import MultipartEncoder
#     import os
#     OPENAI_API_KEY = openai_api_key
#     if not OPENAI_API_KEY:
#         return "OPENAI_API_KEY not set in environment."
#     if not images or not isinstance(images, list):
#         return "No images provided."
#     url = "https://api.openai.com/v1/images/edits"
#     fields = {
#         "model": "gpt-image-1",
#         "prompt": prompt,
#     }
#     # Add each image as image[]
    
    
#     image_files = []
#     for img_path in images:
#         if not os.path.isfile(img_path):
#             return f"Image file not found: {img_path}"
#         image_files.append((os.path.basename(img_path), open(img_path, "rb"), "image/png"))
#     if len(image_files) == 1:
#         fields["image[]"] = image_files[0]
#     else:
#         fields["image[]"] = image_files
        
        
#     m = MultipartEncoder(fields=fields)
#     headers = {
#         "Authorization": f"Bearer {OPENAI_API_KEY}",
#         "Content-Type": m.content_type
#     }
#     try:
#         response = requests.post(url, headers=headers, data=m, timeout=500)
#         response.raise_for_status()
#         result = response.json()
#         # Expecting .data[0].b64_json
#         b64 = result.get("data", [{}])[0].get("b64_json")
#         if not b64:
#             return f"No image data returned: {result}"
#         import base64
#         out_path = f"images/{uuid.uuid4()}.png"
#         with open(out_path, "wb") as f:
#             f.write(base64.b64decode(b64))
#         # Close all opened files
#         for _, file_obj, _ in image_files:
#             file_obj.close()
#         return out_path
#     except Exception as e:
#         return f"Error: {e}"






# print(generate_image("Use this logo to make a tshirt, then make another image with it on a hoodie", ["Picsart_25-08-09_17-53-58-624.png"]))

    





system_prompt = "You are a brand identity expert. here is a list of questions we asked the user and here are the answers they gave: >>>" + ''''<<<. You are supposed to generate the communication for the brand as a json of this format >>> 
{
    "about_the_brand": sss,
    "logos": [
        {
            "prompt": sss,
            "description": sss
        },
        {
            "prompt": sss,
            "description": sss
        },
        {
            "prompt": sss,
            "description": sss
        }
    ],
    "primary_colors": lll (list format sample: {
            "color_name": "Dark Blue",
            "hex_value": "#0033cc",
            "description": "The primary color representing trust and professionalism."
        }), 
    "secondary_colors": lll (list format sample: {
            "color_name": "Accent Orange",
            "hex_value": "#ff6600",
            "description": "An accent color used for highlights and calls to action."
        }),
    "typography": lll (list format sample: {
        "font_family": "Open Sans",
        "font_weight": "Regular",
        "font_size": "16px",
        "line_height": "1.5",
        "description": "The primary font for body text, ensuring readability and clarity."
    }),
    "applications": lll (list sample: {
        "application_type": "Website",
        "prompt": sss,
    })
} <<< For the logo prompts, make sure to write a detailed description of the logo for the best result, straight forward detailed instructions that will yield the best result for an AI image generation model to use, the logos should be very professional, creative and attrative, no simple logos or empty logos, just logos that are straight up creative and very good, either with an icon, or decorated initials or any other, be creative, specify the brand name, also mention the tagline, if necessary, not all logos should have a tagline under. Brand name: '''+ ''', tagline: '''+'''. The application prompt is to illustrate a couple items like shirts, mugs or the like, with the logo on them, put between 3 to 5 applications, be very detailed about where to put the logo, size, position and the like, on the object, we are passing the logo along with this prompt so be direct and just tell the ai what to do with the logo, the application prompt is standalone, and carries all details, it is supposed to prompt the model to generate the item, describing the item and its evironment in full detail, as well as where to put the logo, do not use words that other AI's will think are sensitive. Make sure each font object in the list of fonts has just one font. Make sure to generate the values for the different parts. Replace sss with the string values you generate and lll with a list. Make sure you replace sss with strings. Do not use any other format or add any other information. Make sure to generate the values for the different parts, using information from the questions and answers. Make sure to respect the json format and do not add any other information. Be more elaborate with the responses, dont be too brief. Make it sound legit and good. Your resonses should not just be single sentences. Try to write a paragraph of valuable information sometimes. Sound more human as possible. Make it serious and not just rushed'''
        
prompt = "Please give me the communication for my brand as json, and make sure to fill the information in the json as pecified"
# response = get_text_prediction(system_prompt, prompt)
# print(response)

# print(get_text_prediction("You are a cat", "What do you see?", image_input=[r"C:\Users\kumra\Desktop\Work\Customers\Tooth AI\app 4\images\A_man_dancing_in_a_car_1755069107.png"]))
