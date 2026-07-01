# agent.py - Simple Large Context Version
from langchain_xai import ChatXAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

llm = ChatXAI(model="grok-4", temperature=0.7, max_tokens=800)

store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

LOG_FILE = "chatbox_logs.jsonl"

def log_interaction(session_id: str, user_input: str, response_text: str):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "user_query": user_input,
        "response_preview": response_text[:500] + "..." if len(response_text) > 500 else response_text,
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

BASE_SYSTEM_PROMPT = """
You are Chatbox, a friendly and encouraging Course Advisor.
Be supportive and practical.
"""

def run_chatbox(user_input: str, extracted_text: str = "", thread_id: str = "default"):
    history = get_session_history(thread_id)
    
    if extracted_text:
        # Large context (increased from 4000 → 12000)
        context = f"\n\n=== SYLLABUS CONTENT ===\n{extracted_text[:12000]}"
        
        system_prompt = SystemMessage(content=f"""{BASE_SYSTEM_PROMPT}

You have been given a large portion of the course syllabus.
Answer questions as accurately as possible using the provided syllabus content.
If the information is not in the syllabus, clearly say so.
""")
        
        messages = [system_prompt] + history.messages + [HumanMessage(content=user_input + context)]
        response = llm.invoke(messages)
        
        final_response = response.content if hasattr(response, 'content') else str(response)
        
        log_interaction(thread_id, user_input, final_response)
        history.add_user_message(user_input)
        history.add_ai_message(final_response)
        return final_response
    
    else:
        final_response = "Please upload your course syllabus (PDF or DOCX) first so I can give accurate answers."
        log_interaction(thread_id, user_input, final_response)
        history.add_user_message(user_input)
        history.add_ai_message(final_response)
        return final_response