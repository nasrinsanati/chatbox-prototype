# file_parser.py - Final Recommended Version
import pdfplumber
from pypdf import PdfReader
from docx import Document
import streamlit as st
import re

def clean_extracted_text(text: str) -> str:
    """
    Clean and normalize extracted text.
    Removes excessive whitespace and improves readability.
    """
    if not text:
        return ""
    
    # Collapse multiple newlines into max 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Collapse multiple spaces into single space
    text = re.sub(r' {2,}', ' ', text)
    
    # Remove very short artifact lines
    lines = [line.strip() for line in text.split('\n') if len(line.strip()) > 2]
    
    return '\n'.join(lines).strip()


def extract_text_from_pdf(uploaded_file):
    """
    Extract text from PDF with page markers and table handling.
    Uses pdfplumber as the primary extractor.
    """
    try:
        text = ""
        with pdfplumber.open(uploaded_file) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                # Add page marker
                text += f"\n\n[Page {i}]\n"
                
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                
                # Extract tables in a readable format
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        text += "\n[Table]\n"
                        for row in table:
                            clean_row = [str(cell).strip() if cell else "" for cell in row]
                            text += " | ".join(clean_row) + "\n"
                        text += "[/Table]\n"
        
        return clean_extracted_text(text)
    
    except Exception as e:
        st.warning(f"pdfplumber failed, falling back to pypdf: {e}")
        
        # Fallback to pypdf
        try:
            reader = PdfReader(uploaded_file)
            text = ""
            for i, page in enumerate(reader.pages, start=1):
                text += f"\n\n[Page {i}]\n"
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return clean_extracted_text(text)
        except Exception as e2:
            st.error(f"PDF extraction failed: {e2}")
            return ""


def extract_text_from_docx(uploaded_file):
    """Extract text from DOCX file"""
    try:
        doc = Document(uploaded_file)
        text = ""
        for para in doc.paragraphs:
            if para.text.strip():
                text += para.text + "\n"
        return clean_extracted_text(text)
    except Exception as e:
        st.error(f"DOCX extraction failed: {e}")
        return ""