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
import secrets
import string
from google_oauth import get_google_auth_url, verify_google_token, create_flow

FONT_DIR = os.path.join(os.path.dirname(__file__), 'fonts')
UNICODE_FONT_PATH = os.path.join(FONT_DIR, 'DejaVuSans.ttf')
UNICODE_FONT_BOLD_PATH = os.path.join(FONT_DIR, 'DejaVuSans-Bold.ttf')
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

def generate_referral_code(length=8):
    """Generate a unique referral code"""
    characters = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(secrets.choice(characters) for _ in range(length))
        # Check if code already exists in database
        try:
            with db.get_db_connection() as cursor:
                cursor.execute("SELECT COUNT(*) FROM users WHERE referral_code = %s", (code,))
                if cursor.fetchone()[0] == 0:
                    return code
        except:
            return code

def process_referral(referrer_id, new_user_id):
    """Process referral and update referral stats"""
    try:
        with db.get_db_connection() as cursor:
            # Update referrer's stats
            cursor.execute("""
                UPDATE users 
                SET referred_users = referred_users + 1,
                    referred_amount = referred_amount + 1000,
                    can_refer = TRUE
                WHERE userId = %s
            """, (referrer_id,))
            
            # Update new user's referred_by field
            cursor.execute("""
                UPDATE users 
                SET referred_by = %s
                WHERE userId = %s
            """, (referrer_id, new_user_id))
            
            return True
    except Exception as e:
        print(f"Error processing referral: {e}")
        return False

