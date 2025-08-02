from flask import Flask, request, jsonify, send_from_directory, send_file, redirect, url_for, session
from flask_cors import CORS
import db
import questions
import openAI
import suggestions
import json
import os
import results2
import cloudinary_utils
import time
import traceback
from db import get_global_question_number
from fpdf import FPDF  # Change to fpdf2
import io, requests, os
import tempfile
import re
from google_oauth import get_google_auth_url, verify_google_token, create_flow

FONT_DIR = os.path.join(os.path.dirname(__file__), 'fonts')
UNICODE_FONT_PATH = os.path.join(FONT_DIR, 'DejaVuSans.ttf')
UNICODE_FONT_BOLD_PATH = os.path.join(FONT_DIR, 'DejaVuSans-Bold.ttf')  # Make sure this file exists
UNICODE_FONT_ITALIC_PATH = os.path.join(FONT_DIR, 'DejaVuSans-Oblique.ttf')
UNICODE_FONT_BOLD_ITALIC_PATH = os.path.join(FONT_DIR, 'DejaVuSans-BoldOblique.ttf')

def remove_emojis(text):
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002700-\U000027BF"  # Dingbats
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U00002600-\U000026FF"  # Misc symbols
        "\U00002B50-\U00002B55"  # Stars
        "\U00002300-\U000023FF"  # Misc technical
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)

