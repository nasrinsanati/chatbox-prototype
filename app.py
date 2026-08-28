# app.py - Clean Stable Version
import streamlit as st
from agent import run_chatbox
import json
from datetime import datetime
from file_parser import extract_text_from_pdf, extract_text_from_docx


def save_survey(answers):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "session_id": st.session_state.get("thread_id", "default"),
        "event_type": "survey",
        "survey": answers,
    }
    with open("chatbox_logs.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")


st.set_page_config(page_title="Chatbox - Course Advisor", page_icon="📚")
st.title("📚 Chatbox - Your Course Advisor")
st.caption("Ask me anything about the syllabus, deadlines, policies, or course topics!")

# Sidebar
with st.sidebar:
    st.header("Faculty Tools")

    st.subheader("Upload Syllabus (PDF or DOCX)")
    uploaded_file = st.file_uploader(
        "Upload your syllabus file",
        type=["pdf", "docx"],
        help="Upload PDF or Word document. Text will be extracted automatically."
    )

    st.caption("Tip: For tables and due dates, a Word (.docx) syllabus usually works better than PDF.")

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
            st.success("Syllabus uploaded successfully!")

            with st.expander("View Extracted Text", expanded=False):
                st.text_area(
                    label="Extracted Content",
                    value=extracted_text,
                    height=800,
                    disabled=True
                )
                st.caption(f"Total characters extracted: {len(extracted_text):,}")
        else:
            st.error("Could not extract text from the file.")

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

    st.header("Interaction Logs")
    if st.button("View All Logs"):
        try:
            with open("chatbox_logs.jsonl", "r") as f:
                logs = [json.loads(line) for line in f.readlines()]

            if logs:
                st.subheader(f"Total Interactions: {len(logs)}")
                for log in reversed(logs[-30:]):
                    st.write(f"**{log.get('timestamp', '')}** | Session: {str(log.get('session_id', 'default'))[:8]}")
                    if log.get("event_type") == "survey":
                        survey = log.get("survey", {})
                        st.write("**Event:** Survey")
                        st.write(f"**Role:** {survey.get('role', '')}")
                        st.write(f"**Found info:** {survey.get('found_info', '')}")
                        st.write(f"**Saved time:** {survey.get('saved_time', '')}")
                        st.write(f"**Ease of use:** {survey.get('ease_of_use', '')}")
                        if survey.get("comment"):
                            st.write(f"**Comment:** {survey.get('comment')}")
                    else:
                        st.write(f"**Query:** {log.get('user_query', '')}")
                        if log.get("tool_used"):
                            st.write(f"**Tool Used:** {log['tool_used']}")
                        response_text = log.get("response_preview") or "No response saved"
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
        st.session_state.question_count = 0
        st.session_state.survey_completed = False
        st.rerun()

# Main Chat Interface
if "messages" not in st.session_state:
    st.session_state.messages = []

if "question_count" not in st.session_state:
    st.session_state.question_count = 0

if "survey_completed" not in st.session_state:
    st.session_state.survey_completed = False

if "thread_id" not in st.session_state:
    st.session_state.thread_id = "default"

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Type your question here...")

if prompt:
    if st.session_state.question_count >= 1 and not st.session_state.survey_completed:
        st.warning("Please submit the short survey before asking another question.")
    else:
        st.session_state.question_count += 1
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                extracted_text = st.session_state.get("extracted_syllabus_text", "")
                response = run_chatbox(prompt, extracted_text)
                st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

if st.session_state.question_count >= 1 and not st.session_state.survey_completed:
    st.warning("Please submit the short survey before asking another question.")

    with st.form("in_agent_survey"):
        role = st.radio(
            "1. Which best describes you?",
            ["Student", "Educator", "Instructional designer", "Other"],
            index=None,
        )
        q2 = st.slider("2. Chatbox helped me find the course information I needed.", 1, 5, 3)
        q3 = st.slider("3. Chatbox saved me time compared with searching the syllabus myself.", 1, 5, 3)
        q4 = st.slider("4. Chatbox was easy to use.", 1, 5, 3)
        q5 = st.text_area("5. What is one thing that would make Chatbox more useful? (optional)")
        submitted = st.form_submit_button("Submit feedback")

    if submitted:
        if not role:
            st.warning("Please choose your role before continuing.")
        else:
            save_survey({
                "role": role,
                "found_info": q2,
                "saved_time": q3,
                "ease_of_use": q4,
                "comment": q5,
            })
            st.session_state.survey_completed = True
            st.rerun()