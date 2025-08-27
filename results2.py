import os
import db
import questions
import openAI
import json
import imagen
import functions
import uuid
import setup
import textOnImage
import cloudinary_utils
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

# Function to check keys
def check_keys(data, expected_structure):
    # Handle None data
    if data is None:
        print("Error: Received None data instead of JSON object")
        return False
    
    all_keys_present = True
    for section, keys in expected_structure.items():
        if section not in data:
            print(f"Missing section: {section}")
            all_keys_present = False
        else:
            # Special handling for 'logos' which is a list of dicts
            if section == "logos":
                if not isinstance(data[section], list) or len(data[section]) == 0:
                    print(f"'logos' section is not a non-empty list")
                    all_keys_present = False
                else:
                    for i, logo in enumerate(data[section]):
                        for key in keys:
                            if key not in logo:
                                print(f"Missing key '{key}' in logo {i}")
                                all_keys_present = False
            else:
                for key in keys:
                    if key not in data[section]:
                        print(f"Missing key in '{section}': {key}")
                        all_keys_present = False
    return all_keys_present


def clean_and_parse_json(raw_response):
    """
    Cleans the raw output from an LLM and parses it into a Python dictionary.
    Handles responses that are lists of strings or strings with markdown fences.
    """
    if not raw_response:
        print("Warning: Received empty or None response")
        return None
    
    print(f"Cleaning response of type: {type(raw_response)}")
    full_string = "".join(raw_response) if isinstance(raw_response, list) else str(raw_response)
    print(f"Full string length: {len(full_string)}")
    print(f"First 200 chars: {full_string[:200]}")
    
    start_index = full_string.find('{')
    end_index = full_string.rfind('}')
    
    print(f"JSON start index: {start_index}, end index: {end_index}")
    
    if start_index == -1 or end_index == -1:
        print("Warning: Could not find a JSON object in the response.")
        print(f"Available content: {full_string}")
        return None
    
    json_string = full_string[start_index : end_index + 1]
    print(f"Extracted JSON string: {json_string[:200]}...")
    
    try:
        parsed_json = json.loads(json_string)
        print(f"Successfully parsed JSON with keys: {list(parsed_json.keys()) if isinstance(parsed_json, dict) else 'Not a dict'}")
        return parsed_json
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON after cleaning: {e}")
        print(f"Problematic JSON string: {json_string}")
        return None

def _generate_brand_strategy(question_and_answers):
    system_prompt = "You are a branding strategy expert. here is a list of questions we asked the user and here are the answers they gave: >>>" + question_and_answers + '''<<<. You are supposed to generate the brand strategy  for the user as a json of this format >>> 
    {
        "our_purpose": {
            "title": "Our Purpose",
            "what_our_customers_mean_to_us": sss,
            "we_believe_in_something_bigger_than_ourselves": sss,
            "purpose_statement": sss,
        },
        "our_vision": {
            "our_vision_is_bright": sss,
        },
        "our_mission": {
            "we_are_committed_to": sss,
        },
        "our_values": {
            "how_we_do_wellness_business": sss,
            "values": lll
        }
    } <<< Make sure to generate the values for the different parts. Replace sss with the values you generate and lll with a list of values. Make sure you replace sss with strings. Do not use any other format or add any other information. Make sure to generate the values for the different parts, using information from the questions and answers. Make sure to respect the json format and do not add any other information. Be more elaborate with the responses, dont be too brief. Make it sound legit and good. Your resonses should not just be single sentences. Try to write a paragraph of valuable information sometimes. Sound more human as possible. Make it serious and not just rushed. For the mission  and vision, you MUST not write more than a sentence, make the mission and vision straight to the point.'''
            
    prompt = "Please give me my branding strategy as json, and make sure to fill the information in the json as pecified"

    passed = False
    response = None
    while passed == False:
        print("Processing section ...")
        response = openAI.get_text_prediction(system_prompt, prompt)
        response = clean_and_parse_json(response)
        # Define the expected structure
        expected_structure = {
            "our_purpose": ["title", "what_our_customers_mean_to_us", "purpose_statement"],
            "our_vision": ["our_vision_is_bright"],
            "our_mission": ["we_are_committed_to"],
            "our_values": ["how_we_do_wellness_business", "values"]
        }
        
        if check_keys(response, expected_structure):
            passed = True
            print("Section success \n\n")
        else:
            print("Error in response format. Retrying...")
    return response

def _generate_customer_profile(question_and_answers):
    system_prompt = "You are a customer profile expert. here is a list of questions we asked the user and here are the answers they gave: >>>" + question_and_answers + '''<<<. You are supposed to generate a sample customer profile for the brand as a json of this format >>> 
    {
        "name": sss,
        "demographics": sss,
        "psychographics": sss,
        "personality": sss,
        "fears": sss,
        "desires": sss,
        "challenges_and_pain_points": sss,
    } <<< Make sure to generate the values for the different parts. Replace sss with the string values you generate. Make sure you replace sss with strings. Do not use any other format or add any other information. Make sure to generate the values for the different parts, using information from the questions and answers. Make sure to respect the json format and do not add any other information. Be more elaborate with the responses, dont be too brief. Make it sound legit and good. Your resonses should not just be single sentences. Try to write a paragraph of valuable information sometimes. Sound more human as possible. Make it serious and not just rushed'''
            
    prompt = "Please give me a sample customer profile as json, and make sure to fill the information in the json as pecified"
    
    passed = False
    response = None
    while passed == False:
        print("Processing section ...")
        response = openAI.get_text_prediction(system_prompt, prompt)
        response = clean_and_parse_json(response)
        # Define the expected structure
        expected_structure = {
            "name": [],
            "demographics": [],
            "psychographics": [],
            "personality": [],
            "fears": [],
            "desires": [],
            "challenges_and_pain_points": []
        }
        
        if check_keys(response, expected_structure):
            passed = True
            print("Section success \n\n")
        else:
            print("Error in response format. Retrying...")
    return response

def _generate_competitors(question_and_answers):
    system_prompt = "You are a competitor profile expert. here is a list of questions we asked the user and here are the answers they gave: >>>" + question_and_answers + "<<< Be more elaborate with the responses, dont be too brief. Make it sound legit and good. Your resonses should not just be single sentences. Try to write a paragraph of valuable information. Sound more human as possible. Make it serious and not just rushed"
                    
    prompt = "Please give me a profile of my top competitors as a string. Do not style it. Do not add any syntax. Just a paragraph of text. No labeling please."
    
    print("Processing section ...")
    response = openAI.get_text_prediction(system_prompt, prompt)
    print("Section success \n\n")
    return response

def _generate_differentiators(question_and_answers):
    system_prompt = "You are a branding expert. here is a list of questions we asked the user and here are the answers they gave: >>>" + question_and_answers + '''<<<. You are supposed to generate the reasons that make the brand different as a json of this format >>> 
    {
        "the_difference_we_provide": sss,
        "positioning_statement": sss,
    }
    <<< Make sure to generate the values for the different parts. Replace sss with the string values you generate. Make sure you replace sss with strings. Do not use any other format or add any other information. Make sure to generate the values for the different parts, using information from the questions and answers. Make sure to respect the json format and do not add any other information. Be more elaborate with the responses, dont be too brief. Make it sound legit and good. Your resonses should not just be single sentences. Try to write a paragraph of valuable information sometimes. Sound more human as possible. Make it serious and not just rushed'''
            
    prompt = "Please give me a sample what makes us different as json, and make sure to fill the information in the json as specified"

    passed = False
    response = None
    while passed == False:
        print("Processing section ...")
        response = openAI.get_text_prediction(system_prompt, prompt)
        response = clean_and_parse_json(response)
        # Define the expected structure
        expected_structure = {
            "the_difference_we_provide": [],
            "positioning_statement": []
        }
        
        if check_keys(response, expected_structure):
            passed = True
            print("Section success \n\n")
        else:
            print("Error in response format. Retrying...")
    return response

