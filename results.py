import os
import db
import questions
import openAI
import json
import imagen
import functions
import uuid
import setup







# Function to check keys
def check_keys(data, expected_structure):
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



















def generate_results(userId, brandId):
    
    user = db.get_user(userId)
    brand = db.get_brand(brandId)
    answers = db.get_answer(brand["answerId"])
    
    previous_questions = questions.get_previous_questions(5, 1)
    previous_answers = db.get_previous_answers(answers["answerId"], 5, 1)
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
    } <<< Make sure to generate the values for the different parts. Replace sss with the values you generate and lll with a list of values. Make sure you replace sss with strings. Do not use any other format or add any other information. Make sure to generate the values for the different parts, using information from the questions and answers. Make sure to respect the json format and do not add any other information. Be more elaborate with the responses, dont be too brief. Make it sound legit and good. Your resonses should not just be single sentences. Try to write a paragraph of valuable information sometimes. Sound more human as possible. Make it serious and not just rushed'''
            
    prompt = "Please give me my branding strategy as json, and make sure to fill the information in the json as pecified"

    passed = False
    while passed == False:
        print("Processing section ...")
        response = openAI.get_text_prediction(system_prompt, prompt)
        response = json.loads(response)
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
        response = json.loads(response)
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
        response = json.loads(response)
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
        response = json.loads(response)
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
            "application_type": "Website",
            "prompt": sss,
        })
    } <<< For the logo prompts, make sure to write a detailed description of the logo for the best result, straight forward detailed instructions that will yield the best result for an AI image generation model to use, the logos should be very professional, creative and attrative, no simple logos or empty logos, just logos that are straight up creative and very good, either with an icon, or decorated initials or any other, be creative, specify the brand name, also mention the tagline, if necessary, not all logos should have a tagline under. Brand name: '''+brand_name+''', tagline: '''+brand_tagline+'''. The application prompt is to illustrate a couple items like shirts, mugs or the like, with the logo on them, put between 3 to 5 applications, be very detailed about where to put the logo, size, position and the like, on the object, we are passing the logo along with this prompt so be direct and just tell the ai what to do with the logo, the application prompt is standalone, and carries all details, it is supposed to prompt the model to generate the item, describing the item and its evironment in full detail, as well as where to put the logo, do not use words that other AI's will think are sensitive. Make sure each font object in the list of fonts has just one font. Make sure to generate the values for the different parts. Replace sss with the string values you generate and lll with a list. Make sure you replace sss with strings. Do not use any other format or add any other information. Make sure to generate the values for the different parts, using information from the questions and answers. Make sure to respect the json format and do not add any other information. Be more elaborate with the responses, dont be too brief. Make it sound legit and good. Your resonses should not just be single sentences. Try to write a paragraph of valuable information sometimes. Sound more human as possible. Make it serious and not just rushed'''
            
    prompt = "Please give me the communication for my brand as json, and make sure to fill the information in the json as pecified"
    # response = openAI.get_text_prediction(system_prompt, prompt)
    # print(response)
    # raise Exception("Error")
    logo_prompt1 = ""
    logo_prompt2 = ""
    logo_prompt3 = ""
    
    passed = False
    while passed == False:
        print("Processing section ...")
        response = openAI.get_text_prediction(system_prompt, prompt)
        response = json.loads(response)
        # Define the expected structure
        expected_structure = {
            "about_the_brand": [],
            "logos": ["prompt", "description"],
            "primary_colors": [],
            "secondary_colors": [],
            "typography": [],
            "applications": []
        }
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
    # ...existing code...


    generated_logo_1 = imagen.generate_replicate_image(logo_prompt1)
    filename1 = str(uuid.uuid4()) + ".jpg"
    downloaded_logo_path1 = functions.download_image(generated_logo_1, "images", filename1)
    logo_url_1 = setup.server_address + "/image/" + filename1
    
    generated_logo_2 = imagen.generate_replicate_image(logo_prompt2)
    filename2 = str(uuid.uuid4()) + ".jpg"
    downloaded_logo_path2 = functions.download_image(generated_logo_2, "images", filename2)
    logo_url_2 = setup.server_address + "/image/" + filename2
    
    generated_logo_3 = imagen.generate_replicate_image(logo_prompt3)
    filename3 = str(uuid.uuid4()) + ".jpg"
    downloaded_logo_path3 = functions.download_image(generated_logo_3, "images", filename3)
    logo_url_3 = setup.server_address + "/image/" + filename3
    











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
            "applications": applications
        },
        "marketing_and_social_media_strategy": {
            "content_calender": content_calender
        }
    }
    
    
    db.update_brand(brandId, "brand_strategy", json.dumps(results["brand_strategy"]))
    db.update_brand(brandId, "brand_communication", json.dumps(results["brand_communication"]))
    db.update_brand(brandId, "brand_identity", json.dumps(results["brand_identity"]))
    db.update_brand(brandId, "marketing_and_social_media_strategy", json.dumps(results["marketing_and_social_media_strategy"]))
    
    
    
    return results




# print(generate_results("72aa6589-0cdb-4795-acf3-b0db2a8d7fad", "7be4efdc-7d3d-4344-b823-8300f6e81bb0"))
# print("\n\n\n\n"+str(db.get_brand("7be4efdc-7d3d-4344-b823-8300f6e81bb0")))

# generate_results("72aa6589-0cdb-4795-acf3-b0db2a8d7fad", "7be4efdc-7d3d-4344-b823-8300f6e81bb0")