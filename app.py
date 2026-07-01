STRUCTURING_PROMPT = """
You are an expert academic assistant specialized in analyzing course syllabi.

Your task is to carefully read the syllabus provided below and extract key information into a clean, structured JSON format.

Follow these strict rules:
- Only extract information that is **explicitly stated** in the syllabus.
- If a piece of information is not found, use `null` or an empty string/object/array.
- Do **not** make up or infer information.
- Return **only valid JSON**. Do not add any explanation before or after the JSON.

Use the following JSON structure:

{
  "course_info": {
    "title": "",
    "code": "",
    "semester": "",
    "modality": ""
  },
  "instructor": {
    "name": "",
    "email": "",
    "office_hours": ""
  },
  "grading_breakdown": {},
  "late_work_policy": "",
  "academic_integrity_policy": "",
  "generative_ai_policy": "",
  "netiquette_policy": "",
  "attendance_policy": "",
  "required_materials": [],
  "important_dates": {},
  "key_policies": {},
  "additional_notes": ""
}

Now analyze the syllabus below and return the filled JSON:
"""

# app.py - Final Version with LLM Structuring
import streamlit as st
from agent import run_chatbox
import json
from datetime import datetime
from file_parser import extract_text_from_pdf, extract_text_from_docx
from langchain_xai import ChatXAI
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Chatbox - Course Advisor", page_icon="📚")
st.title("📚 Chatbox - Your Course Advisor")
st.caption("Ask me anything about the syllabus, deadlines, policies, or course topics!")

# Initialize LLM for structuring
structuring_llm = ChatXAI(model="grok-4", temperature=0.3, max_tokens=2000)

# Sidebar
with st.sidebar:
    st.header("Faculty Tools")
    
    # PDF / DOCX Uploader with Structuring
    st.subheader("Upload Syllabus (PDF or DOCX)")
    uploaded_file = st.file_uploader(
        "Upload your syllabus file", 
        type=["pdf", "docx"],
        help="Upload PDF or Word document. It will be automatically structured."
    )
    
    if uploaded_file is not None:
        file_type = uploaded_file.name.split(".")[-1].lower()
        
        with st.spinner("Processing syllabus..."):
            if file_type == "pdf":
                raw_text = extract_text_from_pdf(uploaded_file)
            elif file_type == "docx":
                raw_text = extract_text_from_docx(uploaded_file)
            else:
                raw_text = ""
        
        if raw_text:
            st.session_state.raw_syllabus_text = raw_text
            
            # Call LLM to structure the syllabus
            with st.spinner("Structuring syllabus content..."):
                try:
                    messages = [
                        {"role": "system", "content": STRUCTURING_PROMPT},
                        {"role": "user", "content": raw_text[:18000]}  # Limit input size
                    ]
                    response = structuring_llm.invoke(messages)
                    structured_json = json.loads(response.content)
                    st.session_state.structured_syllabus = structured_json
                    st.success("✅ Syllabus uploaded and structured successfully!")
                except Exception as e:
                    st.warning("Could not fully structure the syllabus. Using raw text instead.")
                    st.session_state.structured_syllabus = None
            
            with st.expander("📄 View Extracted Text", expanded=False):
                st.text_area("Extracted Content", raw_text, height=400, disabled=True)
                st.caption(f"Total characters: {len(raw_text):,}")
        else:
            st.error("Could not extract text from the file.")
    
    # JSON Uploader (Backup)
    st.divider()
    st.subheader("Or upload as JSON")
    json_file = st.file_uploader("Upload Syllabus (JSON)", type=["json"], key="json_uploader")
    if json_file is not None:
        try:
            syllabus = json.load(json_file)
            st.session_state.syllabus = syllabus
            st.success("JSON Syllabus uploaded!")
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
            raw_text = st.session_state.get('raw_syllabus_text', '')
            structured_data = st.session_state.get('structured_syllabus', None)
            response = run_chatbox(prompt, raw_text, structured_data)
            st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})STRUCTURING_PROMPT = """
You are an expert academic assistant specialized in analyzing course syllabi.

Your task is to carefully read the syllabus provided below and extract key information into a clean, structured JSON format.

Follow these strict rules:
- Only extract information that is **explicitly stated** in the syllabus.
- If a piece of information is not found, use `null` or an empty string/object/array.
- Do **not** make up or infer information.
- Return **only valid JSON**. Do not add any explanation before or after the JSON.

Use the following JSON structure:

{
  "course_info": {
    "title": "",
    "code": "",
    "semester": "",
    "modality": ""
  },
  "instructor": {
    "name": "",
    "email": "",
    "office_hours": ""
  },
  "grading_breakdown": {},
  "late_work_policy": "",
  "academic_integrity_policy": "",
  "generative_ai_policy": "",
  "netiquette_policy": "",
  "attendance_policy": "",
  "required_materials": [],
  "important_dates": {},
  "key_policies": {},
  "additional_notes": ""
}

Now analyze the syllabus below and return the filled JSON:
"""

