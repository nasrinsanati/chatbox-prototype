# agent.py - Updated with Larger Context (18,000 characters)
from langchain_xai import ChatXAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

# Initialize Grok
llm = ChatXAI(
    model="grok-4",
    temperature=0.7,
    max_tokens=900
)

# Global memory store
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# Logging
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

def run_chatbox(user_input: str, extracted_text: str = "", thread_id: str = "default"):
    history = get_session_history(thread_id)
    
    if extracted_text and len(extracted_text) > 50:
        # Increased context window
        context = f"\n\n=== FULL SYLLABUS CONTENT ===\n{extracted_text[:18000]}"
        
        system_prompt = SystemMessage(content="""
You are Chatbox, a helpful and accurate Course Advisor.

You have been given a large portion of the official course syllabus.
Answer questions **as accurately and specifically as possible** using only the provided syllabus text.

Guidelines:
- If the answer exists in the syllabus, use it directly and be specific.
- Quote or reference relevant sections when helpful.
- If the information is clearly not in the syllabus, say so politely.
- Do not make up or assume information.
""")
        
        messages = [system_prompt] + history.messages + [HumanMessage(content=user_input + context)]
        response = llm.invoke(messages)
        
        final_response = response.content if hasattr(response, 'content') else str(response)
        
        log_interaction(thread_id, user_input, final_response)
        history.add_user_message(user_input)
        history.add_ai_message(final_response)
        return final_response
    
    else:
        final_response = "Please upload your course syllabus (PDF or DOCX) first so I can give accurate answers based on your specific course."
        
        log_interaction(thread_id, user_input, final_response)
        history.add_user_message(user_input)
        history.add_ai_message(final_response)
        return final_response