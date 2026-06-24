# app.py - Full Version with Syllabus Upload + Logging Dashboard
import streamlit as st
from agent import run_chatbox
import json
import os
from datetime import datetime

st.set_page_config(page_title="Chatbox - Course Advisor", page_icon="📚")
st.title("📚 Chatbox - Your Course Advisor")
st.caption("Ask me anything about the syllabus, deadlines, policies, or course topics!")

# Sidebar
with st.sidebar:
    st.header("Faculty Tools")
    
    # Syllabus Upload
    uploaded_file = st.file_uploader("Upload Syllabus (JSON)", type=["json"])
    if uploaded_file is not None:
        try:
            syllabus = json.load(uploaded_file)
            st.session_state.syllabus = syllabus
            st.success("Syllabus uploaded successfully!")
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
                for log in reversed(logs[-30:]):  # Show last 30
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
            response = run_chatbox(prompt)
            st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})