# app.py - Final Version with LLM Structuring
import streamlit as st
from agent import run_chatbox
import json
from datetime import datetime
from file_parser import extract_text_from_pdf, extract_text_from_docx
from langchain_xai import ChatXAI
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Chatbox - Course Advisor", page_icon="📚")
st.title("📚 Chatbox - Your Course Advisor")
st.caption("Ask me anything about the syllabus, deadlines, policies, or course topics!")

# Initialize LLM for structuring
structuring_llm = ChatXAI(model="grok-4", temperature=0.3, max_tokens=2000)

# Sidebar
with st.sidebar:
    st.header("Faculty Tools")
    
    # PDF / DOCX Uploader with Structuring
    st.subheader("Upload Syllabus (PDF or DOCX)")
    uploaded_file = st.file_uploader(
        "Upload your syllabus file", 
        type=["pdf", "docx"],
        help="Upload PDF or Word document. It will be automatically structured."
    )
    
    # Helpful note about PDF vs DOCX quality
    st.caption("💡 **Tip:** For best accuracy on tables and due dates (such as the Course Schedule), uploading a **Word (.docx)** version of your syllabus usually gives better results than PDF.")
    
    if uploaded_file is not None:
        file_type = uploaded_file.name.split(".")[-1].lower()
        
        with st.spinner("Processing syllabus..."):
            if file_type == "pdf":
                raw_text = extract_text_from_pdf(uploaded_file)
            elif file_type == "docx":
                raw_text = extract_text_from_docx(uploaded_file)
            else:
                raw_text = ""
        
        if raw_text:
            st.session_state.raw_syllabus_text = raw_text
            
            # Call LLM to structure the syllabus
            with st.spinner("Structuring syllabus content..."):
                try:
                    messages = [
                        {"role": "system", "content": STRUCTURING_PROMPT},
                        {"role": "user", "content": raw_text[:18000]}  # Limit input size
                    ]
                    response = structuring_llm.invoke(messages)
                    structured_json = json.loads(response.content)
                    st.session_state.structured_syllabus = structured_json
                    st.success("✅ Syllabus uploaded and structured successfully!")
                except Exception as e:
                    st.warning("Could not fully structure the syllabus. Using raw text instead.")
                    st.session_state.structured_syllabus = None
            
            with st.expander("📄 View Extracted Text", expanded=False):
                st.text_area("Extracted Content", raw_text, height=400, disabled=True)
                st.caption(f"Total characters: {len(raw_text):,}")
        else:
            st.error("Could not extract text from the file.")
    
    # JSON Uploader (Backup)
    st.divider()
    st.subheader("Or upload as JSON")
    json_file = st.file_uploader("Upload Syllabus (JSON)", type=["json"], key="json_uploader")
    if json_file is not None:
        try:
            syllabus = json.load(json_file)
            st.session_state.syllabus = syllabus
            st.success("JSON Syllabus uploaded!")
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
            raw_text = st.session_state.get('raw_syllabus_text', '')
            structured_data = st.session_state.get('structured_syllabus', None)
            response = run_chatbox(prompt, raw_text, structured_data)
            st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})