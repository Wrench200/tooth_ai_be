from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import db
import questions
import openAI
import suggestions
import json
import os
import results
import cloudinary_utils
import time
import traceback
from db import get_global_question_number






app = Flask(__name__)
CORS(
    app,
    origins="*",  # Add your frontend URLs
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
    supports_credentials=True)


@app.route('/', methods=['GET'])
def home():
    return 'Welcome to the Flask App!'

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint to keep the app awake"""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'message': 'ToothAI API is running'
    })





@app.route('/send_answer', methods=['POST'])
def send_answer():
    data = request.get_json()
    # data = {
    #     'question': 1,
    #     'section': 2,  # Add this field
    #     'answer': 'This is a sample answer.',
    #     'userId': 'userId',
    #     'brandId': 'brandId'
    # }

    # Map frontend question to backend question number
    section_number = data.get('section', 1)  # Default to section 1 if not provided
    frontend_question_number = data['question']
    backend_question_number = map_frontend_to_backend_question(section_number, frontend_question_number)
    global_question_number = get_global_question_number(section_number, frontend_question_number)
    
    if backend_question_number is None:
        return jsonify({'error': f'Invalid section/question combination: section {section_number}, question {frontend_question_number}'}), 400

    brand = db.get_brand(data['brandId'])
    
    # Debug: Print the brand object to see its structure
    print("Brand object:", brand)
    
    if not brand:
        return jsonify({'error': 'Brand not found'}), 404
    
    if 'answerid' not in brand or not brand['answerid']:
        return jsonify({'error': 'Brand has no answerId - answers creation failed'}), 500
    
    answer = data['answer']
    question = questions.get_question(backend_question_number)

    response = openAI.validate_answer(question, answer)
    if isinstance(response, str):
        start = response.find('{')
        end = response.rfind('}') + 1
        if start != -1 and end != -1:
            json_str = response[start:end]
            response = json.loads(json_str)
            print(response)
        else:
            print("No JSON found")

    if not response["error"]:
        db.update_answer(brand['answerid'], global_question_number, answer)
        return response, 200
    else:
        return response, 400






def map_frontend_to_backend_question(section_number, question_number):
    """
    Map frontend section/question numbers to backend question numbers.
    
    Frontend structure:
    - Section 1 (Brand Strategy): Questions 1-5 → Backend: 1-5
    - Section 2 (Brand Communication): Questions 1-2 → Backend: 6-7
    - Section 3 (Brand Identity): Questions 1-1 → Backend: 8
    - Section 4 (Marketing Content): Questions 1-2 → Backend: 9-10
    """
    section_mappings = {
        1: [1, 2, 3, 4, 5],      # Brand Strategy
        2: [6, 7],               # Brand Communication
        3: [8],                  # Brand Identity
        4: [9, 10]               # Marketing Content
    }
    
    if section_number in section_mappings and 1 <= question_number <= len(section_mappings[section_number]):
        return section_mappings[section_number][question_number - 1]
    else:
        return None


@app.route('/get_suggestions', methods=['POST'])
def get_suggestions():
    data = request.get_json()
    # data = {
    #     'question': 1,
    #     'section': 2,  # Add this field
    #     'brandId': 'brandId',
    #     'userId': 'userId'
    # }

    user = db.get_user(data['userId'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    brand = db.get_brand(data['brandId'])
    if not brand:
        return jsonify({'error': 'Brand not found'}), 404
    
    answer = db.get_answer(brand['answerid'])
    if not answer:
        return jsonify({'error': 'Answer not found'}), 404
    
    # Map frontend question to backend question number
    section_number = data.get('section', 1)  # Default to section 1 if not provided
    frontend_question_number = data['question']
    backend_question_number = map_frontend_to_backend_question(section_number, frontend_question_number)
    
    if backend_question_number is None:
        return jsonify({'error': f'Invalid section/question combination: section {section_number}, question {frontend_question_number}'}), 400
    
    # Debug: Print the values being passed
    print(f"get_suggestions debug:")
    print(f"  frontend section: {section_number}, question: {frontend_question_number}")
    print(f"  backend question: {backend_question_number}")
    print(f"  answer['answerId']: {answer.get('answerId', 'NOT FOUND')}")
    print(f"  answer keys: {list(answer.keys())}")

    if backend_question_number == 1:
        return jsonify({'error': 'No suggestions available for this question.'}), 400

    try:
        # Use new signature for generate_suggestions
        mySuggestions = suggestions.generate_suggestions(section_number, frontend_question_number, answer['answerId'])
        print(f"  suggestions result: {mySuggestions}")
        
        if isinstance(mySuggestions, str):
            mySuggestions = json.loads(mySuggestions)
        
        if not "error" in mySuggestions:
            mySuggestions = {
                'question': frontend_question_number,
                'section': section_number,
                'userId': data['userId'],
                'suggestions': mySuggestions
            }
            return jsonify(mySuggestions)
        else:
            return jsonify(mySuggestions), 400
    except Exception as e:
        print(f"Error in get_suggestions: {e}")
        return jsonify({'error': f'Suggestions generation failed: {str(e)}'}), 500





@app.route('/register_user', methods=['POST'])
def register_user():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        required_fields = ['userName', 'email', 'password']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400
        try:
            if db.get_user_from_email(data['email']):
                return jsonify({'error': 'User with this email already exists'}), 400
        except Exception as e:
            print("REGISTER ERROR (db.get_user_from_email):", e)
            traceback.print_exc()
            return jsonify({'error': 'Database error during user lookup', 'details': str(e)}), 500
        try:
            user = db.create_user(data['userName'], data['email'], data['password'])
        except Exception as e:
            print("REGISTER ERROR (db.create_user):", e)
            traceback.print_exc()
            return jsonify({'error': 'Database error during user creation', 'details': str(e)}), 500
        if user:
            # Ensure user is serializable and has required keys
            if not isinstance(user, dict):
                print("REGISTER ERROR: User object is not a dict", user)
                return jsonify({'error': 'User object is not a valid dictionary', 'raw': str(user)}), 500
            for key in ['userId', 'username', 'email']:
                if key not in user:
                    print(f"REGISTER ERROR: Missing key in user object: {key}")
                    return jsonify({'error': f'Missing key in user object: {key}', 'raw': user}), 500
            try:
                return jsonify({
                    'success': True,
                    'message': 'User registered successfully',
                    'user': user
                }), 201
            except Exception as e:
                print("REGISTER ERROR (jsonify):", e)
                traceback.print_exc()
                return jsonify({'error': 'Failed to serialize user object', 'details': str(e), 'raw': user}), 500
        else:
            print("REGISTER ERROR: Failed to create user (no user object returned)")
            return jsonify({'error': 'Failed to create user'}), 500
    except Exception as e:
        print("REGISTER ERROR (outer):", e)
        traceback.print_exc()
        return jsonify({'error': 'Unexpected error during registration', 'details': str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        if 'email' not in data or not data['email']:
            return jsonify({'error': 'Email is required'}), 400
        if 'password' not in data or not data['password']:
            return jsonify({'error': 'Password is required'}), 400
        try:
            user = db.get_user_from_email(data['email'])
        except Exception as e:
            print("LOGIN ERROR (db.get_user_from_email):", e)
            traceback.print_exc()
            return jsonify({'error': 'Database error during user lookup', 'details': str(e)}), 500
        if not user:
            return jsonify({'error': 'User not found'}), 404
        if not isinstance(user, dict):
            print("LOGIN ERROR: User object is not a dict", user)
            return jsonify({'error': 'User object is not a valid dictionary', 'raw': str(user)}), 500
        if 'password' not in user:
            print("LOGIN ERROR: User object missing password key", user)
            return jsonify({'error': 'User object missing password key', 'raw': user}), 500
        if user['password'] != data['password']:
            return jsonify({'error': 'Incorrect password'}), 401
        try:
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': user
            }), 200
        except Exception as e:
            print("LOGIN ERROR (jsonify):", e)
            traceback.print_exc()
            return jsonify({'error': 'Failed to serialize user object', 'details': str(e), 'raw': user}), 500
    except Exception as e:
        print("LOGIN ERROR (outer):", e)
        traceback.print_exc()
        return jsonify({'error': 'Unexpected error during login', 'details': str(e)}), 500





@app.route('/user', methods=['POST'])
def user():
    data = request.get_json()
    # data = {
    #     'userId': 'userId',
    # }

    user = db.get_user(data['userId'])

    return jsonify(user), 200






@app.route('/user_brands', methods=['POST'])
def user_brands():
    data = request.get_json()
    # data = {
    #     'userId': 'userId',
    # }

    brands = db.get_all_user_brands(data['userId'])
    response = {'userId': data['userId'], 'brands': brands}

    return jsonify(response), 200





@app.route('/brand', methods=['POST'])
def brand():
    data = request.get_json()
    # data = {
    #     'brandId': 'brandId',
    # }

    brand = db.get_brand(data["brandId"])

    return jsonify(brand), 200






@app.route('/create_brand', methods=['POST'])
def create_brand():
    data = request.get_json()
    # data = {
    #     'userId': 'userId',
    # }

    brand = db.create_brand(data['userId'])

    return jsonify({
        'success': True,
        'message': 'success',
        'brand': brand
    }), 200
    
    
    
    
@app.route('/get_results', methods=['POST'])
def get_results():
    data = request.get_json()
    # data = {
    #     'userId': 'userId',
    #     'brandId': 'brandId'
    # }

    brandId = data['brandId']
    userId = data['userId']
    
    try:
        # Set a longer timeout for this operation
        response = results.generate_results(userId, brandId)
        return jsonify(response), 200
    except Exception as e:
        print(f"Error in get_results: {e}")
        return jsonify({
            'error': 'Results generation failed. Please try again.',
            'details': str(e)
        }), 500





@app.route('/image/<filename>', methods=['GET'])
def get_image(filename):
    image_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')
    return send_from_directory(image_folder, filename)

@app.route('/generate_and_upload_image', methods=['POST'])
def generate_and_upload_image():
    """
    Generate an image using Replicate API and upload it to Cloudinary
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['prompt', 'answerId', 'section', 'question', 'userId']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        answer_id = data['answerId']
        section_number = data['section']
        question_number = data['question']
        prompt = data['prompt']
        user_id = data['userId']
        
        # Verify the answer belongs to the user
        answer = db.get_answer(answer_id)
        if not answer or answer.get('userId') != user_id:
            return jsonify({'error': 'Answer not found or access denied'}), 404
        
        # Generate image using Replicate API and upload to Cloudinary
        import imagen
        public_id = f"toothai/{answer_id}/section_{section_number}_question_{question_number}"
        cloudinary_url = imagen.generate_image(prompt, public_id=public_id)
        
        if not cloudinary_url:
            return jsonify({'error': 'Failed to generate and upload image'}), 500
        
        # Save to database
        success = db.save_image_url(
            answer_id,
            section_number,
            question_number,
            cloudinary_url,
            public_id
        )
        
        if not success:
            return jsonify({'error': 'Failed to save image URL to database'}), 500
        
        return jsonify({
            'success': True,
            'image_url': cloudinary_url,
            'public_id': public_id,
            'message': 'Image generated and uploaded successfully'
        })
        
    except Exception as e:
        print(f"Error in generate_and_upload_image: {e}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/get_image', methods=['POST'])
def get_image_url():
    """
    Get the Cloudinary image URL for a specific answer/question
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['answerId', 'section', 'question', 'userId']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        answer_id = data['answerId']
        section_number = data['section']
        question_number = data['question']
        user_id = data['userId']
        
        # Verify the answer belongs to the user
        answer = db.get_answer(answer_id)
        if not answer or answer.get('userId') != user_id:
            return jsonify({'error': 'Answer not found or access denied'}), 404
        
        # Get image from database
        image_data = db.get_image_url(answer_id, section_number, question_number)
        
        if not image_data:
            return jsonify({'error': 'Image not found'}), 404
        
        return jsonify({
            'success': True,
            'image_url': image_data['cloudinary_url'],
            'public_id': image_data['cloudinary_public_id'],
            'created_at': image_data['created_at'].isoformat() if image_data['created_at'] else None
        })
        
    except Exception as e:
        print(f"Error in get_image_url: {e}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/delete_image', methods=['POST'])
def delete_image():
    """
    Delete an image from Cloudinary and database
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['answerId', 'section', 'question', 'userId']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        answer_id = data['answerId']
        section_number = data['section']
        question_number = data['question']
        user_id = data['userId']
        
        # Verify the answer belongs to the user
        answer = db.get_answer(answer_id)
        if not answer or answer.get('userId') != user_id:
            return jsonify({'error': 'Answer not found or access denied'}), 404
        
        # Get image data first
        image_data = db.get_image_url(answer_id, section_number, question_number)
        
        if not image_data:
            return jsonify({'error': 'Image not found'}), 404
        
        # Delete from Cloudinary
        cloudinary_success = cloudinary_utils.delete_image(image_data['cloudinary_public_id'])
        
        # Delete from database
        db_success = db.delete_image_url(answer_id, section_number, question_number)
        
        if cloudinary_success and db_success:
            return jsonify({
                'success': True,
                'message': 'Image deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Image deletion partially failed',
                'cloudinary_deleted': cloudinary_success,
                'database_deleted': db_success
            }), 500
        
    except Exception as e:
        print(f"Error in delete_image: {e}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/get_all_images', methods=['POST'])
def get_all_images():
    """
    Get all images for a specific answer
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['answerId', 'userId']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        answer_id = data['answerId']
        user_id = data['userId']
        
        # Verify the answer belongs to the user
        answer = db.get_answer(answer_id)
        if not answer or answer.get('userId') != user_id:
            return jsonify({'error': 'Answer not found or access denied'}), 404
        
        # Get all images from database
        images = db.get_all_images_for_answer(answer_id)
        
        return jsonify({
            'success': True,
            'images': images
        })
        
    except Exception as e:
        print(f"Error in get_all_images: {e}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/status', methods=['GET'])
def app_status():
    """Get application status and uptime"""
    try:
        # Test database connection
        db_status = "healthy" if db.test_connection() else "unhealthy"
        
        return jsonify({
            'status': 'running',
            'database': db_status,
            'timestamp': time.time(),
            'uptime': 'active'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': time.time()
        }), 500

if __name__ == '__main__':
    # Run on host 0.0.0.0 to be accessible from outside, port 8080
    app.run(host='0.0.0.0', port=8080, debug=True)
