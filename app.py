# app.py - Simplified & Clean Version (Best Performance)
import streamlit as st
from agent import run_chatbox
import json
from datetime import datetime
from file_parser import extract_text_from_pdf, extract_text_from_docx

st.set_page_config(page_title="Chatbox - Course Advisor", page_icon="📚")
st.title("📚 Chatbox - Your Course Advisor")
st.caption("Ask me anything about the syllabus, deadlines, policies, or course topics!")

# Sidebar
with st.sidebar:
    st.header("Faculty Tools")
    
    # PDF / DOCX Uploader
    st.subheader("Upload Syllabus (PDF or DOCX)")
    uploaded_file = st.file_uploader(
        "Upload your syllabus file", 
        type=["pdf", "docx"],
        help="Upload PDF or Word document. Text will be extracted automatically."
    )
    
    if uploaded_file is not None:
        file_type = uploaded_file.name.split(".")[-1].lower()
        
        with st.spinner("Extracting text from document..."):
            if file_type == "pdf":
                extracted_text = extract_text_from_pdf(uploaded_file)
            elif file_type == "docx":
                extracted_text = extract_text_from_docx(uploaded_file)
            else:
                extracted_text = ""
        
        if extracted_text:
            st.session_state.extracted_syllabus_text = extracted_text
            st.success("✅ Syllabus uploaded successfully!")
            
            with st.expander("📄 View Extracted Text", expanded=False):
                st.text_area(
                    label="Extracted Content",
                    value=extracted_text,
                    height=450,
                    disabled=True
                )
                st.caption(f"Total characters extracted: {len(extracted_text):,}")
        else:
            st.error("Could not extract text from the file.")
    
    # JSON Uploader (Backup Option)
    st.divider()
    st.subheader("Or upload as JSON")
    json_file = st.file_uploader("Upload Syllabus (JSON)", type=["json"], key="json_uploader")
    if json_file is not None:
        try:
            syllabus = json.load(json_file)
            st.session_state.syllabus = syllabus
            st.success("JSON Syllabus uploaded!")
            st.json(syllabus, expanded=False)
        except Exception as e:
            st.error(f"Invalid JSON file: {str(e)}")

    # Logging Dashboard
    st.header("Interaction Logs")
    if st.button("View All Logs"):
        try:
            with open("chatbox_logs.jsonl", "r") as f:
                logs = [json.loads(line) for line in f.readlines()]
            
            if logs:
                st.subheader(f"Total Interactions: {len(logs)}")
                for log in reversed(logs[-30:]):
                    st.write(f"**{log['timestamp']}** | Session: {log['session_id'][:8]}")
                    st.write(f"**Query:** {log['user_query']}")
                    if log.get('tool_used'):
                        st.write(f"**Tool Used:** {log['tool_used']}")
                    response_text = log.get('response_preview') or "No response saved"
                    st.write(f"**Response:** {response_text}")
                    st.divider()
            else:
                st.info("No logs yet.")
        except FileNotFoundError:
            st.info("No logs file yet. Start chatting to generate logs.")
        except Exception as e:
            st.error(f"Error reading logs: {str(e)}")

    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# Main Chat Interface
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Type your question here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            extracted_text = st.session_state.get('extracted_syllabus_text', '')
            response = run_chatbox(prompt, extracted_text)
            st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})