def get_referral_stats(user_id):
    """Get referral statistics for a user"""
    try:
        with db.get_db_connection() as cursor:
            cursor.execute("""
                SELECT referral_code, referred_users, referred_amount, can_refer
                FROM users 
                WHERE userId = %s
            """, (user_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'referral_code': result[0],
                    'referred_users': result[1] or 0,
                    'referred_amount': result[2] or 0,
                    'can_refer': result[3] or False
                }
            return None
    except Exception as e:
        print(f"Error getting referral stats: {e}")
        return None

class BrandPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.set_margins(20, 20, 20)
        
        # Add fonts first before setting them
        self.add_font('DejaVu', '', UNICODE_FONT_PATH)
        self.add_font('DejaVu', 'B', UNICODE_FONT_BOLD_PATH)
        self.add_font('DejaVu', 'I', UNICODE_FONT_ITALIC_PATH)
        self.add_font('DejaVu', 'BI', UNICODE_FONT_BOLD_ITALIC_PATH)
        
        # Now set the default font
        self.set_font('DejaVu', '', 12)
        
    def header(self):
        # Add header with page number
        self.set_font('DejaVu', '', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'R')
        self.ln(15)
        
    def footer(self):
        # Add footer
        self.set_y(-15)
        self.set_font('DejaVu', '', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, 'Brand Style Guide', 0, 0, 'C')
        
    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def add_cover(self, brand_name, brand_tagline, primary_colors=None, secondary_colors=None):
        self.add_page()
        
        # Get primary color for styling
        hex_primary = primary_colors[0].get('hex_value', '#1E90FF') if primary_colors else '#1E90FF'
        primary_rgb = self.hex_to_rgb(hex_primary)
        
        # Create a modern cover design
        # Top accent bar
        self.set_fill_color(*primary_rgb)
        self.rect(0, 0, self.w, 40, style='F')
        
        # Main content area
        self.set_y(60)
        
        # Brand Style Guide title
        self.set_font('DejaVu', 'B', 36)
        self.set_text_color(*primary_rgb)
        self.cell(0, 20, '', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.cell(0, 20, 'BRAND GUIDE', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        
        # Brand name
        self.set_y(140)
        self.set_font('DejaVu', 'B', 24)
        self.set_text_color(50, 50, 50)
        self.cell(0, 15, brand_name.upper(), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        
        # Tagline
        if brand_tagline:
            self.set_font('DejaVu', 'I', 14)
            self.set_text_color(100, 100, 100)
            self.cell(0, 10, f'"{brand_tagline}"', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        
        # Date
        self.set_y(200)
        self.set_font('DejaVu', '', 10)
        self.set_text_color(150, 150, 150)
        from datetime import datetime
        self.cell(0, 10, f'Generated on {datetime.now().strftime("%B %d, %Y")}', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        
        # Bottom accent
        self.set_y(self.h - 60)
        self.set_fill_color(*primary_rgb)
        self.rect(0, self.h - 60, self.w, 60, style='F')
        
        self.set_text_color(0, 0, 0)

    def add_section_title(self, title, emphasize=False, color=None):
        # Add page break for new sections
        self.add_page()
        
        # Section number (dynamic counter)
        if not hasattr(self, '_section_counter'):
            self._section_counter = 0
        self._section_counter += 1
        section_number = f"{self._section_counter:02d}"
        
        # Section title with modern styling
        self.set_font('DejaVu', 'B', 24)
        if color:
            self.set_text_color(*color)
        else:
            self.set_text_color(50, 50, 50)
        
        # Add section number
        self.set_font('DejaVu', '', 12)
        self.set_text_color(150, 150, 150)
        self.cell(0, 8, f'SECTION {section_number}', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
        
        # Main title
        self.set_font('DejaVu', 'B', 24)
        if color:
            self.set_text_color(*color)
        else:
            self.set_text_color(50, 50, 50)
        self.cell(0, 15, remove_emojis(title).upper(), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
        
        # Underline
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.5)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        
        self.ln(15)
        self.set_text_color(0, 0, 0)

    def add_sub_section_title(self, title, emphasize=False):
        self.ln(10)
        self.set_font('DejaVu', 'B', 16 if emphasize else 14)
        self.set_text_color(70, 70, 70)
        self.cell(0, 10, remove_emojis(title), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
        
        # Small accent line
        self.set_draw_color(220, 220, 220)
        self.set_line_width(0.3)
        self.line(self.l_margin, self.get_y(), self.l_margin + 30, self.get_y())
        
        self.ln(8)
        self.set_text_color(0, 0, 0)

    def add_key_value(self, key, value, emphasize=False):
        # Check if we need a page break
        if self.get_y() > self.h - 50:
            self.add_page()
        
        # Key styling
        self.set_font('DejaVu', 'B', 12 if emphasize else 11)
        self.set_text_color(50, 50, 50)
        
        # Create a modern key-value layout
        key_width = 60
        value_width = self.w - self.l_margin - self.r_margin - key_width - 10
        
        # Key with background
        self.set_fill_color(245, 245, 245)
        self.cell(key_width, 8, remove_emojis(f"{key}"), border=0, fill=True, align='L')
        
        # Value
        self.set_font('DejaVu', '', 11)
        self.set_text_color(80, 80, 80)
        self.set_fill_color(255, 255, 255)
        
        value_str = str(value).strip()
        import re
        value_str = re.sub(r'\n+', '\n', value_str)
        
        # Handle multi-line values
        if '\n' in value_str or len(value_str) > 80:
            self.cell(0, 8, '', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.multi_cell(0, 6, remove_emojis(value_str))
        else:
            self.cell(value_width, 8, remove_emojis(value_str), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        self.ln(8)
        self.set_text_color(0, 0, 0)

    def add_color_palette(self, colors, title):
        self.add_sub_section_title(title)
        
        # Create a modern color palette layout
        colors_per_row = 2
        color_box_size = 40
        spacing = 20
        
        for i, color in enumerate(colors):
            if i % colors_per_row == 0:
                self.ln(5)
            
            hex_val = color.get('hex_value', '#000000')
            color_name = color.get('color_name', '')
            description = color.get('description', '')
            
            try:
                r = int(hex_val[1:3], 16)
                g = int(hex_val[3:5], 16)
                b = int(hex_val[5:7], 16)
            except Exception:
                r, g, b = 0, 0, 0
            
            # Calculate position
            x_pos = self.l_margin + (i % colors_per_row) * (color_box_size + spacing + 80)
            y_pos = self.get_y()
            
            # Color box
            self.set_fill_color(r, g, b)
            self.rect(x_pos, y_pos, color_box_size, color_box_size, style='F')
            
            # Color info
            self.set_xy(x_pos + color_box_size + 10, y_pos)
            self.set_font('DejaVu', 'B', 11)
            self.set_text_color(50, 50, 50)
            self.cell(70, 6, color_name, new_x=XPos.RIGHT, new_y=YPos.TOP)
            
            self.set_font('DejaVu', '', 10)
            self.set_text_color(100, 100, 100)
            self.cell(70, 6, hex_val, new_x=XPos.RIGHT, new_y=YPos.TOP)
            
            # Description
            if description:
                self.set_font('DejaVu', '', 9)
                self.set_text_color(150, 150, 150)
                self.multi_cell(70, 4, description)
            
            # Move to next row if needed
            if (i + 1) % colors_per_row == 0:
                self.ln(color_box_size + 10)
        
        self.ln(10)

    def add_info_box(self, title, content, color=None):
        """Add a modern info box for important information"""
        if color is None:
            color = (240, 248, 255)  # Light blue default
        
        # Box background
        self.set_fill_color(*color)
        self.rect(self.l_margin, self.get_y(), self.w - self.l_margin - self.r_margin, 0, style='F')
        
        # Title
        self.set_font('DejaVu', 'B', 12)
        self.set_text_color(50, 50, 50)
        self.cell(0, 8, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
        
        # Content
        self.set_font('DejaVu', '', 10)
        self.set_text_color(80, 80, 80)
        self.multi_cell(0, 6, content)
        
        self.ln(8)

    def add_application_image(self, image_url, image_name):
        """Add an application image (business card, letterhead, etc.) with proper margin handling"""
        if image_url and not image_url.startswith('Error:'):
            try:
                response = requests.get(image_url)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_img:
                    tmp_img.write(response.content)
                    tmp_img.flush()
                    tmp_img_path = tmp_img.name
                
                # Calculate optimal size while maintaining aspect ratio and respecting margins
                from PIL import Image
                with Image.open(tmp_img_path) as img:
                    img_width, img_height = img.size
                    aspect_ratio = img_width / img_height
                    
                    # Calculate available space within margins
                    available_width = self.w - self.l_margin - self.r_margin
                    available_height = self.h - self.t_margin - self.b_margin - 80  # Leave space for title and spacing
                    
                    # Calculate maximum size that fits within margins
                    if aspect_ratio > (available_width / available_height):
                        # Image is wider than available space, fit to width
                        display_width = available_width
                        display_height = available_width / aspect_ratio
                    else:
                        # Image is taller than available space, fit to height
                        display_height = available_height
                        display_width = available_height * aspect_ratio
                    
                    # Center the image horizontally within margins
                    x = self.l_margin + (available_width - display_width) / 2
                    y = self.get_y() + 20  # Add some spacing after title
                    
                    self.image(tmp_img_path, x=x, y=y, w=display_width, h=display_height)
                
                os.remove(tmp_img_path)
                
            except Exception as e:
                print(f"Error loading {image_name} image: {e}")
                self.add_key_value("Error", f"{image_name} image could not be loaded")

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
                    self.image(tmp_img_path, w=self.w - self.l_margin - self.r_margin)
                    os.remove(tmp_img_path)
                except Exception as e:
                    print(f"Error loading image {url}: {e}")
                    self.set_font('DejaVu', '', 10)
                    self.cell(0, 8, '[Image could not be loaded]', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.ln(2)
            self.set_font('DejaVu', '', 10)
            self.multi_cell(0, 8, remove_emojis(logo.get('description', '')))
            self.ln(4)

    def add_brand_logo(self, logo_url, brand_name=""):
        """Add the main brand logo from the brand field"""
        self.add_sub_section_title("Brand Logo")
        
        if logo_url and logo_url.strip():
            try:
                response = requests.get(logo_url)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_img:
                    tmp_img.write(response.content)
                    tmp_img.flush()
                    tmp_img_path = tmp_img.name
                
                # Create a centered logo display with background
                logo_width = min(self.w - self.l_margin - self.r_margin - 40, 120)  # Max 120mm width
                
                # Add background box for logo
                self.set_fill_color(250, 250, 250)
                self.rect(self.l_margin, self.get_y(), self.w - self.l_margin - self.r_margin, logo_width + 20, style='F')
                
                # Center the logo
                x_pos = (self.w - logo_width) / 2
                y_pos = self.get_y() + 10
                
                self.image(tmp_img_path, x=x_pos, y=y_pos, w=logo_width)
                os.remove(tmp_img_path)
                
                # Logo information
                self.set_y(y_pos + logo_width + 15)
                self.set_font('DejaVu', 'B', 12)
                self.set_text_color(50, 50, 50)
                self.cell(0, 8, f"{brand_name} Official Logo", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
                
                self.set_font('DejaVu', '', 10)
                self.set_text_color(100, 100, 100)
                self.multi_cell(0, 6, "This is the official brand logo for use across all brand materials, marketing collateral, and digital platforms.", align='C')
                
                self.ln(10)
                
            except Exception as e:
                print(f"Error loading brand logo {logo_url}: {e}")
                self.set_font('DejaVu', '', 10)
                self.set_text_color(150, 150, 150)
                self.cell(0, 8, '[Brand logo could not be loaded]', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
                self.ln(2)
                self.multi_cell(0, 6, f"Logo URL: {logo_url}", align='C')
                self.ln(4)
        else:
            self.set_font('DejaVu', '', 10)
            self.set_text_color(150, 150, 150)
            self.cell(0, 8, 'No brand logo available', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
            self.ln(4)

    def add_typography(self, typography):
        self.add_sub_section_title("Typography")
        import os
        font_dir = FONT_DIR
        
        for font in typography:
            # Check if we need a page break
            if self.get_y() > self.h - 80:
                self.add_page()
            
            font_family = font.get('font_family', 'DejaVu')
            font_weight = font.get('font_weight', '').lower()
            font_size = font.get('font_size', '16px')
            
            # Parse and limit font size to prevent overflow
            font_size_num = 16
            try:
                font_size_num = int(''.join([c for c in font_size if c.isdigit()]))
                # Limit font size to prevent overflow (max 24pt for display)
                font_size_num = min(font_size_num, 24)
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
            
            # Create a modern typography display
            # Font name header
            self.set_font('DejaVu', 'B', 14)
            self.set_text_color(50, 50, 50)
            self.cell(0, 10, f"{font_family} {font_weight.title()}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            # Sample text with the actual font (if available)
            sample_text = "The quick brown fox jumps over the lazy dog. 1234567890"
            
            # Check if we have enough space for the sample text
            sample_height = font_size_num * 0.4 + 10  # Sample text height + margin
            if self.get_y() + sample_height > self.h - 60:
                self.add_page()
            
            if font_file:
                try:
                    self.add_font(font_family, font_style, font_file)
                    self.set_font(font_family, font_style, font_size_num)
                    self.set_text_color(80, 80, 80)
                    self.cell(0, font_size_num * 0.4, sample_text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                    self.ln(2)  # Add small spacing after sample text
                except Exception:
                    # Fallback to DejaVu
                    self.set_font('DejaVu', font_style, font_size_num)
                    self.set_text_color(80, 80, 80)
                    self.cell(0, font_size_num * 0.4, sample_text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                    self.ln(2)  # Add small spacing after sample text
            else:
                # Fallback to DejaVu
                self.set_font('DejaVu', font_style, font_size_num)
                self.set_text_color(80, 80, 80)
                self.cell(0, font_size_num * 0.4, sample_text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                self.ln(2)  # Add small spacing after sample text
            
            # Font details
            self.set_font('DejaVu', '', 10)
            self.set_text_color(100, 100, 100)
            self.cell(0, 6, f"Size: {font_size}   |   Line Height: {line_height}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.ln(2)  # Add spacing after details
            
            # Description
            if description:
                self.set_font('DejaVu', '', 9)
                self.set_text_color(150, 150, 150)
                self.multi_cell(0, 5, remove_emojis(description))
                self.ln(2)  # Add spacing after description
            
            # Add separator line between fonts
            self.set_draw_color(220, 220, 220)
            self.set_line_width(0.2)
            self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
            
            self.ln(10)  # Add more spacing between font samples

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
        # Draw circles for each color in a grid layout
        page_width = self.w - self.l_margin - self.r_margin
        colors_per_row = 3 if len(colors) > 2 else len(colors)
        gap = 20
        x_start = self.l_margin
        y = self.get_y()
        for idx, color in enumerate(colors):
            row = idx // colors_per_row
            col = idx % colors_per_row
            x = x_start + col * (circle_diameter + gap)
            y_row = y + row * (circle_diameter + 40)
            hex_val = color.get('hex_value', '#000000')
            r = int(hex_val[1:3], 16)
            g = int(hex_val[3:5], 16)
            b = int(hex_val[5:7], 16)
            # Draw circle
            self.set_fill_color(r, g, b)
            self.ellipse(x, y_row, circle_diameter, circle_diameter, style='F')
            # Hex code in center
            self.set_xy(x, y_row + circle_diameter / 2 - 6)
            self.set_text_color(255, 255, 255)
            self.set_font('DejaVu', 'B', 14)
            self.cell(circle_diameter, 12, hex_val, align='C', new_x=XPos.RIGHT, new_y=YPos.TOP)
            # Label below
            self.set_xy(x, y_row + circle_diameter + 2)
            self.set_text_color(40, 40, 40)
            self.set_font('DejaVu', 'B', 12)
            self.multi_cell(circle_diameter, 7, color.get('color_name', ''), align='C')
        # Move below the circles for the description (if any)
        total_rows = (len(colors) + colors_per_row - 1) // colors_per_row
        end_y = y + total_rows * (circle_diameter + 40)
        self.set_y(end_y)
        if description:
            self.set_font('DejaVu', '', 12)
            self.set_text_color(40, 40, 40)
            self.multi_cell(0, 8, description, align='C')
            self.ln(5)
        else:
            self.ln(5)

    def add_recommended_logo(self, logo_url, description=None):
        self.add_sub_section_title("Recommended Logo")
        if logo_url and not logo_url.lower().startswith("error"): 
            try:
                response = requests.get(logo_url)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_img:
                    tmp_img.write(response.content)
                    tmp_img.flush()
                    tmp_img_path = tmp_img.name
                self.image(tmp_img_path, w=self.w - self.l_margin - self.r_margin)
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
    allow_headers=["Content-Type", "Authorization", "Accept","x-user-id","x-user-email","x-user-data"],
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
        required_fields = ['userName', 'email', 'password', 'phoneNumber']
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
        phone_number = str(data['phoneNumber']).strip()
        auth_provider = str(data.get('authProvider', '')).strip()
        referral_code = str(data.get('referralCode', '')).strip()
        
        
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
        
        # Validate phone number format
        import re
        phone_pattern = re.compile(r'^\+?[\d\s\-\(\)]{7,20}$')
        if not phone_pattern.match(phone_number):
            return jsonify({
                'success': False,
                'error': 'Invalid phone number format. Please use a valid phone number with country code (e.g., +1234567890)'
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
        
        # Check for referral code
        referral_code = data.get('referralCode', '').strip()
        referrer_id = None
        
        if referral_code:
            try:
                with db.get_db_connection() as cursor:
                    cursor.execute("SELECT userId FROM users WHERE referral_code = %s", (referral_code,))
                    referrer = cursor.fetchone()
                    if referrer:
                        referrer_id = referrer[0]
                    else:
                        return jsonify({
                            'success': False,
                            'error': 'Invalid referral code'
                        }), 400
            except Exception as e:
                print(f"Error checking referral code: {e}")
                return jsonify({
                    'success': False,
                    'error': 'Error processing referral code'
            }), 500
        
        # Create user
        try:
            user = db.create_user(username, email, password, phone_number)
            
            # Generate referral code for new user
            if user:
                new_referral_code = generate_referral_code()
                try:
                    with db.get_db_connection() as cursor:
                        cursor.execute("UPDATE users SET referral_code = %s WHERE userId = %s", 
                                     (new_referral_code, user['userId']))
                        user['referral_code'] = new_referral_code
                except Exception as e:
                    print(f"Error setting referral code: {e}")
                
                # Track referral relationship (no rewards yet)
                if referrer_id:
                    try:
                        with db.get_db_connection() as cursor:
                            cursor.execute("UPDATE users SET referred_by = %s WHERE userId = %s", 
                                         (referrer_id, user['userId']))
                            user['referred_by'] = referrer_id
                            print(f"Referral relationship established: {referrer_id} referred {user['userId']} (no rewards yet)")
                    except Exception as e:
                        print(f"Error establishing referral relationship: {e}")
                        
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
            'email': user['email'],
            'phoneNumber': user.get('phone_number', ''),
            'referral_code': user.get('referral_code', '')
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
            'email': user['email'],
            'phoneNumber': user.get('phone_number', ''),
            'referral_code': user.get('referral_code', '')
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
@app.route('/get_answer/<answer_id>', methods=['GET'])
def get_answer_endpoint(answer_id):
    """
    Get the complete answer object for a given answer ID.
    """
    try:
        if not answer_id:
            return jsonify({
                'success': False,
                'message': 'answer_id is required',
                'answer': None
            }), 400
        
        answer = db.get_answer(answer_id)
        
        if answer:
            return jsonify({
                'success': True,
                'message': 'Answer retrieved successfully',
                'answer': answer
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Answer not found',
                'answer': None
            }), 404
            
    except Exception as e:
        print(f"Error getting answer: {e}")
        return jsonify({
            'success': False,
            'message': f'Error retrieving answer: {str(e)}',
            'answer': None
        }), 500


@app.route('/all_brands_with_users', methods=['GET'])
def all_brands_with_users():
    """
    Get all brands with their associated user information.
    """
    try:
        brands = db.get_all_brands_with_user_info()
        return jsonify({
            'success': True,
            'brands': brands
        }), 200
    except Exception as e:
        print(f"Error getting all brands with users: {e}")
        return jsonify({
            'success': False,
            'message': f'Error retrieving brands: {str(e)}',
            'brands': []
        }), 500


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

    print(f"🔄 CREATE_BRAND endpoint called for user: {data.get('userId', 'unknown')}")
    print(f"🔄 Request data: {data}")
    
    brand = db.create_brand(data['userId'])
    
    if brand is None:
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
        custom_colors = data.get('customColors', None)
        
        # Validate custom colors format if provided
        if custom_colors is not None:
            if not isinstance(custom_colors, dict):
                return jsonify({
                    'success': False,
                    'message': 'customColors must be a dictionary object',
                    'results': None
                }), 400
            
            # Validate color structure
            valid_color_keys = ['primary_colors', 'secondary_colors', 'brand_colors']
            for key in custom_colors.keys():
                if key not in valid_color_keys:
                    return jsonify({
                        'success': False,
                        'message': f'Invalid color key: {key}. Valid keys are: {", ".join(valid_color_keys)}',
                        'results': None
                    }), 400
                
                # Validate that color values are lists
                if not isinstance(custom_colors[key], list):
                    return jsonify({
                        'success': False,
                        'message': f'Color values must be lists. {key} is not a list.',
                        'results': None
                    }), 400
        
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
            others,
            custom_colors
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


@app.route('/admin/stats', methods=['GET'])
def admin_stats():
    """Get admin statistics"""
    try:
        total_users = db.count_total_users()
        total_brands = db.count_total_brands()
        first_payment_brands = db.count_brands_with_first_payment()
        premium_payment_brands = db.count_brands_with_premium_payment()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_users': total_users,
                'total_brands': total_brands,
                'first_payment_brands': first_payment_brands,
                'premium_payment_brands': premium_payment_brands
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ===================== REFERRAL SYSTEM =====================

@app.route('/referral/stats/<user_id>', methods=['GET'])
def get_user_referral_stats(user_id):
    """Get referral statistics for a user"""
    try:
        stats = get_referral_stats(user_id)
        if stats:
            return jsonify({
                'success': True,
                'stats': stats
            })
        else:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/referral/validate/<referral_code>', methods=['GET'])
def validate_referral_code(referral_code):
    """Validate a referral code"""
    try:
        with db.get_db_connection() as cursor:
            cursor.execute("""
                SELECT userId, username, email 
                FROM users 
                WHERE referral_code = %s
            """, (referral_code,))
            
            referrer = cursor.fetchone()
            if referrer:
                return jsonify({
                    'success': True,
                    'valid': True,
                    'referrer': {
                        'id': referrer[0],
                        'username': referrer[1],
                        'email': referrer[2]
                    }
                })
            else:
                return jsonify({
                    'success': True,
                    'valid': False,
                    'message': 'Invalid referral code'
                })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/referral/referrals/<user_id>', methods=['GET'])
def get_user_referrals(user_id):
    """Get list of users referred by a specific user"""
    try:
        with db.get_db_connection() as cursor:
            cursor.execute("""
                SELECT userId, username, email, created_at
                FROM users 
                WHERE referred_by = %s
                ORDER BY created_at DESC
            """, (user_id,))
            
            referrals = cursor.fetchall()
            referral_list = []
            
            for ref in referrals:
                referral_list.append({
                    'id': ref[0],
                    'username': ref[1],
                    'email': ref[2],
                    'joined_date': ref[3].isoformat() if ref[3] else None
                })
            
            return jsonify({
                'success': True,
                'referrals': referral_list,
                'total_referrals': len(referral_list)
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/referral/leaderboard', methods=['GET'])
def get_referral_leaderboard():
    """Get referral leaderboard"""
    try:
        with db.get_db_connection() as cursor:
            cursor.execute("""
                SELECT username, referred_users, referred_amount
                FROM users 
                WHERE referred_users > 0
                ORDER BY referred_users DESC, referred_amount DESC
                LIMIT 20
            """)
            
            leaderboard = cursor.fetchall()
            leaderboard_list = []
            
            for i, user in enumerate(leaderboard, 1):
                leaderboard_list.append({
                    'rank': i,
                    'username': user[0],
                    'referred_users': user[1] or 0,
                    'referred_amount': user[2] or 0
                })
            
            return jsonify({
                'success': True,
                'leaderboard': leaderboard_list
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/referral/generate-code/<user_id>', methods=['POST'])
def regenerate_referral_code(user_id):
    """Generate a new referral code for a user"""
    try:
        new_code = generate_referral_code()
        
        with db.get_db_connection() as cursor:
            cursor.execute("UPDATE users SET referral_code = %s WHERE userId = %s", 
                         (new_code, user_id))
            
            if cursor.rowcount > 0:
                return jsonify({
                    'success': True,
                    'new_referral_code': new_code
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'User not found'
                }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/referral/rewards/<user_id>', methods=['GET'])
def get_referral_rewards(user_id):
    """Get referral reward history and statistics for a user"""
    try:
        print(f"🔄 Getting referral rewards for user: {user_id}")
        
        # Get referral reward history
        reward_history = db.get_referral_reward_history(user_id)
        
        if not reward_history:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Calculate additional statistics
        total_earnings = reward_history.get('referred_amount', 0)
        total_referrals = reward_history.get('referred_users', 0)
        
        return jsonify({
            'success': True,
            'data': {
                'userId': reward_history['userId'],
                'referral_code': reward_history['referral_code'],
                'total_referrals': total_referrals,
                'total_earnings': total_earnings,
                'can_refer': reward_history.get('can_refer', False),
                'referred_by': reward_history.get('referred_by'),
                'earnings_breakdown': {
                    'from_referrals': total_earnings,
                    'from_purchases': 0,  # This could be calculated from payment history
                    'total': total_earnings
                }
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Error getting referral rewards: {e}")
        return jsonify({
            'success': False,
            'message': f'Error retrieving referral rewards: {str(e)}'
        }), 500

@app.route('/referral/history/<user_id>', methods=['GET'])
def get_referral_history(user_id):
    """Get detailed referral history for a user"""
    try:
        print(f"🔄 Getting referral history for user: {user_id}")
        
        with db.get_db_connection() as cursor:
            # Get users referred by this user
            cursor.execute("""
                SELECT 
                    u.userId,
                    u.username,
                    u.email,
                    u.created_at,
                    u.referred_amount,
                    COUNT(b.id) as brand_count,
                    MAX(b.created_at) as last_brand_created
                FROM users u
                LEFT JOIN brands b ON u.userId = b.userId
                WHERE u.referred_by = %s
                GROUP BY u.userId, u.username, u.email, u.created_at, u.referred_amount
                ORDER BY u.created_at DESC
            """, (user_id,))
            
            referrals = cursor.fetchall()
            
            referral_history = []
            for referral in referrals:
                user_id_ref, username, email, created_at, referred_amount, brand_count, last_brand_created = referral
                
                # Determine status based on whether they've created brands and earned rewards
                if referred_amount > 0:
                    status = "completed"
                    reward = referred_amount
                elif brand_count > 0:
                    status = "pending"
                    reward = 0
                else:
                    status = "registered"
                    reward = 0
                
                referral_history.append({
                    'id': user_id_ref,
                    'name': username or 'Unknown User',
                    'email': email or 'No email',
                    'status': status,
                    'date': created_at.isoformat() if created_at else None,
                    'reward': reward,
                    'brandCreated': brand_count > 0,
                    'brandCount': brand_count,
                    'lastBrandCreated': last_brand_created.isoformat() if last_brand_created else None
                })
            
            return jsonify({
                'success': True,
                'data': referral_history
            }), 200
        
    except Exception as e:
        print(f"❌ Error getting referral history: {e}")
        return jsonify({
            'success': False,
            'message': f'Error retrieving referral history: {str(e)}'
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
    brand_name = brand_communication.get('brand_name', brand.get('name', ''))
    brand_tagline = brand_communication.get('brand_tagline', '')

    primary_colors = brand_identity.get('primary_colors') if brand_identity else None
    secondary_colors = brand_identity.get('secondary_colors') if brand_identity else None
    brand_logo_url = brand.get('logo', '')  # Get logo from brand field
    pdf = BrandPDF()
    pdf.add_cover(brand_name, brand_tagline, primary_colors, secondary_colors)
    
    # Add table of contents
    pdf.add_page()
    pdf.set_font('DejaVu', 'B', 24)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 15, 'TABLE OF CONTENTS', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(20)
    
    # TOC items
    toc_items = [
        "Brand Communication",
        "Brand Strategy", 
        "Brand Identity",
        "Color Palette",
        "Typography",
        "Brand Logo",
        "Brand Guidelines",
        "Digital Specifications",
        "Brand Applications",
        "Social Media Content"
    ]
    
    pdf.set_font('DejaVu', '', 12)
    for i, item in enumerate(toc_items, 1):
        pdf.set_text_color(70, 70, 70)
        pdf.cell(0, 8, f"{i:02d}. {item}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
        pdf.ln(2)
    
    pdf.ln(20)
    
    primary_hex = None
    if primary_colors and isinstance(primary_colors, list) and len(primary_colors) > 0:
     primary_hex = primary_colors[0].get('hex_value', '#1E90FF')
    else:
     primary_hex = '#1E90FF'
    primary_rgb = pdf.hex_to_rgb(primary_hex)
    # Brand Communication Section
    if brand_communication:
        pdf.add_section_title("Brand Communication", True, primary_rgb)
        
        # Brand overview info box
        brand_name = brand_communication.get('brand_name', '')
        brand_tagline = brand_communication.get('brand_tagline', '')
        
        if brand_name or brand_tagline:
            overview_content = f"Brand: {brand_name}\nTagline: {brand_tagline}"
            pdf.add_info_box("Brand Overview", overview_content, (248, 250, 252))
        
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
                values_list = ovs.get('values', [])
                if isinstance(values_list, list):
                    # Extract the 'name' from each dictionary in the list
                    value_names = [str(v.get('name', '')) for v in values_list if isinstance(v, dict)]
                    pdf.add_key_value("Our Values", ', '.join(value_names))
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
        
        # # Business Strategy Section (from brand_assets)
        # if brand_assets and brand_assets.get('premium_assets', {}).get('business_strategy'):
        #     business_strategy = brand_assets['premium_assets']['business_strategy']
        #     pdf.add_page()
        #     pdf.add_section_title("Business Strategy", True, primary_rgb)
            
        #     # Market Positioning
        #     if business_strategy.get('market_positioning'):
        #         positioning = business_strategy['market_positioning']
        #         pdf.add_sub_section_title("Market Positioning", True)
        #         for key, value in positioning.items():
        #             if isinstance(value, list):
        #                 pdf.add_key_value(key.replace('_', ' ').title(), ', '.join(value), True)
        #             else:
        #                 pdf.add_key_value(key.replace('_', ' ').title(), str(value), True)
            
        #     # SWOT Analysis
        #     if business_strategy.get('swot_analysis'):
        #         swot = business_strategy['swot_analysis']
        #         pdf.add_sub_section_title("SWOT Analysis", True)
        #         for category, items in swot.items():
        #             if isinstance(items, list):
        #                 pdf.add_key_value(category.title(), ', '.join(items), True)
        #             else:
        #                 pdf.add_key_value(category.title(), str(items), True)
            
        #     # Target Audience Profiles
        #     if business_strategy.get('target_audience_profiles'):
        #         profiles = business_strategy['target_audience_profiles']
        #         pdf.add_sub_section_title("Target Audience Profiles", True)
        #         for i, profile in enumerate(profiles):
        #             if isinstance(profile, dict):
        #                 pdf.add_key_value(f"Persona {i+1}: {profile.get('persona_name', 'Unknown')}", 
        #                                 f"Demographics: {profile.get('demographics', 'N/A')} | "
        #                                 f"Motivations: {', '.join(profile.get('motivations', []))} | "
        #                                 f"Pain Points: {', '.join(profile.get('pain_points', []))}", True)
            
        #     # Competitive Analysis
        #     if business_strategy.get('competitive_analysis'):
        #         competitors = business_strategy['competitive_analysis']
        #         pdf.add_sub_section_title("Competitive Analysis", True)
        #         for i, competitor in enumerate(competitors):
        #             if isinstance(competitor, dict):
        #                 comp_name = competitor.get('competitor_name', f'Competitor {i+1}')
        #                 strengths = ', '.join(competitor.get('strengths', []))
        #                 weaknesses = ', '.join(competitor.get('weaknesses', []))
        #                 pdf.add_key_value(f"{comp_name} - Strengths", strengths, True)
        #                 pdf.add_key_value(f"{comp_name} - Weaknesses", weaknesses, True)
        
        # # Implementation Roadmap Section (from brand_assets)
        # if brand_assets and brand_assets.get('premium_assets', {}).get('implementation_roadmap'):
        #     roadmap = brand_assets['premium_assets']['implementation_roadmap']
        #     pdf.add_page()
        #     pdf.add_section_title("Implementation Roadmap", True, primary_rgb)
            
        #     # Launch Timeline
        #     if roadmap.get('launch_timeline'):
        #         timeline = roadmap['launch_timeline']
        #         pdf.add_sub_section_title("Launch Timeline", True)
        #         for phase in timeline:
        #             if isinstance(phase, dict):
        #                 phase_name = phase.get('phase', 'Unknown Phase')
        #                 duration = phase.get('duration', 'N/A')
        #                 deliverables = ', '.join(phase.get('deliverables', []))
        #                 pdf.add_key_value(f"{phase_name} ({duration})", deliverables, True)
            
        #     # Budget Estimates
        #     if roadmap.get('budget_estimates'):
        #         budgets = roadmap['budget_estimates']
        #         pdf.add_sub_section_title("Budget Estimates", True)
        #         for budget in budgets:
        #             if isinstance(budget, dict):
        #                 category = budget.get('category', 'Unknown')
        #                 cost = budget.get('estimated_cost', 'N/A')
        #                 description = budget.get('description', '')
        #                 pdf.add_key_value(f"{category} - {cost}", description, True)
            
        #     # Quality Assurance
        #     if roadmap.get('quality_assurance'):
        #         qa = roadmap['quality_assurance']
        #         pdf.add_sub_section_title("Quality Assurance", True)
        #         for checkpoint in qa:
        #             if isinstance(checkpoint, dict):
        #                 checkpoint_name = checkpoint.get('checkpoint', 'Unknown')
        #                 criteria = ', '.join(checkpoint.get('criteria', []))
        #                 metrics = ', '.join(checkpoint.get('success_metrics', []))
        #                 pdf.add_key_value(f"{checkpoint_name} - Criteria", criteria, True)
        #                 pdf.add_key_value(f"{checkpoint_name} - Success Metrics", metrics, True)

    # Brand Identity Section
    if brand_identity:
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
        # Brand Logo
        pdf.add_page()
        if brand_logo_url:
            pdf.add_brand_logo(brand_logo_url, brand_name)
        else:
            pdf.add_sub_section_title("Brand Logo")
            pdf.set_font('DejaVu', '', 10)
            pdf.cell(0, 8, 'No brand logo available', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(4)
        
        # Brand Guidelines Section (from brand_assets)
        if brand_assets and brand_assets.get('premium_assets', {}).get('brand_guidelines'):
            guidelines = brand_assets['premium_assets']['brand_guidelines']
           
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
        # if brand_assets and brand_assets.get('premium_assets', {}).get('digital_specifications'):
        #     digital_specs = brand_assets['premium_assets']['digital_specifications']
        #     pdf.add_page()
        #     pdf.add_section_title("Digital Specifications", True, primary_rgb)
            
        #     # Color Profiles
        #     if digital_specs.get('color_profiles'):
        #         profiles = digital_specs['color_profiles']
        #         pdf.add_sub_section_title("Color Profiles", True)
        #         for profile in profiles:
        #             if isinstance(profile, dict):
        #                 profile_type = profile.get('profile_type', 'Unknown')
        #                 color_values = profile.get('color_values', 'N/A')
        #                 usage = profile.get('usage_context', 'N/A')
        #                 pdf.add_key_value(f"{profile_type} Profile", f"{color_values} | {usage}", True)
            
        #     # Digital Specifications
        #     if digital_specs.get('digital_specifications'):
        #         specs = digital_specs['digital_specifications']
        #         pdf.add_sub_section_title("Platform Specifications", True)
        #         for spec in specs:
        #             if isinstance(spec, dict):
        #                 platform = spec.get('platform', 'Unknown')
        #                 dimensions = spec.get('dimensions', 'N/A')
        #                 format_type = spec.get('format', 'N/A')
        #                 file_size = spec.get('file_size', 'N/A')
        #                 pdf.add_key_value(f"{platform} ({dimensions})", f"Format: {format_type} | Size: {file_size}", True)
            
        #     # File Format Guidelines
        #     if digital_specs.get('file_format_guidelines'):
        #         formats = digital_specs['file_format_guidelines']
        #         pdf.add_sub_section_title("File Format Guidelines", True)
        #         for format_guide in formats:
        #             if isinstance(format_guide, dict):
        #                 format_type = format_guide.get('format', 'Unknown')
        #                 use_case = format_guide.get('use_case', 'N/A')
        #                 specs = format_guide.get('specifications', 'N/A')
        #                 pdf.add_key_value(f"{format_type} Format", f"{use_case} | {specs}", True)
            
        #     # Print Specifications
        #     if digital_specs.get('print_specifications'):
        #         print_specs = digital_specs['print_specifications']
        #         pdf.add_sub_section_title("Print Specifications", True)
        #         for print_spec in print_specs:
        #             if isinstance(print_spec, dict):
        #                 resolution = print_spec.get('resolution', 'N/A')
        #                 color_mode = print_spec.get('color_mode', 'N/A')
        #                 material = print_spec.get('material', 'N/A')
        #                 pdf.add_key_value(f"Print Specs", f"Resolution: {resolution} | Color: {color_mode} | Material: {material}", True)


    # Brand Applications Section
    if brand_assets:
        full_brand_identity = brand_assets.get('full_brand_identity')
        if full_brand_identity and isinstance(full_brand_identity, dict):
            # Business Cards
            business_cards = full_brand_identity.get('business_cards', [])
            if business_cards:
                for i, card in enumerate(business_cards):
                   
                    # Add title for business card
                    pdf.add_section_title("Business Card", True, primary_rgb)
                    image_url = card.get('image_url')
                    pdf.add_application_image(image_url, "Business Card")
            
            # Letterheads
            letterheads = full_brand_identity.get('letterheads', [])
            if letterheads:
                for i, letterhead in enumerate(letterheads):
                    
                    # Add title for letterhead
                    pdf.add_section_title("Letterhead", True, primary_rgb)
                    image_url = letterhead.get('image_url')
                    pdf.add_application_image(image_url, "Letterhead")
            
            # T-Shirt Mockups
            t_shirt_mockups = full_brand_identity.get('t_shirt_mockups', [])
            if t_shirt_mockups:
                for i, tshirt in enumerate(t_shirt_mockups):
                    
                    # Add title for t-shirt mockup
                    pdf.add_section_title("T-Shirt Mockup", True, primary_rgb)
                    image_url = tshirt.get('image_url')
                    pdf.add_application_image(image_url, "T-Shirt Mockup")
            
            # Cap Mockups
            cap_mockups = full_brand_identity.get('cap_mockups', [])
            if cap_mockups:
                for i, cap in enumerate(cap_mockups):
                    
                    # Add title for cap mockup
                    pdf.add_section_title("Cap Mockup", True, primary_rgb)
                    image_url = cap.get('image_url')
                    pdf.add_application_image(image_url, "Cap Mockup")
            
            # Signboards
            signboards = full_brand_identity.get('signboards', [])
            if signboards:
                for i, signboard in enumerate(signboards):
                    
                    # Add title for signboard
                    pdf.add_section_title("Signboard", True, primary_rgb)
                    image_url = signboard.get('image_url')
                    pdf.add_application_image(image_url, "Signboard")
            
            # Brand Patterns
            brand_patterns = full_brand_identity.get('brand_patterns', [])
            if brand_patterns:
                for i, pattern in enumerate(brand_patterns):
                    
                    # Add title for brand pattern
                    pdf.add_section_title("Brand Pattern", True, primary_rgb)
                    image_url = pattern.get('image_url')
                    pdf.add_application_image(image_url, "Brand Pattern")
        
        
        # Social Media Content Section (from brand_assets)
        if brand_assets and brand_assets.get('social_media_content'):
            social_content = brand_assets['social_media_content']
            
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

@app.route('/delete_brand', methods=['POST'])
def delete_brand():
    """Delete a brand and all its associated data"""
    try:
        data = request.get_json()
        if not data or 'brandId' not in data:
            return jsonify({
                'success': False,
                'message': 'brandId is required',
                'deleted': False
            }), 400
        
        brand_id = data['brandId']
        user_id = data.get('userId')  # Optional user ID for additional validation
        
        print(f"🔄 DELETE_BRAND endpoint called for brandId: {brand_id}, userId: {user_id}")
        
        # Check if brand exists
        brand_exists = db.get_brand(brand_id)
        if not brand_exists:
            return jsonify({
                'success': False,
                'message': 'Brand not found',
                'deleted': False
            }), 404
        
        # Optional: Verify user owns the brand (if userId provided)
        if user_id and brand_exists.get('userId') != user_id:
            return jsonify({
                'success': False,
                'message': 'Unauthorized: You can only delete your own brands',
                'deleted': False
            }), 403
        
        # Delete the brand (this will cascade delete related data due to foreign key constraints)
        deleted = db.delete_brand(brand_id)
        
        if deleted:
            print(f"✅ Brand {brand_id} deleted successfully")
            return jsonify({
                'success': True,
                'message': 'Brand deleted successfully',
                'deleted': True
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to delete brand',
                'deleted': False
            }), 500
            
    except Exception as e:
        print(f"❌ Error deleting brand: {e}")
        return jsonify({
            'success': False,
            'message': f'Error deleting brand: {str(e)}',
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
        if not data or 'brandId' not in data or 'paymentStatus' not in data or 'transactionId' not in data:
            return jsonify({
                'success': False,
                'message': 'brandId, paymentStatus, and transactionId are required',
                'updated': False
            }), 400
        
        brand_id = data['brandId']
        payment_status = data['paymentStatus']
        transaction_id = data['transactionId']
        # Get the userid from the headers
        userid = request.headers.get('x-user-id')
        if not userid:
            return jsonify({
                'success': False,
                'message': 'userid header is required',
                'updated': False
            }), 400
        
        # Validate payment_status is boolean
        if not isinstance(payment_status, bool):
            return jsonify({
                'success': False,
                'message': 'paymentStatus must be a boolean value',
                'updated': False
            }), 400
        
        # Check if transaction already exists to prevent duplicate processing
        if db.check_transaction_exists(transaction_id):
            return jsonify({
                'success': False,
                'message': 'Transaction ID already exists. Payment status not updated.',
                'updated': False
            }), 400
        
        # Create transaction record
        if not db.create_transaction(transaction_id, userid, brand_id):
            return jsonify({
                'success': False,
                'message': 'Failed to create transaction record',
                'updated': False
            }), 500
        
        success = db.update_brand_payment_status(brand_id, payment_status)
        
        if success:
            # Mark transaction as paid
            db.mark_transaction_paid(transaction_id, payment_status)
            
            # Check if referral rewards should be processed
            referral_message = ""
            if payment_status:  # Only process rewards when payment is successful
                try:
                    with db.get_db_connection() as cursor:
                        # Get brand owner info
                        cursor.execute("SELECT userid FROM brands WHERE id = %s", (brand_id,))
                        brand_info = cursor.fetchone()
                        if brand_info:
                            user_id = brand_info[0]
                            # Check if user was referred by someone
                            cursor.execute("SELECT referred_by FROM users WHERE userId = %s", (user_id,))
                            referrer_info = cursor.fetchone()
                            if referrer_info and referrer_info[0]:
                                referrer_id = referrer_info[0]
                                # Increment referrer's referral amount by 1000 and referred_users by 1
                                cursor.execute("""
                                    UPDATE users 
                                    SET referred_amount = referred_amount + 4500,
                                        referred_users = referred_users + 1
                                    WHERE userId = %s
                                """, (referrer_id,))
                                
                                if cursor.rowcount > 0:
                                    # Mark referral reward as processed
                                    db.mark_referral_reward_processed(transaction_id)
                                    referral_message = f" Referral reward of 4,500 processed for user {referrer_id}. Referred users count incremented."
                                    print(f"Referral reward processed: {referrer_id} earned 4,500 from {user_id}, referred_users incremented")
                                else:
                                    print(f"Failed to update referral stats for user {referrer_id}")
                except Exception as e:
                    print(f"Error processing referral reward: {e}")
                    # Don't fail the payment update if referral processing fails
            
            return jsonify({
                'success': True,
                'message': f'Payment status updated successfully.{referral_message}',
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
                'phoneNumber': existing_user.get('phone_number', ''),
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
                    'phoneNumber': new_user.get('phone_number', ''),
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
                'phoneNumber': existing_user.get('phone_number', ''),
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
                    'phoneNumber': new_user.get('phone_number', ''),
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

# ===================== Fapshi Payment Endpoints =====================

@app.route('/api/payment/initiate', methods=['POST'])
def initiate_fapshi_payment():
    """Initiate a Fapshi payment transaction"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['amount', 'brandId']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Extract data
        amount = data['amount']
        brand_id = data['brandId']
        email = data.get('email')
        redirect_url = data.get('redirectUrl')
        user_id = data.get('userId')
        message = data.get('message', f'Payment for Brand Kit - {brand_id}')
        
        # Generate unique external ID
        import uuid
        external_id = f"brand_ai_{brand_id}_{uuid.uuid4().hex[:8]}"
        
        # Import Fapshi payment handler
        try:
            from fapshi_payment import fapshi
        except ImportError:
            return jsonify({
                'success': False,
                'error': 'Payment service not available'
            }), 500
        
        # Initiate payment
        result = fapshi.initiate_payment(
            amount=amount,
            email=email,
            redirect_url=redirect_url,
            user_id=user_id,
            external_id=external_id,
            message=message
        )
        
        if result['success']:
            # Store payment transaction in database
            transaction_id = db.create_payment_transaction(
                external_id=external_id,
                brand_id=brand_id,
                user_id=user_id,
                amount=amount,
                currency='XAF',
                redirect_url=redirect_url,
                message=message,
                payer_email=email
            )
            
            # Update with Fapshi transaction details
            if transaction_id and result['data']:
                db.update_payment_transaction(
                    external_id=external_id,
                    fapshi_trans_id=result['data'].get('transId'),
                    payment_link=result['data'].get('link'),
                    status='PENDING'
                )
            
            return jsonify({
                'success': True,
                'message': 'Payment initiated successfully',
                'data': result['data'],
                'external_id': external_id
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        print(f"Error initiating Fapshi payment: {e}")
        return jsonify({
            'success': False,
            'error': f'Error initiating payment: {str(e)}'
        }), 500

@app.route('/api/payment/verify', methods=['POST'])
def verify_fapshi_payment():
    """Verify a Fapshi payment transaction"""
    try:
        data = request.get_json()
        
        print(f"🔄 VERIFY_PAYMENT endpoint called with data: {data}")
        
        if not data or 'transId' not in data:
            print("❌ Missing transaction ID in request")
            return jsonify({
                'success': False,
                'error': 'Transaction ID is required'
            }), 400
        
        trans_id = data['transId']
        print(f"🔄 Verifying payment for transaction ID: {trans_id}")
        
        # Import Fapshi payment handler
        try:
            from fapshi_payment import fapshi
        except ImportError:
            return jsonify({
                'success': False,
                'error': 'Payment service not available'
            }), 500
        
        # Verify payment
        result = fapshi.verify_payment(trans_id)
        print(f"🔄 Fapshi verification result: {result}")
        
        if result['success']:
            if result['verified']:
                # Payment was successful
                payment_data = result['payment_data']
                print(f"✅ Payment verified successfully: {payment_data}")
                
                # Extract brand_id from external_id if available
                external_id = payment_data.get('externalId', '')
                if external_id.startswith('brand_ai_'):
                    parts = external_id.split('_')
                    if len(parts) >= 3:
                        brand_id = parts[2]
                        
                        # Update payment transaction status
                        db.update_payment_transaction(
                            external_id=external_id,
                            status='SUCCESSFUL',
                            payment_data=payment_data,
                            payer_name=payment_data.get('payerName'),
                            payer_phone=payment_data.get('phone_number'),
                            payment_method=payment_data.get('medium')
                        )
                        
                        # Update brand payment status
                        db.update_brand_payment_status(brand_id, True)
                        print(f"✅ Fapshi payment successful for brand {brand_id}")
                        
                        # Process referral rewards (20% of 15k = 3k XAF shared equally)
                        try:
                            # Get the user who owns this brand
                            brand_info = db.get_brand(brand_id)
                            if brand_info and brand_info.get('userId'):
                                user_id = brand_info['userId']
                                payment_amount = payment_data.get('amount', 15000)  # Default to 15k if not specified
                                
                                print(f"🔄 Processing referral rewards for user {user_id}, amount {payment_amount}")
                                referral_result = db.process_referral_reward(brand_id, user_id, payment_amount)
                                
                                if referral_result['success']:
                                    print(f"✅ Referral rewards processed: {referral_result}")
                                else:
                                    print(f"❌ Failed to process referral rewards: {referral_result}")
                            else:
                                print(f"❌ Could not find brand owner for brand {brand_id}")
                        except Exception as e:
                            print(f"❌ Error processing referral rewards: {e}")
                            # Don't fail the payment verification if referral processing fails
                
                return jsonify({
                    'success': True,
                    'verified': True,
                    'message': 'Payment verified successfully',
                    'payment_data': payment_data
                }), 200
            else:
                # Payment failed or pending
                error_msg = result.get('error', 'Payment verification failed')
                print(f"❌ Payment verification failed: {error_msg}")
                return jsonify({
                    'success': True,
                    'verified': False,
                    'error': error_msg,
                    'payment_data': result.get('payment_data', {})
                }), 200
        else:
            error_msg = result['error']
            print(f"❌ Payment verification error: {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
            
    except Exception as e:
        print(f"Error verifying Fapshi payment: {e}")
        return jsonify({
            'success': False,
            'error': f'Error verifying payment: {str(e)}'
        }), 500

@app.route('/api/payment/status', methods=['GET'])
def get_fapshi_payment_status():
    """Get Fapshi payment status"""
    try:
        trans_id = request.args.get('transId')
        
        if not trans_id:
            return jsonify({
                'success': False,
                'error': 'Transaction ID is required'
            }), 400
        
        # Import Fapshi payment handler
        try:
            from fapshi_payment import fapshi
        except ImportError:
            return jsonify({
                'success': False,
                'error': 'Payment service not available'
            }), 500
        
        # Get payment status
        try:
            payment_data = fapshi.get_payment_status(trans_id)
            
            return jsonify({
                'success': True,
                'payment_data': payment_data
            }), 200
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
            
    except Exception as e:
        print(f"Error getting Fapshi payment status: {e}")
        return jsonify({
            'success': False,
            'error': f'Error getting payment status: {str(e)}'
        }), 500

@app.route('/api/payment/callback', methods=['POST'])
def fapshi_payment_callback():
    """Handle Fapshi payment callback/webhook"""
    try:
        data = request.get_json()
        
        print(f"Fapshi callback received: {json.dumps(data, indent=2)}")
        
        # Extract payment data from Fapshi callback
        trans_id = data.get('transId')
        status = data.get('status')
        amount = data.get('amount')
        external_id = data.get('externalId')
        
        if status == 'SUCCESSFUL' and trans_id:
            # Payment was successful
            print(f"Fapshi payment successful for transaction: {trans_id}")
            
            # Extract brand_id from external_id if available
            if external_id and external_id.startswith('brand_ai_'):
                parts = external_id.split('_')
                if len(parts) >= 3:
                    brand_id = parts[2]
                    
                    # Update payment transaction status
                    db.update_payment_transaction(
                        external_id=external_id,
                        fapshi_trans_id=trans_id,
                        status='SUCCESSFUL',
                        payment_data=data,
                        payer_name=data.get('payerName'),
                        payer_phone=data.get('phone_number'),
                        payment_method=data.get('medium')
                    )
                    
                    # Update brand payment status
                    db.update_brand_payment_status(brand_id, True)
                    print(f"Payment status updated for brand {brand_id}")
            
            return jsonify({
                'success': True,
                'message': 'Fapshi payment callback processed successfully'
            }), 200
        else:
            print(f"Fapshi payment failed or pending for transaction: {trans_id}")
            print(f"Status: {status}")
            
            return jsonify({
                'success': False,
                'message': f'Fapshi payment not successful. Status: {status}'
            }), 400
            
    except Exception as e:
        print(f"Fapshi callback error: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to process Fapshi callback: {str(e)}'
        }), 500

@app.route('/api/payment/transactions/<brand_id>', methods=['GET'])
def get_payment_transactions_by_brand(brand_id):
    """Get all payment transactions for a specific brand"""
    try:
        transactions = db.get_payment_transactions_by_brand(brand_id)
        
        return jsonify({
            'success': True,
            'transactions': transactions,
            'count': len(transactions)
        }), 200
        
    except Exception as e:
        print(f"Error getting payment transactions for brand {brand_id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Error retrieving payment transactions: {str(e)}'
        }), 500

@app.route('/api/payment/transactions/user/<user_id>', methods=['GET'])
def get_payment_transactions_by_user(user_id):
    """Get all payment transactions for a specific user"""
    try:
        transactions = db.get_payment_transactions_by_user(user_id)
        
        return jsonify({
            'success': True,
            'transactions': transactions,
            'count': len(transactions)
        }), 200
        
    except Exception as e:
        print(f"Error getting payment transactions for user {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Error retrieving payment transactions: {str(e)}'
        }), 500

@app.route('/api/payment/transaction/<external_id>', methods=['GET'])
def get_payment_transaction(external_id):
    """Get a specific payment transaction by external_id"""
    try:
        transaction = db.get_payment_transaction(external_id=external_id)
        
        if transaction:
            return jsonify({
                'success': True,
                'transaction': transaction
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Transaction not found'
            }), 404
        
    except Exception as e:
        print(f"Error getting payment transaction {external_id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Error retrieving payment transaction: {str(e)}'
        }), 500

@app.route('/api/user/<user_id>/brands', methods=['GET'])
def get_user_brands(user_id):
    """Get all brands created by a specific user"""
    try:
        brands = db.get_user_brands(user_id)
        
        return jsonify({
            'success': True,
            'brands': brands,
            'count': len(brands)
        }), 200
        
    except Exception as e:
        print(f"Error getting brands for user {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Error retrieving user brands: {str(e)}'
        }), 500

@app.route('/api/health/database', methods=['GET'])
def api_database_health_check():
    """Check database connection health"""
    try:
        # Get database info
        db_info = db.get_database_info()
        
        # Perform health check
        is_healthy = db.check_database_health()
        
        return jsonify({
            'success': True,
            'healthy': is_healthy,
            'database_info': db_info,
            'timestamp': datetime.now().isoformat()
        }), 200 if is_healthy else 503
        
    except Exception as e:
        print(f"Database health check error: {e}")
        return jsonify({
            'success': False,
            'healthy': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503

@app.route('/api/health', methods=['GET'])
def api_health_check():
    """General health check endpoint"""
    try:
        # Check database health
        db_healthy = db.check_database_health()
        
        return jsonify({
            'success': True,
            'status': 'healthy' if db_healthy else 'unhealthy',
            'database': 'connected' if db_healthy else 'disconnected',
            'timestamp': datetime.now().isoformat()
        }), 200 if db_healthy else 503
        
    except Exception as e:
        print(f"Health check error: {e}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503


if __name__ == '__main__':
    # Run on host 0.0.0.0 to be accessible from outside, port 8080
    app.run(host='0.0.0.0', port=8080, debug=True)
    
