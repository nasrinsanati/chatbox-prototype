from pypdf import PdfReader
from docx import Document
import streamlit as st

def extract_text_from_pdf(uploaded_file):
    """Extract text from PDF"""
    try:
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        st.error(f"PDF Error: {e}")
        return ""

def extract_text_from_docx(uploaded_file):
    """Extract text from DOCX"""
    try:
        doc = Document(uploaded_file)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text.strip()
    except Exception as e:
        st.error(f"DOCX Error: {e}")
        return ""