class BrandPDF(FPDF):
    def header(self):
        pass
    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def add_cover(self, brand_name, brand_tagline, primary_colors=None, secondary_colors=None):
        self.add_page()
        # Gradient background (vertical from primary to secondary)
        hex_primary = primary_colors[0].get('hex_value', '#1E90FF') if primary_colors else '#1E90FF'
        hex_secondary = secondary_colors[0].get('hex_value', '#0099CC') if secondary_colors else '#0099CC'
        r1, g1, b1 = int(hex_primary[1:3], 16), int(hex_primary[3:5], 16), int(hex_primary[5:7], 16)
        r2, g2, b2 = int(hex_secondary[1:3], 16), int(hex_secondary[3:5], 16), int(hex_secondary[5:7], 16)
        steps = 20
        for i in range(steps):
            r = int(r1 + (r2 - r1) * i / steps)
            g = int(g1 + (g2 - g1) * i / steps)
            b = int(b1 + (b2 - b1) * i / steps)
            self.set_fill_color(r, g, b)
            y = i * (self.h / steps)
            self.rect(0, y, self.w, self.h / steps + 1, style='F')
        # Fonts
        self.add_font('DejaVu', '', UNICODE_FONT_PATH, uni=True)
        self.add_font('DejaVu', 'B', UNICODE_FONT_BOLD_PATH, uni=True)
        self.add_font('DejaVu', 'I', UNICODE_FONT_ITALIC_PATH, uni=True)
        self.add_font('DejaVu', 'BI', UNICODE_FONT_BOLD_ITALIC_PATH, uni=True)
        # Centered 'Brand Blueprint'
        self.set_text_color(255, 255, 255)
        self.set_font('DejaVu', '', 20)
        self.set_y(self.h * 0.25)
        self.cell(0, 10, 'Brand Blueprint', ln=True, align='C')
        # White underline
        y_underline = self.get_y() + 0.4
        self.set_draw_color(255, 255, 255)
        self.set_line_width(0.7)
        self.line(self.w * 0.37, y_underline, self.w * 0.638, y_underline)
        # 'For: {brand_name}'
        self.set_y(y_underline + 8)
        self.set_font('DejaVu', 'B', 28)
        self.cell(0, 14, f'{brand_name}', ln=True, align='C')
        # Tagline (italic, smaller, white)
        self.set_y(self.get_y() + 2)
        self.set_font('DejaVu', 'I', 14)
        self.set_text_color(255, 255, 255)
        self.cell(0, 12, f'"{brand_tagline}"', ln=True, align='C')
        self.set_text_color(0, 0, 0)

    def add_section_title(self, title, emphasize=False, color=None):
       self.add_font('DejaVu', 'B', UNICODE_FONT_PATH, uni=True)
       self.set_font('DejaVu', 'B', 18)
       if color:
        self.set_text_color(*color)
       else:
        self.set_text_color(40, 40, 120) if emphasize else self.set_text_color(0, 0, 0)
       self.cell(0, 12, remove_emojis(title), ln=True, align='C')
       self.set_text_color(0, 0, 0)
       self.ln(4)
       self.set_y(self.get_y() + 10)

    def add_sub_section_title(self, title, emphasize=False):
        self.add_font('DejaVu', 'B', UNICODE_FONT_BOLD_PATH, uni=True)
        self.set_font('DejaVu', 'B', 18 if emphasize else 14)
        self.set_text_color(40, 40, 120) if emphasize else self.set_text_color(0, 0, 0)
        self.cell(0, 12, remove_emojis(title), ln=True, align='L')
        self.set_text_color(0, 0, 0)
        self.ln(4)
        self.set_y(self.get_y() + 4)

    def add_key_value(self, key, value, emphasize=False):
        self.add_font('DejaVu', '', UNICODE_FONT_PATH, uni=True)
        self.set_font('DejaVu', 'B', 12 if emphasize else 11)
        self.set_fill_color(230, 230, 230)  # Light gray
        import re
        value_str = str(value).strip()
        value_str = re.sub(r'\n+', '\n', value_str)
        self.set_font('DejaVu', 'B', 12)
        # Estimate lines for value
        cell_width = self.w - self.l_margin - self.r_margin
        lines = 0
        for paragraph in value_str.split('\n'):
            if not paragraph:
                lines += 1
                continue
            string_width = self.get_string_width(remove_emojis(paragraph))
            lines += max(1, int(string_width / cell_width) + 1)
        key_height = 8
        gap_height = 3
        value_height = lines * 6  # 6 is the height used in multi_cell
        total_height = key_height + gap_height + value_height + 6  # 6 for bottom ln
        if self.get_y() + total_height > self.h - self.b_margin:
            self.add_page()
        self.cell(0, 8, remove_emojis(f"{key}"), ln=1, fill=True)
        self.ln(3)
        self.set_font('DejaVu', '', 12)
        self.multi_cell(0, 6, remove_emojis(value_str))
        self.ln(6)

    def add_color_palette(self, colors, title):
        self.add_section_title(title)
        for color in colors:
            hex_val = color.get('hex_value', '#000000')
            try:
                r = int(hex_val[1:3], 16)
                g = int(hex_val[3:5], 16)
                b = int(hex_val[5:7], 16)
            except Exception:
                r, g, b = 0, 0, 0
            self.set_fill_color(r, g, b)
            self.cell(20, 10, '', 0, 0, '', True)
            self.set_font('DejaVu', '', 12)
            self.cell(0, 10, remove_emojis(f"{color.get('color_name', '')} ({hex_val}) - {color.get('description', '')}"), ln=1)
        self.ln(2)

    def add_logo_images(self, logos):
        self.add_sub_section_title("Logos")
        for logo in logos:
            url = logo.get('image_url') or logo.get('url') or logo.get('cloudinary_url')
            if url:
                try:
                    response = requests.get(url)
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_img:
                        tmp_img.write(response.content)
                        tmp_img.flush()
                        tmp_img_path = tmp_img.name
                    self.image(tmp_img_path, w=40)
                    os.remove(tmp_img_path)
                except Exception as e:
                    print(f"Error loading image {url}: {e}")
                    self.set_font('DejaVu', '', 10)
                    self.cell(0, 8, '[Image could not be loaded]', ln=1)
            self.ln(2)
            self.set_font('DejaVu', '', 10)
            self.multi_cell(0, 8, remove_emojis(logo.get('description', '')))
            self.ln(4)

    def add_typography(self, typography):
        self.add_sub_section_title("Typography")
        import os
        font_dir = FONT_DIR
        for font in typography:
            font_family = font.get('font_family', 'DejaVu')
            font_weight = font.get('font_weight', '').lower()
            font_size = font.get('font_size', '16px')
            font_size_num = 16
            try:
                font_size_num = int(''.join([c for c in font_size if c.isdigit()]))
            except Exception:
                font_size_num = 16
            line_height = font.get('line_height', '')
            description = font.get('description', '')
            # Try to register the font if available
            font_file = None
            font_style = ''
            if font_weight in ['bold', 'b']:
                font_style = 'B'
            elif font_weight in ['italic', 'i']:
                font_style = 'I'
            elif font_weight in ['bolditalic', 'bi', 'ib']:
                font_style = 'BI'
            # Try to find a matching font file in fonts dir
            font_file_candidates = [
                os.path.join(font_dir, f"{font_family.replace(' ', '')}-{font_style}.ttf"),
                os.path.join(font_dir, f"{font_family.replace(' ', '')}.ttf"),
                os.path.join(font_dir, f"{font_family}.ttf"),
            ]
            for candidate in font_file_candidates:
                if os.path.exists(candidate):
                    font_file = candidate
                    break
            if font_file:
                try:
                    self.add_font(font_family, font_style, font_file, uni=True)
                except Exception:
                    pass
                self.set_font(font_family, font_style, font_size_num)
            else:
                # Fallback to DejaVu
                self.set_font('DejaVu', font_style, font_size_num)
            # Font name in its style
            self.cell(0, 10, f"{font_family} {font_weight.title()}", ln=1)
            # Sample text
            sample_text = "The quick brown fox jumps over the lazy dog. 1234567890"
            self.cell(0, 10, sample_text, ln=1)
            # Font details
            self.set_font('DejaVu', '', 11)
            self.cell(0, 8, f"Size: {font_size}   |   Line Height: {line_height}", ln=1)
            self.multi_cell(0, 8, remove_emojis(description))
            self.ln(4)

    def add_content_calendar(self, calendar_entries, max_entries=5):
        self.add_section_title("Content Calendar Sample")
        if not calendar_entries:
            self.set_font('DejaVu', '', 11)
            self.cell(0, 8, "No content calendar entries available.", ln=1)
            return
        # Table headers
        headers = ["Date", "Event", "Design concept", "Caption"]
        col_widths = [35, 35, 60, 60]
        self.set_font('DejaVu', 'B', 11)
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 8, remove_emojis(header), border=1, align='C')
        self.ln()
        self.set_font('DejaVu', '', 10)
        for entry in calendar_entries[:max_entries]:
            self.cell(col_widths[0], 8, remove_emojis(str(entry.get('Date', ''))), border=1)
            self.cell(col_widths[1], 8, remove_emojis(str(entry.get('Event', ''))), border=1)
            self.cell(col_widths[2], 8, remove_emojis(str(entry.get('Design concept', ''))), border=1)
            self.cell(col_widths[3], 8, remove_emojis(str(entry.get('Caption', ''))), border=1)
            self.ln()
        self.ln(2)

    def add_color_section(self, colors, description=None, circle_diameter=70, section_title="Colour", subtitle="Primary Colour", title_align='L', subtitle_align='C'):
        # Section title
        if section_title:
            self.set_font('DejaVu', 'B', 32)
            self.set_text_color(40, 40, 40)
            self.cell(0, 30, section_title, ln=True, align=title_align)
            self.ln(5)
        # Subtitle
        if subtitle:
            self.set_font('DejaVu', 'B', 18)
            self.cell(0, 10, subtitle, ln=True, align=subtitle_align)
            self.ln(10)
        # Draw circles for each color
        page_width = self.w - self.l_margin - self.r_margin
        n = len(colors)
        # Calculate gap so all circles fit on one row
        if n > 1:
            gap = max(20, (page_width - n * circle_diameter) // (n - 1))
        else:
            gap = 0
        total_width = n * circle_diameter + (n - 1) * gap
        start_x = (self.w - total_width) / 2
        y = self.get_y()
        for i, color in enumerate(colors):
            x = start_x + i * (circle_diameter + gap)
            hex_val = color.get('hex_value', '#000000')
            r = int(hex_val[1:3], 16)
            g = int(hex_val[3:5], 16)
            b = int(hex_val[5:7], 16)
            # Draw circle
            self.set_fill_color(r, g, b)
            self.ellipse(x, y, circle_diameter, circle_diameter, style='F')
            # Hex code in center
            self.set_xy(x, y + circle_diameter / 2 - 6)
            self.set_text_color(255, 255, 255)
            self.set_font('DejaVu', 'B', 14)
            self.cell(circle_diameter, 12, hex_val, align='C', ln=0)
            # Label below
            self.set_xy(x, y + circle_diameter + 2)
            self.set_text_color(40, 40, 40)
            self.set_font('DejaVu', 'B', 12)
            self.multi_cell(circle_diameter, 7, color.get('color_name', ''), align='C')
        # Move below the circles for the description (if any)
        if description:
            self.set_y(y + circle_diameter + 30)
            self.set_font('DejaVu', '', 12)
            self.set_text_color(40, 40, 40)
            self.multi_cell(0, 8, description, align='C')
            self.ln(10)
        else:
            self.set_y(y + circle_diameter + 30)
            self.ln(10)

    def add_recommended_logo(self, logo_url, description=None):
        self.add_sub_section_title("Recommended Logo")
        if logo_url and not logo_url.lower().startswith("error"): 
            try:
                response = requests.get(logo_url)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_img:
                    tmp_img.write(response.content)
                    tmp_img.flush()
                    tmp_img_path = tmp_img.name
                self.image(tmp_img_path, w=60)
                os.remove(tmp_img_path)
            except Exception as e:
                print(f"Error loading recommended logo {logo_url}: {e}")
                self.set_font('DejaVu', '', 10)
                self.cell(0, 8, '[Image could not be loaded]', ln=1)
        if description:
            self.set_font('DejaVu', '', 10)
            self.multi_cell(0, 8, remove_emojis(description))
        self.ln(4)

    def add_logo_variants(self, variants):
        self.add_sub_section_title("Logo Variants")
        if not variants or all(v.lower().startswith("error") for v in variants):
            self.set_font('DejaVu', '', 10)
            self.cell(0, 8, "No logo variants available.", ln=1)
            return
        for v in variants:
            if v and not v.lower().startswith("error"):
                try:
                    response = requests.get(v)
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_img:
                        tmp_img.write(response.content)
                        tmp_img.flush()
                        tmp_img_path = tmp_img.name
                    self.image(tmp_img_path, w=40)
                    os.remove(tmp_img_path)
                except Exception as e:
                    print(f"Error loading logo variant {v}: {e}")
                    self.set_font('DejaVu', '', 10)
                    self.cell(0, 8, '[Image could not be loaded]', ln=1)
                self.ln(2)
        self.ln(4)

    def add_applications(self, applications):
        self.add_sub_section_title("Applications")
        if not applications or all(a.get('image_url', '').lower().startswith("error") for a in applications):
            self.set_font('DejaVu', '', 10)
            self.cell(0, 8, "No application images available.", ln=1)
            return
        for app in applications:
            url = app.get('image_url', '')
            app_type = app.get('application_type', '')
            if url and not url.lower().startswith("error"):
                self.add_page()
                try:
                    response = requests.get(url)
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_img:
                        tmp_img.write(response.content)
                        tmp_img.flush()
                        tmp_img_path = tmp_img.name
                    # Calculate max width/height with margin
                    margin = 15
                    max_width = self.w - 2 * margin
                    max_height = self.h - 2 * margin - 20  # leave space for caption
                    # Get image size
                    from PIL import Image
                    img = Image.open(tmp_img_path)
                    img_w, img_h = img.size
                    aspect = img_w / img_h
                    if max_width / aspect <= max_height:
                        display_w = max_width
                        display_h = max_width / aspect
                    else:
                        display_h = max_height
                        display_w = max_height * aspect
                    x = (self.w - display_w) / 2
                    y = margin
                    self.image(tmp_img_path, x=x, y=y, w=display_w, h=display_h)
                    os.remove(tmp_img_path)
                except Exception as e:
                    print(f"Error loading application image {url}: {e}")
                    self.set_font('DejaVu', '', 10)
                    self.cell(0, 8, '[Image could not be loaded]', ln=1)
                # Caption below image
                if app_type:
                    self.set_y(y + display_h + 5)
                    self.set_font('DejaVu', 'B', 14)
                    self.cell(0, 12, remove_emojis(app_type), ln=1, align='C')
                self.ln(4)


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
    """
    Register a new user with comprehensive validation and error handling
    """
    try:
        # Validate request format
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['userName', 'email', 'password']
        missing_fields = []
        for field in required_fields:
            if field not in data or not data[field]:
                missing_fields.append(field)
        
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Extract and sanitize input
        username = str(data['userName']).strip()
        email = str(data['email']).strip().lower()
        password = str(data['password'])
        
        # Validate username
        if len(username) < 2:
            return jsonify({
                'success': False,
                'error': 'Username must be at least 2 characters long'
            }), 400
        
        if len(username) > 50:
            return jsonify({
                'success': False,
                'error': 'Username must be less than 50 characters'
            }), 400
        
        # Validate email format
        import re
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(email):
            return jsonify({
                'success': False,
                'error': 'Invalid email format'
            }), 400
        
        # Validate password strength
        if len(password) < 6:
            return jsonify({
                'success': False,
                'error': 'Password must be at least 6 characters long'
            }), 400
        
        if len(password) > 128:
            return jsonify({
                'success': False,
                'error': 'Password must be less than 128 characters'
            }), 400
        
        # Check if user already exists
        try:
            existing_user = db.get_user_from_email(email)
            if existing_user:
                return jsonify({
                    'success': False,
                    'error': 'User with this email already exists'
                }), 409
        except Exception as e:
            print(f"REGISTER ERROR (db.get_user_from_email): {e}")
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': 'Database error during user lookup'
            }), 500
        
        # Create user
        try:
            user = db.create_user(username, email, password)
        except Exception as e:
            print(f"REGISTER ERROR (db.create_user): {e}")
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': 'Database error during user creation'
            }), 500
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'Failed to create user'
            }), 500
        
        # Validate user object structure
        if not isinstance(user, dict):
            print(f"REGISTER ERROR: User object is not a dict: {user}")
            return jsonify({
                'success': False,
                'error': 'Invalid user object returned from database'
            }), 500
        
        required_user_keys = ['userId', 'username', 'email']
        missing_keys = [key for key in required_user_keys if key not in user]
        if missing_keys:
            print(f"REGISTER ERROR: Missing keys in user object: {missing_keys}")
            return jsonify({
                'success': False,
                'error': f'Invalid user object structure: missing {", ".join(missing_keys)}'
            }), 500
        
        # Remove password from response for security
        user_response = {
            'userId': user['userId'],
            'username': user['username'],
            'email': user['email']
        }
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'user': user_response
        }), 201
        
    except Exception as e:
        print(f"REGISTER ERROR (unexpected): {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'Unexpected error during registration'
        }), 500

