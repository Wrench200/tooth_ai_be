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
                if not isinstance(data[section], list) or len(data[section]) < 3:
                    print(f"'logos' section is not a list of at least 3 items")
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















def generate_results(userId, brandId):
    import shutil
    images_dir = 'images'
    try:
        user = db.get_user(userId)
        brand = db.get_brand(brandId)
        answers = db.get_answer(brand["answerid"])
        
        previous_questions = questions.get_previous_questions(11)
        previous_answers = db.get_previous_answers(answers["answerId"], 11)
        question_and_answers = " ".join([f"Question: {q} Answer: {a}." for q, a in zip(previous_questions, previous_answers)])
        
        # print(question_and_answers)
        
        
        
        # ================================== Prepare varaiables for results ==================================
        
        what_our_customers_mean_to_us = ""
        we_believe_in_something_bigger_than_ourselves = ""
        purpose_statement = ""

        our_vision_is_bright = ""

        we_are_committed_to = ""

        how_we_do_wellness_business = ""
        values = []

        position_name = ""
        demographics = ""
        psychographics = ""
        personality = ""
        fears = ""
        desires = ""
        challenges_and_pain_points = ""

        top_competitors = [
            {
                "name": "Competitor 1",
                "description": "A leading competitor in the wellness industry, known for its innovative products and strong community engagement.",
                "website": "https://competitor1.com",
                "facebook": "https://facebook.com/competitor1",
                "youTube": "https://youtube.com/competitor1",
                "instagram": "https://instagram.com/competitor1",
            }
        ]
        
        elevator_pitch = ""

        the_difference_we_provide = ""
        position_statement = ""

        brand_name = ""
        brand_tagline = ""

        who_we_serve = ""
        where_they_need_help = ""
        the_key_benefits_they_get = ""
        their_market_alternative = ""
        our_key_differences = ""

        about_the_brand = ""


        logo_url_1 = "https://example.com/primary_logo.png"
        logo_url_2 = "https://example.com/secondary_logo.png"

        logo_description_1 = ""
        logo_description_2 = ""

        primary_colors = [
            {
                "color_name": "Primary Blue",
                "hex_value": "#0033cc",
                "description": "The primary color representing trust and professionalism."
            },
            {
                "color_name": "Secondary Green",
                "hex_value": "#66cc66",
                "description": "A secondary color symbolizing growth and wellness."
            }
        ]

        secondary_colors = [
            {
                "color_name": "Accent Orange",
                "hex_value": "#ff6600",
                "description": "An accent color used for highlights and calls to action."
            },
            {
                "color_name": "Background White",
                "hex_value": "#ffffff",
                "description": "A clean background color for a fresh look."
            },
            {
                "color_name": "Text Gray",
                "hex_value": "#333333",
                "description": "A neutral text color for readability."
            }
        ]


        typography = [
            {
                "font_family": "Open Sans",
                "font_weight": "Regular",
                "font_size": "16px",
                "line_height": "1.5",
                "description": "The primary font for body text, ensuring readability and clarity."
            },
            {
                "font_family": "Roboto",
                "font_weight": "Bold",
                "font_size": "24px",
                "line_height": "1.2",
                "description": "A bold font for headings, providing emphasis and impact."
            }
        ]





        # ================================== Generate information for results  ==================================

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
                what_our_customers_mean_to_us = response["our_purpose"]["what_our_customers_mean_to_us"]
                we_believe_in_something_bigger_than_ourselves = response["our_purpose"]["we_believe_in_something_bigger_than_ourselves"]
                purpose_statement = response["our_purpose"]["purpose_statement"]
                our_vision_is_bright = response["our_vision"]["our_vision_is_bright"]
                we_are_committed_to = response["our_mission"]["we_are_committed_to"]
                how_we_do_wellness_business = response["our_values"]["how_we_do_wellness_business"]
                values = response["our_values"]["values"]
                passed = True
                print("Section success \n\n")
            else:
                print("Error in response format. Retrying...")
                
                
                
                
                
                
        
                
                
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
                position_name = response["name"]
                demographics = response["demographics"]
                psychographics = response["psychographics"]
                personality = response["personality"]
                fears = response["fears"]
                desires = response["desires"]
                challenges_and_pain_points = response["challenges_and_pain_points"]
                passed = True
                print("Section success \n\n")
            else:
                print("Error in response format. Retrying...")
                    
                
                
                
                
                
                
                
                
            system_prompt = "You are a competitor profile expert. here is a list of questions we asked the user and here are the answers they gave: >>>" + question_and_answers + "<<< Be more elaborate with the responses, dont be too brief. Make it sound legit and good. Your resonses should not just be single sentences. Try to write a paragraph of valuable information. Sound more human as possible. Make it serious and not just rushed"
                    
            prompt = "Please give me a profile of my top competitors as a string. Do not style it. Do not add any syntax. Just a paragraph of text. No labeling please."
            
            print("Processing section ...")
            response = openAI.get_text_prediction(system_prompt, prompt)
            top_competitors = response
            print("Section success \n\n")
                    
                
                
                 
                
                
                
                
                
        system_prompt = "You are a branding expert. here is a list of questions we asked the user and here are the answers they gave: >>>" + question_and_answers + '''<<<. You are supposed to generate the reasons that make the brand different as a json of this format >>> 
    {
        "the_difference_we_provide": the_difference_we_provide,
        "positioning_statement": position_statement,
    }
    <<< Make sure to generate the values for the different parts. Replace sss with the string values you generate. Make sure you replace sss with strings. Do not use any other format or add any other information. Make sure to generate the values for the different parts, using information from the questions and answers. Make sure to respect the json format and do not add any other information. Be more elaborate with the responses, dont be too brief. Make it sound legit and good. Your resonses should not just be single sentences. Try to write a paragraph of valuable information sometimes. Sound more human as possible. Make it serious and not just rushed'''
            
        prompt = "Please give me a sample what makes us different as json, and make sure to fill the information in the json as specified"

        passed = False
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
                the_difference_we_provide = response["the_difference_we_provide"]
                position_statement = response["positioning_statement"]
                passed = True
                print("Section success \n\n")
            else:
                print("Error in response format. Retrying...")
                
                
                
                
                
                
                
                
                
        system_prompt = "You are a brand communication expert. here is a list of questions we asked the user and here are the answers they gave: >>>" + question_and_answers + '''<<<. You are supposed to generate the communication for the brand as a json of this format >>> 
    {
        "brand_name": sss,
        "brand_tagline": sss,
        "primary_core_message": {
            "who_we_serve": sss,
            "where_they_need_help": sss,
            "the_key_benefits_they_get": sss,
            "their_market_alternative": sss,
            "our_key_differences": sss,
        },
        elevator_pitch: sss
    } <<< Make sure to generate the values for the different parts. Replace sss with the string values you generate. Make sure you replace sss with strings. Do not use any other format or add any other information. Make sure to generate the values for the different parts, using information from the questions and answers. Make sure to respect the json format and do not add any other information. Be more elaborate with the responses, dont be too brief. Make it sound legit and good. Your resonses should not just be single sentences. Try to write a paragraph of valuable information sometimes. Sound more human as possible. Make it serious and not just rushed'''
            
        prompt = "Please give me the communication for my brand as json, and make sure to fill the information in the json as pecified"
        
        passed = False
        while passed == False:
            print("Processing section ...")
            response = openAI.get_text_prediction(system_prompt, prompt)
            response = clean_and_parse_json(response)
            # Define the expected structure
            expected_structure = {
                "brand_name": [],
                "brand_tagline": [],
                "primary_core_message": [
                    "who_we_serve",
                    "where_they_need_help",
                    "the_key_benefits_they_get",
                    "their_market_alternative",
                    "our_key_differences"
                ],
                "elevator_pitch": []
            }
            
            if check_keys(response, expected_structure):
                brand_name = response["brand_name"]
                brand_tagline = response["brand_tagline"]
                who_we_serve = response["primary_core_message"]["who_we_serve"]
                where_they_need_help = response["primary_core_message"]["where_they_need_help"]
                the_key_benefits_they_get = response["primary_core_message"]["the_key_benefits_they_get"]
                their_market_alternative = response["primary_core_message"]["their_market_alternative"]
                our_key_differences = response["primary_core_message"]["our_key_differences"]
                # Add elevator_pitch extraction
                elevator_pitch = response.get("elevator_pitch", "")
                passed = True
                print("Section success \n\n")
            else:
                print("Error in response format. Retrying...")
                
                
                
                
                
                
                
                
                
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
        })
    } <<< For the logo prompts, make sure to write a detailed description of the logo for the best result, straight forward detailed instructions that will yield the best result for an AI image generation model to use, the logos should be very professional, creative and attrative, no simple logos or empty logos, just logos that are straight up creative and very good, either with an icon, or decorated initials or any other, be creative, specify the brand name, also mention the tagline, if necessary, not all logos should have a tagline under. Brand name: '''+brand_name+''', tagline: '''+brand_tagline+'''. Make sure each font object in the list of fonts has just one font. Make sure to generate the values for the different parts. Replace sss with the string values you generate and lll with a list. Make sure you replace sss with strings. Do not use any other format or add any other information. Make sure to generate the values for the different parts, using information from the questions and answers. Make sure to respect the json format and do not add any other information. Be more elaborate with the responses, dont be too brief. Make it sound legit and good. Your resonses should not just be single sentences. Try to write a paragraph of valuable information sometimes. Sound more human as possible. Make it serious and not just rushed'''
            
        prompt = "Please give me the identity for my brand as json, and make sure to fill the information in the json as pecified"
        # response = openAI.get_text_prediction(system_prompt, prompt)
        # print(response)
        # raise Exception("Error")
        logo_prompt1 = ""
        logo_prompt2 = ""
        
        passed = False
        max_retries = 3
        retry_count = 0
        
        brand_identity = ""
        while passed == False and retry_count < max_retries:
            print(f"Processing section (attempt {retry_count + 1}/{max_retries})...")
            try:
                raw_response = openAI.get_text_prediction(system_prompt, prompt)
                print(f"Raw API response type: {type(raw_response)}")
                print(f"Raw API response: {raw_response[:200]}..." if raw_response else "Raw API response: None")
                
                response = clean_and_parse_json(raw_response)
                print(f"Parsed response: {response}")
                brand_identity = response
                
                # Define the expected structure
                expected_structure = {
                    "about_the_brand": [],
                    "logos": ["prompt", "description"],
                    "primary_colors": [],
                    "secondary_colors": [],
                    "typography": []
                }
                
                if response is None:
                    print("Error: API response could not be parsed as JSON")
                    retry_count += 1
                    continue
                    
                if check_keys(response, expected_structure):
                    about_the_brand = response["about_the_brand"]
                    # Extract logo descriptions and prompts
                    logo_description_1 = response["logos"][0]["description"]
                    logo_description_2 = response["logos"][1]["description"]
                    
                    logo_prompt1 = response["logos"][0]["prompt"]
                    logo_prompt2 = response["logos"][1]["prompt"]
                    
                    # Optionally, you could use the prompts for logo generation elsewhere
                    primary_colors = response["primary_colors"]
                    secondary_colors = response["secondary_colors"]
                    typography = response["typography"]
                    applications = response["applications"]
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
            about_the_brand = "Default brand description"
            logo_description_1 = "Default logo description 1"
            logo_description_2 = "Default logo description 2"
            logo_prompt1 = "A simple, professional logo design"
            logo_prompt2 = "A modern, minimalist logo design"
            primary_colors = []
            secondary_colors = []
            typography = []
            applications = []
        # ...existing code...





        # ================================== Prepare results object  ==================================


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
                "elevator_pitch": elevator_pitch
            },
            "brand_identity": {
                "about_the_brand": about_the_brand,
                "logos": [
                    {
                        "image_url": logo_url_1,
                        "description": logo_description_1
                    },
                    {
                        "image_url": logo_url_2,
                        "description": logo_description_2
                    },
                ],
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





# print(generate_results("24d0c547-8685-4ee9-95a4-b362da16da3c", "96266589-80bb-4f14-aff9-6baf8cc4dffd"))
# print("\n\n\n\n"+str(db.get_brand("7be4efdc-7d3d-4344-b823-8300f6e81bb0")))

# generate_results("72aa6589-0cdb-4795-acf3-b0db2a8d7fad", "7be4efdc-7d3d-4344-b823-8300f6e81bb0")























































def generate_final_results(userId, brandId, userName, userEmail, userPhoneNumbers, registrationNumber, website, brandLogo, others = {}):
    import shutil
    images_dir = 'images'
    try:
        user = db.get_user(userId)
        brand = db.get_brand(brandId)
        answers = db.get_answer(brand["answerid"])
        
        previous_questions = questions.get_previous_questions(11)
        previous_answers = db.get_previous_answers(answers["answerId"], 11)
        question_and_answers = " ".join([f"Question: {q} Answer: {a}." for q, a in zip(previous_questions, previous_answers)])
        previously_generated_brand_identity = brand["brand_identity"]
        
        
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
            return assets["image_url"]

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
                "<<<. Generate 3 unique, visually appealing brand pattern prompts for an AI image generator. Each pattern should reflect the brand's personality, colors, and style, and must respect the previously generated brand identity (especially colors, typography, and any other relevant details). Output as a list of 3 detailed prompts. Do not add any extra text or formatting. You MUST respond with a list of strings in angle braces, in this format: ["prompt1", "prompt2"]. '''
            ),
            prompt="Please give me 3 brand pattern prompts as a list.",
            expected_count=3,
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
                "<<<. Generate 2 highly detailed prompts for an AI image generator to create business card mockups for the brand. Each prompt should specify the brand name, tagline, colors, and style, and must respect the previously generated brand identity (especially colors, typography, and any other relevant details). Output as a list of 2 prompts. No extra text. You MUST respond with a list of strings in angle braces, in this format: ["prompt1", "prompt2"]. '''
            ),
            prompt="Please give me 2 business card prompts as a list.",
            expected_count=2,
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
                "<<<. Generate 2 detailed prompts for an AI image generator to create t-shirt mockups for the brand. Specify logo placement, colors, and style, and must respect the previously generated brand identity (especially colors, typography, and any other relevant details). Output as a list of 2 prompts. You MUST respond with a list of strings in angle braces, in this format: ["prompt1", "prompt2"]. '''
            ),
            prompt="Please give me 2 t-shirt mockup prompts as a list.",
            expected_count=2,
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
        social_media_json_structure = {
            "ready_made_posts": [
                {
                    "caption": "string",
                    "design_concept": "string"
                }
            ],
            "ad_copies": [
                "string"
            ],
            "relevant_marketing_strategies": [
                "string"
            ]
        }
        system_prompt = (
            "You are a social media content expert. Here is a list of questions we asked the user and here are the answers they gave: >>>"
            + question_and_answers +
            "<<<. Generate social media content for the brand in the following JSON structure:\n"
            + json.dumps(social_media_json_structure, indent=2) +
            "\n- ready_made_posts: 6 objects, each with a 'caption' and a 'design_concept'.\n"
            "- ad_copies: 3 creative ad copy strings.\n"
            "- relevant_marketing_strategies: 3 relevant marketing strategies as strings.\n"
            "Do not add any extra text or formatting. Only output valid JSON."
        )
        prompt = "Please give me the social media content as JSON in the specified structure."
        response = openAI.get_text_prediction(system_prompt, prompt)
        try:
            social_media_content = json.loads(response.strip())
            ready_made_posts = social_media_content.get("ready_made_posts", [])
            ad_copies = social_media_content.get("ad_copies", [])
            relevant_marketing_strategies = social_media_content.get("relevant_marketing_strategies", [])
        except Exception as e:
            print(f"Error parsing social media content: {e}")
            ready_made_posts = []
            ad_copies = []
            relevant_marketing_strategies = []


        # ================================== Prepare results object  ==================================


        results = {
            "userId": userId,
            "brandId": brandId,
            "full_brand_identity": {
                "brand_patterns": brandPatterns,
                "business_cards": business_cards,
                "letterheads": letterheads,
                "tshirt_mockups": tshirt_mockups,
                "cap_mockups": cap_mockups,
                "signboards": signboards,
            },
            "social_media_content": {
                "ready_made_posts": ready_made_posts,
                "ad_copies": ad_copies,
                "relevant_marketing_strategies": relevant_marketing_strategies
            }
        }
        
        
        
        # db.update_brand(brandId, "brand_strategy", json.dumps(results["brand_strategy"]))
        # db.update_brand(brandId, "brand_communication", json.dumps(results["brand_communication"]))
        # db.update_brand(brandId, "brand_identity", json.dumps(results["brand_identity"]))
        # db.update_brand(brandId, "marketing_and_social_media_strategy", json.dumps(results["marketing_and_social_media_strategy"]))
        
        
        
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
            
            
            
            
print("\n\n\n\nFinal result\n\n")
print(generate_final_results("24d0c547-8685-4ee9-95a4-b362da16da3c", "96266589-80bb-4f14-aff9-6baf8cc4dffd", "Kum Randy", "myemail@gmail.com", "652932842", "", "www.toothai.com", "https://logomoose.com/wp-content/uploads/2016/01/18.jpg"))