def _generate_brand_communication(question_and_answers):
    system_prompt = "You are a brand communication expert. here is a list of questions we asked the user and here are the answers they gave: >>>" + question_and_answers + '''<<<. You are supposed to generate the communication for the brand as a json of this format >>> 
    {
        "brand_name": sss (You MUST use the brand name specified by the user in the answers),
        "brand_tagline": sss,
        "primary_core_message": {
            "who_we_serve": sss,
            "where_they_need_help": sss,
            "the_key_benefits_they_get": sss,
            "their_market_alternative": sss,
            "our_key_differences": sss,
        },
    } <<< Make sure to generate the values for the different parts. Replace sss with the string values you generate. Make sure you replace sss with strings. Do not use any other format or add any other information. Make sure to generate the values for the different parts, using information from the questions and answers. Make sure to respect the json format and do not add any other information. Be more elaborate with the responses, dont be too brief. Make it sound legit and good. Your resonses should not just be single sentences. Try to write a paragraph of valuable information sometimes. Sound more human as possible. Make it serious and not just rushed'''
            
    prompt = "Please give me the communication for my brand as json, and make sure to fill the information in the json as pecified"
    
    passed = False
    response = None
    while passed == False:
        print("Processing section ...")
        response = openAI.get_text_prediction(system_prompt, prompt)
        response = clean_and_parse_json(response)
        # Define the expected structure
        expected_structure = {
            "brand_name": [],
            "brand_tagline": [],
            "primary_core_message": ["who_we_serve", "where_they_need_help", "the_key_benefits_they_get", "their_market_alternative", "our_key_differences"]
        }
        
        if check_keys(response, expected_structure):
            passed = True
            print("Section success \n\n")
        else:
            print("Error in response format. Retrying...")
    return response

def _generate_brand_identity(question_and_answers, brand_name, brand_tagline):
    system_prompt = "You are a brand identity expert. here is a list of questions we asked the user and here are the answers they gave: >>>" + question_and_answers + '''<<<. You are supposed to generate the communication for the brand as a json of this format >>> 
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
            "application_type": "Tshirt",
            "prompt": sss,
        })
    } <<< For the logo prompts, make sure to write a detailed description of the logo for the best result, straight forward detailed instructions that will yield the best result for an AI image generation model to use, the logos should be very professional, creative and attrative, no simple logos or empty logos, just logos that are straight up creative and very good, either with an icon, or decorated initials or any other, be creative, specify the brand name, also mention the tagline, if necessary, not all logos should have a tagline under. Brand name: '''+brand_name+''', tagline: '''+brand_tagline+'''. The application prompt is to illustrate a couple of items like shirts, mugs or the like, with the logo on them, put between 3 to 5 applications, be very detailed about where to put the logo, size, position and the like, on the object, we are passing the logo along with this prompt so be direct and just tell the ai what to do with the logo, the application prompt is standalone, and carries all details, it is supposed to prompt the model to generate the item, describing the item and its evironment in full detail, as well as where to put the logo, do not use words that other AI's will think are sensitive. Make sure to specify presenation styles for the applications, like cinematic, studio lighting, high quality, professional photography, commercial shot and the like... Add as many as possible to make the applications look visually stunning and well presented. Add a lot of details to the applications prompt. Mak sure to put all extremely detailed explanations and styles in the application prompts. Make sure each font object in the list of fonts has just one font. Make sure to generate the values for the different parts. Replace sss with the string values you generate and lll with a list. Make sure you replace sss with strings. Do not use any other format or add any other information. Make sure to generate the values for the different parts, using information from the questions and answers. Make sure to respect the json format and do not add any other information. Be more elaborate with the responses, dont be too brief. Make it sound legit and good. Your resonses should not just be single sentences. Try to write a paragraph of valuable information sometimes. Sound more human as possible. Make it serious and not just rushed'''
            
    prompt = "Please give me the identity for my brand as json, and make sure to fill the information in the json as pecified"
    
    passed = False
    max_retries = 3
    retry_count = 0
    response = None
    
    while passed == False and retry_count < max_retries:
        print(f"Processing section (attempt {retry_count + 1}/{max_retries})...")
        try:
            raw_response = openAI.get_text_prediction(system_prompt, prompt)
            print(f"Raw API response type: {type(raw_response)}")
            print(f"Raw API response: {raw_response[:200]}..." if raw_response else "Raw API response: None")
            
            response = clean_and_parse_json(raw_response)
            print(f"Parsed response: {response}")
            
            # Define the expected structure
            expected_structure = {
                "about_the_brand": [],
                "logos": ["prompt", "description"],
                "primary_colors": [],
                "secondary_colors": [],
                "typography": [],
                "applications": []
            }
            
            if response is None:
                print("Error: API response could not be parsed as JSON")
                retry_count += 1
                continue
                
            if check_keys(response, expected_structure):
                passed = True
                print("Section success \n\n")
            else:
                print("Error in response format. Retrying...")
                retry_count += 1
        except Exception as e:
            print(f"Exception during processing: {e}")
            retry_count += 1
    
    if not passed:
        print(f"Failed to process section after {max_retries} attempts. Using default values.")
        # Set default values to prevent further errors
        response = {
            "about_the_brand": "Default brand description",
            "logos": [{"prompt": "A simple, professional logo design", "description": "Default logo description 1"}],
            "primary_colors": [],
            "secondary_colors": [],
            "typography": [],
            "applications": []
        }
    return response

