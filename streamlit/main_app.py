import streamlit as st
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import pages
from pages.email_generator import email_generator_page
from pages.club_contacts import club_contacts_page

def main():
    """Main application"""
    
    # Page configuration
    st.set_page_config(
        page_title="Photo Club Email Tool",
        page_icon="📧",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main {
        padding-top: 2rem;
    }
    .stSelectbox > div > div > select {
        background-color: #f0f2f6;
    }
    .stButton > button {
        width: 100%;
    }
    .metric-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #007bff;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    # 📧 Photo Club Email Personalization Tool
    **Professional Email Generator for Photography Club Partnerships**
    """)
    
    # Page navigation
    page_selection = st.selectbox(
        "📄 Select Page",
        ["Email Generator", "Club Contacts"],
        key="page_selector"
    )
    
    st.markdown("---")
    
    # Show app description in sidebar
    with st.sidebar:
        st.markdown("""
        ### 📋 How It Works
        
        **Email Generator:**
        1. **Select Club & Email Type** - Choose from database
        2. **Generate Email** - Auto-research + personalized content
        3. **Edit & Send** - Review and customize
        
        **Club Contacts:**
        1. **Filter by Status** - Find clubs by response stage
        2. **Select Club & Contact** - Choose person & role
        3. **Send & Track** - Via Brevo with conversation history
        4. **Record Responses** - Mark positive/negative replies
        5. **Bell Notifications** - Real-time response alerts
        
        ### 🎯 Email Types
        - **Introduction**: First contact with discount offer
        - **Checkup**: Follow-up when no response
        - **Acceptance**: Guide clubs through discount process
        
        ### ⚡ Features
        - **Auto Research**: Smart club research
        - **Brevo Integration**: Email sending & tracking
        - **Conversation View**: Full email history
        - **Metrics**: Open rates, replies, analytics
        """)
    
    # Main page content
    if page_selection == "Email Generator":
        email_generator_page()
    elif page_selection == "Club Contacts":
        club_contacts_page()
    else:
        email_generator_page()  # Default
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p>Photo Club Email Personalization Tool | Professional Partnership Outreach</p>
        <p>Research cached for 30 days | Uses O3 web search for accurate club information</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 