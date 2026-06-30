# agent.py - Final Version with Structured Syllabus Support
from langchain_xai import ChatXAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

llm = ChatXAI(model="grok-4", temperature=0.7, max_tokens=900)

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

def run_chatbox(user_input: str, raw_text: str = "", structured_data: dict = None, thread_id: str = "default"):
    history = get_session_history(thread_id)
    
    if structured_data:
        # Use structured data when available (more reliable for factual questions)
        context = f"\n\n=== STRUCTURED SYLLABUS DATA ===\n{json.dumps(structured_data, indent=2)}"
        
        system_prompt = SystemMessage(content="""
You are Chatbox, a precise and helpful Course Advisor.

You have access to both structured syllabus data and raw syllabus text.
For factual questions (grading, due dates, policies, instructor info), prioritize the structured data.
For open-ended or detailed questions, use the raw text when needed.
Be accurate and quote relevant parts when helpful.
""")
        
        messages = [system_prompt] + history.messages + [HumanMessage(content=user_input + context)]
        response = llm.invoke(messages)
        
        final_response = response.content if hasattr(response, 'content') else str(response)
        
        log_interaction(thread_id, user_input, final_response)
        history.add_user_message(user_input)
        history.add_ai_message(final_response)
        return final_response
    
    elif raw_text:
        # Fallback to raw text with large context
        context = f"\n\n=== SYLLABUS CONTENT ===\n{raw_text[:18000]}"
        
        system_prompt = SystemMessage(content="""
You are Chatbox, a helpful and accurate Course Advisor.
Answer questions as accurately as possible using the provided syllabus content.
""")
        
        messages = [system_prompt] + history.messages + [HumanMessage(content=user_input + context)]
        response = llm.invoke(messages)
        
        final_response = response.content if hasattr(response, 'content') else str(response)
        
        log_interaction(thread_id, user_input, final_response)
        history.add_user_message(user_input)
        history.add_ai_message(final_response)
        return final_response
    
    else:
        final_response = "Please upload your course syllabus first so I can answer questions accurately."
        log_interaction(thread_id, user_input, final_response)
        history.add_user_message(user_input)
        history.add_ai_message(final_response)
        return final_response