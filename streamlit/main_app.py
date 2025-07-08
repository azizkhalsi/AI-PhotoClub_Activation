import streamlit as st
import sys
import os

# Add paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.email_personalizer import EmailPersonalizer
from src.config import *
from pages.email_generator import email_generator_page

# Page configuration
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize the email personalizer
@st.cache_resource
def get_personalizer():
    try:
        return EmailPersonalizer()
    except Exception as e:
        st.error(f"Failed to initialize EmailPersonalizer: {e}")
        return None

def check_api_key():
    """Check if OpenAI API key is configured"""
    if not OPENAI_API_KEY:
        st.error("⚠️ OpenAI API key not configured!")
        st.info("Please set your OPENAI_API_KEY in the .env file")
        st.code("OPENAI_API_KEY=your_api_key_here")
        return False
    return True

def main():
    st.title("📸 " + APP_TITLE)
    st.markdown(APP_DESCRIPTION)
    
    # Check API key
    if not check_api_key():
        st.stop()
    
    # Initialize personalizer
    personalizer = get_personalizer()
    if not personalizer:
        st.error("Could not initialize the application. Please check your configuration.")
        st.stop()
    
    # Model information in sidebar
    st.sidebar.title("🤖 AI Models")
    st.sidebar.info(f"**Search:** {SEARCH_MODEL}")
    st.sidebar.info(f"**Content:** {CONTENT_MODEL}")
    
    # Main email generator page
    email_generator_page(personalizer)

if __name__ == "__main__":
    main() 