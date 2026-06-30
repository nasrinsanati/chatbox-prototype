# agent.py - RAG Version
from langchain_xai import ChatXAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from tools import lookup_syllabus, recommend_resource, check_deadlines
from rag_utils import get_relevant_chunks
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

llm = ChatXAI(model="grok-4", temperature=0.7, max_tokens=800)
tools = [lookup_syllabus, recommend_resource, check_deadlines]
llm_with_tools = llm.bind_tools(tools)

store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

LOG_FILE = "chatbox_logs.jsonl"

def log_interaction(session_id: str, user_input: str, response_text: str, tool_used: str = None):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "user_query": user_input,
        "response_preview": response_text[:500] + "..." if len(response_text) > 500 else response_text,
        "tool_used": tool_used,
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

BASE_PROMPT = "You are Chatbox, a friendly and encouraging Course Advisor. Be supportive and practical."

def run_chatbox(user_input: str, syllabus_chunks: list = None, thread_id: str = "default"):
    history = get_session_history(thread_id)
    
    if syllabus_chunks:
        # RAG Mode - Use relevant chunks
        relevant_chunks = get_relevant_chunks(user_input, syllabus_chunks, top_k=6)
        context = "\n\n".join([f"--- Chunk {i+1} ---\n{chunk}" for i, chunk in enumerate(relevant_chunks)])
        
        system_prompt = SystemMessage(content=f"""{BASE_PROMPT}

You have access to relevant sections of the course syllabus below. 
Answer questions using only the provided chunks. If the answer is not in the chunks, say so clearly.
""")
        
        messages = [system_prompt] + history.messages + [HumanMessage(content=f"{user_input}\n\n{context}")]
        response = llm.invoke(messages)
        
        final_response = response.content if hasattr(response, 'content') else str(response)
        
        log_interaction(thread_id, user_input, final_response)
        history.add_user_message(user_input)
        history.add_ai_message(final_response)
        return final_response
    
    else:
        # Original tool-based mode (for JSON uploads)
        system_prompt = SystemMessage(content=f"""{BASE_PROMPT}

CRITICAL RULES:
- When the user asks about deadlines, due dates, or policies, use tools immediately.
- Be encouraging.
""")
        
        messages = [system_prompt] + history.messages + [HumanMessage(content=user_input)]
        response = llm_with_tools.invoke(messages)
        
        # Tool calling logic (same as before)
        tool_used = None
        if hasattr(response, 'tool_calls') and response.tool_calls:
            tool_used = response.tool_calls[0]["name"]
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                args = tool_call["args"]
                if tool_name == "lookup_syllabus":
                    tool_result = lookup_syllabus.invoke(args)
                elif tool_name == "recommend_resource":
                    tool_result = recommend_resource.invoke(args)
                elif tool_name == "check_deadlines":
                    tool_result = check_deadlines.invoke(args)
                else:
                    tool_result = "Tool not found."
                
                messages.append(response)
                messages.append(HumanMessage(content=f"Tool result: {tool_result}"))
                response = llm_with_tools.invoke(messages)
        
        final_response = response.content if hasattr(response, 'content') else str(response)
        
        log_interaction(thread_id, user_input, final_response, tool_used)
        history.add_user_message(user_input)
        history.add_ai_message(final_response)
        return final_response