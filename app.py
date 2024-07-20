from flask import Flask, request, render_template, redirect, url_for, session
from dotenv import load_dotenv
import os
import pdf2image
import io
import base64
import google.generativeai as genai
import markdown

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")  # Set a secret key for session management
load_dotenv()  # Load environment variables from .env file

google_api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=google_api_key)

def get_gemini_response(input_text, pdf_content, prompt):
    model = genai.GenerativeModel('models/gemini-1.5-pro-latest')
    response = model.generate_content([input_text, pdf_content[0], prompt])
    return response.text

def input_pdf_setup(uploaded_file):
    images = pdf2image.convert_from_bytes(uploaded_file.read())
    first_page = images[0]
    img_byte_arr = io.BytesIO()
    first_page.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()

    pdf_parts = [
        {
            "mime_type": "image/jpeg",
            "data": base64.b64encode(img_byte_arr).decode()  # encode to base64
        }
    ]
    return pdf_parts

@app.before_request
def before_request():
    session.modified = True  # Ensure session is marked as modified on each request
    print("Session before request:", session)  # Debugging output

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        session['input_text'] = request.form.get("input_text")
        session['action'] = request.form.get("action")
        uploaded_file = request.files.get("uploaded_file")

        if uploaded_file:
            pdf_content = input_pdf_setup(uploaded_file)
            action = session['action']  # Retrieve action from session

            # Define prompts based on action
            if action == "review_my_resume":
                prompt = """
                Act as an experienced Technical Human Resource Manager. Review the provided resume against the job description. 
                Share a professional evaluation of whether the candidate's profile aligns with the role, highlighting strengths and weaknesses relative to the job requirements.
                """
            elif action == "improve_skill":
                prompt = """
                Act as a Technical Human Resource Manager specializing in data science. Analyze the resume in light of the job description. 
                Provide insights on the candidate's suitability for the role, offer advice on skill enhancement, and identify areas needing improvement.
                """
            elif action == "keywords":
                prompt = """
                Act as a skilled ATS (Applicant Tracking System) scanner with expertise in data science and ATS functionality. 
                Assess the resume against the job description, identifying missing keywords and offering recommendations for skill enhancement and areas needing improvement.
                """
            elif action == "percentage":
                prompt = """
                Act as a skilled ATS (Applicant Tracking System) scanner with expertise in data science and ATS functionality. 
                Evaluate the resume against the job description, providing the percentage match and mismatch with the role's requirements.
                """
            elif action == "highlight":
                prompt = """
                Highlight the 5 most important responsibilities in this job description
                """
            elif action == "cover_letter":
                prompt = """
                Please write a personalized cover letter for this Job Description
                """
            elif action == "interview":
                prompt = """
                Provide me a list of 5 interview questions based on job description.
                """

            # Get Gemini response
            response = get_gemini_response(session['input_text'], pdf_content, prompt)

            # Convert Markdown to HTML
            response = markdown.markdown(response)
            # Ensure session data is cleared after displaying result

            session.pop('action', None)

            # Redirect to results page with the response
            return redirect(url_for('result', response=response))
        else:
            response = "Please upload a PDF file to proceed."

    return render_template('index.html', input_text=session.get('input_text', ''))  # Pass input_text to template

# Route to display the result page
@app.route('/result')
def result():
    response = request.args.get('response')


    return render_template('result.html', response=response)


if __name__ == '__main__':
    app.run(debug=True)
