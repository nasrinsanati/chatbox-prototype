import pdfplumber
from pypdf import PdfReader
from docx import Document
import streamlit as st

def extract_text_from_pdf(uploaded_file):
    """Improved PDF extraction using pdfplumber (better quality)"""
    try:
        text = ""
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
        return clean_text(text)
    except Exception as e:
        st.warning(f"pdfplumber failed, trying pypdf fallback: {e}")
        # Fallback to pypdf
        try:
            reader = PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return clean_text(text)
        except Exception as e2:
            st.error(f"Both PDF extractors failed: {e2}")
            return ""

def clean_text(text):
    """Clean up extracted text"""
    import re
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()

def extract_text_from_docx(uploaded_file):
    """Extract text from DOCX"""
    try:
        doc = Document(uploaded_file)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return clean_text(text)
    except Exception as e:
        st.error(f"DOCX Error: {e}")
        return ""