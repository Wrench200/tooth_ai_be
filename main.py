from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import db
import questions
import openAI
import suggestions
import json
import os
import results






app = Flask(__name__)
CORS(
    app,
    origins=[
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://localhost:5173", "http://127.0.0.1:5173",
        "https://brand-app-psi.vercel.app","https://www.toothai.site"
    ],  # Add your frontend URLs
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
    supports_credentials=True)


@app.route('/', methods=['GET'])
def home():
    return 'Welcome to the Flask App!'





@app.route('/send_answer', methods=['POST'])
def send_answer():
    data = request.get_json()
    # data = {
    #     'question': 1,
    #     'section': 1,
    #     'answer': 'This is a sample answer.',
    #     'userId': 'userId',
    #     'brandId': 'brandId'
    # }

    sectionNumber = data['section']
    questionNumber = data['question']

    brand = db.get_brand(data['brandId'])
    answer = data['answer']
    question = questions.get_question(sectionNumber, questionNumber)

    response = openAI.validate_answer(question, answer)
    # print(response)
    if isinstance(response, str):
        response = json.loads(response)

    if not response["error"]:
        db.update_answer(brand['answerId'], sectionNumber, questionNumber,
                         answer)
        return response, 200
    else:
        return response, 400






@app.route('/get_suggestions', methods=['POST'])
def get_suggestions():
    data = request.get_json()
    # data = {
    #     'question': 1,
    #     'section': 1,
    #     'brandId': 'brandId',
    #     'userId': 'userId'
    # }

    user = db.get_user(data['userId'])
    brand = db.get_brand(data['brandId'])
    answer = db.get_answer(brand['answerId'])
    sectionNumber = data['section']
    questionNumber = data['question']

    if sectionNumber == 1 and questionNumber == 1:
        return jsonify(
            {'error': 'No suggestions available for this question.'}), 400

    mySuggestions = suggestions.generate_suggestions(sectionNumber,
                                                     questionNumber,
                                                     answer['answerId'])
    mySuggestions = json.loads(mySuggestions)

    if not "error" in mySuggestions:
        mySuggestions = {
            'question': 1,
            'section': 1,
            'userId': 'userId',
            'suggestions': mySuggestions
        }
        return jsonify(mySuggestions)





@app.route('/register_user', methods=['POST'])
def register_user():
    try:
        data = request.get_json()
        
        # data ={
        #     "userName": "user4",
        #     "email": "email4",
        #     "password": "password4"
        # }   

        # Check if JSON data is provided
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        # Check for required fields
        required_fields = ['userName', 'email', 'password']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400

        # Check if user already exists
        if db.get_user_from_email(data['email']):
            return jsonify({'error':
                            'User with this email already exists'}), 400

        # Create user
        user = db.create_user(data['userName'], data['email'],
                              data['password'])

        if user:
            return jsonify({
                'success': True,
                'message': 'User registered successfully',
                'user': user
            }), 201
        else:
            return jsonify({'error': 'Failed to create user'}), 500

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500







@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        # data = {
        #     "email": "email4",
        #     "password": "password4"
        # }

        # Check if JSON data is provided
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        # Check for required fields
        if 'email' not in data or not data['email']:
            return jsonify({'error': 'Email is required'}), 400

        if 'password' not in data or not data['password']:
            return jsonify({'error': 'Password is required'}), 400

        # Check if user exists
        user = db.get_user_from_email(data['email'])
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Check password
        if user['password'] != data['password']:
            return jsonify({'error': 'Incorrect password'}), 401

        # Login successful
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': user
        }), 200

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500





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
    
    response = results.generate_results(userId, brandId)

    return jsonify(response), 200





@app.route('/image/<filename>', methods=['GET'])
def get_image(filename):
    image_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')
    return send_from_directory(image_folder, filename)







if __name__ == '__main__':
    # Run on host 0.0.0.0 to be accessible from outside, port 8080
    app.run(host='0.0.0.0', port=8080, debug=True)