@app.route('/login', methods=['POST'])
def login():
    """
    Authenticate user with comprehensive validation and error handling
    """
    try:
        # Validate request format
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        # Validate required fields
        if 'email' not in data or not data['email']:
            return jsonify({
                'success': False,
                'error': 'Email is required'
            }), 400
        
        if 'password' not in data or not data['password']:
            return jsonify({
                'success': False,
                'error': 'Password is required'
            }), 400
        
        # Extract and sanitize input
        email = str(data['email']).strip().lower()
        password = str(data['password'])
        
        # Validate email format
        import re
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(email):
            return jsonify({
                'success': False,
                'error': 'Invalid email format'
            }), 400
        
        # Validate password is not empty
        if not password:
            return jsonify({
                'success': False,
                'error': 'Password cannot be empty'
            }), 400
        
        # Get user from database
        try:
            user = db.get_user_from_email(email)
        except Exception as e:
            print(f"LOGIN ERROR (db.get_user_from_email): {e}")
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': 'Database error during user lookup'
            }), 500
        
        # Check if user exists
        if not user:
            return jsonify({
                'success': False,
                'error': 'Invalid email or password'
            }), 401
        
        # Validate user object structure
        if not isinstance(user, dict):
            print(f"LOGIN ERROR: User object is not a dict: {user}")
            return jsonify({
                'success': False,
                'error': 'Invalid user object returned from database'
            }), 500
        
        if 'password' not in user:
            print(f"LOGIN ERROR: User object missing password key: {user}")
            return jsonify({
                'success': False,
                'error': 'Invalid user object structure'
            }), 500
        
        # Verify password
        if user['password'] != password:
            return jsonify({
                'success': False,
                'error': 'Invalid email or password'
            }), 401
        
        # Remove password from response for security
        user_response = {
            'userId': user['userid'],
            'username': user['username'],
            'email': user['email']
        }
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': user_response
        }), 200
        
    except Exception as e:
        print(f"LOGIN ERROR (unexpected): {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'Unexpected error during login'
        }), 500





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
      response = results2.generate_results(userId, brandId)
      return jsonify(response), 200
    except Exception as e:
        print(f"Error in get_results: {e}")
        return jsonify({
            'error': 'Results generation failed. Please try again.',
            'details': str(e)
        }), 500

