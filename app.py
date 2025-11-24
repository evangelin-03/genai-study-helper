import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI
import PyPDF2

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

st.title("GenAI Study Helper")
st.write("Paste your notes below or upload a PDF to generate quiz questions or flashcards!")

uploaded_file = st.file_uploader("Upload a PDF", type="pdf")#uploading pdf file 

pdf_text = ""
if uploaded_file is not None:
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    for page in pdf_reader.pages:
        pdf_text += page.extract_text() or ""  #extract text safely

notes = st.text_area("Paste your notes here:", value=pdf_text) #notes area


if st.button("Generate Questions"): #generate questions
    if notes.strip() == "":
        st.warning("Please paste notes or upload a PDF first.")
    else:
        num_questions = 30  
        prompt = f"Turn the following notes into {num_questions} multiple-choice quiz questions:\n\n{notes}"
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        st.subheader("Generated Questions")
        st.write(response.choices[0].message.content)

# --- Generate Flashcards ---
if st.button("Generate Flashcards"):
    if notes.strip() == "":
        st.warning("Please paste notes or upload a PDF first.")
    else:
        prompt = f"Turn the following notes into 20 flashcards with Question and Answer format:\n\n{notes}"
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        st.subheader("Generated Flashcards")
        st.write(response.choices[0].message.content)