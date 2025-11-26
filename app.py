import streamlit as st
import os
from dotenv import load_dotenv
import PyPDF2
from google import genai
import re

# Page configuration
st.set_page_config(
    page_title="GenAI Study Helper",
    page_icon="📚",
    layout="wide"
)

# Custom CSS for better styling including flashcard flip animation
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #1E88E5;
        color: white;
        font-weight: bold;
        padding: 0.75rem;
        border-radius: 8px;
        border: none;
        transition: background-color 0.3s;
    }
    .stButton>button:hover {
        background-color: #1565C0;
    }
    .success-box {
        padding: 1rem;
        border-radius: 8px;
        background-color: #E8F5E9;
        border-left: 4px solid #4CAF50;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 8px;
        background-color: #666;
        border-left: 4px solid #2196F3;
        margin: 1rem 0;
    }
    [data-testid="stFileUploader"] {
        width: 100%;
    }
    .uploadedFile {
        display: none;
    }
    .flashcard-container {
        perspective: 1000px;
        margin: 2rem auto;
        max-width: 600px;
    }
    .flashcard {
        background: white;
        border-radius: 15px;
        padding: 3rem 2rem;
        min-height: 300px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        cursor: pointer;
        transition: transform 0.3s;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
    }
    .flashcard:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(0,0,0,0.25);
    }
    .flashcard-question {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    .flashcard-answer {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
    }
    .flashcard-label {
        font-size: 0.9rem;
        font-weight: bold;
        opacity: 0.8;
        margin-bottom: 1rem;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .flashcard-text {
        font-size: 1.3rem;
        line-height: 1.6;
    }
    .flashcard-hint {
        margin-top: 2rem;
        font-size: 0.85rem;
        opacity: 0.7;
    }
    .progress-bar {
        width: 100%;
        height: 8px;
        background: #e0e0e0;
        border-radius: 10px;
        overflow: hidden;
        margin: 1rem 0;
    }
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        transition: width 0.3s;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'generated_content' not in st.session_state:
    st.session_state.generated_content = None
if 'content_type' not in st.session_state:
    st.session_state.content_type = None
if 'flashcards_list' not in st.session_state:
    st.session_state.flashcards_list = []
if 'current_card_index' not in st.session_state:
    st.session_state.current_card_index = 0
if 'show_answer' not in st.session_state:
    st.session_state.show_answer = False
if 'studied_cards' not in st.session_state:
    st.session_state.studied_cards = set()

# Load environment variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# Initialize client
try:
    client = genai.Client()
except Exception as e:
    st.error(f"Failed to initialize API client: {str(e)}")
    st.stop()


def parse_flashcards_to_list(raw_text):
    """Parse flashcard text into a list of dictionaries"""
    flashcards_list = []
    
    # Split by "Flashcard" markers with numbers
    cards = re.split(r'(?=Flashcard\s+\d+)', raw_text, flags=re.IGNORECASE)
    
    for card in cards:
        if not card.strip() or 'Flashcard' not in card:
            continue
        
        # More precise extraction: look for Q: and A: patterns
        q_match = re.search(r'\bQ\s*:\s*(.+?)(?=\s*\bA\s*:)', card, re.DOTALL | re.IGNORECASE)
        a_match = re.search(r'\bA\s*:\s*(.+?)(?=\n\s*---|\n\s*Flashcard|\Z)', card, re.DOTALL | re.IGNORECASE)
        
        if q_match and a_match:
            question = q_match.group(1).strip()
            answer = a_match.group(1).strip()
            
            # Clean up any markdown or extra formatting
            question = re.sub(r'\*\*', '', question)
            answer = re.sub(r'\*\*', '', answer)
            
            flashcards_list.append({"question": question, "answer": answer})
    
    return flashcards_list





def format_flashcards(raw_text):
    """Post-process flashcards for consistent formatting"""
    cards = re.split(r'\n\s*\n(?=Flashcard|\d+\.)', raw_text)
    formatted_output = []
    
    for card in cards:
        if not card.strip():
            continue
            
        num_match = re.search(r'(?:Flashcard\s*)?(\d+)', card)
        if not num_match:
            continue
        card_num = num_match.group(1)
        
        q_match = re.search(r'Q\s*:?\s*(.+?)(?=A\s*:)', card, re.DOTALL | re.IGNORECASE)
        a_pattern = r'A\s*:?\s*(.+?)$'
        a_match = re.search(a_pattern, card, re.DOTALL | re.IGNORECASE)
        
        if q_match and a_match:
            question = q_match.group(1).strip()
            answer = a_match.group(1).strip()
            
            formatted_card = f"**Flashcard {card_num}**\n\n"
            formatted_card += f"**Q:** {question}\n\n"
            formatted_card += f"**A:** {answer}\n\n"
            formatted_card += "---\n"
            
            formatted_output.append(formatted_card)
    
    return "\n".join(formatted_output)


# Header
st.markdown('<p class="main-header">GenAI Study Helper</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Transform your notes into interactive study materials with AI</p>', unsafe_allow_html=True)

# Main layout with columns
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### Input Your Study Material")
    
    uploaded_file = st.file_uploader(
        "Upload a PDF document",
        type="pdf",
        help="Upload a PDF file containing your study notes"
    )
    
    pdf_text = ""
    if uploaded_file is not None:
        try:
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            page_count = len(pdf_reader.pages)
            
            with st.spinner(f"Extracting text from {page_count} pages..."):
                for page in pdf_reader.pages:
                    pdf_text += page.extract_text() or ""
            
            st.markdown(f'<div class="success-box">Successfully extracted text from {page_count} pages ({len(pdf_text)} characters)</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error reading PDF: {str(e)}")
    
    notes = st.text_area(
        "Or paste your notes here:",
        value=pdf_text,
        height=300,
        placeholder="Paste your study notes, lecture content, or any text you want to convert into study materials...",
        help="You can either upload a PDF or paste text directly"
    )
    
    if notes:
        st.caption(f"Character count: {len(notes)}")

with col2:
    st.markdown("### Generate Study Materials")
    
    st.markdown('<div class="info-box"><strong>Tip:</strong> The more detailed your notes, the better the generated content will be!</div>', unsafe_allow_html=True)
    
    num_questions = st.slider(
        "Number of Questions",
        min_value=5,
        max_value=50,
        value=30,
        step=5,
        help="Select how many quiz questions to generate"
    )
    
    num_flashcards = st.slider(
        "Number of Flashcards",
        min_value=5,
        max_value=50,
        value=20,
        step=5,
        help="Select how many flashcards to generate"
    )
    
    st.markdown("---")
    
    if st.button("Generate Quiz Questions", use_container_width=True):
        if notes.strip() == "":
            st.warning("Please paste notes or upload a PDF first.")
        else:
            with st.spinner("Generating quiz questions..."):
                try:
                    prompt = f"""Generate {num_questions} multiple-choice quiz questions based on the provided notes.

For each question:
1. Number the question (1., 2., 3., etc.)
2. Write the question text
3. Provide 4 answer options labeled A), B), C), D)
4. Indicate the correct answer

Notes:
{notes}"""
                    response = client.models.generate_content(
                        model="gemini-2.0-flash-exp",
                        contents=prompt
                    )
                    
                    st.session_state.generated_content = response.text
                    st.session_state.content_type = "questions"
                    st.success("Quiz questions generated successfully!")
                except Exception as e:
                    st.error(f"Error generating questions: {str(e)}")
    
    if st.button("Generate Flashcards", use_container_width=True):
        if notes.strip() == "":
            st.warning("Please paste notes or upload a PDF first.")
        else:
            with st.spinner("Creating flashcards..."):
                try:
                    prompt = f"""Generate {num_flashcards} flashcards based on the provided notes.

For each flashcard:
1. Number it (Flashcard 1, Flashcard 2, etc.)
2. Write "Q:" followed by the question
3. Write "A:" followed by the answer

Notes:
{notes}"""
                    response = client.models.generate_content(
                        model="gemini-2.0-flash-exp",
                        contents=prompt
                    )
                    
                    formatted_content = format_flashcards(response.text)
                    st.session_state.generated_content = formatted_content
                    st.session_state.content_type = "flashcards"
                    
                    # Parse flashcards into interactive list
                    st.session_state.flashcards_list = parse_flashcards_to_list(response.text)
                    st.session_state.current_card_index = 0
                    st.session_state.show_answer = False
                    st.session_state.studied_cards = set()
                    
                    st.success("Flashcards generated successfully!")
                except Exception as e:
                    st.error(f"Error generating flashcards: {str(e)}")

# Display generated content
if st.session_state.generated_content:
    st.markdown("---")
    
    if st.session_state.content_type == "questions":
        st.markdown("### Generated Quiz Questions")
        with st.expander("View Generated Content", expanded=True):
            st.markdown(st.session_state.generated_content)
        
        st.download_button(
            label="Download as Text File",
            data=st.session_state.generated_content,
            file_name=f"study_material_{st.session_state.content_type}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    elif st.session_state.content_type == "flashcards" and st.session_state.flashcards_list:
        st.markdown("### Interactive Flashcards")
        
        # Progress tracking
        total_cards = len(st.session_state.flashcards_list)
        studied_count = len(st.session_state.studied_cards)
        progress_pct = (studied_count / total_cards * 100) if total_cards > 0 else 0
        
        st.markdown(f"**Progress:** {studied_count}/{total_cards} cards studied ({progress_pct:.0f}%)")
        st.markdown(f'<div class="progress-bar"><div class="progress-fill" style="width: {progress_pct}%"></div></div>', unsafe_allow_html=True)
        
        # Navigation controls
        nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([1, 1, 1, 1])
        
        with nav_col1:
            if st.button("Previous", use_container_width=True):
                if st.session_state.current_card_index > 0:
                    st.session_state.current_card_index -= 1
                    st.session_state.show_answer = False
                    st.rerun()
        
        with nav_col2:
            if st.button("Flip Card", use_container_width=True):
                st.session_state.show_answer = not st.session_state.show_answer
                if st.session_state.show_answer:
                    st.session_state.studied_cards.add(st.session_state.current_card_index)
                st.rerun()
        
        with nav_col3:
            if st.button("Next", use_container_width=True):
                if st.session_state.current_card_index < len(st.session_state.flashcards_list) - 1:
                    st.session_state.current_card_index += 1
                    st.session_state.show_answer = False
                    st.rerun()
        
        with nav_col4:
            if st.button("Shuffle", use_container_width=True):
                import random
                random.shuffle(st.session_state.flashcards_list)
                st.session_state.current_card_index = 0
                st.session_state.show_answer = False
                st.rerun()
        
        # Display current flashcard
        current_card = st.session_state.flashcards_list[st.session_state.current_card_index]
        card_number = st.session_state.current_card_index + 1
        
        if not st.session_state.show_answer:
            # Show question
            st.markdown(f"""
            <div class="flashcard-container">
                <div class="flashcard flashcard-question">
                    <div class="flashcard-label">Question {card_number} of {total_cards}</div>
                    <div class="flashcard-text">{current_card['question']}</div>
                    <div class="flashcard-hint">Click "Flip Card" to see the answer</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Show answer
            st.markdown(f"""
            <div class="flashcard-container">
                <div class="flashcard flashcard-answer">
                    <div class="flashcard-label">Answer {card_number} of {total_cards}</div>
                    <div class="flashcard-text">{current_card['answer']}</div>
                    <div class="flashcard-hint">Click "Flip Card" to see the question</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Download option
        st.markdown("---")
        with st.expander("View All Flashcards (Text Format)"):
            st.markdown(st.session_state.generated_content)
        
        st.download_button(
            label="Download Flashcards as Text File",
            data=st.session_state.generated_content,
            file_name="study_flashcards.txt",
            mime="text/plain",
            use_container_width=True
        )

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #666; font-size: 0.9rem;'>Made with Streamlit and Google Gemini AI</p>",
    unsafe_allow_html=True
)