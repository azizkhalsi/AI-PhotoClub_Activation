import streamlit as st
import os
from src.config import *

def settings_page():
    """Settings and configuration page"""
    st.header("⚙️ Settings & Configuration")
    
    # API Configuration
    st.subheader("🔑 OpenAI API Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        api_key_status = "✅ Configured" if OPENAI_API_KEY else "❌ Not Configured"
        st.info(f"**API Key Status:** {api_key_status}")
        if OPENAI_API_KEY:
            masked_key = f"{OPENAI_API_KEY[:8]}...{OPENAI_API_KEY[-4:]}"
            st.caption(f"Key: {masked_key}")
    
    with col2:
        st.info(f"**Search Model:** {SEARCH_MODEL}")
        st.info(f"**Content Model:** {CONTENT_MODEL}")
    
    # Model Information
    st.subheader("🤖 Model Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**O3 (Search & Research):**")
        st.markdown(f"""
        - **Purpose:** Club research and web search
        - **Input Cost:** ${PRICING['o3']['input']:.2f} per 1M tokens
        - **Cached Input:** ${PRICING['o3']['cached_input']:.2f} per 1M tokens
        - **Output Cost:** ${PRICING['o3']['output']:.2f} per 1M tokens
        - **Configuration:** No temperature/max_tokens (as requested)
        """)
    
    with col2:
        st.markdown("**GPT-4.1-nano (Content Generation):**")
        st.markdown(f"""
        - **Purpose:** Personalized content generation
        - **Input Cost:** ${PRICING['gpt-4.1-nano']['input']:.3f} per 1M tokens
        - **Cached Input:** ${PRICING['gpt-4.1-nano']['cached_input']:.3f} per 1M tokens
        - **Output Cost:** ${PRICING['gpt-4.1-nano']['output']:.3f} per 1M tokens
        - **Configuration:** Temperature=0.8, Max Tokens=150
        """)
    
    st.info(f"🌐 **Web Search Cost:** ${WEB_SEARCH_COST_PER_QUERY:.3f} per query (${WEB_SEARCH_COST_PER_1K_CALLS:.2f} per 1K calls)")
    
    # File Configuration
    st.subheader("📁 File Configuration")
    
    files_to_check = [
        ("Clubs CSV", CLUBS_CSV_PATH, "Contains club data for personalization"),
        ("Email Template", EMAIL_TEMPLATE_PATH, "Base email template with {{Company name}} placeholder"),
        ("Database", DATABASE_PATH, "SQLite database for tracking emails and costs")
    ]
    
    for file_name, file_path, description in files_to_check:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            file_exists = os.path.exists(file_path)
            status = "✅ Found" if file_exists else "❌ Missing"
            st.info(f"**{file_name}:** {status}")
        
        with col2:
            st.caption(f"📍 **Path:** {file_path}")
            st.caption(f"📋 **Description:** {description}")
    
    # Project Structure
    st.subheader("📂 Project Structure")
    
    structure_info = """
    ```
    AI-PhotoClub_Activation/
    ├── app.py                    # Main entry point
    ├── .env                      # Environment variables (API keys)
    ├── requirements.txt          # Python dependencies
    ├── Introduction Email        # Email template
    ├── test_results_*.csv        # Club data
    ├── email_tracking.db         # Generated database
    │
    ├── src/                      # Core application logic
    │   ├── config.py            # Configuration settings
    │   └── email_personalizer.py # Main personalization logic
    │
    ├── streamlit/               # UI components
    │   ├── main_app.py         # Main Streamlit app
    │   └── pages/              # Individual page components
    │       ├── email_generator.py
    │       ├── club_status.py
    │       ├── cost_analytics.py
    │       └── settings.py
    │
    ├── test/                    # Testing scripts
    └── doc/                     # Documentation
    ```
    """
    
    st.code(structure_info, language="text")
    
    # Setup Instructions
    st.subheader("🚀 Setup Instructions")
    
    st.markdown("""
    ### 1. Environment Setup
    Create a `.env` file in the project root with:
    ```env
    OPENAI_API_KEY=your_openai_api_key_here
    SEARCH_MODEL=o3-mini
    CONTENT_MODEL=gpt-4o-mini
    ```
    
    ### 2. Required Files
    - **Club Data:** Ensure `test_results_20250701_092437.csv` contains club information
    - **Email Template:** Ensure `Introduction Email` exists with proper placeholders
    
    ### 3. Installation
    ```bash
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\\Scripts\\activate
    
    # Install dependencies
    pip install -r requirements.txt
    
    # Run the application
    streamlit run app.py
    ```
    
    ### 4. Usage Workflow
    1. **Generate Email:** Select a club and generate personalized email
    2. **Review Costs:** Monitor generation costs in real-time
    3. **Track Status:** Use dashboard to manage email status
    4. **Analyze Costs:** Review cost analytics for optimization
    """)
    
    # Environment Variables
    st.subheader("🌍 Environment Variables")
    
    env_vars = [
        ("OPENAI_API_KEY", OPENAI_API_KEY, "Your OpenAI API key"),
        ("SEARCH_MODEL", SEARCH_MODEL, "Model for club research"),
        ("CONTENT_MODEL", CONTENT_MODEL, "Model for content generation"),
        ("DATABASE_PATH", DATABASE_PATH, "SQLite database location"),
        ("CLUBS_CSV_PATH", CLUBS_CSV_PATH, "Path to clubs CSV file"),
        ("EMAIL_TEMPLATE_PATH", EMAIL_TEMPLATE_PATH, "Path to email template"),
    ]
    
    for var_name, var_value, description in env_vars:
        col1, col2, col3 = st.columns([1, 2, 2])
        
        with col1:
            st.code(var_name)
        
        with col2:
            if var_name == "OPENAI_API_KEY" and var_value:
                masked_value = f"{var_value[:8]}...{var_value[-4:]}"
                st.text(masked_value)
            else:
                st.text(str(var_value) if var_value else "Not set")
        
        with col3:
            st.caption(description)
    
    # Troubleshooting
    st.subheader("🔧 Troubleshooting")
    
    with st.expander("🚨 Common Issues"):
        st.markdown("""
        **API Key Issues:**
        - Ensure `.env` file exists in project root
        - Check API key has proper permissions for O3 and GPT-4o-mini models
        - Verify API key is valid and has sufficient credits
        
        **Model Access Issues:**
        - O3 models may require special access - contact OpenAI if needed
        - Consider using `gpt-4o-mini` for both search and content if O3 unavailable
        
        **File Issues:**
        - Ensure CSV file has required columns: Club, Country, Website, Name, Role, Email
        - Check email template contains `{{Company name}}` placeholder
        - Verify file paths in configuration
        
        **Cost Tracking Issues:**
        - Database is created automatically on first run
        - Cost calculations depend on proper API response metadata
        - Check pricing configuration in `src/config.py`
        """)
    
    with st.expander("💡 Performance Tips"):
        st.markdown("""
        **Cost Optimization:**
        - Use shorter, more focused prompts
        - Consider batching similar clubs for research efficiency
        - Monitor token usage in cost analytics
        
        **Application Performance:**
        - Close unused browser tabs running the app
        - Restart app if memory usage grows high
        - Use bulk operations for processing multiple clubs
        
        **Database Maintenance:**
        - Regularly backup `email_tracking.db`
        - Clear old test data if needed
        - Monitor database size for large datasets
        """)
    
    # System Information
    st.subheader("💻 System Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("**Application Version:** 2.0.0")
        st.info("**Architecture:** O3 + GPT-4o-mini")
        st.info("**Cost Tracking:** Enabled")
    
    with col2:
        st.info("**Framework:** Streamlit")
        st.info("**Database:** SQLite")
        st.info("**AI Provider:** OpenAI")
    
    # Reset Options
    st.subheader("🗑️ Reset Options")
    
    st.warning("⚠️ **Danger Zone** - These actions cannot be undone!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Clear All Email Data", type="secondary"):
            if st.session_state.get('confirm_clear_data'):
                try:
                    if os.path.exists(DATABASE_PATH):
                        os.remove(DATABASE_PATH)
                    st.success("✅ All email data cleared!")
                    st.info("🔄 Please restart the application to reinitialize the database.")
                except Exception as e:
                    st.error(f"❌ Error clearing data: {e}")
            else:
                st.session_state.confirm_clear_data = True
                st.error("⚠️ Click again to confirm deletion of ALL email data!")
    
    with col2:
        if st.button("🔄 Reset Cost Tracking", type="secondary"):
            st.info("💡 This would reset all cost tracking data. Feature coming soon.") 