from flask import Flask, request, jsonify, send_from_directory, send_file, redirect, url_for, session, render_template
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
from fpdf import FPDF, XPos, YPos
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
        self.add_font('DejaVu', '', UNICODE_FONT_PATH)
        self.add_font('DejaVu', 'B', UNICODE_FONT_BOLD_PATH)
        self.add_font('DejaVu', 'I', UNICODE_FONT_ITALIC_PATH)
        self.add_font('DejaVu', 'BI', UNICODE_FONT_BOLD_ITALIC_PATH)
        # Centered 'Brand Blueprint'
        self.set_text_color(255, 255, 255)
        self.set_font('DejaVu', '', 20)
        self.set_y(self.h * 0.25)
        self.cell(0, 10, 'Brand Blueprint', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        # White underline
        y_underline = self.get_y() + 0.4
        self.set_draw_color(255, 255, 255)
        self.set_line_width(0.7)
        self.line(self.w * 0.37, y_underline, self.w * 0.638, y_underline)
        # 'For: {brand_name}'
        self.set_y(y_underline + 8)
        self.set_font('DejaVu', 'B', 28)
        self.cell(0, 14, f'{brand_name}', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        # Tagline (italic, smaller, white)
        self.set_y(self.get_y() + 2)
        self.set_font('DejaVu', 'I', 14)
        self.set_text_color(255, 255, 255)
        self.cell(0, 12, f'"{brand_tagline}"', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.set_text_color(0, 0, 0)

    def add_section_title(self, title, emphasize=False, color=None):
       self.add_font('DejaVu', 'B', UNICODE_FONT_PATH)
       self.set_font('DejaVu', 'B', 18)
       if color:
        self.set_text_color(*color)
       else:
        self.set_text_color(40, 40, 120) if emphasize else self.set_text_color(0, 0, 0)
       self.cell(0, 12, remove_emojis(title), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
       self.set_text_color(0, 0, 0)
       self.ln(4)
       self.set_y(self.get_y() + 10)

    def add_sub_section_title(self, title, emphasize=False):
        self.add_font('DejaVu', 'B', UNICODE_FONT_BOLD_PATH)
        self.set_font('DejaVu', 'B', 18 if emphasize else 14)
        self.set_text_color(40, 40, 120) if emphasize else self.set_text_color(0, 0, 0)
        self.cell(0, 12, remove_emojis(title), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
        self.set_text_color(0, 0, 0)
        self.ln(4)
        self.set_y(self.get_y() + 4)

    def add_key_value(self, key, value, emphasize=False):
        self.add_font('DejaVu', '', UNICODE_FONT_PATH)
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
        self.cell(0, 8, remove_emojis(f"{key}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
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
            self.cell(0, 10, remove_emojis(f"{color.get('color_name', '')} ({hex_val}) - {color.get('description', '')}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
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
                    self.cell(0, 8, '[Image could not be loaded]', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
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
                    self.add_font(font_family, font_style, font_file)
                except Exception:
                    pass
                self.set_font(font_family, font_style, font_size_num)
            else:
                # Fallback to DejaVu
                self.set_font('DejaVu', font_style, font_size_num)
            # Font name in its style
            self.cell(0, 10, f"{font_family} {font_weight.title()}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            # Sample text
            sample_text = "The quick brown fox jumps over the lazy dog. 1234567890"
            self.cell(0, 10, sample_text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            # Font details
            self.set_font('DejaVu', '', 11)
            self.cell(0, 8, f"Size: {font_size}   |   Line Height: {line_height}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.multi_cell(0, 8, remove_emojis(description))
            self.ln(4)

    def add_content_calendar(self, calendar_entries, max_entries=5):
        self.add_section_title("Content Calendar Sample")
        if not calendar_entries:
            self.set_font('DejaVu', '', 11)
            self.cell(0, 8, "No content calendar entries available.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
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
            self.cell(0, 30, section_title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=title_align)
            self.ln(5)
        # Subtitle
        if subtitle:
            self.set_font('DejaVu', 'B', 18)
            self.cell(0, 10, subtitle, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=subtitle_align)
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
            self.cell(circle_diameter, 12, hex_val, align='C', new_x=XPos.RIGHT, new_y=YPos.TOP)
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
                self.cell(0, 8, '[Image could not be loaded]', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        if description:
            self.set_font('DejaVu', '', 10)
            self.multi_cell(0, 8, remove_emojis(description))
        self.ln(4)

    def add_logo_variants(self, variants):
        self.add_sub_section_title("Logo Variants")
        if not variants or all(v.lower().startswith("error") for v in variants):
            self.set_font('DejaVu', '', 10)
            self.cell(0, 8, "No logo variants available.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
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
                    self.cell(0, 8, '[Image could not be loaded]', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                # Caption below image
                if app_type:
                    self.set_y(y + display_h + 5)
                    self.set_font('DejaVu', 'B', 14)
                    self.cell(0, 12, remove_emojis(app_type), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
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
    return render_template('index.html')

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
        
        # Handle the case where OpenAI returns a JSON string
        if isinstance(mySuggestions, str):
            try:
                # Remove any markdown code block formatting if present
                if mySuggestions.startswith('```json'):
                    mySuggestions = mySuggestions.replace('```json', '').replace('```', '').strip()
                elif mySuggestions.startswith('```'):
                    mySuggestions = mySuggestions.replace('```', '').strip()
                mySuggestions = json.loads(mySuggestions)
            except json.JSONDecodeError as e:
                print(f"  JSON decode error: {e}")
                # If JSON parsing fails, treat it as a single suggestion
                mySuggestions = [mySuggestions]

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



@app.route('/check_email_exists', methods=['POST'])
def check_email_exists():
    """
    Check if a user with the given email already exists in the database.
    """
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type must be application/json'
            }), 400

        data = request.get_json()
        if not data or 'email' not in data or not data['email']:
            return jsonify({
                'success': False,
                'error': 'Email is required'
            }), 400

        email = str(data['email']).strip().lower()

        # Validate email format
        import re
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(email):
            return jsonify({
                'success': False,
                'error': 'Invalid email format'
            }), 400

        existing_user = db.get_user_from_email(email)

        if existing_user:
            return jsonify({
                'success': True,
                'exists': True,
                'message': 'User with this email already exists'
            }), 200
        else:
            return jsonify({
                'success': True,
                'exists': False,
                'message': 'User with this email does not exist'
            }), 200

    except Exception as e:
        print(f"CHECK_EMAIL_EXISTS ERROR: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred while checking email existence'
        }), 500


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
        auth_provider = str(data.get('authProvider', '')).strip()
        
        
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
            'userId': user.get('userid') or user.get('userId'),
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
        print("user:", user)
        # Remove password from response for security
        user_response = {
            'userId': user.get('userid') or user.get('userId'),
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
    
    if brand is None:
        # Check if it's because user has already generated a brand
        generated_status = db.check_user_generated_status(data['userId'])
        if generated_status is True:
            return jsonify({
                'success': False,
                'message': 'You have already generated a brand. You can only generate one brand per account.',
                'brand': None
            }), 400
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to create brand. Please try again.',
                'brand': None
            }), 500

    return jsonify({
        'success': True,
        'message': 'Brand created successfully',
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
    # Get full brand data including brand assets
    full_brand = db.get_full_brand(brandId)
    if not full_brand:
        return jsonify({'error': 'Brand not found'}), 404

    brand = full_brand['brand']
    brand_assets = full_brand['brand_assets']

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
                            # Validate that headers are not empty and have unique names
                            if headers and len(set(headers)) == len(headers):
                                result = []
                                for row in rows[1:]:
                                    # Ensure row has the same number of elements as headers
                                    if len(row) == len(headers):
                                        try:
                                            row_dict = dict(zip(headers, [cell.strip() for cell in row]))
                                            result.append(row_dict)
                                        except Exception as e:
                                            print(f"Error creating dict from row: {e}")
                                            print(f"Headers: {headers}")
                                            print(f"Row: {row}")
                                            continue
                                return result if result else field
                return field
        return field

    # Extract and parse detailed brand fields
    brand_strategy = parse_json_field(brand.get('brand_strategy', {}))
    brand_identity = parse_json_field(brand.get('brand_identity', {}))
    brand_communication = parse_json_field(brand.get('brand_communication', {}))
    marketing = parse_json_field(brand.get('marketing_and_social_media_strategy', {}))

    # Cover page info
    if not isinstance(brand_communication, dict):
        brand_communication = {}
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
        
        # Business Strategy Section (from brand_assets)
        if brand_assets and brand_assets.get('premium_assets', {}).get('business_strategy'):
            business_strategy = brand_assets['premium_assets']['business_strategy']
            pdf.add_page()
            pdf.add_section_title("Business Strategy", True, primary_rgb)
            
            # Market Positioning
            if business_strategy.get('market_positioning'):
                positioning = business_strategy['market_positioning']
                pdf.add_sub_section_title("Market Positioning", True)
                for key, value in positioning.items():
                    if isinstance(value, list):
                        pdf.add_key_value(key.replace('_', ' ').title(), ', '.join(value), True)
                    else:
                        pdf.add_key_value(key.replace('_', ' ').title(), str(value), True)
            
            # SWOT Analysis
            if business_strategy.get('swot_analysis'):
                swot = business_strategy['swot_analysis']
                pdf.add_sub_section_title("SWOT Analysis", True)
                for category, items in swot.items():
                    if isinstance(items, list):
                        pdf.add_key_value(category.title(), ', '.join(items), True)
                    else:
                        pdf.add_key_value(category.title(), str(items), True)
            
            # Target Audience Profiles
            if business_strategy.get('target_audience_profiles'):
                profiles = business_strategy['target_audience_profiles']
                pdf.add_sub_section_title("Target Audience Profiles", True)
                for i, profile in enumerate(profiles):
                    if isinstance(profile, dict):
                        pdf.add_key_value(f"Persona {i+1}: {profile.get('persona_name', 'Unknown')}", 
                                        f"Demographics: {profile.get('demographics', 'N/A')} | "
                                        f"Motivations: {', '.join(profile.get('motivations', []))} | "
                                        f"Pain Points: {', '.join(profile.get('pain_points', []))}", True)
            
            # Competitive Analysis
            if business_strategy.get('competitive_analysis'):
                competitors = business_strategy['competitive_analysis']
                pdf.add_sub_section_title("Competitive Analysis", True)
                for i, competitor in enumerate(competitors):
                    if isinstance(competitor, dict):
                        comp_name = competitor.get('competitor_name', f'Competitor {i+1}')
                        strengths = ', '.join(competitor.get('strengths', []))
                        weaknesses = ', '.join(competitor.get('weaknesses', []))
                        pdf.add_key_value(f"{comp_name} - Strengths", strengths, True)
                        pdf.add_key_value(f"{comp_name} - Weaknesses", weaknesses, True)
        
        # Implementation Roadmap Section (from brand_assets)
        if brand_assets and brand_assets.get('premium_assets', {}).get('implementation_roadmap'):
            roadmap = brand_assets['premium_assets']['implementation_roadmap']
            pdf.add_page()
            pdf.add_section_title("Implementation Roadmap", True, primary_rgb)
            
            # Launch Timeline
            if roadmap.get('launch_timeline'):
                timeline = roadmap['launch_timeline']
                pdf.add_sub_section_title("Launch Timeline", True)
                for phase in timeline:
                    if isinstance(phase, dict):
                        phase_name = phase.get('phase', 'Unknown Phase')
                        duration = phase.get('duration', 'N/A')
                        deliverables = ', '.join(phase.get('deliverables', []))
                        pdf.add_key_value(f"{phase_name} ({duration})", deliverables, True)
            
            # Budget Estimates
            if roadmap.get('budget_estimates'):
                budgets = roadmap['budget_estimates']
                pdf.add_sub_section_title("Budget Estimates", True)
                for budget in budgets:
                    if isinstance(budget, dict):
                        category = budget.get('category', 'Unknown')
                        cost = budget.get('estimated_cost', 'N/A')
                        description = budget.get('description', '')
                        pdf.add_key_value(f"{category} - {cost}", description, True)
            
            # Quality Assurance
            if roadmap.get('quality_assurance'):
                qa = roadmap['quality_assurance']
                pdf.add_sub_section_title("Quality Assurance", True)
                for checkpoint in qa:
                    if isinstance(checkpoint, dict):
                        checkpoint_name = checkpoint.get('checkpoint', 'Unknown')
                        criteria = ', '.join(checkpoint.get('criteria', []))
                        metrics = ', '.join(checkpoint.get('success_metrics', []))
                        pdf.add_key_value(f"{checkpoint_name} - Criteria", criteria, True)
                        pdf.add_key_value(f"{checkpoint_name} - Success Metrics", metrics, True)

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
        
        # Brand Guidelines Section (from brand_assets)
        if brand_assets and brand_assets.get('premium_assets', {}).get('brand_guidelines'):
            guidelines = brand_assets['premium_assets']['brand_guidelines']
            pdf.add_page()
            pdf.add_section_title("Brand Guidelines", True, primary_rgb)
            
            # Brand Voice
            if guidelines.get('brand_voice'):
                voice = guidelines['brand_voice']
                pdf.add_sub_section_title("Brand Voice", True)
                for key, value in voice.items():
                    if isinstance(value, list):
                        pdf.add_key_value(key.replace('_', ' ').title(), ', '.join(value), True)
                    else:
                        pdf.add_key_value(key.replace('_', ' ').title(), str(value), True)
            
            # Logo Usage Rules
            if guidelines.get('logo_usage_rules'):
                rules = guidelines['logo_usage_rules']
                pdf.add_sub_section_title("Logo Usage Rules", True)
                for i, rule in enumerate(rules):
                    if isinstance(rule, dict):
                        rule_name = rule.get('rule', f'Rule {i+1}')
                        description = rule.get('description', '')
                        examples = rule.get('examples', '')
                        pdf.add_key_value(f"{rule_name}", f"{description} | Examples: {examples}", True)
            
            # Style Guide
            if guidelines.get('style_guide'):
                style = guidelines['style_guide']
                pdf.add_sub_section_title("Style Guide", True)
                
                # Color Usage
                if style.get('color_usage'):
                    pdf.add_key_value("Color Usage", "", True)
                    for color in style['color_usage']:
                        if isinstance(color, dict):
                            color_name = color.get('color_name', 'Unknown')
                            hex_value = color.get('hex_value', 'N/A')
                            usage = color.get('usage_context', 'N/A')
                            pdf.add_key_value(f"{color_name} ({hex_value})", usage, False)
                
                # Typography Rules
                if style.get('typography_rules'):
                    pdf.add_key_value("Typography Rules", "", True)
                    for typo in style['typography_rules']:
                        if isinstance(typo, dict):
                            font = typo.get('font_family', 'Unknown')
                            usage = typo.get('usage', 'N/A')
                            size_range = typo.get('size_range', 'N/A')
                            pdf.add_key_value(f"{font} ({size_range})", usage, False)
            
            # Visual Hierarchy
            if guidelines.get('visual_hierarchy'):
                hierarchy = guidelines['visual_hierarchy']
                pdf.add_sub_section_title("Visual Hierarchy", True)
                for element in hierarchy:
                    if isinstance(element, dict):
                        element_name = element.get('element', 'Unknown')
                        guidelines_text = element.get('guidelines', '')
                        priority = element.get('priority', 'N/A')
                        pdf.add_key_value(f"{element_name} ({priority})", guidelines_text, True)
        
        # Digital Specifications Section (from brand_assets)
        if brand_assets and brand_assets.get('premium_assets', {}).get('digital_specifications'):
            digital_specs = brand_assets['premium_assets']['digital_specifications']
            pdf.add_page()
            pdf.add_section_title("Digital Specifications", True, primary_rgb)
            
            # Color Profiles
            if digital_specs.get('color_profiles'):
                profiles = digital_specs['color_profiles']
                pdf.add_sub_section_title("Color Profiles", True)
                for profile in profiles:
                    if isinstance(profile, dict):
                        profile_type = profile.get('profile_type', 'Unknown')
                        color_values = profile.get('color_values', 'N/A')
                        usage = profile.get('usage_context', 'N/A')
                        pdf.add_key_value(f"{profile_type} Profile", f"{color_values} | {usage}", True)
            
            # Digital Specifications
            if digital_specs.get('digital_specifications'):
                specs = digital_specs['digital_specifications']
                pdf.add_sub_section_title("Platform Specifications", True)
                for spec in specs:
                    if isinstance(spec, dict):
                        platform = spec.get('platform', 'Unknown')
                        dimensions = spec.get('dimensions', 'N/A')
                        format_type = spec.get('format', 'N/A')
                        file_size = spec.get('file_size', 'N/A')
                        pdf.add_key_value(f"{platform} ({dimensions})", f"Format: {format_type} | Size: {file_size}", True)
            
            # File Format Guidelines
            if digital_specs.get('file_format_guidelines'):
                formats = digital_specs['file_format_guidelines']
                pdf.add_sub_section_title("File Format Guidelines", True)
                for format_guide in formats:
                    if isinstance(format_guide, dict):
                        format_type = format_guide.get('format', 'Unknown')
                        use_case = format_guide.get('use_case', 'N/A')
                        specs = format_guide.get('specifications', 'N/A')
                        pdf.add_key_value(f"{format_type} Format", f"{use_case} | {specs}", True)
            
            # Print Specifications
            if digital_specs.get('print_specifications'):
                print_specs = digital_specs['print_specifications']
                pdf.add_sub_section_title("Print Specifications", True)
                for print_spec in print_specs:
                    if isinstance(print_spec, dict):
                        resolution = print_spec.get('resolution', 'N/A')
                        color_mode = print_spec.get('color_mode', 'N/A')
                        material = print_spec.get('material', 'N/A')
                        pdf.add_key_value(f"Print Specs", f"Resolution: {resolution} | Color: {color_mode} | Material: {material}", True)


    # Brand Applications Section
    if brand_assets:
        full_brand_identity = brand_assets.get('full_brand_identity')
        if full_brand_identity and isinstance(full_brand_identity, dict):
            # Business Cards
            business_cards = full_brand_identity.get('business_cards', [])
            if business_cards:
                for i, card in enumerate(business_cards):
                    pdf.add_page()
                    # Add title for business card
                    pdf.add_section_title("Business Card", True, primary_rgb)
                    image_url = card.get('image_url')
                    if image_url and not image_url.startswith('Error:'):
                        try:
                            response = requests.get(image_url)
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_img:
                                tmp_img.write(response.content)
                                tmp_img.flush()
                                tmp_img_path = tmp_img.name
                            # Calculate optimal size while maintaining aspect ratio
                            from PIL import Image
                            with Image.open(tmp_img_path) as img:
                                img_width, img_height = img.size
                                aspect_ratio = img_width / img_height
                                
                                # Calculate maximum size that fits the page (accounting for title space)
                                page_width = pdf.w
                                page_height = pdf.h - 50  # Leave space for title
                                page_aspect = page_width / page_height
                                
                                if aspect_ratio > page_aspect:
                                    # Image is wider than page, fit to width
                                    display_width = page_width
                                    display_height = page_width / aspect_ratio
                                    x = 0
                                    y = 50 + (page_height - display_height) / 2  # Start below title
                                else:
                                    # Image is taller than page, fit to height
                                    display_height = page_height
                                    display_width = page_height * aspect_ratio
                                    x = (page_width - display_width) / 2
                                    y = 50  # Start below title
                                
                                pdf.image(tmp_img_path, x=x, y=y, w=display_width, h=display_height)
                            os.remove(tmp_img_path)
                        except Exception as e:
                            print(f"Error loading business card image: {e}")
                            pdf.add_key_value("Error", "Business card image could not be loaded")
            
            # Letterheads
            letterheads = full_brand_identity.get('letterheads', [])
            if letterheads:
                for i, letterhead in enumerate(letterheads):
                    pdf.add_page()
                    # Add title for letterhead
                    pdf.add_section_title("Letterhead", True, primary_rgb)
                    image_url = letterhead.get('image_url')
                    if image_url and not image_url.startswith('Error:'):
                        try:
                            response = requests.get(image_url)
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_img:
                                tmp_img.write(response.content)
                                tmp_img.flush()
                                tmp_img_path = tmp_img.name
                            # Calculate optimal size while maintaining aspect ratio
                            from PIL import Image
                            with Image.open(tmp_img_path) as img:
                                img_width, img_height = img.size
                                aspect_ratio = img_width / img_height
                                
                                # Calculate maximum size that fits the page (accounting for title space)
                                page_width = pdf.w
                                page_height = pdf.h - 50  # Leave space for title
                                page_aspect = page_width / page_height
                                
                                if aspect_ratio > page_aspect:
                                    # Image is wider than page, fit to width
                                    display_width = page_width
                                    display_height = page_width / aspect_ratio
                                    x = 0
                                    y = 50 + (page_height - display_height) / 2  # Start below title
                                else:
                                    # Image is taller than page, fit to height
                                    display_height = page_height
                                    display_width = page_height * aspect_ratio
                                    x = (page_width - display_width) / 2
                                    y = 50  # Start below title
                                
                                pdf.image(tmp_img_path, x=x, y=y, w=display_width, h=display_height)
                            os.remove(tmp_img_path)
                        except Exception as e:
                            print(f"Error loading letterhead image: {e}")
                            pdf.add_key_value("Error", "Letterhead image could not be loaded")
            
            # T-Shirt Mockups
            t_shirt_mockups = full_brand_identity.get('t_shirt_mockups', [])
            if t_shirt_mockups:
                for i, tshirt in enumerate(t_shirt_mockups):
                    pdf.add_page()
                    # Add title for t-shirt mockup
                    pdf.add_section_title("T-Shirt Mockup", True, primary_rgb)
                    image_url = tshirt.get('image_url')
                    if image_url and not image_url.startswith('Error:'):
                        try:
                            response = requests.get(image_url)
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_img:
                                tmp_img.write(response.content)
                                tmp_img.flush()
                                tmp_img_path = tmp_img.name
                            # Calculate optimal size while maintaining aspect ratio
                            from PIL import Image
                            with Image.open(tmp_img_path) as img:
                                img_width, img_height = img.size
                                aspect_ratio = img_width / img_height
                                
                                # Calculate maximum size that fits the page (accounting for title space)
                                page_width = pdf.w
                                page_height = pdf.h - 50  # Leave space for title
                                page_aspect = page_width / page_height
                                
                                if aspect_ratio > page_aspect:
                                    # Image is wider than page, fit to width
                                    display_width = page_width
                                    display_height = page_width / aspect_ratio
                                    x = 0
                                    y = 50 + (page_height - display_height) / 2  # Start below title
                                else:
                                    # Image is taller than page, fit to height
                                    display_height = page_height
                                    display_width = page_height * aspect_ratio
                                    x = (page_width - display_width) / 2
                                    y = 50  # Start below title
                                
                                pdf.image(tmp_img_path, x=x, y=y, w=display_width, h=display_height)
                            os.remove(tmp_img_path)
                        except Exception as e:
                            print(f"Error loading t-shirt mockup image: {e}")
                            pdf.add_key_value("Error", "T-shirt mockup image could not be loaded")
            
            # Cap Mockups
            cap_mockups = full_brand_identity.get('cap_mockups', [])
            if cap_mockups:
                for i, cap in enumerate(cap_mockups):
                    pdf.add_page()
                    # Add title for cap mockup
                    pdf.add_section_title("Cap Mockup", True, primary_rgb)
                    image_url = cap.get('image_url')
                    if image_url and not image_url.startswith('Error:'):
                        try:
                            response = requests.get(image_url)
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_img:
                                tmp_img.write(response.content)
                                tmp_img.flush()
                                tmp_img_path = tmp_img.name
                            # Calculate optimal size while maintaining aspect ratio
                            from PIL import Image
                            with Image.open(tmp_img_path) as img:
                                img_width, img_height = img.size
                                aspect_ratio = img_width / img_height
                                
                                # Calculate maximum size that fits the page (accounting for title space)
                                page_width = pdf.w
                                page_height = pdf.h - 50  # Leave space for title
                                page_aspect = page_width / page_height
                                
                                if aspect_ratio > page_aspect:
                                    # Image is wider than page, fit to width
                                    display_width = page_width
                                    display_height = page_width / aspect_ratio
                                    x = 0
                                    y = 50 + (page_height - display_height) / 2  # Start below title
                                else:
                                    # Image is taller than page, fit to height
                                    display_height = page_height
                                    display_width = page_height * aspect_ratio
                                    x = (page_width - display_width) / 2
                                    y = 50  # Start below title
                                
                                pdf.image(tmp_img_path, x=x, y=y, w=display_width, h=display_height)
                            os.remove(tmp_img_path)
                        except Exception as e:
                            print(f"Error loading cap mockup image: {e}")
                            pdf.add_key_value("Error", "Cap mockup image could not be loaded")
            
            # Signboards
            signboards = full_brand_identity.get('signboards', [])
            if signboards:
                for i, signboard in enumerate(signboards):
                    pdf.add_page()
                    # Add title for signboard
                    pdf.add_section_title("Signboard", True, primary_rgb)
                    image_url = signboard.get('image_url')
                    if image_url and not image_url.startswith('Error:'):
                        try:
                            response = requests.get(image_url)
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_img:
                                tmp_img.write(response.content)
                                tmp_img.flush()
                                tmp_img_path = tmp_img.name
                            # Calculate optimal size while maintaining aspect ratio
                            from PIL import Image
                            with Image.open(tmp_img_path) as img:
                                img_width, img_height = img.size
                                aspect_ratio = img_width / img_height
                                
                                # Calculate maximum size that fits the page (accounting for title space)
                                page_width = pdf.w
                                page_height = pdf.h - 50  # Leave space for title
                                page_aspect = page_width / page_height
                                
                                if aspect_ratio > page_aspect:
                                    # Image is wider than page, fit to width
                                    display_width = page_width
                                    display_height = page_width / aspect_ratio
                                    x = 0
                                    y = 50 + (page_height - display_height) / 2  # Start below title
                                else:
                                    # Image is taller than page, fit to height
                                    display_height = page_height
                                    display_width = page_height * aspect_ratio
                                    x = (page_width - display_width) / 2
                                    y = 50  # Start below title
                                
                                pdf.image(tmp_img_path, x=x, y=y, w=display_width, h=display_height)
                            os.remove(tmp_img_path)
                        except Exception as e:
                            print(f"Error loading signboard image: {e}")
                            pdf.add_key_value("Error", "Signboard image could not be loaded")
            
            # Brand Patterns
            brand_patterns = full_brand_identity.get('brand_patterns', [])
            if brand_patterns:
                for i, pattern in enumerate(brand_patterns):
                    pdf.add_page()
                    # Add title for brand pattern
                    pdf.add_section_title("Brand Pattern", True, primary_rgb)
                    image_url = pattern.get('image_url')
                    if image_url and not image_url.startswith('Error:'):
                        try:
                            response = requests.get(image_url)
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_img:
                                tmp_img.write(response.content)
                                tmp_img.flush()
                                tmp_img_path = tmp_img.name
                            # Calculate optimal size while maintaining aspect ratio
                            from PIL import Image
                            with Image.open(tmp_img_path) as img:
                                img_width, img_height = img.size
                                aspect_ratio = img_width / img_height
                                
                                # Calculate maximum size that fits the page (accounting for title space)
                                page_width = pdf.w
                                page_height = pdf.h - 50  # Leave space for title
                                page_aspect = page_width / page_height
                                
                                if aspect_ratio > page_aspect:
                                    # Image is wider than page, fit to width
                                    display_width = page_width
                                    display_height = page_width / aspect_ratio
                                    x = 0
                                    y = 50 + (page_height - display_height) / 2  # Start below title
                                else:
                                    # Image is taller than page, fit to height
                                    display_height = page_height
                                    display_width = page_height * aspect_ratio
                                    x = (page_width - display_width) / 2
                                    y = 50  # Start below title
                                
                                pdf.image(tmp_img_path, x=x, y=y, w=display_width, h=display_height)
                            os.remove(tmp_img_path)
                        except Exception as e:
                            print(f"Error loading brand pattern image: {e}")
                            pdf.add_key_value("Error", "Brand pattern image could not be loaded")
        
        # Copywriting Framework (from brand_assets) with fallback to Marketing Templates
        if brand_assets and brand_assets.get('premium_assets'):
            premium_assets = brand_assets['premium_assets']
            copy_fw = premium_assets.get('copywriting_framework')
            if copy_fw:
                pdf.add_page()
                pdf.add_section_title("Copywriting Framework", True, primary_rgb)

                # Persona Snapshot
                persona = copy_fw.get('persona_snapshot', {}) if isinstance(copy_fw, dict) else {}
                if persona:
                    pdf.add_sub_section_title("Persona Snapshot", True)
                    pdf.add_key_value("Demographics", persona.get('demographics', ''), True)
                    pdf.add_key_value("Psychographics", persona.get('psychographics', ''), False)
                    fears_list = persona.get('fears', []) or []
                    desires_list = persona.get('desires', []) or []
                    aspirations_list = persona.get('aspirations', []) or []
                    if fears_list:
                        pdf.add_key_value("Fears", ', '.join([str(x) for x in fears_list]), False)
                    if desires_list:
                        pdf.add_key_value("Desires", ', '.join([str(x) for x in desires_list]), False)
                    if aspirations_list:
                        pdf.add_key_value("Aspirations", ', '.join([str(x) for x in aspirations_list]), False)
                    if persona.get('awareness_stage'):
                        pdf.add_key_value("Awareness Stage", persona.get('awareness_stage', ''), False)

                # Message Pillars
                pillars = copy_fw.get('message_pillars', {}) if isinstance(copy_fw, dict) else {}
                if pillars:
                    pdf.add_sub_section_title("Message Pillars", True)
                    pdf.add_key_value("Problem Narrative", pillars.get('problem_narrative', ''), True)
                    pdf.add_key_value("Desired Transformation", pillars.get('desired_transformation', ''), False)
                    if pillars.get('differentiators'):
                        pdf.add_key_value("Differentiators", ', '.join(pillars.get('differentiators', [])), False)
                    if pillars.get('proof_assets'):
                        pdf.add_key_value("Proof Assets", ', '.join(pillars.get('proof_assets', [])), False)
                    if pillars.get('cta_patterns'):
                        pdf.add_key_value("CTA Patterns", ', '.join(pillars.get('cta_patterns', [])), False)

                # Copy Frameworks
                frameworks = copy_fw.get('copy_frameworks', []) if isinstance(copy_fw, dict) else []
                if frameworks:
                    pdf.add_sub_section_title("Copy Frameworks", True)
                    for fw in frameworks:
                        if isinstance(fw, dict):
                            name = fw.get('name', 'Framework')
                            when = fw.get('when_to_use', '')
                            outline = fw.get('outline', []) or []
                            pdf.add_key_value(f"{name} - When to use", when, True)
                            if outline:
                                pdf.add_key_value(f"{name} - Outline", ', '.join([str(x) for x in outline]), False)

                # Writing Guidance
                guidance = copy_fw.get('writing_guidance', {}) if isinstance(copy_fw, dict) else {}
                if guidance:
                    pdf.add_sub_section_title("Writing Guidance", True)
                    for k in ["fears", "desires", "dreams", "aspirations"]:
                        if guidance.get(k):
                            pdf.add_key_value(k.capitalize(), guidance.get(k, ''), True)

                # Tone & Style Rules
                ts = copy_fw.get('tone_style_rules', {}) if isinstance(copy_fw, dict) else {}
                if ts:
                    pdf.add_sub_section_title("Tone & Style Rules", True)
                    pdf.add_key_value("Reading Level", ts.get('reading_level', ''), True)
                    pdf.add_key_value("Formality", ts.get('formality', ''), False)
                    if ts.get('lexicon_use'):
                        pdf.add_key_value("Lexicon (Use)", ', '.join(ts.get('lexicon_use', [])), False)
                    if ts.get('lexicon_avoid'):
                        pdf.add_key_value("Lexicon (Avoid)", ', '.join(ts.get('lexicon_avoid', [])), False)
                    pdf.add_key_value("Voice", ts.get('voice', ''), False)
                    pdf.add_key_value("Cadence", ts.get('cadence', ''), False)

                # Objection Handling
                objections = copy_fw.get('objection_bank', []) if isinstance(copy_fw, dict) else []
                if objections:
                    pdf.add_sub_section_title("Objection Handling", True)
                    for i, obj in enumerate(objections):
                        if isinstance(obj, dict):
                            pdf.add_key_value(f"Objection {i+1}", obj.get('objection', ''), True)
                            if obj.get('reframe'):
                                pdf.add_key_value("Reframe", obj.get('reframe', ''), False)
                            if obj.get('proof'):
                                pdf.add_key_value("Proof", obj.get('proof', ''), False)
                            if obj.get('risk_reversal'):
                                pdf.add_key_value("Risk Reversal", obj.get('risk_reversal', ''), False)

                # Hook Bank
                hooks = copy_fw.get('hook_bank', []) if isinstance(copy_fw, dict) else []
                if hooks:
                    pdf.add_sub_section_title("Hook Bank", True)
                    for i, hook in enumerate(hooks):
                        if isinstance(hook, dict):
                            text = hook.get('text', '')
                            tag = hook.get('tag', '')
                            stage = hook.get('awareness_stage', '')
                            label = f"Hook {i+1}"
                            details = ", ".join([v for v in [tag, stage] if v])
                            pdf.add_key_value(label, text, True)
                            if details:
                                pdf.add_key_value("Details", details, False)

                # CTA Bank
                ctas = copy_fw.get('cta_bank', []) if isinstance(copy_fw, dict) else []
                if ctas:
                    pdf.add_sub_section_title("CTA Bank", True)
                    for i, cta in enumerate(ctas):
                        if isinstance(cta, dict):
                            text = cta.get('text', '')
                            fl = cta.get('friction_level', '')
                            pdf.add_key_value(f"CTA {i+1}", text, True)
                            if fl:
                                pdf.add_key_value("Friction", fl, False)

                # Channel Adaptation
                channels = copy_fw.get('channel_adaptation', {}) if isinstance(copy_fw, dict) else {}
                if channels:
                    pdf.add_sub_section_title("Channel Adaptation", True)
                    mapping = {
                        'whatsapp': 'WhatsApp',
                        'instagram': 'Instagram',
                        'linkedin': 'LinkedIn',
                        'landing_page': 'Landing Page',
                        'radio_ooh': 'Radio/OOH'
                    }
                    for key, label in mapping.items():
                        if channels.get(key):
                            pdf.add_key_value(label, channels.get(key, ''), True)

                # Asset Recipe
                recipe = copy_fw.get('asset_recipe', []) if isinstance(copy_fw, dict) else []
                if recipe:
                    pdf.add_sub_section_title("Asset Recipe", True)
                    for i, step in enumerate(recipe):
                        pdf.add_key_value(f"Step {i+1}", str(step), True)

                # Measurement
                meas = copy_fw.get('measurement', {}) if isinstance(copy_fw, dict) else {}
                if meas:
                    pdf.add_sub_section_title("Measurement", True)
                    if meas.get('metrics'):
                        pdf.add_key_value("Metrics", ', '.join([str(x) for x in meas.get('metrics', [])]), True)
                    if meas.get('ab_tests'):
                        pdf.add_key_value("A/B Tests", ', '.join([str(x) for x in meas.get('ab_tests', [])]), False)
                    if meas.get('iteration_rules'):
                        pdf.add_key_value("Iteration Rules", ', '.join([str(x) for x in meas.get('iteration_rules', [])]), False)
            elif premium_assets.get('marketing_templates'):
                # Backward-compatible rendering for legacy marketing templates
                templates = premium_assets['marketing_templates']
                pdf.add_page()
                pdf.add_section_title("Marketing Templates", True, primary_rgb)
                
                # Landing Page Copy
                if templates.get('landing_page_copy'):
                    landing = templates['landing_page_copy']
                    pdf.add_sub_section_title("Landing Page Copy", True)
                    pdf.add_key_value("Hero Headline", landing.get('hero_headline', ''), True)
                    pdf.add_key_value("Hero Subheadline", landing.get('hero_subheadline', ''), True)
                    pdf.add_key_value("Call to Action", landing.get('call_to_action', ''), True)
                    
                    if landing.get('benefits'):
                        pdf.add_key_value("Benefits", ', '.join(landing['benefits']), True)
                    
                    if landing.get('features'):
                        pdf.add_key_value("Features", ', '.join(landing['features']), True)
                    
                    if landing.get('testimonials'):
                        pdf.add_key_value("Testimonials", '', True)
                        for i, testimonial in enumerate(landing['testimonials']):
                            pdf.add_key_value(f"Testimonial {i+1}", testimonial, False)
                
                # Email Templates
                if templates.get('email_templates'):
                    emails = templates['email_templates']
                    pdf.add_sub_section_title("Email Templates", True)
                    for i, email in enumerate(emails):
                        if isinstance(email, dict):
                            template_name = email.get('template_name', f'Email Template {i+1}')
                            subject = email.get('subject_line', '')
                            greeting = email.get('greeting', '')
                            body = email.get('body', '')
                            closing = email.get('closing', '')
                            signature = email.get('signature', '')
                            
                            pdf.add_key_value(f"{template_name} - Subject", subject, True)
                            pdf.add_key_value(f"{template_name} - Greeting", greeting, False)
                            pdf.add_key_value(f"{template_name} - Body", body, False)
                            pdf.add_key_value(f"{template_name} - Closing", f"{closing} {signature}", False)
                
                # Brochure Content
                if templates.get('brochure_content'):
                    brochure = templates['brochure_content']
                    pdf.add_sub_section_title("Brochure Content", True)
                    for i, section in enumerate(brochure):
                        if isinstance(section, dict):
                            section_title = section.get('section_title', f'Section {i+1}')
                            content = section.get('content', '')
                            call_to_action = section.get('call_to_action', '')
                            
                            pdf.add_key_value(f"{section_title}", content, True)
                            if call_to_action:
                                pdf.add_key_value(f"{section_title} - CTA", call_to_action, False)
                
                # Presentation Templates
                if templates.get('presentation_templates'):
                    presentations = templates['presentation_templates']
                    pdf.add_sub_section_title("Presentation Templates", True)
                    for i, slide in enumerate(presentations):
                        if isinstance(slide, dict):
                            slide_title = slide.get('slide_title', f'Slide {i+1}')
                            content = slide.get('content', '')
                            key_points = ', '.join(slide.get('key_points', []))
                            visual_suggestions = slide.get('visual_suggestions', '')
                            
                            pdf.add_key_value(f"{slide_title}", content, True)
                            if key_points:
                                pdf.add_key_value(f"{slide_title} - Key Points", key_points, False)
                            if visual_suggestions:
                                pdf.add_key_value(f"{slide_title} - Visual Suggestions", visual_suggestions, False)
        
        # Social Media Content Section (from brand_assets)
        if brand_assets and brand_assets.get('social_media_content'):
            social_content = brand_assets['social_media_content']
            pdf.add_page()
            pdf.add_section_title("Social Media Content", True, primary_rgb)
            
            # Ad Copies
            if social_content.get('ad_copies'):
                ads = social_content['ad_copies']
                pdf.add_sub_section_title("Ad Copies", True)
                for i, ad in enumerate(ads):
                    pdf.add_key_value(f"Ad Copy {i+1}", ad, True)
            
            # Ready Made Posts
            if social_content.get('ready_made_posts'):
                posts = social_content['ready_made_posts']
                pdf.add_sub_section_title("Ready Made Posts", True)
                for i, post in enumerate(posts):
                    if isinstance(post, dict):
                        caption = post.get('caption', '')
                        design_concept = post.get('design_concept', '')
                        
                        pdf.add_key_value(f"Post {i+1} - Caption", caption, True)
                        if design_concept:
                            pdf.add_key_value(f"Post {i+1} - Design Concept", design_concept, False)
            
            # Marketing Strategies
            if social_content.get('relevant_marketing_strategies'):
                strategies = social_content['relevant_marketing_strategies']
                pdf.add_sub_section_title("Marketing Strategies", True)
                for i, strategy in enumerate(strategies):
                    pdf.add_key_value(f"Strategy {i+1}", strategy, True)

    # Final note
    pdf.add_page()
    pdf.add_section_title("Implementation Guide", True, primary_rgb)
    pdf.add_key_value(
        "Next Steps",
        "This brand blueprint provides the foundation for all your marketing materials, website design, and business communications. Use these guidelines consistently across all touchpoints to build a strong, recognizable brand identity.",
        True
    )

    pdf_bytes = pdf.output()
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

@app.route('/get_full_brand/<brand_id>', methods=['GET'])
def get_full_brand(brand_id):
    """Get complete brand information including brand details and brand assets"""
    try:
        if not brand_id:
            return jsonify({
                'success': False,
                'message': 'brandId is required',
                'full_brand': None
            }), 400
        
        full_brand = db.get_full_brand(brand_id)
        
        if full_brand:
            return jsonify({
                'success': True,
                'message': 'Full brand information retrieved successfully',
                'full_brand': full_brand
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Brand not found',
                'full_brand': None
            }), 404
            
    except Exception as e:
        print(f"Error getting full brand: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error retrieving full brand information: {str(e)}',
            'full_brand': None
        }), 500

@app.route('/update_brand_payment_status', methods=['POST'])
def update_brand_payment_status():
    """Update the payment status of a brand"""
    try:
        data = request.get_json()
        if not data or 'brandId' not in data or 'paymentStatus' not in data:
            return jsonify({
                'success': False,
                'message': 'brandId and paymentStatus are required',
                'updated': False
            }), 400
        
        brand_id = data['brandId']
        payment_status = data['paymentStatus']
        
        # Validate payment_status is boolean
        if not isinstance(payment_status, bool):
            return jsonify({
                'success': False,
                'message': 'paymentStatus must be a boolean value',
                'updated': False
            }), 400
        
        success = db.update_brand_payment_status(brand_id, payment_status)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Payment status updated successfully',
                'updated': True
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to update payment status',
                'updated': False
            }), 500
            
    except Exception as e:
        print(f"Error updating brand payment status: {e}")
        return jsonify({
            'success': False,
            'message': f'Error updating payment status: {str(e)}',
            'updated': False
        }), 500

@app.route('/check_brand_payment_status/<brand_id>', methods=['GET'])
def check_brand_payment_status(brand_id):
    """Check the payment status of a brand"""
    try:
        if not brand_id:
            return jsonify({
                'success': False,
                'message': 'brandId is required',
                'payment_status': None
            }), 400
        
        payment_status = db.check_brand_payment_status(brand_id)
        
        if payment_status is not None:
            return jsonify({
                'success': True,
                'message': 'Payment status retrieved successfully',
                'payment_status': payment_status
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Brand not found',
                'payment_status': None
            }), 404
            
    except Exception as e:
        print(f"Error checking brand payment status: {e}")
        return jsonify({
            'success': False,
            'message': f'Error checking payment status: {str(e)}',
            'payment_status': None
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

# ===================== Flutterwave Payment Endpoints =====================

@app.route('/payment/initiate', methods=['POST'])
def initiate_payment():
    """Initiate a payment transaction"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['amount', 'email', 'phone_number', 'name', 'brand_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Extract data
        amount = data['amount']
        email = data['email']
        phone_number = data['phone_number']
        name = data['name']
        brand_id = data['brand_id']
        currency = data.get('currency', 'NGN')
        
        # Generate unique transaction reference
        import uuid
        tx_ref = f"brand_ai_{brand_id}_{uuid.uuid4().hex[:8]}"
        
        # Import Flutterwave payment handler
        try:
            from flutterwave_payment import flutterwave
        except ImportError:
            return jsonify({
                'success': False,
                'message': 'Payment service not available'
            }), 500
        
        # Initiate payment
        result = flutterwave.initiate_payment(
            amount=amount,
            email=email,
            phone_number=phone_number,
            name=name,
            tx_ref=tx_ref,
            currency=currency
        )
        
        if result['success']:
            # Store payment info in database (optional)
            # You can create a payments table to track payment attempts
            
            return jsonify({
                'success': True,
                'message': 'Payment initiated successfully',
                'payment_url': result['payment_url'],
                'tx_ref': result['tx_ref'],
                'flw_ref': result['flw_ref']
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400
            
    except Exception as e:
        print(f"Error initiating payment: {e}")
        return jsonify({
            'success': False,
            'message': f'Error initiating payment: {str(e)}'
        }), 500

@app.route('/payment/verify', methods=['POST'])
def verify_payment():
    """Verify a payment transaction"""
    try:
        data = request.get_json()
        
        if not data or 'transaction_id' not in data:
            return jsonify({
                'success': False,
                'message': 'Transaction ID is required'
            }), 400
        
        transaction_id = data['transaction_id']
        
        # Import Flutterwave payment handler
        try:
            from flutterwave_payment import flutterwave
        except ImportError:
            return jsonify({
                'success': False,
                'message': 'Payment service not available'
            }), 500
        
        # Verify payment
        result = flutterwave.verify_payment(transaction_id)
        
        if result['success']:
            # Update brand payment status if payment is successful
            if result['status'] == 'successful':
                # Extract brand_id from tx_ref (format: brand_ai_{brand_id}_{random})
                tx_ref = result['tx_ref']
                if tx_ref.startswith('brand_ai_'):
                    parts = tx_ref.split('_')
                    if len(parts) >= 3:
                        brand_id = parts[2]
                        # Update payment status
                        db.update_brand_payment_status(brand_id, True)
                        print(f"Payment successful for brand {brand_id}")
            
            return jsonify({
                'success': True,
                'message': 'Payment verified successfully',
                'payment_data': result
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400
            
    except Exception as e:
        print(f"Error verifying payment: {e}")
        return jsonify({
            'success': False,
            'message': f'Error verifying payment: {str(e)}'
        }), 500

@app.route('/payment/callback', methods=['GET'])
def payment_callback():
    """Handle payment callback from Flutterwave"""
    try:
        # Get query parameters
        status = request.args.get('status')
        tx_ref = request.args.get('tx_ref')
        transaction_id = request.args.get('transaction_id')
        
        if status == 'successful':
            # Verify the payment
            try:
                from flutterwave_payment import flutterwave
                result = flutterwave.verify_payment(transaction_id)
                
                if result['success'] and result['status'] == 'successful':
                    # Extract brand_id from tx_ref
                    if tx_ref.startswith('brand_ai_'):
                        parts = tx_ref.split('_')
                        if len(parts) >= 3:
                            brand_id = parts[2]
                            # Update payment status
                            db.update_brand_payment_status(brand_id, True)
                            print(f"Payment successful for brand {brand_id}")
                    
                    return jsonify({
                        'success': True,
                        'message': 'Payment completed successfully',
                        'tx_ref': tx_ref,
                        'transaction_id': transaction_id
                    }), 200
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Payment verification failed'
                    }), 400
            except ImportError:
                return jsonify({
                    'success': False,
                    'message': 'Payment service not available'
                }), 500
        else:
            return jsonify({
                'success': False,
                'message': f'Payment failed with status: {status}'
            }), 400
            
    except Exception as e:
        print(f"Error in payment callback: {e}")
        return jsonify({
            'success': False,
            'message': f'Error processing payment callback: {str(e)}'
        }), 500

@app.route('/payment/webhook', methods=['POST'])
def payment_webhook():
    """Handle webhook from Flutterwave"""
    try:
        # Get the raw request body and signature
        payload = request.get_data(as_text=True)
        signature = request.headers.get('Verif-Hash')
        
        if not signature:
            return jsonify({
                'success': False,
                'message': 'Missing webhook signature'
            }), 400
        
        # Parse the payload
        try:
            webhook_data = json.loads(payload)
        except json.JSONDecodeError:
            return jsonify({
                'success': False,
                'message': 'Invalid JSON payload'
            }), 400
        
        # Import Flutterwave payment handler
        try:
            from flutterwave_payment import flutterwave
        except ImportError:
            return jsonify({
                'success': False,
                'message': 'Payment service not available'
            }), 500
        
        # Process webhook
        result = flutterwave.process_webhook(webhook_data, signature)
        
        if result['success']:
            # Handle successful payment
            if result['event'] == 'charge.completed':
                # Extract brand_id from tx_ref
                tx_ref = result['tx_ref']
                if tx_ref.startswith('brand_ai_'):
                    parts = tx_ref.split('_')
                    if len(parts) >= 3:
                        brand_id = parts[2]
                        # Update payment status
                        db.update_brand_payment_status(brand_id, True)
                        print(f"Webhook: Payment successful for brand {brand_id}")
            
            return jsonify({
                'success': True,
                'message': 'Webhook processed successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400
            
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return jsonify({
            'success': False,
            'message': f'Error processing webhook: {str(e)}'
        }), 500

if __name__ == '__main__':
    # Run on host 0.0.0.0 to be accessible from outside, port 8080
    app.run(host='0.0.0.0', port=8080, debug=True)
