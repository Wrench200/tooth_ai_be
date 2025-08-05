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
        logo_url_3 = "https://example.com/alternative_logo.png"

        logo_description_1 = ""
        logo_description_2 = ""
        logo_description_3 = ""

        recommended_logo = ""

        logo_variants = {
            "primary_logo": logo_url_1,
            "secondary_logo": logo_url_2,
            "alternative_logo": logo_url_3
        }

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

        applications = [
            {
                "application_type": "Website",
                "image_url": "",
            },{
                "application_type": "Mug",
                "image_url": "",
            }
        ]

        content_calender = ""





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
                "primary_core_message": ["who_we_serve", "where_they_need_help", "the_key_benefits_they_get", "their_market_alternative", "our_key_differences"]
            }
            
            if check_keys(response, expected_structure):
                brand_name = response["brand_name"]
                brand_tagline = response["brand_tagline"]
                who_we_serve = response["primary_core_message"]["who_we_serve"]
                where_they_need_help = response["primary_core_message"]["where_they_need_help"]
                the_key_benefits_they_get = response["primary_core_message"]["the_key_benefits_they_get"]
                their_market_alternative = response["primary_core_message"]["their_market_alternative"]
                our_key_differences = response["primary_core_message"]["our_key_differences"]
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
        # response = openAI.get_text_prediction(system_prompt, prompt)
        # print(response)
        # raise Exception("Error")
        logo_prompt1 = ""
        logo_prompt2 = ""
        logo_prompt3 = ""
        
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
                    "typography": [],
                    "applications": []
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
                    logo_description_3 = response["logos"][2]["description"]
                    
                    logo_prompt1 = response["logos"][0]["prompt"]
                    logo_prompt2 = response["logos"][1]["prompt"]
                    logo_prompt3 = response["logos"][2]["prompt"]
                    
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
            logo_description_3 = "Default logo description 3"
            logo_prompt1 = "A simple, professional logo design"
            logo_prompt2 = "A modern, minimalist logo design"
            logo_prompt3 = "A creative, distinctive logo design"
            primary_colors = []
            secondary_colors = []
            typography = []
            applications = []
        # ...existing code...


        # Generate logos and upload to Cloudinary
        try:
            print("Generating logos and uploading to Cloudinary...")
            logo_url_1 = imagen.generate_image(logo_prompt1, public_id=f"toothai/{brandId}/logo_1")
            logo_url_2 = imagen.generate_image(logo_prompt2, public_id=f"toothai/{brandId}/logo_2")
            logo_url_3 = imagen.generate_image(logo_prompt3, public_id=f"toothai/{brandId}/logo_3")
            
            # Check if any logos failed to generate
            if not logo_url_1:
                print("Warning: Logo 1 generation failed, using placeholder")
                logo_url_1 = "https://via.placeholder.com/400x200?text=Logo+1"
            if not logo_url_2:
                print("Warning: Logo 2 generation failed, using placeholder")
                logo_url_2 = "https://via.placeholder.com/400x200?text=Logo+2"
            if not logo_url_3:
                print("Warning: Logo 3 generation failed, using placeholder")
                logo_url_3 = "https://via.placeholder.com/400x200?text=Logo+3"
                
            print("Logo generation completed successfully")
        except Exception as e:
            print(f"Error during logo generation: {e}")
            print("Using placeholder logos")
            logo_url_1 = "https://via.placeholder.com/400x200?text=Logo+1"
            logo_url_2 = "https://via.placeholder.com/400x200?text=Logo+2"
            logo_url_3 = "https://via.placeholder.com/400x200?text=Logo+3"
            
            
        # # Get logo recommendation
        # if logo_url_1 != "https://via.placeholder.com/400x200?text=Logo+1":
        #     logo_file_1 = functions.download_image(logo_url_1)
        #     logo_file_2 = functions.download_image(logo_url_2)
        #     logo_file_3 = functions.download_image(logo_url_3)
            
        #     logo_with_label_1 = textOnImage.add_text_top_left(logo_file_1, "Logo 1")
        #     logo_with_label_2 = textOnImage.add_text_top_left(logo_file_2, "Logo 2")
        #     logo_with_label_3 = textOnImage.add_text_top_left(logo_file_3, "Logo 3")
            
        #     logo_options = [logo_with_label_1, logo_with_label_2, logo_with_label_3]
            
        #     system_prompt = "You are a brand identity expert. here is a list of questions we asked the user and here are the answers they gave: >>>" + question_and_answers + '<<<. I just attached 3 logo options for the brand. I need you to recommend the best logo for the brand. Just out either "Logo 1", "Logo 2" or "Logo 3" as the best logo for the brand. Do not add any other information, just the name of the logo. Make sure to not say say any other thing, make sure to output just the name of the logo, and do not say anything extra. Make sure to make just one choice'
        #     prompt = "Please give me the best logo for the brand"
        #     print("Processing section ...")
        #     response = openAI.get_text_prediction(system_prompt, prompt, image_input=logo_options)
        #     recommended_logo = response.strip()
        #     print(recommended_logo)
        #     print("Section success \n\n")
            
            
        
        # # Design logo variants
        # system_prompt = "You are a brand identity expert. here is a list of questions we asked the user and here are the answers they gave: >>>" + question_and_answers + '<<<. Here are the primary and secondary colors for the brand >>> Primary colors: '+str(primary_colors)+'. Secondary colors: '+str(secondary_colors)+'<<<. I need you to design logo variants for the brand, using the attached recommended logo. You have to write a list of 3 prompts prompting an AI image generation model to generate 3 completely different logo varients using the attached logo, in the format: ["prompt 1", "prompt 2", "prompt 3"]. The varients need to be the exact same logo, but with different colors, styles, and designs. Make sure Insist in the prompt that it should be a varient of the same logo. Add every detailed instruction in the prompt. Make sure to use the primary and secondary colors of the brand in the design. Make sure to use words like, clean, high quality and the like in the prompts where needed to make it very good. Make sure to use the attached logo as a base for the design. Make sure to not say any other thing, make sure to output just the list of prompts, and do not say anything extra. Make sure to not style anywhere in the prompts with **, ---, #### or anything similar'
        # prompt = "Please give me the logo variants for the brand as a list of prompts"
        
        # print("Processing section ...")
        
        # recommended_logo_url = ""
        # if recommended_logo == "Logo 1":
        #     recommended_logo_file = logo_file_1
        #     recommended_logo_url = logo_url_1
        # elif recommended_logo == "Logo 2":
        #     recommended_logo_file = logo_file_2
        #     recommended_logo_url = logo_url_2
        # elif recommended_logo == "Logo 3":
        #     recommended_logo_file = logo_file_3
        #     recommended_logo_url = logo_url_3
            
        # recommended_logo = recommended_logo_url
        # print(f"\n\nRecommended logo url: {recommended_logo}")

        # response = openAI.get_text_prediction(system_prompt, prompt, image_input=[recommended_logo_file])
        # response = response.strip()
        # logo_variants_prompts = response
        # print(f"\n\nLogo variants prompts: {logo_variants_prompts}")
        # logo_variants_prompts = json.loads(logo_variants_prompts)
        
        # # print(f"\n\nLogo variants prompts: {logo_variants_prompts}")
        # # print("\n\n")
        # logo_variants = []
        # for prompt in logo_variants_prompts:
        #     new_varient = openAI.generate_image(prompt, [recommended_logo_file])
        #     print(f"Generated logo variant: {new_varient}")
        #     # Upload the variant to Cloudinary if it is a file path
        #     variant_url = None
        #     if new_varient and os.path.isfile(new_varient):
        #         try:
        #             upload_result = cloudinary_utils.upload_image_from_file(new_varient, folder=f"toothai/{brandId}/logo_variants")
        #             if upload_result and "secure_url" in upload_result:
        #                 variant_url = upload_result["secure_url"]
        #             else:
        #                 print(f"Failed to upload variant to Cloudinary: {upload_result}")
        #         except Exception as e:
        #             print(f"Error uploading variant to Cloudinary: {e}")
        #     else:
        #         variant_url = new_varient  # fallback, may be a URL or error string
        #     logo_variants.append(variant_url)
            
        # print("Logo Variant section success \n\n")
        
        







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
                    {
                        "image_url": logo_url_3,
                        "description": logo_description_3
                    }
                ],
                "reommended_logo": recommended_logo,
                "logo_variants": logo_variants,
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


























































