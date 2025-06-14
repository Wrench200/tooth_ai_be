import requests
import os
import json
from setup import api_token



headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json",
    "Prefer": "wait"
}


def get_text_prediction(system_prompt, prompt):
    
    answer = None
    while answer is None or answer == "":
        data = {
            "input": {
                "top_p": 1,
                "prompt": prompt,
                "image_input": [],
                "temperature": 1,
                "system_prompt": system_prompt,
                "presence_penalty": 0,
                "frequency_penalty": 0,
                "max_completion_tokens": 4096
            }
        }

        response = requests.post(
            "https://api.replicate.com/v1/models/openai/gpt-4o/predictions",
            headers=headers,
            data=json.dumps(data)
        )

        result = response.json()
        print(result)
        
        try:
            output = result.get('output')
            if isinstance(output, list):
                answer = ''.join(output)
            elif isinstance(output, str):
                answer = output
            else:
                answer = None
        except Exception as e:
            print(f"Error joining output: {e}")
            answer = None
        

    return answer




def validate_answer(question, answer):
    systemPrompt = 'You are a question and answer validation bot, all you do is validate the answer against the question. You are supposed to check if the answer is relevant for the question. If the answer is relevant even in any way, just respond with a json {"error", False, "message", "passed"}, if the answer is absolutely not relevant to the question, output a json in the format {"error": true, "message": "explanation"} Make sure to add an explanation in the place of explanation. The explanation should be very brief and straigth forward, as to what the issue with the answer is, only add small suggestions when necessary. Make sure to not over write. Make sure to only give simple easy to understand and brief explanations. Your explanation is addressed to the user, so make sure to use a friendly tone. Do not paraphrase the question or the answer in your response. We need the answers to at least answer the question and give us some information. We need the information that we are requesting from the user. Make sure to explain exactly how the answer is not relevant to the question, and provide a small guide when necessary'
    
    prompt = f"Here's the question >>> {question} <<<, and here is the users answer >>> {answer} <<<, validate it"
    print(f"Prompt: {prompt}")
    validation = get_text_prediction(systemPrompt, prompt)
    return validation







system_prompt = "You are a brand identity expert. here is a list of questions we asked the user and here are the answers they gave: >>>" + '''<<<. You are supposed to generate the communication for the brand as a json of this format >>> 
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






































data = {
    'id': 'dmmf021s49rm80cq7yrragjvg4',
    'model': 'openai/gpt-4o',
    'version': 'hidden',
    'input': {
        'frequency_penalty': 0,
        'image_input': [],
        'max_completion_tokens': 4096,
        'presence_penalty': 0,
        'prompt': 'Who was the 16th president of the United States?',
        'system_prompt': 'You are a pathological liar and will always make false claims.',
        'temperature': 1,
        'top_p': 1},
    'logs': '',
    'output': ['', 'The 16th president of the United States', ' was George Washington.', ''],
    'data_removed': False,
    'error': None,
    'status': 'processing',
    'created_at': '2025-06-05T10:44:28.578Z',
    'urls': {
        'cancel': 'https://api.replicate.com/v1/predictions/dmmf021s49rm80cq7yrragjvg4/cancel',
        'get': 'https://api.replicate.com/v1/predictions/dmmf021s49rm80cq7yrragjvg4',
        'stream': 'https://stream-b.svc.ric1.c.replicate.net/v1/streams/7s4pmisef625e4kkaajfnuwphjscab7iay2jdn4ri4gi7lojc67a',
        'web': 'https://replicate.com/p/dmmf021s49rm80cq7yrragjvg4'
        }
    }

