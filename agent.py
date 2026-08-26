# agent.py - Grok Version
from langchain_xai import ChatXAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from tools import lookup_syllabus, recommend_resource, check_deadlines
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

llm = ChatXAI(
    model="grok-4",
    temperature=0.7,
    max_tokens=700
)

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

system_prompt = SystemMessage(content=(
    "You are Chatbox, a friendly and encouraging Course Advisor. "
    "Be supportive and practical. "
    "Use the provided syllabus content first, including later sections and tables. "
    "When the user asks about deadlines, due dates, assignments, grading, GPA, or policies, "
    "give exact information from the syllabus. "
    "If the answer is not in the syllabus, say so clearly. "
    "Do not invent dates or policies."
))

def run_chatbox(user_input: str, extracted_text: str = "", thread_id: str = "default"):
    history = get_session_history(thread_id)

    if not extracted_text:
        final_response = "Please upload your course syllabus (PDF or DOCX) first so I can give accurate answers."
        log_interaction(thread_id, user_input, final_response)
        history.add_user_message(user_input)
        history.add_ai_message(final_response)
        return final_response

    if len(extracted_text) <= 40000:
        syllabus_text = extracted_text
    else:
        syllabus_text = extracted_text[:20000] + "\n\n...\n\n" + extracted_text[-20000:]

    context = "\n\n=== SYLLABUS CONTENT ===\n" + syllabus_text
    messages = [system_prompt] + history.messages + [HumanMessage(content=user_input + context)]
    response = llm_with_tools.invoke(messages)

    tool_used = None
    if hasattr(response, "tool_calls") and response.tool_calls:
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
            messages.append(HumanMessage(content="Tool result: " + str(tool_result)))
            response = llm_with_tools.invoke(messages)

    final_response = response.content if hasattr(response, "content") else str(response)
    if isinstance(final_response, list):
        pieces = []
        for item in final_response:
            if isinstance(item, dict) and "text" in item:
                pieces.append(item["text"])
            else:
                pieces.append(str(item))
        final_response = "\n".join(pieces)

    final_response = str(final_response)
    log_interaction(thread_id, user_input, final_response, tool_used)
    history.add_user_message(user_input)
    history.add_ai_message(final_response)
    return final_response