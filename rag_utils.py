# rag_utils.py - Simple RAG for Syllabus
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import numpy as np
import streamlit as st

# Load embedding model (runs locally, free)
@st.cache_resource
def get_embedding_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

def chunk_syllabus(text: str, chunk_size: int = 800, chunk_overlap: int = 100):
    """Split syllabus into overlapping chunks"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    return splitter.split_text(text)

def get_relevant_chunks(query: str, chunks: list, top_k: int = 5):
    """Find most relevant chunks using embeddings"""
    if not chunks:
        return []
    
    model = get_embedding_model()
    
    # Embed query and chunks
    query_embedding = model.encode(query)
    chunk_embeddings = model.encode(chunks)
    
    # Compute cosine similarity
    similarities = np.dot(chunk_embeddings, query_embedding) / (
        np.linalg.norm(chunk_embeddings, axis=1) * np.linalg.norm(query_embedding)
    )
    
    # Get top k most similar chunks
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    relevant_chunks = [chunks[i] for i in top_indices]
    
    return relevant_chunks