def generate_results(userId, brandId):
    images_dir = 'images'
    try:
        user = db.get_user(userId)
        brand = db.get_brand(brandId)
        answers = db.get_answer(brand["answerid"])
        
        previous_questions = questions.get_previous_questions(11)
        previous_answers = db.get_previous_answers(answers["answerId"], 11)
        question_and_answers = " ".join([f"Question: {q} Answer: {a}." for q, a in zip(previous_questions, previous_answers)])
        # print(f"\n\nPrevious Q and A: {question_and_answers}\n\n")
        # return
        
        brand_strategy_data = {}
        customer_profile_data = {}
        competitors_data = ""
        differentiators_data = {}
        brand_communication_data = {}
        brand_identity_data = {}

        with ThreadPoolExecutor() as executor:
            future_to_task = {
                executor.submit(_generate_brand_strategy, question_and_answers): "brand_strategy",
                executor.submit(_generate_customer_profile, question_and_answers): "customer_profile",
                executor.submit(_generate_competitors, question_and_answers): "competitors",
                executor.submit(_generate_differentiators, question_and_answers): "differentiators",
                executor.submit(_generate_brand_communication, question_and_answers): "brand_communication",
            }

            brand_communication_future = next(future for future, name in future_to_task.items() if name == "brand_communication")
            brand_communication_data = brand_communication_future.result()
            brand_name = brand_communication_data.get("brand_name", "")
            brand_tagline = brand_communication_data.get("brand_tagline", "")

            future_to_task[executor.submit(_generate_brand_identity, question_and_answers, brand_name, brand_tagline)] = "brand_identity"

            for future in as_completed(future_to_task):
                task_name = future_to_task[future]
                try:
                    data = future.result()
                    if task_name == "brand_strategy":
                        brand_strategy_data = data
                    elif task_name == "customer_profile":
                        customer_profile_data = data
                    elif task_name == "competitors":
                        competitors_data = data
                    elif task_name == "differentiators":
                        differentiators_data = data
                    elif task_name == "brand_identity":
                        brand_identity_data = data
                except Exception as exc:
                    print(f'{task_name} generated an exception: {exc}')

        what_our_customers_mean_to_us = brand_strategy_data.get("our_purpose", {}).get("what_our_customers_mean_to_us", "")
        we_believe_in_something_bigger_than_ourselves = brand_strategy_data.get("our_purpose", {}).get("we_believe_in_something_bigger_than_ourselves", "")
        purpose_statement = brand_strategy_data.get("our_purpose", {}).get("purpose_statement", "")
        our_vision_is_bright = brand_strategy_data.get("our_vision", {}).get("our_vision_is_bright", "")
        we_are_committed_to = brand_strategy_data.get("our_mission", {}).get("we_are_committed_to", "")
        how_we_do_wellness_business = brand_strategy_data.get("our_values", {}).get("how_we_do_wellness_business", "")
        values = brand_strategy_data.get("our_values", {}).get("values", [])
        
        position_name = customer_profile_data.get("name", "")
        demographics = customer_profile_data.get("demographics", "")
        psychographics = customer_profile_data.get("psychographics", "")
        personality = customer_profile_data.get("personality", "")
        fears = customer_profile_data.get("fears", "")
        desires = customer_profile_data.get("desires", "")
        challenges_and_pain_points = customer_profile_data.get("challenges_and_pain_points", "")

        top_competitors = competitors_data

        the_difference_we_provide = differentiators_data.get("the_difference_we_provide", "")
        position_statement = differentiators_data.get("positioning_statement", "")

        who_we_serve = brand_communication_data.get("primary_core_message", {}).get("who_we_serve", "")
        where_they_need_help = brand_communication_data.get("primary_core_message", {}).get("where_they_need_help", "")
        the_key_benefits_they_get = brand_communication_data.get("primary_core_message", {}).get("the_key_benefits_they_get", "")
        their_market_alternative = brand_communication_data.get("primary_core_message", {}).get("their_market_alternative", "")
        our_key_differences = brand_communication_data.get("primary_core_message", {}).get("our_key_differences", "")

        about_the_brand = brand_identity_data.get("about_the_brand", "")
        logos_list = brand_identity_data.get("logos", [])
        logo_prompt_1 = logos_list[0].get("prompt", "") if len(logos_list) > 0 else ""
        logo_prompt_2 = logos_list[1].get("prompt", "") if len(logos_list) > 1 else ""
        logo_prompt_3 = logos_list[2].get("prompt", "") if len(logos_list) > 2 else ""
        logo_description_1 = logos_list[0].get("description", "") if len(logos_list) > 0 else ""
        logo_description_2 = logos_list[1].get("description", "") if len(logos_list) > 1 else ""
        logo_description_3 = logos_list[2].get("description", "") if len(logos_list) > 2 else ""
        primary_colors = brand_identity_data.get("primary_colors", [])
        secondary_colors = brand_identity_data.get("secondary_colors", [])
        typography = brand_identity_data.get("typography", [])
        applications = brand_identity_data.get("applications", [])

        # Generate 3 logos and upload to Cloudinary in parallel
        try:
            print("Generating 3 logos and uploading to Cloudinary...")
            def generate_logo_url(prompt, idx):
                url = imagen.generate_image(prompt, public_id=f"toothai/{brandId}/logo_{idx}")
                if not url:
                    print(f"Warning: Logo {idx} generation failed, using placeholder")
                    url = f"https://via.placeholder.com/400x200?text=Logo+{idx}"
                return url
            with ThreadPoolExecutor(max_workers=3) as executor:
                future1 = executor.submit(generate_logo_url, logo_prompt_1, 1)
                future2 = executor.submit(generate_logo_url, logo_prompt_2, 2)
                future3 = executor.submit(generate_logo_url, logo_prompt_3, 3)
                logo_image_url_1 = future1.result()
                logo_image_url_2 = future2.result()
                logo_image_url_3 = future3.result()
            print("Logo generation completed successfully")
        except Exception as e:
            print(f"Error during logo generation: {e}")
            print("Using placeholder logos")
            logo_image_url_1 = "https://via.placeholder.com/400x200?text=Logo+1"
            logo_image_url_2 = "https://via.placeholder.com/400x200?text=Logo+2"
            logo_image_url_3 = "https://via.placeholder.com/400x200?text=Logo+3"

        results = {
            "userId": userId,
            "brandId": brandId,
            "brand_strategy": {
                "brand_substance": {
                    "our_purpose": {
                        "title": "Our Purpose",
                        "what_our_customers_mean_to_us": what_our_customers_mean_to_us,
                        "we_believe_in_something_bigger_than_ourselves": we_believe_in_something_bigger_than_ourselves,
                        "purpose_statement": purpose_statement,
                    },
                    "our_vision": {
                        "our_vision_is_bright": our_vision_is_bright,
                    },
                    "our_mission": {
                        "we_are_committed_to": we_are_committed_to,
                    },
                    "our_values": {
                        "how_we_do_wellness_business": how_we_do_wellness_business,
                        "values": values
                    }
                },
                "our_position": {
                    "name": position_name,
                    "demographics": demographics,
                    "psychographics": psychographics,
                    "personality": personality,
                    "fears": fears,
                    "desires": desires,
                    "challenges_and_pain_points": challenges_and_pain_points,
                },
                "top_competitors": top_competitors,
                "why_we_are_different": {
                    "the_difference_we_provide": the_difference_we_provide,
                    "positioning_statement": position_statement,
                }
            },
            "brand_communication": {
                "brand_name": brand_name,
                "brand_tagline": brand_tagline,
                "primary_core_message": {
                    "who_we_serve": who_we_serve,
                    "where_they_need_help": where_they_need_help,
                    "the_key_benefits_they_get": the_key_benefits_they_get,
                    "their_market_alternative": their_market_alternative,
                    "our_key_differences": our_key_differences,
                },
            },
            "brand_identity": {
                "about_the_brand": about_the_brand,
                "logos": [{
                    "image_url": logo_image_url_1,
                    "description": logo_description_1
                },{
                    "image_url": logo_image_url_2,
                    "description": logo_description_2
                },{
                    "image_url": logo_image_url_3,
                    "description": logo_description_3
                }],
                "reommended_logo": "",
                "logo_variants": {},
                "primary_colors": primary_colors,
                "secondary_colors": secondary_colors,
                "typography": typography,
            }
        }
        
        db.update_brand(brandId, "name", brand_name)
        db.update_brand(brandId, "brand_strategy", json.dumps(results["brand_strategy"]))
        db.update_brand(brandId, "brand_communication", json.dumps(results["brand_communication"]))
        db.update_brand(brandId, "brand_identity", json.dumps(results["brand_identity"]))
     
        
        
        
        return results
    except Exception as e:
        print(f"Error in generate_results: {e}")
        import traceback
        traceback.print_exc()
        return {"error": True, "message": str(e)}
    finally:
        # Cleanup: delete the entire images folder and its contents
        try:
            if os.path.exists(images_dir):
                shutil.rmtree(images_dir)
                print(f"Deleted images directory: {images_dir}")
        except Exception as cleanup_error:
            print(f"Error deleting images directory: {cleanup_error}")













