@app.route('/get_final_results', methods=['POST'])
def get_final_results():
    """
    Generate comprehensive brand assets for paid users (full brand identity + social media content)
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['userId', 'brandId', 'userName', 'userEmail']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}',
                    'results': None
                }), 400
        
        # Extract parameters
        user_id = data['userId']
        brand_id = data['brandId']
        user_name = data['userName']
        user_email = data['userEmail']
        print(data)
        # Optional parameters with defaults
        user_phone_numbers = data.get('userPhoneNumbers', '')
        registration_number = data.get('registrationNumber', '')
        website = data.get('website', '')
        brand_logo = data.get('brandLogo', '')
        others = data.get('others', {})
        
        # Verify the brand belongs to the user
        brand = db.get_brand(brand_id)
        print("brand", brand)
        if not brand:
            return jsonify({
                'success': False,
                'message': 'Brand not found or access denied',
                'results': None
            }), 404
        
        # Import and call the generate_final_results function
        from results2 import generate_final_results
        response = generate_final_results(
            user_id, 
            brand_id, 
            user_name, 
            user_email, 
            user_phone_numbers, 
            registration_number, 
            website, 
            brand_logo, 
            others
        )
        
        if response and 'error' in response:
            return jsonify({
                'success': False,
                'message': response.get('message', 'Final results generation failed'),
                'results': None
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Final results generated successfully',
            'results': response
        }), 200
        
    except Exception as e:
        print(f"Error in get_final_results: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Final results generation failed: {str(e)}',
            'results': None
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


@app.route('/download_brand_pdf/<brandId>', methods=['GET'])
def download_brand_pdf(brandId):
    brand = db.get_brand(brandId)
    if not brand:
        return jsonify({'error': 'Brand not found'}), 404

    import json
    def parse_json_field(field):
        if isinstance(field, str):
            try:
                # Try JSON first
                return json.loads(field)
            except Exception:
                # Try CSV for content_calendar
                if '\\n' in field or '\n' in field or '\r' in field or '\r\n' in field or '\n' in field.replace('\\n', '\n'):
                    lines = field.splitlines()
                    if lines:
                        rows = [line.split('!@!') for line in lines]
                        if len(rows) > 1:
                            headers = [h.strip() for h in rows[0]]
                            return [dict(zip(headers, [cell.strip() for cell in row])) for row in rows[1:] if len(row) == len(headers)]
                return field
        return field

    # Extract and parse detailed brand fields
    brand_strategy = parse_json_field(brand.get('brand_strategy', {}))
    brand_identity = parse_json_field(brand.get('brand_identity', {}))
    brand_communication = parse_json_field(brand.get('brand_communication', {}))
    marketing = parse_json_field(brand.get('marketing_and_social_media_strategy', {}))


    # Cover page info
    brand_name = brand_communication.get('brand_name', brand.get('name', ''))
    brand_tagline = brand_communication.get('brand_tagline', '')

    primary_colors = brand_identity.get('primary_colors') if brand_identity else None
    secondary_colors = brand_identity.get('secondary_colors') if brand_identity else None
    logos = brand_identity.get('logos') if brand_identity else None
    pdf = BrandPDF()
    pdf.add_cover(brand_name, brand_tagline, primary_colors, secondary_colors)
    pdf.add_page()  # Start all other content on a new page after the cover
    primary_hex = None
    if primary_colors and isinstance(primary_colors, list) and len(primary_colors) > 0:
     primary_hex = primary_colors[0].get('hex_value', '#1E90FF')
    else:
     primary_hex = '#1E90FF'
    primary_rgb = pdf.hex_to_rgb(primary_hex)
    # Brand Communication Section
    if brand_communication:
        pdf.add_section_title("Brand Communication", True, primary_rgb)
        pdf.add_key_value("Brand Name", brand_communication.get('brand_name', ''), True)
        pdf.add_key_value("Brand Tagline", brand_communication.get('brand_tagline', ''), True)
        pcm = brand_communication.get('primary_core_message', {})
        if pcm:
            pdf.add_sub_section_title("Primary Core Message")
            pdf.add_key_value("Who We Serve", pcm.get('who_we_serve', ''))
            pdf.add_key_value("Where They Need Help", pcm.get('where_they_need_help', ''))
            pdf.add_key_value("Their Market Alternative", pcm.get('their_market_alternative', ''))
            pdf.add_key_value("Key Benefits They Get", pcm.get('the_key_benefits_they_get', ''))
            pdf.add_key_value("Our Key Differences", pcm.get('our_key_differences', ''))

    # Brand Strategy Section
    if brand_strategy:
        pdf.add_page()
        pdf.add_section_title("Brand Strategy", True, primary_rgb)
        bs = brand_strategy.get('brand_substance', {})
        if bs:
            pdf.add_sub_section_title("Brand Substance")
            op = bs.get('our_purpose', {})
            if op:
                pdf.add_key_value(op.get('title', 'Our Purpose'), op.get('purpose_statement', ''), True)
                pdf.add_key_value("What Customers Mean to Us", op.get('what_our_customers_mean_to_us', ''))
                pdf.add_key_value("We Believe In Something Bigger", op.get('we_believe_in_something_bigger_than_ourselves', ''))
            ov = bs.get('our_vision', {})
            if ov:
                pdf.add_key_value("Our Vision", ov.get('our_vision_is_bright', ''))
            om = bs.get('our_mission', {})
            if om:
                pdf.add_key_value("Our Mission", om.get('we_are_committed_to', ''))
            ovs = bs.get('our_values', {})
            if ovs:
                pdf.add_key_value("Our Values", ', '.join(ovs.get('values', [])))
                pdf.add_key_value("Values in Action", ovs.get('how_we_do_wellness_business', ''))
        # Customer Persona
        opn = brand_strategy.get('our_position', {})
        if opn:
            pdf.add_sub_section_title("Customer Persona")
            for key, label in [
                ('name', 'Name'),
                ('demographics', 'Demographics'),
                ('psychographics', 'Psychographics'),
                ('personality', 'Personality'),
                ('fears', 'Fears'),
                ('desires', 'Desires'),
                ('challenges_and_pain_points', 'Challenges and Pain Points')
            ]:
                value = opn.get(key, '')
                if value:
                    pdf.add_key_value(label, value)
        # Competitive Analysis
        if brand_strategy.get('top_competitors'):
            pdf.add_key_value("Competitive Analysis", brand_strategy.get('top_competitors'))
        # What Makes Us Different
        wmd = brand_strategy.get('why_we_are_different', {})
        if wmd:
            pdf.add_sub_section_title("What Makes Us Different")
            pdf.add_key_value("Positioning Statement", wmd.get('positioning_statement', ''), True)
            pdf.add_key_value("The Difference We Provide", wmd.get('the_difference_we_provide', ''))

    # Brand Identity Section
    if brand_identity:
        pdf.add_page()
        pdf.add_section_title("Brand Identity", True, primary_rgb)
        pdf.add_key_value("About The Brand", brand_identity.get('about_the_brand', ''), True)
        # If you want to use the new color section for primary colors:
        pdf.add_page()
        if brand_identity.get('primary_colors'):
            # Compose a description from the color objects if available
            color_descs = []
            for color in brand_identity['primary_colors']:
                desc = color.get('description', '')
                if desc:
                    color_descs.append(desc)
            description = '\n'.join(color_descs) if color_descs else ''
            pdf.add_color_section(brand_identity['primary_colors'], description, circle_diameter=70, section_title="Colors", subtitle="Primary Colors",title_align='L',subtitle_align='L')
        else:
            pdf.add_section_title("Brand Identity", True, primary_rgb)
            pdf.add_key_value("About The Brand", brand_identity.get('about_the_brand', ''), True)
        # Color Palettes (secondary colors)
        if brand_identity.get('secondary_colors'):
            pdf.add_color_section(
                brand_identity['secondary_colors'],
                description=None,
                circle_diameter=50,
                section_title="",
                subtitle="Secondary Colors",
                title_align='L',
                subtitle_align='L'
            )
        # Typography
        pdf.add_page()
        if brand_identity.get('typography'):
            pdf.add_typography(brand_identity['typography'])
        # Logos
        pdf.add_page()
        if brand_identity.get('logos'):
            pdf.add_logo_images(brand_identity['logos'])
        # Recommended Logo
        pdf.add_page()
        if brand_identity.get('reommended_logo'):
            pdf.add_recommended_logo(brand_identity['reommended_logo'])
        # Logo Variants
        if brand_identity.get('logo_variants'):
            pdf.add_logo_variants(brand_identity['logo_variants'])
        # Applications
        pdf.add_page()
        if brand_identity.get('applications'):
            pdf.add_applications(brand_identity['applications'])

    # Marketing & Social Media Section
    content_calendar = None
    if marketing:
        pdf.add_page()
        print('DEBUG: marketing type:', type(marketing), 'value:', marketing)
        pdf.add_section_title("Marketing & Social Media Strategy", True, primary_rgb)
        if isinstance(marketing, dict):
            print('marketing:', marketing)
            for key, value in marketing.items():
                print('DEBUG: marketing key:', key, 'type:', type(value))
                if key.lower() in ["strategy", "description", "summary"]:
                    pdf.add_key_value(key.replace('_', ' ').title(), value, True)
                if key.lower() in ["content_calendar", "content_calender", "contentcalender", "calendar"]:
                    content_calendar = value
            print('DEBUG: content_calendar:', content_calendar)
            if content_calendar:
                pdf.add_content_calendar(parse_json_field(content_calendar), 5)
        elif isinstance(marketing, str) and marketing.strip():
            pdf.add_key_value("Strategy", marketing.strip(), True)

    # Final note
    pdf.add_page()
    pdf.add_section_title("Implementation Guide", True, primary_rgb)
    pdf.add_key_value(
        "Next Steps",
        "This brand blueprint provides the foundation for all your marketing materials, website design, and business communications. Use these guidelines consistently across all touchpoints to build a strong, recognizable brand identity.",
        True
    )

    pdf_bytes = pdf.output(dest='S').encode('latin1')
    pdf_output = io.BytesIO(pdf_bytes)
    pdf_output.seek(0)
    return send_file(pdf_output, as_attachment=True, download_name=f"brand_{brandId}_blueprint.pdf", mimetype='application/pdf')

# ===================== Brand Assets Endpoints ===========================================

@app.route('/brand_assets', methods=['POST'])
def get_brand_assets():
    """Get brand assets for a specific brand"""
    try:
        data = request.get_json()
        if not data or 'brandId' not in data:
            return jsonify({
                'success': False,
                'message': 'brandId is required',
                'brand_assets': None
            }), 400
        
        brand_id = data['brandId']
        brand_assets = db.get_brand_assets(brand_id)
        
        if brand_assets:
            return jsonify({
                'success': True,
                'message': 'Brand assets retrieved successfully',
                'brand_assets': brand_assets
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Brand assets not found',
                'brand_assets': None
            }), 404
            
    except Exception as e:
        print(f"Error getting brand assets: {e}")
        return jsonify({
            'success': False,
            'message': f'Error retrieving brand assets: {str(e)}',
            'brand_assets': None
        }), 500

@app.route('/user_brand_assets', methods=['POST'])
def get_user_brand_assets():
    """Get all brand assets for a specific user"""
    try:
        data = request.get_json()
        if not data or 'userId' not in data:
            return jsonify({
                'success': False,
                'message': 'userId is required',
                'brand_assets': []
            }), 400
        
        user_id = data['userId']
        brand_assets = db.get_brand_assets_by_user(user_id)
        
        return jsonify({
            'success': True,
            'message': 'User brand assets retrieved successfully',
            'brand_assets': brand_assets
        }), 200
            
    except Exception as e:
        print(f"Error getting user brand assets: {e}")
        return jsonify({
            'success': False,
            'message': f'Error retrieving user brand assets: {str(e)}',
            'brand_assets': []
        }), 500

@app.route('/delete_brand_assets', methods=['POST'])
def delete_brand_assets():
    """Delete brand assets for a specific brand"""
    try:
        data = request.get_json()
        if not data or 'brandId' not in data:
            return jsonify({
                'success': False,
                'message': 'brandId is required',
                'deleted': False
            }), 400
        
        brand_id = data['brandId']
        deleted = db.delete_brand_assets(brand_id)
        
        if deleted:
            return jsonify({
                'success': True,
                'message': 'Brand assets deleted successfully',
                'deleted': True
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Brand assets not found or could not be deleted',
                'deleted': False
            }), 404
            
    except Exception as e:
        print(f"Error deleting brand assets: {e}")
        return jsonify({
            'success': False,
            'message': f'Error deleting brand assets: {str(e)}',
            'deleted': False
        }), 500

@app.route('/get_brand_results/<brand_id>', methods=['GET'])
def get_brand_results(brand_id):
    """
    Fetch complete brand results including all JSON fields from the brand table
    """
    try:
        if not brand_id:
            return jsonify({
                'success': False,
                'message': 'brandId is required',
                'brand_results': None
            }), 400
        brand = db.get_brand(brand_id)
        
        if not brand:
            return jsonify({
                'success': False,
                'message': 'Brand not found',
                'brand_results': None
            }), 404
        
        # Debug: Print available keys
        print(f"Available brand keys: {list(brand.keys())}")
        
        # Parse JSON fields if they exist
        brand_results = {
            'id': brand.get('id'),
            'userId': brand.get('userid') or brand.get('userId'),  # Try both cases
            'answerId': brand.get('answerid') or brand.get('answerId'),  # Try both cases
            'name': brand.get('name'),
            'logo': brand.get('logo')
        }
        
        # Parse JSON fields if they exist and are not empty
        brand_strategy = brand.get('brand_strategy')
        if brand_strategy:
            try:
                brand_results['brand_strategy'] = json.loads(brand_strategy)
            except (json.JSONDecodeError, TypeError):
                brand_results['brand_strategy'] = brand_strategy
        else:
            brand_results['brand_strategy'] = None
            
        brand_communication = brand.get('brand_communication')
        if brand_communication:
            try:
                brand_results['brand_communication'] = json.loads(brand_communication)
            except (json.JSONDecodeError, TypeError):
                brand_results['brand_communication'] = brand_communication
        else:
            brand_results['brand_communication'] = None
            
        brand_identity = brand.get('brand_identity')
        if brand_identity:
            try:
                brand_results['brand_identity'] = json.loads(brand_identity)
            except (json.JSONDecodeError, TypeError):
                brand_results['brand_identity'] = brand_identity
        else:
            brand_results['brand_identity'] = None
            
        marketing_strategy = brand.get('marketing_and_social_media_strategy')
        if marketing_strategy:
            try:
                brand_results['marketing_and_social_media_strategy'] = json.loads(marketing_strategy)
            except (json.JSONDecodeError, TypeError):
                brand_results['marketing_and_social_media_strategy'] = marketing_strategy
        else:
            brand_results['marketing_and_social_media_strategy'] = None
        
        return jsonify({
            'success': True,
            'message': 'Brand results retrieved successfully',
            'brand_results': brand_results
        }), 200
            
    except Exception as e:
        print(f"Error getting brand results: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error retrieving brand results: {str(e)}',
            'brand_results': None
        }), 500

# ===================== Google OAuth Endpoints ===========================================

@app.route('/auth/google', methods=['GET'])
def google_auth():
    """Initiate Google OAuth flow"""
    try:
        authorization_url, state = get_google_auth_url()
        return jsonify({
            'success': True,
            'auth_url': authorization_url,
            'state': state
        }), 200
    except Exception as e:
        print(f"Error initiating Google auth: {e}")
        return jsonify({
            'success': False,
            'message': f'Error initiating Google authentication: {str(e)}'
        }), 500

@app.route('/auth/google/callback', methods=['GET'])
def google_auth_callback():
    """Handle Google OAuth callback"""
    try:
        # Get authorization code from callback
        code = request.args.get('code')
        state = request.args.get('state')
        
        if not code:
            return jsonify({
                'success': False,
                'message': 'Authorization code not received'
            }), 400
        
        # Exchange code for tokens
        flow = create_flow()
        flow.fetch_token(code=code)
        
        # Get user info from Google
        session = flow.authorized_session()
        user_info = session.get('https://www.googleapis.com/oauth2/v2/userinfo').json()
        
        # Extract user data
        google_id = user_info['id']
        email = user_info['email']
        name = user_info.get('name', '')
        profile_picture = user_info.get('picture', '')
        
        # Check if user exists
        existing_user = db.get_user_by_google_id(google_id)
        if existing_user:
            # User exists, log them in
            user_response = {
                'userId': existing_user.get('userid') or existing_user.get('userId'),
                'username': existing_user['username'],
                'email': existing_user['email'],
                'profile_picture': existing_user.get('profile_picture'),
                'auth_provider': existing_user.get('auth_provider', 'google')
            }
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': user_response
            }), 200
        else:
            # Create new user
            new_user = db.create_google_user(google_id, email, name, profile_picture)
            if new_user:
                user_response = {
                    'userId': new_user['userId'],
                    'username': new_user['username'],
                    'email': new_user['email'],
                    'profile_picture': new_user.get('profile_picture'),
                    'auth_provider': 'google'
                }
                return jsonify({
                    'success': True,
                    'message': 'Registration successful',
                    'user': user_response
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to create user'
                }), 500
                
    except Exception as e:
        print(f"Error in Google auth callback: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error during Google authentication: {str(e)}'
        }), 500

@app.route('/auth/google/token', methods=['POST'])
def google_token_auth():
    """Authenticate with Google ID token (for mobile apps)"""
    try:
        data = request.get_json()
        if not data or 'id_token' not in data:
            return jsonify({
                'success': False,
                'message': 'ID token is required'
            }), 400
        
        # Verify the Google ID token
        user_info = verify_google_token(data['id_token'])
        if not user_info:
            return jsonify({
                'success': False,
                'message': 'Invalid Google token'
            }), 401
        
        # Check if user exists
        existing_user = db.get_user_by_google_id(user_info['google_id'])
        if existing_user:
            # User exists, log them in
            user_response = {
                'userId': existing_user.get('userid') or existing_user.get('userId'),
                'username': existing_user['username'],
                'email': existing_user['email'],
                'profile_picture': existing_user.get('profile_picture'),
                'auth_provider': existing_user.get('auth_provider', 'google')
            }
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': user_response
            }), 200
        else:
            # Create new user
            new_user = db.create_google_user(
                user_info['google_id'],
                user_info['email'],
                user_info['name'],
                user_info['picture']
            )
            if new_user:
                user_response = {
                    'userId': new_user['userId'],
                    'username': new_user['username'],
                    'email': new_user['email'],
                    'profile_picture': new_user.get('profile_picture'),
                    'auth_provider': 'google'
                }
                return jsonify({
                    'success': True,
                    'message': 'Registration successful',
                    'user': user_response
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to create user'
                }), 500
                
    except Exception as e:
        print(f"Error in Google token auth: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error during Google token authentication: {str(e)}'
        }), 500

if __name__ == '__main__':
    # Run on host 0.0.0.0 to be accessible from outside, port 8080
    app.run(host='0.0.0.0', port=8080, debug=True)
