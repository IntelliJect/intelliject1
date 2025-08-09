import os
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import tempfile
import datetime
from sqlalchemy.orm import sessionmaker
from database import engine, SessionLocal
from models import PDFHistory
from utils import extract_text_from_pdf
from rag_pipeline import infer_subtopic, get_relevant_pyqs
from nltk.tokenize import sent_tokenize
try:
    from langchain_community.chat_models import ChatOpenAI
except ImportError:
    from langchain.chat_models import ChatOpenAI
import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO
import base64
from dotenv import load_dotenv

# Load environment variables once
load_dotenv()

# Environment-specific configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

# Set OpenAI API key
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Single FastAPI app initialization with environment-specific settings
app = FastAPI(
    title="IntelliJect API", 
    description="Smart PYQ-PDF Enhancer API",
    docs_url="/docs" if ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if ENVIRONMENT != "production" else None
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database session
SessionLocal = sessionmaker(bind=engine)

class PDFResponse(BaseModel):
    success: bool
    message: str
    chunks_count: int = 0

class ChunkData(BaseModel):
    chunk_index: int
    subtopic: str
    questions: List[Dict[str, Any]]
    highlighted_image: str  # base64 encoded image
    answers_highlighted: List[str]

class ProcessedPDFResponse(BaseModel):
    success: bool
    message: str
    total_chunks: int
    chunk_data: List[ChunkData]

class HistoryItem(BaseModel):
    filename: str
    subject: str
    timestamp: str

class HistoryResponse(BaseModel):
    success: bool
    history: List[HistoryItem]

def extract_answer_from_chunk(chunk: str, question: str) -> str:
    """Extract answer from chunk using OpenAI LLM - same logic as in Streamlit"""
    prompt = f"""
Given the following notes and a question, extract the exact sentence(s) from the notes that directly answer the question if possible. Only return the excerpt(s), not any explanation.

Notes:
\"\"\"{chunk}\"\"\"

Question:
\"\"\"{question}\"\"\"

Answer/excerpt:
"""
    try:
        llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
        answer = llm.predict(prompt).strip()
        return answer
    except Exception as e:
        print(f"Error extracting answer: {e}")
        return ""

@app.get("/", response_model=Dict[str, str])
async def root():
    return {"message": "IntelliJect API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint for Render"""
    return {"status": "healthy", "environment": ENVIRONMENT}

@app.get("/history", response_model=HistoryResponse)
async def get_pdf_history():
    """Get PDF upload history - same logic as sidebar in Streamlit"""
    try:
        with SessionLocal() as db:
            pdfs = db.query(PDFHistory).order_by(PDFHistory.timestamp.desc()).all()
            history_items = []
            for pdf in pdfs:
                history_items.append(HistoryItem(
                    filename=pdf.filename,
                    subject=pdf.subject,
                    timestamp=pdf.timestamp.strftime('%d %b, %Y %I:%M %p')
                ))
            return HistoryResponse(success=True, history=history_items)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not load PDF history: {e}")

@app.post("/upload-pdf", response_model=PDFResponse)
async def upload_pdf(file: UploadFile = File(...), subject: str = Form(...)):
    """Upload PDF and save to database - same logic as in Streamlit"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_pdf_path = tmp_file.name
    
    try:
        # Save to database - same logic as in Streamlit
        with SessionLocal() as db:
            history = PDFHistory(
                filename=file.filename,
                subject=subject,
                timestamp=datetime.datetime.utcnow()
            )
            db.add(history)
            db.commit()
        
        # Extract text chunks - same logic as in Streamlit
        text_chunks = extract_text_from_pdf(tmp_pdf_path)
        
        if not text_chunks:
            os.unlink(tmp_pdf_path)  # Clean up temp file
            raise HTTPException(status_code=400, detail="Could not extract content from the PDF")
        
        # Clean up temp file
        os.unlink(tmp_pdf_path)
        
        return PDFResponse(
            success=True, 
            message=f"PDF '{file.filename}' uploaded successfully",
            chunks_count=len(text_chunks)
        )
    
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(tmp_pdf_path):
            os.unlink(tmp_pdf_path)
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {e}")

@app.post("/process-pdf", response_model=ProcessedPDFResponse)
async def process_pdf(file: UploadFile = File(...), subject: str = Form(...)):
    """Process PDF and return all chunk
