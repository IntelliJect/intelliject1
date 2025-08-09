# utils.py

import fitz  # PyMuPDF
import re

# 📥 Extract text from PDF and clean
# utils.py
import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_path: str):
    """
    Extracts text from each page of the PDF and returns
    a list of text chunks (one chunk per page).
    """
    doc = fitz.open(pdf_path)
    pages_text = []
    for page in doc:
        text = page.get_text("text")  # Extract page text as plain text
        pages_text.append(text)
    return pages_text


# ✂️ Simple chunking logic (split by size)
def chunk_text(text: str, chunk_size: int = 500) -> list:
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

# ✨ HTML highlighting of chunks
def highlight_chunks(text: str) -> str:
    return f"<div style='background-color:#f9f9f9;padding:10px;border-left:4px solid #4CAF50;margin-bottom:10px'>{text}</div>"
