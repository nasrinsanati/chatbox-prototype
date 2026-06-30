# agent.py - Improved Version with Better Syllabus Text Handling
from langchain_xai import ChatXAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from tools import lookup_syllabus, recommend_resource, check_deadlines
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

# Initialize Grok
llm = ChatXAI(
    model="grok-4",
    temperature=0.7,
    max_tokens=800
)

tools = [lookup_syllabus, recommend_resource, check_deadlines]
llm_with_tools = llm.bind_tools(tools)

# Global memory store
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# Logging
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

# Base System Prompt
BASE_SYSTEM_PROMPT = """
You are Chatbox, a friendly and encouraging Course Advisor.
Be supportive and practical.
"""

def run_chatbox(user_input: str, extracted_text: str = "", thread_id: str = "default"):
    history = get_session_history(thread_id)
    
    if extracted_text:
        # When PDF/DOCX is uploaded → Prioritize the extracted text
        context = f"\n\n=== FULL SYLLABUS CONTENT ===\n{extracted_text[:12000]}"
        
        system_prompt = SystemMessage(content=f"""{BASE_SYSTEM_PROMPT}

CRITICAL INSTRUCTIONS:
- You have been given the FULL syllabus content below.
- Answer questions **directly from the provided syllabus text**.
- If the answer exists in the syllabus, use it exactly.
- Do NOT use generic answers or assume information.
- Be precise and quote relevant parts when helpful.
- If something is not in the syllabus, clearly say so.
""")
        
        messages = [system_prompt] + history.messages + [HumanMessage(content=user_input + context)]
        
        # Get response without forcing tools
        response = llm.invoke(messages)
        
        if hasattr(response, 'content'):
            final_response = response.content
        else:
            final_response = str(response)
        
        log_interaction(thread_id, user_input, final_response)
        history.add_user_message(user_input)
        history.add_ai_message(final_response)
        
        return final_response
    
    else:
        # No extracted text → Use original tool-based behavior (for JSON uploads)
        system_prompt = SystemMessage(content=f"""{BASE_SYSTEM_PROMPT}

CRITICAL RULES:
- When the user asks about deadlines, due dates, midterms, assignments, or policies, ALWAYS use the appropriate tool immediately.
- Do not ask for clarification if the question is clear.
- Provide exact information from the syllabus using tools.
- Be encouraging after giving facts.
""")
        
        messages = [system_prompt] + history.messages + [HumanMessage(content=user_input)]
        response = llm_with_tools.invoke(messages)
        
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
        
        if hasattr(response, 'content'):
            final_response = response.content
        else:
            final_response = str(response)
        
        log_interaction(thread_id, user_input, final_response, tool_used)
        history.add_user_message(user_input)
        history.add_ai_message(final_response)
        
        return final_response