import os
import streamlit as st
import pdfplumber
import docx2txt
from groq import Groq

# Page configuration
st.set_page_config(
    page_title="ATS Resume Checker",
    page_icon="📄",
    layout="wide"
)

# Function to extract text from PDF
def extract_text_from_pdf(uploaded_file):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    return text

# Function to extract text from DOCX
def extract_text_from_docx(uploaded_file):
    return docx2txt.process(uploaded_file)

# Function to analyze resume using Groq LLM
def analyze_resume(api_key, resume_text, job_description=""):
    client = Groq(api_key=api_key)
    
    system_prompt = (
        "You are an expert ATS (Applicant Tracking System) reviewer and hiring manager. "
        "Analyze the candidate's resume and provide an evaluation."
    )
    
    user_prompt = f"""
    Resume Content:
    {resume_text}
    
    Target Job Description (Optional):
    {job_description if job_description else "General Software/Tech Industry standard evaluation"}
    
    Please provide the evaluation structured as follows:
    1. Overall ATS Score (0 to 100).
    2. Executive Summary (2-3 sentences).
    3. Key Strengths (3 bullet points).
    4. Missing Keywords & Skills.
    5. Formatting & Structure Feedback.
    6. Actionable Improvement Recommendations (Detailed bullet points).
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2,
        max_tokens=2048
    )
    
    return response.choices[0].message.content

# --- Streamlit UI Setup ---
st.title("📄 ATS Resume Score & Improvement Assistant")
st.write("Upload your resume (PDF or DOCX) to get an ATS compatibility score and recommendations.")

# Sidebar for API Key input
with st.sidebar:
    st.header("Settings")
    # Retrieve key from environment variable (Streamlit Secrets) or fallback to text input
    env_api_key = os.environ.get("GROQ_API_KEY", "")
    api_key_input = st.text_input(
        "Enter Groq API Key:", 
        value=env_api_key, 
        type="password",
        help="Get a free key from https://console.groq.com/keys"
    )

# Main UI Inputs
job_desc = st.text_area("Target Job Description (Optional)", height=150, placeholder="Paste the job requirements here for targeted matching...")
uploaded_file = st.file_uploader("Upload Resume", type=["pdf", "docx"])

if st.button("Analyze Resume", type="primary"):
    if not api_key_input:
        st.error("Please provide a Groq API Key in the sidebar or via secrets.")
    elif uploaded_file is None:
        st.warning("Please upload a resume file before analyzing.")
    else:
        with st.spinner("Extracting text and analyzing resume..."):
            try:
                # Extract text based on file extension
                if uploaded_file.name.endswith(".pdf"):
                    resume_text = extract_text_from_pdf(uploaded_file)
                elif uploaded_file.name.endswith(".docx"):
                    resume_text = extract_text_from_docx(uploaded_file)
                else:
                    resume_text = ""

                if not resume_text.strip():
                    st.error("Could not extract readable text from the file. Ensure it is not a scanned image PDF.")
                else:
                    # Run AI analysis
                    result = analyze_resume(api_key_input, resume_text, job_desc)
                    st.success("Analysis Complete!")
                    st.markdown("---")
                    st.markdown(result)
            except Exception as e:
                st.error(f"An error occurred during analysis: {e}")