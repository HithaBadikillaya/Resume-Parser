from flask import Flask, request, render_template
import pdfplumber
import os
import re
from werkzeug.utils import secure_filename
import traceback

# Set the template folder relative to the "api" folder.
app = Flask(__name__, template_folder="../templates")

# IMPORTANT: Use /tmp for file uploads on Vercel (writable location for serverless functions)
UPLOAD_FOLDER = "/tmp/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def calculate_match_percentage(found_skills, total_skills):
    return round((len(found_skills) / total_skills) * 100) if total_skills > 0 else 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_resume():
    try:
        uploaded_file = request.files['resume']
        skills_input = request.form.get('skills_input', '')

        skills_list = [skill.strip() for skill in skills_input.split(',') if skill.strip()]
        filename = secure_filename(uploaded_file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        uploaded_file.save(file_path)

        text = ""
        with pdfplumber.open(file_path) as pdf:
            text = "\n".join(page.extract_text() or '' for page in pdf.pages)

        parsed_data = {
            "name": "Not Found",
            "email": "Not Found",
            "phone": "Not Found",
            "skills": []
        }

        lines = text.split('\n')
        if lines:
            parsed_data["name"] = lines[0].strip()

        email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        phone_match = re.search(r"\+?\d[\d -]{8,12}\d", text)
        
        parsed_data["email"] = email_match.group() if email_match else "Not Found"
        parsed_data["phone"] = phone_match.group().strip() if phone_match else "Not Found"

        found_skills = [skill for skill in skills_list if re.search(rf'\b{re.escape(skill)}\b', text, re.IGNORECASE)]
        parsed_data["skills"] = found_skills
        match_percentage = calculate_match_percentage(found_skills, len(skills_list))

        return render_template('index.html', data=parsed_data, skills_input=skills_input, match_percentage=match_percentage)
    except Exception as e:
        # Log the traceback for debugging purposes (visible in Vercel logs)
        print(traceback.format_exc())
        return "Internal Server Error", 500

if __name__ == '__main__':
    app.run(debug=True)
