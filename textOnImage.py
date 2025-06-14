import os
from PIL import Image, ImageDraw, ImageFont

def add_text_top_left(image_path: str, text: str) -> str:
    """
    Adds text to the top-left corner of an image with a background rectangle,
    and saves the image with 'edited' appended to the filename.

    Args:
        image_path (str): Path to the input image.
        text (str): Text to write on the image.

    Returns:
        str: Path to the saved edited image.
    """
    # Load image
    image = Image.open(image_path).convert("RGBA")
    txt_layer = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(txt_layer)

    # Load font (fallback to default if not available)
    try:
        font = ImageFont.truetype("arial.ttf", 50)
    except IOError:
        font = ImageFont.load_default()

    # Calculate text box size
    padding = 10
    text_bbox = draw.textbbox((0, 0), text, font=font)
    box_width = text_bbox[2] - text_bbox[0] + padding * 2
    box_height = text_bbox[3] - text_bbox[1] + padding * 2

    # Draw background rectangle
    draw.rectangle((0, 0, box_width, box_height), fill=(0, 0, 0, 160))  # semi-transparent black

    # Draw text
    draw.text((padding, padding), text, font=font, fill=(255, 255, 255, 255))

    # Merge layers
    combined = Image.alpha_composite(image, txt_layer).convert("RGB")

    # Save with "edited" in filename
    base, ext = os.path.splitext(image_path)
    new_path = f"{base}_edited{ext}"
    combined.save(new_path)

    return new_path

