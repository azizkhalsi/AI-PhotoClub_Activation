import streamlit as st
import sys
import os

# Add paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.email_personalizer import EmailPersonalizer
from src.config import *
from streamlit.pages.email_generator import email_generator_page
from streamlit.pages.club_status import club_status_page
from streamlit.pages.settings import settings_page
from streamlit.pages.cost_analytics import cost_analytics_page

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
    
    # Sidebar for navigation
    st.sidebar.title("🧭 Navigation")
    
    # Show cost summary in sidebar
    try:
        total_costs = personalizer.get_total_costs()
        st.sidebar.markdown("### 💰 Cost Summary")
        st.sidebar.metric("Total Cost", f"${total_costs['total_cost']:.4f}")
        st.sidebar.metric("Emails Generated", total_costs['total_emails'])
        if total_costs['total_emails'] > 0:
            avg_cost = total_costs['total_cost'] / total_costs['total_emails']
            st.sidebar.metric("Avg Cost/Email", f"${avg_cost:.4f}")
    except Exception as e:
        st.sidebar.error(f"Error loading cost summary: {e}")
    
    # Navigation
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["📧 Generate Email", "📊 Club Status Dashboard", "💰 Cost Analytics", "⚙️ Settings"]
    )
    
    # Model information
    st.sidebar.markdown("### 🤖 AI Models")
    st.sidebar.info(f"**Search:** {SEARCH_MODEL}")
    st.sidebar.info(f"**Content:** {CONTENT_MODEL}")
    
    # Route to appropriate page
    if page == "📧 Generate Email":
        email_generator_page(personalizer)
    elif page == "📊 Club Status Dashboard":
        club_status_page(personalizer)
    elif page == "💰 Cost Analytics":
        cost_analytics_page(personalizer)
    elif page == "⚙️ Settings":
        settings_page()

if __name__ == "__main__":
    main() 