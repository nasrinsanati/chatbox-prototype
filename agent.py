# agent.py - Improved Version (20k Context + Stronger Prompt)
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
        # Increased to 20,000 characters
        context = f"\n\n=== FULL SYLLABUS CONTENT ===\n{extracted_text[:20000]}"
        
        system_prompt = SystemMessage(content="""
You are Chatbox, a precise and helpful Course Advisor.

You have been given a large portion of the official course syllabus below.

Your task is to answer questions **as accurately and thoroughly as possible** using ONLY the provided syllabus text.

Important Rules:
- Carefully read the entire syllabus content before answering.
- If the answer exists anywhere in the syllabus (even in later sections), use it.
- Be specific and quote relevant parts when helpful.
- If the information is truly not in the syllabus, clearly say so.
- Do not make up information or use external knowledge.
""")
        
        messages = [system_prompt] + history.messages + [HumanMessage(content=user_input + context)]
        response = llm.invoke(messages)
        
        final_response = response.content if hasattr(response, 'content') else str(response)
        
        log_interaction(thread_id, user_input, final_response)
        history.add_user_message(user_input)
        history.add_ai_message(final_response)
        return final_response
    
    else:
        final_response = "Please upload your course syllabus (PDF or DOCX) first so I can give you accurate answers based on your specific course."
        
        log_interaction(thread_id, user_input, final_response)
        history.add_user_message(user_input)
        history.add_ai_message(final_response)
        return final_response