import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import base64

# Configure the API base URL - try different options if localhost doesn't work
API_BASE_URL = "http://127.0.0.1:8000"  # Changed to match error message
# Alternative options to try:
# API_BASE_URL = "http://localhost:8000"
# API_BASE_URL = "http://0.0.0.0:8000"

st.set_page_config(page_title="IntelliJect", layout="wide")
st.title("🧠 IntelliJect: Smart PYQ-PDF Enhancer")

# Test API connection
@st.cache_data(ttl=60)  # Cache for 1 minute
def test_api_connection():
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        return response.status_code == 200
    except:
        return False

# Show connection status
if not test_api_connection():
    st.error(f"⚠ Cannot connect to API server at {API_BASE_URL}. Please make sure the FastAPI server is running.")
    st.info("To start the API server, run: python main.py in a separate terminal")
    st.stop()
else:
    st.success("✅ Connected to API server")

st.markdown("""
    <style>
    .question-card {
        background-color: #283250;
        color: #d6f5e3 !important;
        border-radius: 6px;
        padding: 10px 12px;
        margin: 10px 0 6px 0;
        font-size: 15px;
    }
    .highlight-answer {
        display: inline-block;
        background: #ffe44d;
        color: #232323 !important;
        border-radius: 5px;
        padding: 2px 6px;
        margin: 6px 0 2px 0;
        font-weight: 600;
        font-family: 'Georgia', serif;
        font-size: 15px;
    }
    </style>
""", unsafe_allow_html=True)

def get_pdf_history():
    """Fetch PDF history from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/history")
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "history": []}
    except Exception as e:
        st.error(f"Failed to fetch history: {e}")
        return {"success": False, "history": []}

def process_pdf_with_api(uploaded_file, subject):
    """Process PDF using the API"""
    try:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
        data = {"subject": subject}
        
        # Add timeout and better error handling
        response = requests.post(
            f"{API_BASE_URL}/process-pdf", 
            files=files, 
            data=data, 
            timeout=300  # 5 minutes timeout
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            try:
                error_detail = response.json().get("detail", "Unknown error")
            except:
                error_detail = f"HTTP {response.status_code}: {response.text}"
            st.error(f"API Error: {error_detail}")
            return None
    except requests.exceptions.Timeout:
        st.error("Request timed out. The PDF might be too large or complex.")
        return None
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to API server at {API_BASE_URL}. Make sure the FastAPI server is running.")
        return None
    except Exception as e:
        st.error(f"Failed to process PDF: {e}")
        return None

# Sidebar - PDF History (same UI as before)
with st.sidebar:
    st.header("📜 PDF Upload History")
    history_data = get_pdf_history()
    
    if not history_data["success"] or not history_data["history"]:
        st.info("No history found.")
    else:
        for item in history_data["history"]:
            st.markdown(
                f"- *{item['filename']}* ({item['subject']}) - "
                f"{item['timestamp']}"
            )

# Main UI (same layout as before)
col1, col2 = st.columns(2)
with col1:
    uploaded_file = st.file_uploader("📑 Upload your notes PDF", type=["pdf"])
with col2:
    subject = st.selectbox("📚 Select Subject", ["Cyber Security", "Environmental Sciences"])

if uploaded_file and subject:
    st.subheader("📑 Processing PDF...")
    
    # Show progress and status
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Process PDF using API
    try:
        status_text.text("🔄 Connecting to API server...")
        progress_bar.progress(10)
        
        status_text.text("📤 Uploading PDF to server...")
        progress_bar.progress(30)
        
        status_text.text("🔍 Extracting and analyzing content...")
        progress_bar.progress(50)
        
        result = process_pdf_with_api(uploaded_file, subject)
        
        if result and result["success"]:
            progress_bar.progress(100)
            status_text.text("✅ Processing complete!")
            st.success(f"✅ Successfully processed {result['total_chunks']} chunks.")
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            pdf_doc = None
            num_pages = result['total_chunks']
            
            if result['total_chunks'] != num_pages:
                st.warning(f"⚠ Number of text chunks ({result['total_chunks']}) may not match number of PDF pages. Highlighting may be inaccurate.")
            
            # Display results for each chunk (same UI as before)
            for chunk_data in result["chunk_data"]:
                col_img, col_pyqs = st.columns([1.5, 1])
                
                with col_pyqs:
                    st.markdown(f"<span style='font-size:20px;font-weight:bold;'>🔎 Subtopic: {chunk_data['subtopic']}</span>", unsafe_allow_html=True)
                    
                    if chunk_data["questions"]:
                        for q_data in chunk_data["questions"]:
                            st.markdown(
                                f"<div class='question-card'>"
                                f"❓ <b>Q:</b> {q_data['question']}<br>"
                                f"<span style='font-size:14px;opacity:0.8;'>"
                                f"🧩 Topic: {q_data['sub_topic']} | "
                                f"📝 Marks: {q_data['marks']} | "
                                f"📅 {q_data['year']}"
                                f"</span><br>"
                                f"<span class='highlight-answer'><b>📌 Answer:</b> {q_data['answer']}</span>"
                                f"</div>", unsafe_allow_html=True
                            )
                            st.markdown("---", unsafe_allow_html=True)
                    else:
                        st.info("❗ No relevant PYQs found for this chunk.")
                
                with col_img:
                    try:
                        if chunk_data["highlighted_image"]:
                            # Decode base64 image
                            img_data = base64.b64decode(chunk_data["highlighted_image"])
                            img = Image.open(BytesIO(img_data))
                            st.image(img, caption=f"PDF Page {chunk_data['chunk_index']+1} (Highlighted Answers)", use_container_width=True)
                        else:
                            st.warning(f"Could not render PDF page {chunk_data['chunk_index']+1} image")
                    except Exception as e:
                        st.warning(f"Could not display image for chunk {chunk_data['chunk_index']+1}: {e}")
        else:
            progress_bar.empty()
            status_text.empty()
            st.error("❌ Failed to process PDF.")
    
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ Unexpected error: {e}")