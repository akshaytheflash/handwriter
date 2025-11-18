from flask import Flask, render_template, request, send_file, jsonify
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os
import io
from datetime import datetime

app = Flask(__name__)

CHAR_DIR = "handwriting_trimmed"
PAGE_WIDTH, PAGE_HEIGHT = A4


def load_chars():
    chars = {}
    max_h = 0

    for f in os.listdir(CHAR_DIR):
        if f.endswith(".png"):
            name = os.path.splitext(f)[0]
            img_path = os.path.join(CHAR_DIR, f)
            img = Image.open(img_path)
            chars[name] = img_path
            max_h = max(max_h, img.size[1])

    return chars, max_h


def render_pdf(text, settings):
    chars, MAX_H = load_chars()
    
    # Extract settings
    left_margin = settings.get('left_margin', 50)
    right_margin = settings.get('right_margin', 50)
    top_margin = settings.get('top_margin', 50)
    bottom_margin = settings.get('bottom_margin', 50)
    font_size = settings.get('font_size', 1.0)
    space_width = settings.get('space_width', 35)
    line_height = settings.get('line_height', 90)
    letter_spacing = settings.get('letter_spacing', 5)
    
    # Create PDF in memory
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    x = left_margin
    y = PAGE_HEIGHT - top_margin - (line_height * font_size)

    for ch in text:

        if ch == "\n":
            x = left_margin
            y -= line_height * font_size
            continue

        if ch == " ":
            x += space_width * font_size
            continue

        key = ch.lower()

        if key not in chars:
            continue

        # Load image dimensions
        img_path = chars[key]
        img = Image.open(img_path)
        w, h = img.size
        
        # Apply font size scaling
        scaled_w = w * font_size
        scaled_h = h * font_size

        # WRAP - check if it fits within right margin
        if x + scaled_w > PAGE_WIDTH - right_margin:
            x = left_margin
            y -= line_height * font_size
            
            # Check if we need a new page
            if y < bottom_margin:
                pdf.showPage()
                x = left_margin
                y = PAGE_HEIGHT - top_margin - (line_height * font_size)

        # Draw image directly using the path
        pdf.drawImage(img_path, x, y, width=scaled_w, height=scaled_h, mask='auto')

        x += scaled_w + (letter_spacing * font_size)

    pdf.save()
    buffer.seek(0)
    return buffer


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        text = data.get('text', '')
        settings = data.get('settings', {})
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Generate PDF
        pdf_buffer = render_pdf(text, settings)
        
        # Generate filename with timestamp
        filename = f"handwritten_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)