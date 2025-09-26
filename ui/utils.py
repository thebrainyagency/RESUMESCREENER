import streamlit as st
import os
from typing import Dict, Any

def init_session_state():
    """Initialize all session state variables"""
    # Check for existing API key in environment
    existing_api_key = os.getenv("OPENAI_API_KEY", "")

    defaults = {
        'step': 1,
        'api_key': existing_api_key,  # Use existing env var if available
        'model_choice': "gpt-4o",
        'uploaded_resumes': [],
        'jd_text': "",
        'rubric_text': "",
        'prefilter_percent': 25,
        'results': None
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

def validate_api_key(api_key: str) -> bool:
    """Validate OpenAI API key format"""
    return api_key.startswith("sk-") and len(api_key) > 40

def set_environment_variables(api_key: str, model: str):
    """Set required environment variables"""
    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["OPENAI_MODEL_PARSE"] = model
    os.environ["OPENAI_MODEL_SCORE"] = model

def calculate_k_value(total_resumes: int, percentage: int) -> int:
    """Calculate number of resumes to score based on percentage"""
    return max(1, int(total_resumes * percentage / 100))

def load_sample_rubric() -> str:
    """Load sample rubric from file"""
    try:
        with open("data/rubric_sample.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""

def reset_to_step_one():
    """Reset session state and go back to step 1"""
    st.session_state.step = 1
    st.session_state.results = None
    st.session_state.uploaded_resumes = []
    st.session_state.jd_text = ""
    st.session_state.rubric_text = ""