def generate_final_results(userId, brandId, userName, userEmail, userPhoneNumbers, registrationNumber, website, brandLogo, others = {}):
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
        # brand_identity_data is not defined yet at this point in the function.
        # To fix this, we need to parse it from the brand object before using it.
        # Let's parse brand_identity_data from brand["brand_identity"] if it exists, else use an empty dict.
        if brand.get("brand_identity"):
            try:
                brand_identity_data = json.loads(brand["brand_identity"]) if isinstance(brand["brand_identity"], str) else brand["brand_identity"]
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Error parsing brand_identity JSON: {e}")
                brand_identity_data = {}
        else:
            brand_identity_data = {}
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
        prompt = "Please give me the social media content as JSON in the specified structure."
        response = openAI.get_text_prediction(system_prompt, prompt)
        print('response', response)
        
        # Use the existing clean_and_parse_json function to handle malformed JSON
        social_media_content = clean_and_parse_json(response)
        
        if social_media_content:
            ready_made_posts = social_media_content.get("ready_made_posts", [])
            ad_copies = social_media_content.get("ad_copies", [])
            relevant_marketing_strategies = social_media_content.get("relevant_marketing_strategies", [])
        else:
            print("Warning: Could not parse social media content, using default values")
            ready_made_posts = []
            ad_copies = []
            relevant_marketing_strategies = []

        # ========== Generate Premium Brand Guidelines ==========
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
        brand_guidelines_response = openAI.get_text_prediction(brand_guidelines_system_prompt, brand_guidelines_prompt)
        brand_guidelines = clean_and_parse_json(brand_guidelines_response)
        
        if not brand_guidelines:
            print("Warning: Could not parse brand guidelines, using default values")
            brand_guidelines = {
                "style_guide": {"typography_rules": [], "color_usage": [], "spacing_guidelines": []},
                "logo_usage_rules": [],
                "brand_voice": {"tone": "", "personality_traits": [], "communication_style": "", "do_not_use": []},
                "visual_hierarchy": []
            }

        # ========== Generate Marketing Templates ==========
        marketing_templates_system_prompt = f'''You are a marketing expert. Here is a list of questions we asked the user and here are the answers they gave: >>>
        {question_and_answers} 
        <<<. Generate marketing templates in the following JSON structure:
        {{
            "email_templates": [
                {{
                    "template_name": "string",
                    "subject_line": "string",
                    "greeting": "string",
                    "body": "string",
                    "closing": "string",
                    "signature": "string"
                }}
            ],
            "presentation_templates": [
                {{
                    "slide_title": "string",
                    "content": "string",
                    "key_points": ["string"],
                    "visual_suggestions": "string"
                }}
            ],
            "brochure_content": [
                {{
                    "section_title": "string",
                    "content": "string",
                    "call_to_action": "string"
                }}
            ],
            "landing_page_copy": {{
                "hero_headline": "string",
                "hero_subheadline": "string",
                "benefits": ["string"],
                "features": ["string"],
                "testimonials": ["string"],
                "call_to_action": "string"
            }}
        }}
        
        Make the templates professional, engaging, and tailored to the brand.'''

        marketing_templates_prompt = "Please give me marketing templates as JSON."
        marketing_templates_response = openAI.get_text_prediction(marketing_templates_system_prompt, marketing_templates_prompt)
        marketing_templates = clean_and_parse_json(marketing_templates_response)
        
        if not marketing_templates:
            print("Warning: Could not parse marketing templates, using default values")
            marketing_templates = {
                "email_templates": [],
                "presentation_templates": [],
                "brochure_content": [],
                "landing_page_copy": {"hero_headline": "", "hero_subheadline": "", "benefits": [], "features": [], "testimonials": [], "call_to_action": ""}
            }

        # ========== Generate Business Strategy Documents ==========
        business_strategy_system_prompt = f'''You are a business strategy expert. Here is a list of questions we asked the user and here are the answers they gave: >>>
        {question_and_answers} 
        <<<. Generate business strategy documents in the following JSON structure:
        {{
            "competitive_analysis": [
                {{
                    "competitor_name": "string",
                    "strengths": ["string"],
                    "weaknesses": ["string"],
                    "market_position": "string",
                    "differentiation_opportunities": ["string"]
                }}
            ],
            "swot_analysis": {{
                "strengths": ["string"],
                "weaknesses": ["string"],
                "opportunities": ["string"],
                "threats": ["string"]
            }},
            "target_audience_profiles": [
                {{
                    "persona_name": "string",
                    "demographics": "string",
                    "psychographics": "string",
                    "pain_points": ["string"],
                    "motivations": ["string"],
                    "buying_behavior": "string"
                }}
            ],
            "market_positioning": {{
                "positioning_statement": "string",
                "value_proposition": "string",
                "competitive_advantages": ["string"],
                "market_gaps": ["string"]
            }}
        }}
        
        Make the analysis thorough, data-driven, and actionable.'''

        business_strategy_prompt = "Please give me business strategy documents as JSON."
        business_strategy_response = openAI.get_text_prediction(business_strategy_system_prompt, business_strategy_prompt)
        business_strategy = clean_and_parse_json(business_strategy_response)
        
        if not business_strategy:
            print("Warning: Could not parse business strategy, using default values")
            business_strategy = {
                "competitive_analysis": [],
                "swot_analysis": {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []},
                "target_audience_profiles": [],
                "market_positioning": {"positioning_statement": "", "value_proposition": "", "competitive_advantages": [], "market_gaps": []}
            }

        # ========== Generate Implementation Roadmap ==========
        implementation_roadmap_system_prompt = f'''You are a project management expert. Here is a list of questions we asked the user and here are the answers they gave: >>>
        {question_and_answers} 
        <<<. Generate an implementation roadmap in the following JSON structure:
        {{
            "launch_timeline": [
                {{
                    "phase": "string",
                    "duration": "string",
                    "milestones": ["string"],
                    "deliverables": ["string"],
                    "resources_needed": ["string"]
                }}
            ],
            "budget_estimates": [
                {{
                    "category": "string",
                    "estimated_cost": "string",
                    "priority": "string",
                    "description": "string"
                }}
            ],
            "vendor_recommendations": [
                {{
                    "service_type": "string",
                    "recommended_vendors": ["string"],
                    "selection_criteria": ["string"],
                    "estimated_cost_range": "string"
                }}
            ],
            "quality_assurance": [
                {{
                    "checkpoint": "string",
                    "criteria": ["string"],
                    "testing_method": "string",
                    "success_metrics": ["string"]
                }}
            ]
        }}
        
        Make the roadmap practical, realistic, and actionable.'''

        implementation_roadmap_prompt = "Please give me an implementation roadmap as JSON."
        implementation_roadmap_response = openAI.get_text_prediction(implementation_roadmap_system_prompt, implementation_roadmap_prompt)
        implementation_roadmap = clean_and_parse_json(implementation_roadmap_response)
        
        if not implementation_roadmap:
            print("Warning: Could not parse implementation roadmap, using default values")
            implementation_roadmap = {
                "launch_timeline": [],
                "budget_estimates": [],
                "vendor_recommendations": [],
                "quality_assurance": []
            }

        # ========== Generate Digital Specifications ==========
        digital_specs_system_prompt = f'''You are a technical specifications expert. Here is a list of questions we asked the user and here are the answers they gave: >>>
        {question_and_answers} 
        <<<. Here is the previously generated brand identity for this brand (including colors, typography, etc): >>>
        {previously_generated_brand_identity}
        <<<. Generate digital specifications in the following JSON structure:
        {{
            "file_format_guidelines": [
                {{
                    "format": "string",
                    "use_case": "string",
                    "specifications": "string",
                    "file_naming": "string"
                }}
            ],
            "color_profiles": [
                {{
                    "profile_type": "string",
                    "color_values": "string",
                    "usage_context": "string",
                    "conversion_notes": "string"
                }}
            ],
            "print_specifications": [
                {{
                    "material": "string",
                    "bleed": "string",
                    "margins": "string",
                    "resolution": "string",
                    "color_mode": "string"
                }}
            ],
            "digital_specifications": [
                {{
                    "platform": "string",
                    "dimensions": "string",
                    "file_size": "string",
                    "format": "string",
                    "optimization_notes": "string"
                }}
            ]
        }}
        
        Make the specifications technical, accurate, and industry-standard.'''

        digital_specs_prompt = "Please give me digital specifications as JSON."
        digital_specs_response = openAI.get_text_prediction(digital_specs_system_prompt, digital_specs_prompt)
        digital_specifications = clean_and_parse_json(digital_specs_response)
        
        if not digital_specifications:
            print("Warning: Could not parse digital specifications, using default values")
            digital_specifications = {
                "file_format_guidelines": [],
                "color_profiles": [],
                "print_specifications": [],
                "digital_specifications": []
            }

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
                "marketing_templates": marketing_templates,
                "business_strategy": business_strategy,
                "implementation_roadmap": implementation_roadmap,
                "digital_specifications": digital_specifications
            }
        }
        
        # Save to database
        db.create_brand_assets(brandId, userId, results["full_brand_identity"], results["social_media_content"], results["premium_assets"])
        
        
        
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
# print(generate_final_results("24d0c547-8685-4ee9-95a4-b362da16da3c", "96266589-80bb-4f14-aff9-6baf8cc4dffd", "Kum Randy", "myemail@gmail.com", "652932842", "", "www.toothai.com", "https://logomoose.com/wp-content/uploads/2016/01/18.jpg"))
