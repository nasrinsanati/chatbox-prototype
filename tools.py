# tools.py - Full Version with Dynamic Syllabus Support
from langchain.tools import tool
from datetime import datetime
import streamlit as st

# Default syllabus (fallback)
syllabus_data = {
    "course_name": "Sample Course - EdTech",
    "instructor": "Dr. Rene Corbeil",
    "deadlines": {
        "Assignment 1": "2026-09-15",
        "Midterm Exam": "2026-10-10",
        "Final Project": "2026-12-05"
    },
    "policies": "Late submissions accepted up to 3 days with 10% penalty. No extensions without prior notice.",
    "resources": {
    "recursion": "https://realpython.com/python-recursion/",
    "ai agents": "https://www.langchain.com/",
    "data structures": "https://realpython.com/python-data-structures/"
    }
}

# Use uploaded syllabus if available in Streamlit session
if "syllabus" in st.session_state:
    syllabus_data = st.session_state.syllabus

@tool
def lookup_syllabus(query: str) -> str:
    """Look up information from the course syllabus, deadlines, or policies."""
    query_lower = query.lower()
    
    if "deadline" in query_lower or "due" in query_lower:
        deadlines = "\n".join([f"- {k}: {v}" for k, v in syllabus_data.get("deadlines", {}).items()])
        return f"Here are the important deadlines for {syllabus_data.get('course_name', 'the course')}:\n{deadlines}"
    
    elif "policy" in query_lower or "late" in query_lower:
        return f"Course Policies:\n{syllabus_data.get('policies', 'No specific policies found.')}"
    
    else:
        return f"Course: {syllabus_data.get('course_name', 'Unknown Course')}\nInstructor: {syllabus_data.get('instructor', 'Unknown')}\nAsk me specifically about deadlines, policies, or resources!"

@tool
def recommend_resource(topic: str) -> str:
    """Recommend approved learning resources based on topic."""
    topic_lower = topic.lower()
    resources = syllabus_data.get("resources", {})
    if topic_lower in resources:
        return f"Recommended resource for '{topic}': {resources[topic_lower]}"
    else:
        return f"I recommend searching for '{topic}' in our course materials or let me know more details for better recommendations!"

@tool
def check_deadlines() -> str:
    """Return all upcoming deadlines."""
    today = datetime.now().strftime("%Y-%m-%d")
    deadlines = "\n".join([f"- {k}: {v}" for k, v in syllabus_data.get("deadlines", {}).items()])
    return f"Current Date: {today}\n\nUpcoming Deadlines for {syllabus_data.get('course_name', 'the course')}:\n{deadlines}"