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

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

app = FastAPI(title="IntelliJect API", description="Smart PYQ-PDF Enhancer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    except Exception:
        return ""

@app.get("/", response_model=Dict[str, str])
async def root():
    return {"message": "IntelliJect API is running"}

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
        
        # Store temp file path in session or return it for processing
        return PDFResponse(
            success=True, 
            message=f"PDF '{file.filename}' uploaded successfully",
            chunks_count=len(text_chunks)
        )
    
    except Exception as e:
        os.unlink(tmp_pdf_path)  # Clean up temp file
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {e}")

@app.post("/process-pdf", response_model=ProcessedPDFResponse)
async def process_pdf(file: UploadFile = File(...), subject: str = Form(...)):
    """Process PDF and return all chunk data with highlighted images - same logic as in Streamlit"""
    print(f"Processing PDF: {file.filename} for subject: {subject}")  # Debug log
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_pdf_path = tmp_file.name
    
    try:
        print(f"Temp file created: {tmp_pdf_path}")  # Debug log
        # Extract text chunks - same logic as in Streamlit
        print("Extracting text from PDF...")  # Debug log
        text_chunks = extract_text_from_pdf(tmp_pdf_path)
        
        if not text_chunks:
            os.unlink(tmp_pdf_path)
            raise HTTPException(status_code=400, detail="Could not extract content from the PDF")
        
        print(f"Extracted {len(text_chunks)} chunks")  # Debug log
        
        pdf_doc = fitz.open(tmp_pdf_path)
        num_pages = pdf_doc.page_count
        print(f"PDF has {num_pages} pages")  # Debug log
        
        chunk_data_list = []
        
        # Process each chunk - same logic as in Streamlit main loop
        for i, chunk in enumerate(text_chunks):
            print(f"Processing chunk {i+1}/{len(text_chunks)}")  # Debug log
            answers_to_highlight = []
            questions_data = []
            
            # Infer subtopic - same logic as in Streamlit
            try:
                print(f"Inferring subtopic for chunk {i+1}...")  # Debug log
                subtopic = infer_subtopic(chunk)
                print(f"Subtopic: {subtopic}")  # Debug log
            except Exception as e:
                print(f"Error inferring subtopic: {e}")  # Debug log
                subtopic = "General"
            
            try:
                print(f"Getting relevant PYQs for chunk {i+1}...")  # Debug log
                with SessionLocal() as session:
                    related_qs = get_relevant_pyqs(session, chunk, subject)
                print(f"Found {len(related_qs)} related questions")  # Debug log
            except Exception as e:
                print(f"Error getting PYQs: {e}")  # Debug log
                related_qs = []
            
            # Process questions and extract answers - same logic as in Streamlit
            for j, q in enumerate(related_qs):
                print(f"Processing question {j+1}/{len(related_qs)} for chunk {i+1}")  # Debug log
                try:
                    answer_text = extract_answer_from_chunk(chunk, q.page_content)
                    if answer_text:
                        for sent in sent_tokenize(answer_text):
                            sent_clean = sent.strip()
                            if sent_clean:
                                answers_to_highlight.append(sent_clean)
                    
                    question_data = {
                        "question": q.page_content,
                        "sub_topic": q.metadata.get('sub_topic', 'N/A'),
                        "marks": q.metadata.get('marks', 'N/A'),
                        "year": q.metadata.get('year', ''),
                        "answer": answer_text if answer_text else '(No direct answer found)'
                    }
                    questions_data.append(question_data)
                except Exception as e:
                    print(f"Error processing question {j+1}: {e}")  # Debug log
                    continue
            
            # Generate highlighted image - same logic as in Streamlit
            highlighted_image_b64 = ""
            try:
                print(f"Generating highlighted image for chunk {i+1}...")  # Debug log
                if i < num_pages:
                    page = pdf_doc[i]
                    
                    # Highlight all answer fragments on this page - same logic as in Streamlit
                    for answer_frag in answers_to_highlight:
                        if answer_frag:
                            rects = page.search_for(answer_frag)
                            for r in rects:
                                annot = page.add_highlight_annot(r)
                                annot.set_colors(stroke=(1, 1, 0))  # Yellow
                                annot.update()
                    
                    pix = page.get_pixmap(dpi=150)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    img_bytes = BytesIO()
                    img.save(img_bytes, format="PNG")
                    img_bytes.seek(0)
                    
                    # Convert to base64 for API response
                    highlighted_image_b64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
                    print(f"Generated highlighted image for chunk {i+1}")  # Debug log
            except Exception as e:
                print(f"Error generating highlighted image for chunk {i+1}: {e}")  # Debug log
                pass  # Skip highlighting if error occurs
            
            chunk_data_list.append(ChunkData(
                chunk_index=i,
                subtopic=subtopic,
                questions=questions_data,
                highlighted_image=highlighted_image_b64,
                answers_highlighted=answers_to_highlight
            ))
        
        # IMPORTANT: Close the PDF document before deleting temp file (Windows fix)
        pdf_doc.close()
        
        # Clean up temp file
        print("Cleaning up temporary file...")  # Debug log
        try:
            os.unlink(tmp_pdf_path)
        except PermissionError:
            # On Windows, sometimes need a small delay
            import time
            time.sleep(0.1)
            os.unlink(tmp_pdf_path)
        
        print(f"Successfully processed {len(text_chunks)} chunks")  # Debug log
        return ProcessedPDFResponse(
            success=True,
            message="PDF processed successfully",
            total_chunks=len(text_chunks),
            chunk_data=chunk_data_list
        )
    
    except Exception as e:
        print(f"Error in process_pdf: {str(e)}")  # Debug log
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")  # Debug log
        
        # Close PDF document if it exists before cleanup
        try:
            if 'pdf_doc' in locals():
                pdf_doc.close()
        except:
            pass
            
        # Clean up temp file with better error handling
        try:
            if os.path.exists(tmp_pdf_path):
                import time
                time.sleep(0.1)  # Small delay for Windows
                os.unlink(tmp_pdf_path)
        except PermissionError:
            print(f"Warning: Could not delete temp file {tmp_pdf_path} - file may be in use")
            pass  # Don't fail the entire request just because we can't delete temp file
        except Exception as cleanup_error:
            print(f"Warning: Error during cleanup: {cleanup_error}")
            pass
            
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

if __name__ == "_main_":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)