def generate_final_results(userId, brandId, userName, userEmail, userPhoneNumbers, registrationNumber, website, brandLogo, others = {}, custom_colors = None):
    images_dir = 'images'
    try:
        user = db.get_user(userId)
        brand = db.get_brand(brandId)
        
        # Check if brand exists
        if not brand:
            return {"error": True, "message": "Brand not found"}
        
        # Check payment status
        payment_status = db.check_brand_payment_status(brandId)
        if payment_status is None:
            return {"error": True, "message": "Unable to verify payment status"}
        
        if not payment_status:
            return {"error": True, "message": "Payment required. Please complete payment before generating final results."}
        
        # Update logo field in brand table if brandLogo is provided
        if brandLogo:
            try:
                db.update_brand(brandId, "logo", brandLogo)
                print(f"Updated logo for brand {brandId}: {brandLogo}")
            except Exception as e:
                print(f"Error updating logo: {e}")
                # Continue with generation even if logo update fails
        
        answers = db.get_answer(brand["answerid"])
        
        previous_questions = questions.get_previous_questions(11)
        previous_answers = db.get_previous_answers(answers["answerId"], 11)
        question_and_answers = " ".join([f"Question: {q} Answer: {a}." for q, a in zip(previous_questions, previous_answers)])
        
        # Parse previously generated brand identity
        if brand.get("brand_identity"):
            try:
                brand_identity_data = json.loads(brand["brand_identity"]) if isinstance(brand["brand_identity"], str) else brand["brand_identity"]
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Error parsing brand_identity JSON: {e}")
                brand_identity_data = {}
        else:
            brand_identity_data = {}
        
        # Override colors with custom colors if provided
        if custom_colors and isinstance(custom_colors, dict):
            print(f"Using custom colors: {custom_colors}")
            # Create a modified brand identity with custom colors
            modified_brand_identity = brand_identity_data.copy()
            
            # Update primary colors if provided
            if custom_colors.get('primary_colors'):
                modified_brand_identity['primary_colors'] = custom_colors['primary_colors']
                print(f"Updated primary colors: {custom_colors['primary_colors']}")
            
            # Update secondary colors if provided
            if custom_colors.get('secondary_colors'):
                modified_brand_identity['secondary_colors'] = custom_colors['secondary_colors']
                print(f"Updated secondary colors: {custom_colors['secondary_colors']}")
            
            # Update brand colors if provided
            if custom_colors.get('brand_colors'):
                modified_brand_identity['brand_colors'] = custom_colors['brand_colors']
                print(f"Updated brand colors: {custom_colors['brand_colors']}")
            
            previously_generated_brand_identity = modified_brand_identity
        else:
            previously_generated_brand_identity = brand_identity_data
        
        # print(question_and_answers)
        
        
        
        def generate_identity_assets(
            question_and_answers,
            previously_generated_brand_identity,
            brandId,
            system_prompt_template,
            prompt,
            expected_count,
            cloudinary_folder,
            userName=None,
            userEmail=None,
            userPhoneNumbers=None,
            registrationNumber=None,
            website=None,
            brandLogo=None,
            others=None
        ):
            # Add user info to the system prompt for more context
            user_info = (
                f"\nUser Info:\n"
                f"Name: {userName}\n"
                f"Email: {userEmail}\n"
                f"Phone Numbers: {userPhoneNumbers}\n"
                f"Registration Number: {registrationNumber}\n"
                f"Website: {website}\n"
                f"Other Info: {others}\n"
            )
            system_prompt = system_prompt_template.format(
                question_and_answers=question_and_answers,
                previously_generated_brand_identity=str(previously_generated_brand_identity)
            ) + user_info
            print("\n\nProcessing section ...")
            response = openAI.get_text_prediction(system_prompt, prompt)
            print(f"Raw AI response: {response}")
            try:
                prompts = json.loads(response.strip())
                if not isinstance(prompts, list):
                    prompts = [prompts]
            except Exception:
                prompts = [response.strip()]
            assets = []
            for idx, item_prompt in enumerate(prompts[:expected_count]):
                try:
                    print("Generating image ...")
                    # Pass brandLogo as a list if provided, else empty list
                    logo = functions.download_image(brandLogo)
                    images = [logo] if logo else []
                    img = openAI.generate_image(item_prompt, images=images)
                    print(f"Generated image url: {img}")
                    if img and os.path.isfile(img):
                        upload_result = cloudinary_utils.upload_image_from_file(
                            img, folder=f"toothai/{brandId}/{cloudinary_folder}"
                        )
                        url = upload_result["secure_url"] if upload_result and "secure_url" in upload_result else img
                    else:
                        url = img
                    assets.append({"prompt": item_prompt, "image_url": url})
                    print(f"Generated: {url}")
                except Exception as e:
                    print(f"Error generating {cloudinary_folder} {idx+1}: {e}")
            print("Section success \n\n")
            return assets

        # ========== IMAGE GENERATION ENABLED ==========
        # Usage for each asset type, now passing brandLogo:

        brandPatterns = generate_identity_assets(
            question_and_answers,
            previously_generated_brand_identity,
            brandId,
            system_prompt_template=(
                '''You are a brand identity expert. Here is a list of questions we asked the user and here are the answers they gave: >>>"
                "{question_and_answers}"
                "<<<. Here is the previously generated brand identity for this brand (including colors, typography, etc): >>>"
                "{previously_generated_brand_identity}"
                "<<<. Generate 1 unique, visually appealing brand pattern prompt for an AI image generator. The pattern should reflect the brand's personality, colors, and style, and must respect the previously generated brand identity (especially colors, typography, and any other relevant details). Output as a single detailed prompt. Do not add any extra text or formatting. You MUST respond with a single string prompt. '''
            ),
            prompt="Please give me 1 brand pattern prompt.",
            expected_count=1,
            cloudinary_folder="brand_patterns",
            userName=userName,
            userEmail=userEmail,
            userPhoneNumbers=userPhoneNumbers,
            registrationNumber=registrationNumber,
            website=website,
            brandLogo=brandLogo,
            others=others
        )

        business_cards = generate_identity_assets(
            question_and_answers,
            previously_generated_brand_identity,
            brandId,
            system_prompt_template=(
                '''You are a branding expert. Here is a list of questions we asked the user and here are the answers they gave: >>>"
                "{question_and_answers}"
                "<<<. Here is the previously generated brand identity for this brand (including colors, typography, etc): >>>"
                "{previously_generated_brand_identity}"
                "<<<. Generate 1 highly detailed prompt for an AI image generator to create a business card mockup for the brand. The prompt should specify the brand name, tagline, colors, and style, and must respect the previously generated brand identity (especially colors, typography, and any other relevant details). Output as a single prompt. No extra text. You MUST respond with a single string prompt. '''
            ),
            prompt="Please give me 1 business card prompt.",
            expected_count=1,
            cloudinary_folder="business_cards",
            userName=userName,
            userEmail=userEmail,
            userPhoneNumbers=userPhoneNumbers,
            registrationNumber=registrationNumber,
            website=website,
            brandLogo=brandLogo,
            others=others
        )

        letterheads = generate_identity_assets(
            question_and_answers,
            previously_generated_brand_identity,
            brandId,
            system_prompt_template=(
                '''You are a branding expert. Here is a list of questions we asked the user and here are the answers they gave: >>>"
                "{question_and_answers}"
                "<<<. Here is the previously generated brand identity for this brand (including colors, typography, etc): >>>"
                "{previously_generated_brand_identity}"
                "<<<. Generate 1 detailed prompt for an AI image generator to create a letterhead mockup for the brand. Specify brand name, logo, colors, and layout, and must respect the previously generated brand identity (especially colors, typography, and any other relevant details). Output as a single prompt string. You MUST respond with a list of strings in angle braces, in this format: ["prompt1", "prompt2"]. '''
            ),
            prompt="Please give me a letterhead prompt as a string.",
            expected_count=1,
            cloudinary_folder="letterheads",
            userName=userName,
            userEmail=userEmail,
            userPhoneNumbers=userPhoneNumbers,
            registrationNumber=registrationNumber,
            website=website,
            brandLogo=brandLogo,
            others=others
        )

        tshirt_mockups = generate_identity_assets(
            question_and_answers,
            previously_generated_brand_identity,
            brandId,
            system_prompt_template=(
                '''You are a branding expert. Here is a list of questions we asked the user and here are the answers they gave: >>>"
                "{question_and_answers}"
                "<<<. Here is the previously generated brand identity for this brand (including colors, typography, etc): >>>"
                "{previously_generated_brand_identity}"
                "<<<. Generate 1 detailed prompt for an AI image generator to create a t-shirt mockup for the brand. Specify logo placement, colors, and style, and must respect the previously generated brand identity (especially colors, typography, and any other relevant details). Output as a single prompt. You MUST respond with a single string prompt. '''
            ),
            prompt="Please give me 1 t-shirt mockup prompt.",
            expected_count=1,
            cloudinary_folder="tshirt_mockups",
            userName=userName,
            userEmail=userEmail,
            userPhoneNumbers=userPhoneNumbers,
            registrationNumber=registrationNumber,
            website=website,
            brandLogo=brandLogo,
            others=others
        )

        cap_mockups = generate_identity_assets(
            question_and_answers,
            previously_generated_brand_identity,
            brandId,
            system_prompt_template=(
                '''You are a branding expert. Here is a list of questions we asked the user and here are the answers they gave: >>>"
                "{question_and_answers}"
                "<<<. Here is the previously generated brand identity for this brand (including colors, typography, etc): >>>"
                "{previously_generated_brand_identity}"
                "<<<. Generate 1 detailed prompt for an AI image generator to create a cap mockup for the brand. Specify logo placement, colors, and style, and must respect the previously generated brand identity (especially colors, typography, and any other relevant details). Output as a single prompt string. You MUST respond with a list of strings in angle braces, in this format: ["prompt1", "prompt2"]. '''
            ),
            prompt="Please give me a cap mockup prompt as a string.",
            expected_count=1,
            cloudinary_folder="cap_mockups",
            userName=userName,
            userEmail=userEmail,
            userPhoneNumbers=userPhoneNumbers,
            registrationNumber=registrationNumber,
            website=website,
            brandLogo=brandLogo,
            others=others
        )

        signboards = generate_identity_assets(
            question_and_answers,
            previously_generated_brand_identity,
            brandId,
            system_prompt_template=(
                '''You are a branding expert. Here is a list of questions we asked the user and here are the answers they gave: >>>"
                "{question_and_answers}"
                "<<<. Here is the previously generated brand identity for this brand (including colors, typography, etc): >>>"
                "{previously_generated_brand_identity}"
                "<<<. Generate 1 detailed prompt for an AI image generator to create a signboard mockup for the brand. Specify logo, colors, and style, and must respect the previously generated brand identity (especially colors, typography, and any other relevant details). Output as a single prompt string. You MUST respond with a list of strings in angle braces, in this format: ["prompt1", "prompt2"]. '''
            ),
            prompt="Please give me a signboard mockup prompt as a string.",
            expected_count=1,
            cloudinary_folder="signboards",
            userName=userName,
            userEmail=userEmail,
            userPhoneNumbers=userPhoneNumbers,
            registrationNumber=registrationNumber,
            website=website,
            brandLogo=brandLogo,
            others=others
        )

        # ========== Generate Social Media Content ==========
        print("Generating social media content...")
        
        social_media_json_structure = {
            "ready_made_posts": [
                "string"
            ],
            "ad_copies": [
                "string"
            ],
            "relevant_marketing_strategies": [
                "string"
            ]
        }
        system_prompt = (
            f'''You are a social media content expert. Here is a list of questions we asked the user and here are the answers they gave: >>>
            {question_and_answers} 
            <<<. Generate social media content for the brand in the following JSON structure:
            {json.dumps(social_media_json_structure, indent=2)}
            - ready_made_posts: 6 objects, each with a 'caption' and a 'design_concept'.\n"
            "- ad_copies: 3 creative ad copy strings.\n"
            "- relevant_marketing_strategies: 3 relevant marketing strategies as strings.\n"
            "Do not add any extra text or formatting. Only output valid JSON.
            
            This is a sample post:
            1-  Hello World, Meet Lumirural 🌍✨
            Say hello to Lumirural — a bold new initiative built to light up lives, one village at a time.
            In many rural communities, nightfall means silence, stillness, and struggle. No lights to read. No safe path to walk. No way to keep going.
            We created Lumirural to change that.
            At [Insert Founder's Name]'s core vision was a simple question:
            👉 What if every household, no matter how remote, had access to affordable, clean, and reliable light?
            That question sparked a movement — one that's now empowering families, improving education, and making communities safer through sustainable solar-powered lighting.
            We're not just selling torches.
            We're giving people the ability to live, learn, work, and thrive after dark.
            💛 Follow us to join the journey.
            🌱 Tell a friend in need.
            🔦 Let's bring light to where it matters most.
            #Lumirural #LightingUpLives #SolarForAll #CommunityPower

            2- 👥 Meet the Visionaries Behind Lumirural 🔦🌍
            Behind the scenes of Lumirural is a team passionate about bridging the energy gap in underserved communities across Cameroon and Africa.
            Led by [Founder Name], [brief title e.g. social entrepreneur, engineer, dreamer], Lumirural was born from a deep desire to make sure that no child studies in darkness, and no family is left behind just because they live off the grid.
            Alongside [Team Member 1], [Team Member 2], and an ever-growing community of thinkers, doers, and believers, our mission is simple but powerful:
            Bring light to places the world often overlooks.
            We believe in sustainable energy.
            We believe in community power.
            We believe it's time for rural Africa to shine — literally.
            ✨ This is just the beginning.
            Come along, share our story, and let's brighten the future together.
            #MeetTheTeam #Lumirural #SocialEnergy #FoundersWithPurpose #SolarAfrica

            3- 💡 No Power. No Progress.
            That's the Problem Lumirural is Solving.
            Tired of struggling with darkness in rural homes, kids studying under candlelight, and families closing their day at sunset? So were we.
            That's why we created Lumirural — to bring affordable, clean, and safe solar-powered light to communities that have been left in the dark for far too long.
            Every evening, millions of people across Cameroon and Africa are forced to choose between expensive fuel, dangerous kerosene lamps, or complete darkness.
            We said enough is enough.
            ✅ With Lumirural, children can study at night
            ✅ Small shops can stay open after sunset
            ✅ Women and families can feel safe walking outside
            ✅ Life doesn't have to stop just because the sun sets
            We're lighting homes — but more than that, we're lighting hope.
            Join us as we illuminate the path forward.
            #TheProblemWeSolve #Lumirural #LightUpAfrica #SolarSolutions #EnergyForAll



            4- 🔦 A Closer Look at What's Lighting Up Soon 👀
            Say hello to the tools of transformation — built by Lumirural to power every home, every family, every dream.
            🌞 Solar Lighting Kits
            Affordable, durable, and designed for rural realities — our kits include lights, USB ports, and long-lasting solar panels for families, students, and small businesses.
            📱 Rechargeable Lamps with USB Ports
            For households with zero access to electricity. Charge your phone. Light your path. All in one.
            🔋 Power Stations for Community Use
            Bigger solutions for schools, churches, and health centers — helping entire communities thrive after dark.
            💼 Pay-as-You-Go Solar Options
            Energy shouldn't be a luxury. Our flexible payment plans make light accessible to all.
            From farm to classroom, market to maternity ward, Lumirural is bringing light, safety, and possibility to places the grid forgot.
            This isn't just electricity —
            It's dignity, freedom, and a future that stays on after dark.
            📸 Swipe to see what's coming soon and how you can be part of the change.
            #Lumirural #OurProducts #SolarSolutions #LightChangesEverything #EnergyForDevelopment






            5- 🛠️ The Work Behind the Light ✨
            It's been months of late nights, field visits, dusty roads, power cuts, bold ideas, and real conversations.
            From sketching designs on scrap paper to testing prototypes in remote villages...
            From team brainstorms under torchlight to meeting families who inspired everything we're building...
            Here's a sneak peek behind our launch:
            📸 [Insert photos or videos: packaging, production, team at work, first installations]
            At Lumirural, we're not just assembling solar kits —
            We're co-creating a future where every child can read at night, where mothers can cook safely, and where families no longer fear the dark.
            This journey has been real, raw, and full of purpose.
            And now, we're ready to shine.
            Thank you for being part of the story.
            The lights are coming on — and we're just getting started.
            #BehindLumirural #MakingOf #StartupJourney #LightInTheDark #SolarAfrica #BTSLaunch

            6- 💬 Real Stories. Real Impact.
            Here's what people are already saying about Lumirural…
            🗣️ "Before this light, my children couldn't read after 6pm. Now, they do homework at night — and even help me prepare for market."
            — Mama Elise, Small Business Owner, Babadjou
            🗣️ "I used to charge my phone once a week at a shop far away. Now I charge it at home and even make small money letting others charge theirs."
            — Tata Collins, Farmer, Batibo
            🗣️ "This isn't just light  it's freedom. It's security. It's dignity."
            — Community Health Worker, Ndop
            🌍 From households to health centers, the difference is already being felt — and we're only getting started.
            Because when you give people light, you give them time, safety, and a fighting chance.
            ➡️ Want to be part of the change?
            DM us to get Lumirural in your home or community.
            #TestimonialTuesday #LumiruralVoices #SolarWorks #ImpactInRealLife #LightForChange
            
            
            
            
            
            Here is a sample marketing strategy:
            
            ✅ 1. Community-Based Demonstrations (On-Ground Activation)
            Why it works: Most of your customers may be unfamiliar with solar tech or skeptical of promises. Seeing is believing.
            What to do:
            Partner with local chiefs, churches, health centers, and schools to organize "Light Up" demos.


            Showcase how the products work (especially at night).


            Let a few community members try it out and speak on their experience.


            Offer launch-day discounts or giveaways at the event.


            🎯 Trust is built faster in familiar spaces. Leverage community leaders and peer influence.

            ✅ 2. Agent & Micro-Influencer Network in Rural Zones
            Why it works: Word-of-mouth is gold in rural communities. People trust people they know.
            What to do:
            Recruit local sales agents and train them as Lumirural ambassadors. Give them a small commission on each sale.


            Encourage satisfied customers to refer others through referral rewards.


            Identify local role models (teachers, nurses, pastors) to be informal brand advocates.


            🎯 You're not just selling lights, you're selling empowerment — make people part of the mission.

            ✅ 3. WhatsApp-Based Marketing and Ordering
            Why it works: WhatsApp is the most used digital tool among your target audience — even more than websites or social media.
            What to do:
            Create clear, image-rich status flyers with product info and prices.


            Allow people to order and ask questions via WhatsApp with automated or human responses.


            Use voice notes or short videos (local dialect if possible) to explain product benefits.


            🎯 Make it easy to buy, ask, share — all from one app they already use every day.

            ✅ 4. Radio Campaigns + Call-to-Action
            Why it works: Radio is still the most powerful and accessible form of mass communication in rural Africa.
            What to do:
            Run ads on local-language radio stations, especially during evening news or farming programs.


            Use testimonials from real users, jingle-style intros, or storytelling formats.


            Include a phone number/WhatsApp link for direct purchase or agent sign-up.


            🎯 Target the ears that matter most — and give them an action to take.

            ✅ 5. Flexible Payment Plans + Bundle Promotions
            Why it works: Many potential buyers can afford the product, but not in one go.
            What to do:
            Introduce Pay-As-You-Go (PAYG) or small weekly installment models.


            Bundle offers: e.g., "Buy 3 lights, get 1 for your neighbor free" or "Mother's Pack: Light + Phone Charger for 5,000 off"


            Allow school-based packages for students, supported by PTAs or community sponsors.


            🎯 Lower the barrier to entry, especially in price-sensitive zones.
            
            
            
            
            
            
            Here's a sample Ad:
            
            🔋 AD COPY 1: "Let There Be Light — Even Without ENEO"
            🌞 Tired of being in the dark?
            Talk to us now:
            📲 https://wa.me/237XXXXXXXXX
            Introducing the LUMIrural Home Solar Lighting Kit
            ✅ Lights up to 3 rooms
            ✅ USB ports for phone charging
            ✅ Long-lasting battery
            ✅ No fuel, no noise, no bills
            Perfect for homes, kiosks, and village shops.
            💡 All this for just 25,000 FCFA
            One-time purchase. Lifetime of peace and Free Delivery

            💡 AD COPY 2: "Own the Sun — We'll Package It for You"
            Imagine having light every night without paying monthly bills.
            Let's make it happen:
            📲 https://wa.me/237XXXXXXXXX
            The LUMIrural Solar Kit is:
            ✔️ Rechargeable
            ✔️ Portable and safe for indoor use
            ✔️ Includes solar panel + cables + 3 LED bulbs
            ✔️ Charges your phone and radio too
            Clean, reliable energy that fits your pocket.
            🎁 Get yours now at only 22,500 FCFA
            Limited stock — let's light you up.

            💡 Ad Copy 3:
            "Your Neighbor Has Light. Why Are You Still in the Dark?"
            📲 Order yours now: https://wa.me/237XXXXXXXXX
            The street is talking and it's saying...
            "Lumirural don land!"
            ✅ Clean solar energy
            ✅ Long-lasting bulbs
            ✅ Phone charging that doesn't depend on "Eneo mood"
            ✅ No noise, no smoke, just vibes
            All this brightness for just 15,000 FRS.
            Even your generator is sweating right now. 😅
            Don't let darkness shame your compound.
            We're just one WhatsApp message away.
            
            
            
            Use these samples as inspiration for the content of the brand.

            '''
        )
        # Add conditional instruction based on whether a website exists
        has_website = bool(website and isinstance(website, str) and (website.startswith("http://") or website.startswith("https://")))
        if has_website:
            website_prompt_tail = f" Ensure \"relevant_marketing_strategies\" includes a strategy to improve the existing website ({website}) focusing on SEO, speed, conversion and lead capture."
        else:
            website_prompt_tail = " Ensure \"relevant_marketing_strategies\" includes a strategy to create a professional website (credibility, discovery, lead capture) and place it among the top strategies."

        prompt = f"Please give me the social media content as JSON in the specified structure.{website_prompt_tail}"
        
        try:
            response = openAI.get_text_prediction(system_prompt, prompt)
            print(f'Social media content response received: {len(str(response))} characters')
            
            # Use the existing clean_and_parse_json function to handle malformed JSON
            social_media_content = clean_and_parse_json(response)
        except Exception as e:
            print(f"Error generating social media content: {e}")
            social_media_content = None
        
        if social_media_content:
            ready_made_posts = social_media_content.get("ready_made_posts", [])
            ad_copies = social_media_content.get("ad_copies", [])
            relevant_marketing_strategies = social_media_content.get("relevant_marketing_strategies", [])
        else:
            print("Warning: Could not parse social media content, using default values")
            ready_made_posts = []
            ad_copies = []
            relevant_marketing_strategies = []

        # Post-parse safeguard: enforce website recommendation
        try:
            text_blob = " ".join([s for s in relevant_marketing_strategies if isinstance(s, str)]).lower()
            mentions_site = any(k in text_blob for k in ["website", "site", "landing page", "landing-page", "web page"])
            if not has_website and not mentions_site:
                relevant_marketing_strategies.append(
                    "Create a professional website as your always-on hub for credibility, discovery (SEO), and lead capture; ensure clear value proposition, fast load times, mobile-first design, and a simple contact/WhatsApp CTA."
                )
            if has_website and not mentions_site:
                relevant_marketing_strategies.append(
                    "Improve your website: fix Core Web Vitals, implement on-page SEO (title/meta/H1), add clear CTAs and lead capture (forms/WhatsApp), and track conversions to continuously optimize."
                )
        except Exception as _:
            pass

        # ========== Generate Premium Brand Guidelines ==========
        print("Generating brand guidelines...")
        
        brand_guidelines_system_prompt = f'''You are a brand identity expert. Here is a list of questions we asked the user and here are the answers they gave: >>>
        {question_and_answers} 
        <<<. Here is the previously generated brand identity for this brand (including colors, typography, etc): >>>
        {previously_generated_brand_identity}
        <<<. Generate comprehensive brand guidelines in the following JSON structure:
        {{
            "style_guide": {{
                "typography_rules": [
                    {{
                        "font_family": "string",
                        "usage": "string",
                        "size_range": "string",
                        "line_height": "string",
                        "spacing": "string"
                    }}
                ],
                "color_usage": [
                    {{
                        "color_name": "string",
                        "hex_value": "string",
                        "usage_context": "string",
                        "do_not_use_for": "string"
                    }}
                ],
                "spacing_guidelines": [
                    {{
                        "element": "string",
                        "margin": "string",
                        "padding": "string",
                        "description": "string"
                    }}
                ]
            }},
            "logo_usage_rules": [
                {{
                    "rule": "string",
                    "description": "string",
                    "examples": "string"
                }}
            ],
            "brand_voice": {{
                "tone": "string",
                "personality_traits": ["string"],
                "communication_style": "string",
                "do_not_use": ["string"]
            }},
            "visual_hierarchy": [
                {{
                    "element": "string",
                    "priority": "string",
                    "guidelines": "string"
                }}
            ]
        }}
        
        Make the guidelines comprehensive, professional, and actionable. Include specific rules and examples.'''

        brand_guidelines_prompt = "Please give me comprehensive brand guidelines as JSON."
        
        try:
            brand_guidelines_response = openAI.get_text_prediction(brand_guidelines_system_prompt, brand_guidelines_prompt)
            print(f"Brand guidelines response received: {len(str(brand_guidelines_response))} characters")
            brand_guidelines = clean_and_parse_json(brand_guidelines_response)
        except Exception as e:
            print(f"Error generating brand guidelines: {e}")
            brand_guidelines = None
        
        if not brand_guidelines:
            print("Warning: Could not parse brand guidelines, using default values")
            brand_guidelines = {
                "style_guide": {"typography_rules": [], "color_usage": [], "spacing_guidelines": []},
                "logo_usage_rules": [],
                "brand_voice": {"tone": "", "personality_traits": [], "communication_style": "", "do_not_use": []},
                "visual_hierarchy": []
            }
        
        print("Brand guidelines generation completed.")

        # ========== Generate Copywriting Framework ==========
        print("Generating copywriting framework...")
        
        # Simplified copywriting framework generation with better error handling
        copywriting_framework_system_prompt = f'''You are a senior copywriting strategist. Here is a list of questions we asked the user and the answers they gave: >>>
        {question_and_answers}
        <<<. Based on this, produce a copywriting framework that guides how to write and market to the brand's target audience.

        Generate a JSON object with these sections:
        1. persona_snapshot: demographics, psychographics, fears, desires, aspirations, awareness_stage
        2. message_pillars: problem_narrative, desired_transformation, differentiators, proof_assets, cta_patterns
        3. copy_frameworks: array of copy frameworks (PAS, AIDA, 4P, BAB, FAB)
        4. writing_guidance: fears, desires, dreams, aspirations
        5. tone_style_rules: reading_level, formality, lexicon_use, lexicon_avoid, voice, cadence
        6. objection_bank: array of objections with reframes
        7. hook_bank: array of hooks with tags
        8. cta_bank: array of CTAs with friction levels
        9. channel_adaptation: whatsapp, instagram, linkedin, landing_page, radio_ooh
        10. asset_recipe: array of steps
        11. measurement: metrics, ab_tests, iteration_rules

        Return ONLY valid JSON. No markdown, no extra text.'''

        copywriting_framework_prompt = "Generate the copywriting framework as JSON only."
        
        try:
            copywriting_framework_response = openAI.get_text_prediction(copywriting_framework_system_prompt, copywriting_framework_prompt)
            print(f"Copywriting framework response received: {len(str(copywriting_framework_response))} characters")
            
            # Try to parse the response
            copywriting_framework = clean_and_parse_json(copywriting_framework_response)
            
            if not copywriting_framework:
                print("Warning: Could not parse copywriting framework, trying alternative approach...")
                
                # Try to extract JSON from the response manually
                response_str = str(copywriting_framework_response)
                if '{' in response_str and '}' in response_str:
                    start = response_str.find('{')
                    end = response_str.rfind('}') + 1
                    json_str = response_str[start:end]
                    
                    try:
                        copywriting_framework = json.loads(json_str)
                        print("Successfully parsed JSON using manual extraction")
                    except json.JSONDecodeError as e:
                        print(f"Manual JSON extraction failed: {e}")
                        copywriting_framework = None
                
                if not copywriting_framework:
                    print("Creating fallback copywriting framework...")
                    # Generate a basic framework based on the brand data
                    copywriting_framework = {
                        "persona_snapshot": {
                            "demographics": "Based on brand analysis",
                            "psychographics": "Values and lifestyle patterns",
                            "fears": ["Not achieving goals", "Missing opportunities"],
                            "desires": ["Success", "Recognition", "Growth"],
                            "aspirations": ["Building something meaningful"],
                            "awareness_stage": "problem"
                        },
                        "message_pillars": {
                            "problem_narrative": "Addressing key challenges in the market",
                            "desired_transformation": "Helping customers achieve their goals",
                            "differentiators": ["Unique approach", "Proven results"],
                            "proof_assets": ["Customer testimonials", "Case studies"],
                            "cta_patterns": ["Start your journey", "Get started today"]
                        },
                        "copy_frameworks": [
                            {"name": "PAS", "when_to_use": "Problem awareness", "outline": ["Problem", "Agitation", "Solution"]},
                            {"name": "AIDA", "when_to_use": "General marketing", "outline": ["Attention", "Interest", "Desire", "Action"]},
                            {"name": "4P", "when_to_use": "Product promotion", "outline": ["Picture", "Promise", "Prove", "Push"]}
                        ],
                        "writing_guidance": {
                            "fears": "Address concerns with empathy",
                            "desires": "Highlight benefits and outcomes",
                            "dreams": "Connect with aspirations",
                            "aspirations": "Show path to success"
                        },
                        "tone_style_rules": {
                            "reading_level": "High school",
                            "formality": "Professional but approachable",
                            "lexicon_use": ["innovative", "solutions", "results"],
                            "lexicon_avoid": ["jargon", "complex terms"],
                            "voice": "Authoritative yet friendly",
                            "cadence": "Clear and concise"
                        },
                        "objection_bank": [
                            {"objection": "It's too expensive", "reframe": "Investment in your future", "proof": "ROI data", "risk_reversal": "Money-back guarantee"}
                        ],
                        "hook_bank": [
                            {"text": "Transform your business today", "tag": "desire", "awareness_stage": "solution"}
                        ],
                        "cta_bank": [
                            {"text": "Get Started Now", "friction_level": "low"},
                            {"text": "Schedule a Consultation", "friction_level": "medium"}
                        ],
                        "channel_adaptation": {
                            "whatsapp": "Personal, conversational tone",
                            "instagram": "Visual, engaging content",
                            "linkedin": "Professional, thought leadership",
                            "landing_page": "Clear value proposition",
                            "radio_ooh": "Memorable, action-oriented"
                        },
                        "asset_recipe": [
                            "Define target audience",
                            "Create compelling headlines",
                            "Develop supporting content",
                            "Add clear CTAs",
                            "Test and optimize"
                        ],
                        "measurement": {
                            "metrics": ["Conversion rate", "Engagement rate", "Click-through rate"],
                            "ab_tests": ["Headline variations", "CTA button colors"],
                            "iteration_rules": ["Test one variable at a time", "Run tests for statistical significance"]
                        }
                    }
        except Exception as e:
            print(f"Error generating copywriting framework: {e}")
            print("Using default copywriting framework...")
            copywriting_framework = {
                "persona_snapshot": {
                    "demographics": "Target audience based on brand analysis",
                    "psychographics": "Values and lifestyle patterns",
                    "fears": ["Not achieving goals", "Missing opportunities"],
                    "desires": ["Success", "Recognition", "Growth"],
                    "aspirations": ["Building something meaningful"],
                    "awareness_stage": "problem"
                },
                "message_pillars": {
                    "problem_narrative": "Addressing key challenges in the market",
                    "desired_transformation": "Helping customers achieve their goals",
                    "differentiators": ["Unique approach", "Proven results"],
                    "proof_assets": ["Customer testimonials", "Case studies"],
                    "cta_patterns": ["Start your journey", "Get started today"]
                },
                "copy_frameworks": [
                    {"name": "PAS", "when_to_use": "Problem awareness", "outline": ["Problem", "Agitation", "Solution"]},
                    {"name": "AIDA", "when_to_use": "General marketing", "outline": ["Attention", "Interest", "Desire", "Action"]},
                    {"name": "4P", "when_to_use": "Product promotion", "outline": ["Picture", "Promise", "Prove", "Push"]}
                ],
                "writing_guidance": {
                    "fears": "Address concerns with empathy",
                    "desires": "Highlight benefits and outcomes",
                    "dreams": "Connect with aspirations",
                    "aspirations": "Show path to success"
                },
                "tone_style_rules": {
                    "reading_level": "High school",
                    "formality": "Professional but approachable",
                    "lexicon_use": ["innovative", "solutions", "results"],
                    "lexicon_avoid": ["jargon", "complex terms"],
                    "voice": "Authoritative yet friendly",
                    "cadence": "Clear and concise"
                },
                "objection_bank": [
                    {"objection": "It's too expensive", "reframe": "Investment in your future", "proof": "ROI data", "risk_reversal": "Money-back guarantee"}
                ],
                "hook_bank": [
                    {"text": "Transform your business today", "tag": "desire", "awareness_stage": "solution"}
                ],
                "cta_bank": [
                    {"text": "Get Started Now", "friction_level": "low"},
                    {"text": "Schedule a Consultation", "friction_level": "medium"}
                ],
                "channel_adaptation": {
                    "whatsapp": "Personal, conversational tone",
                    "instagram": "Visual, engaging content",
                    "linkedin": "Professional, thought leadership",
                    "landing_page": "Clear value proposition",
                    "radio_ooh": "Memorable, action-oriented"
                },
                "asset_recipe": [
                    "Define target audience",
                    "Create compelling headlines",
                    "Develop supporting content",
                    "Add clear CTAs",
                    "Test and optimize"
                ],
                "measurement": {
                    "metrics": ["Conversion rate", "Engagement rate", "Click-through rate"],
                    "ab_tests": ["Headline variations", "CTA button colors"],
                    "iteration_rules": ["Test one variable at a time", "Run tests for statistical significance"]
                }
            }
        
        print("Copywriting framework generation completed.")

        # ================================== Prepare results object  ==================================

        # Extract brand identity information from previously generated data
        brand_name = brand.get("name", "")
        
        # Parse brand_identity JSON string if it exists
        brand_identity_data = {}
        if brand.get("brand_identity"):
            try:
                brand_identity_data = json.loads(brand["brand_identity"]) if isinstance(brand["brand_identity"], str) else brand["brand_identity"]
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Error parsing brand_identity JSON: {e}")
                brand_identity_data = {}
        
        brand_identity_description = brand_identity_data.get("brand_identity_description", "")
        brand_colors = brand_identity_data.get("brand_colors", [])
        brand_typography = brand_identity_data.get("brand_typography", {})

        results = {
            "userId": userId,
            "brandId": brandId,
            "full_brand_identity": {
                "brand_name": brand_name,
                "brand_identity_description": brand_identity_description,
                "brand_patterns": brandPatterns,
                "brand_colors": brand_colors,
                "brand_typography": brand_typography,
                "business_cards": business_cards,
                "letterheads": letterheads,
                "t_shirt_mockups": tshirt_mockups,
                "cap_mockups": cap_mockups,
                "signboards": signboards,
            },
            "social_media_content": {
                "ready_made_posts": ready_made_posts,
                "ad_copies": ad_copies,
                "relevant_marketing_strategies": relevant_marketing_strategies
            },
            "premium_assets": {
                "brand_guidelines": brand_guidelines,
                "copywriting_framework": copywriting_framework
            }
        }
        
        # Save to database
        print("Saving brand assets to database...")
        db.create_brand_assets(brandId, userId, results["full_brand_identity"], results["social_media_content"], results["premium_assets"])
        
        print("✅ Full brand generation completed successfully!")
        print(f"Generated assets for brand ID: {brandId}")
        print(f"User ID: {userId}")
        
        return results
    except Exception as e:
        print(f"Error in generate_results: {e}")
        import traceback
        traceback.print_exc()
        return {"error": True, "message": str(e)}
    finally:
        # Cleanup: delete the entire images folder and its contents
        try:
            if os.path.exists(images_dir):
                shutil.rmtree(images_dir)
                print(f"Deleted images directory: {images_dir}")
        except Exception as cleanup_error:
            print(f"Error deleting images directory: {cleanup_error}")
            
            
            
            
# print("\n\n\n\nFinal result\n\n")
# print(generate_final_results("bf286f70-711d-429c-80a6-dfa74e47cb2b", "be3ad5cc-5f4e-45be-aaf0-35439391578e", "Kum Randy", "myemail@gmail.com", "652932842", "", "www.toothai.com", "https://logomoose.com/wp-content/uploads/2016/01/18.jpg"))
# print(generate_results("bf286f70-711d-429c-80a6-dfa74e47cb2b", "be3ad5cc-5f4e-45be-aaf0-35439391578e"))
