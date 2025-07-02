import streamlit as st
import pandas as pd
from email_personalizer import EmailPersonalizer
import config
from datetime import datetime
import os

# Page configuration
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize the email personalizer
@st.cache_resource
def get_personalizer():
    return EmailPersonalizer()

def check_api_key():
    """Check if OpenAI API key is configured"""
    if not config.OPENAI_API_KEY:
        st.error("⚠️ OpenAI API key not configured!")
        st.info("Please set your OPENAI_API_KEY in a .env file:")
        st.code("OPENAI_API_KEY=your_api_key_here")
        return False
    return True

def main():
    st.title("📸 " + config.APP_TITLE)
    st.markdown(config.APP_DESCRIPTION)
    
    # Check API key
    if not check_api_key():
        st.stop()
    
    # Initialize personalizer
    try:
        personalizer = get_personalizer()
    except Exception as e:
        st.error(f"Error initializing application: {e}")
        st.stop()
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["📧 Generate Email", "📊 Club Status", "⚙️ Settings"]
    )
    
    if page == "📧 Generate Email":
        generate_email_page(personalizer)
    elif page == "📊 Club Status":
        club_status_page(personalizer)
    elif page == "⚙️ Settings":
        settings_page()

def generate_email_page(personalizer):
    st.header("📧 Generate Personalized Email")
    
    # Load clubs data
    try:
        clubs_df = personalizer.load_clubs_data()
        if clubs_df.empty:
            st.error("No clubs data found. Please check your CSV file.")
            return
    except Exception as e:
        st.error(f"Error loading clubs data: {e}")
        return
    
    # Club selection
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_club = st.selectbox(
            "Select a Photography Club:",
            options=clubs_df['Club'].tolist(),
            index=0,
            help="Choose a club to generate a personalized email"
        )
    
    with col2:
        # Display club info
        if selected_club:
            club_info = clubs_df[clubs_df['Club'] == selected_club].iloc[0]
            st.info(f"**Country:** {club_info.get('Country', 'N/A')}")
            if club_info.get('Website'):
                st.info(f"**Website:** {club_info['Website']}")
    
    # Check if email already exists
    if selected_club:
        email_exists, email_data = personalizer.check_email_sent(selected_club)
        
        if email_exists:
            st.success("✅ Email already generated for this club!")
            
            # Show email status
            if email_data['email_sent_date']:
                st.info(f"📤 **Status:** Sent on {email_data['email_sent_date'][:10]}")
            else:
                st.warning("📝 **Status:** Generated but not sent")
            
            # Show existing email
            with st.expander("📄 View Generated Email", expanded=True):
                st.text_area(
                    "Generated Email:",
                    value=email_data['generated_email'],
                    height=400,
                    disabled=True
                )
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 Regenerate Email", type="secondary"):
                    regenerate_email(personalizer, selected_club)
            
            with col2:
                if not email_data['email_sent_date']:
                    if st.button("📤 Mark as Sent", type="primary"):
                        personalizer.mark_email_as_sent(selected_club)
                        st.success("Email marked as sent!")
                        st.rerun()
            
            with col3:
                if st.button("📋 Copy to Clipboard", type="secondary"):
                    st.code(email_data['generated_email'])
                    st.info("Email copied above - you can select and copy it!")
        
        else:
            st.info("🆕 No email generated yet for this club.")
            
            # Generate new email
            if st.button("🚀 Generate Personalized Email", type="primary"):
                generate_new_email(personalizer, selected_club)

def generate_new_email(personalizer, club_name):
    """Generate a new personalized email"""
    try:
        with st.spinner(f"🔍 Researching {club_name} and generating personalized email..."):
            email, content, research = personalizer.generate_personalized_email(club_name)
            personalizer.save_generated_email(club_name, content, email)
        
        st.success("✅ Email generated successfully!")
        
        # Show the generated email
        st.subheader("📧 Generated Email")
        st.text_area("Email Content:", value=email, height=400, disabled=True)
        
        # Show research summary
        with st.expander("🔍 Research Summary"):
            st.write(research)
        
        # Show personalized content
        with st.expander("✨ Personalized Content Added"):
            st.write(content)
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📤 Mark as Sent"):
                personalizer.mark_email_as_sent(club_name)
                st.success("Email marked as sent!")
        
        with col2:
            if st.button("📋 Copy Email"):
                st.code(email)
                st.info("Email copied above - you can select and copy it!")
        
        # Refresh the page to show updated status
        st.rerun()
        
    except Exception as e:
        st.error(f"Error generating email: {e}")

def regenerate_email(personalizer, club_name):
    """Regenerate email for a club"""
    try:
        with st.spinner(f"🔄 Regenerating email for {club_name}..."):
            email, content, research = personalizer.generate_personalized_email(club_name)
            personalizer.save_generated_email(club_name, content, email, mark_as_sent=False)
        
        st.success("✅ Email regenerated successfully!")
        st.rerun()
        
    except Exception as e:
        st.error(f"Error regenerating email: {e}")

def club_status_page(personalizer):
    st.header("📊 Club Status Dashboard")
    
    try:
        status_df = personalizer.get_all_clubs_status()
        
        if status_df.empty:
            st.warning("No clubs data available.")
            return
        
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        
        total_clubs = len(status_df)
        sent_count = len(status_df[status_df['status'] == 'Sent'])
        generated_count = len(status_df[status_df['status'] == 'Generated'])
        not_generated_count = len(status_df[status_df['status'] == 'Not Generated'])
        
        with col1:
            st.metric("Total Clubs", total_clubs)
        with col2:
            st.metric("Emails Sent", sent_count)
        with col3:
            st.metric("Generated (Not Sent)", generated_count)
        with col4:
            st.metric("Not Generated", not_generated_count)
        
        # Progress bar
        progress = (sent_count + generated_count) / total_clubs if total_clubs > 0 else 0
        st.progress(progress, text=f"Progress: {progress:.1%} of clubs have emails generated")
        
        # Filter options
        st.subheader("Filter Clubs")
        col1, col2 = st.columns(2)
        
        with col1:
            status_filter = st.selectbox(
                "Filter by Status:",
                options=["All", "Sent", "Generated", "Not Generated"]
            )
        
        with col2:
            country_filter = st.selectbox(
                "Filter by Country:",
                options=["All"] + sorted(status_df['Country'].unique().tolist())
            )
        
        # Apply filters
        filtered_df = status_df.copy()
        
        if status_filter != "All":
            filtered_df = filtered_df[filtered_df['status'] == status_filter]
        
        if country_filter != "All":
            filtered_df = filtered_df[filtered_df['Country'] == country_filter]
        
        # Display filtered data
        st.subheader(f"Clubs ({len(filtered_df)} of {total_clubs})")
        
        # Style the dataframe
        def style_status(status):
            if status == 'Sent':
                return 'background-color: #d4edda; color: #155724'
            elif status == 'Generated':
                return 'background-color: #fff3cd; color: #856404'
            else:
                return 'background-color: #f8d7da; color: #721c24'
        
        styled_df = filtered_df.style.applymap(style_status, subset=['status'])
        st.dataframe(styled_df, use_container_width=True)
        
        # Bulk actions
        if not filtered_df.empty:
            st.subheader("Bulk Actions")
            selected_clubs = st.multiselect(
                "Select clubs for bulk actions:",
                options=filtered_df['Club'].tolist(),
                help="Select multiple clubs to perform bulk actions"
            )
            
            if selected_clubs:
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🚀 Generate Emails for Selected Clubs"):
                        generate_bulk_emails(personalizer, selected_clubs)
                
                with col2:
                    if st.button("📤 Mark Selected as Sent"):
                        mark_bulk_as_sent(personalizer, selected_clubs)
        
    except Exception as e:
        st.error(f"Error loading club status: {e}")

def generate_bulk_emails(personalizer, club_names):
    """Generate emails for multiple clubs"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_clubs = len(club_names)
    
    for i, club_name in enumerate(club_names):
        try:
            status_text.text(f"Processing {club_name}... ({i+1}/{total_clubs})")
            
            # Check if email already exists
            email_exists, _ = personalizer.check_email_sent(club_name)
            
            if not email_exists:
                email, content, research = personalizer.generate_personalized_email(club_name)
                personalizer.save_generated_email(club_name, content, email)
                st.success(f"✅ Generated email for {club_name}")
            else:
                st.info(f"ℹ️ Email already exists for {club_name}")
            
            progress_bar.progress((i + 1) / total_clubs)
            
        except Exception as e:
            st.error(f"❌ Error generating email for {club_name}: {e}")
    
    status_text.text("Bulk generation completed!")
    st.success(f"Processed {total_clubs} clubs")

def mark_bulk_as_sent(personalizer, club_names):
    """Mark multiple emails as sent"""
    for club_name in club_names:
        try:
            personalizer.mark_email_as_sent(club_name)
        except Exception as e:
            st.error(f"Error marking {club_name} as sent: {e}")
    
    st.success(f"Marked {len(club_names)} emails as sent!")

def settings_page():
    st.header("⚙️ Settings")
    
    # API Configuration
    st.subheader("OpenAI Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        api_key_status = "✅ Configured" if config.OPENAI_API_KEY else "❌ Not Configured"
        st.info(f"**API Key Status:** {api_key_status}")
    
    with col2:
        st.info(f"**Model:** {config.OPENAI_MODEL}")
    
    # File Paths
    st.subheader("File Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv_exists = os.path.exists(config.CLUBS_CSV_PATH)
        csv_status = "✅ Found" if csv_exists else "❌ Not Found"
        st.info(f"**Clubs CSV:** {csv_status}")
        st.caption(f"Path: {config.CLUBS_CSV_PATH}")
    
    with col2:
        template_exists = os.path.exists(config.EMAIL_TEMPLATE_PATH)
        template_status = "✅ Found" if template_exists else "❌ Not Found"
        st.info(f"**Email Template:** {template_status}")
        st.caption(f"Path: {config.EMAIL_TEMPLATE_PATH}")
    
    # Database Status
    st.subheader("Database Status")
    db_exists = os.path.exists(config.DATABASE_PATH)
    db_status = "✅ Created" if db_exists else "❌ Not Created"
    st.info(f"**Database:** {db_status}")
    st.caption(f"Path: {config.DATABASE_PATH}")
    
    # Instructions
    st.subheader("Setup Instructions")
    st.markdown("""
    1. **Configure OpenAI API Key:**
       - Create a `.env` file in the project root
       - Add: `OPENAI_API_KEY=your_api_key_here`
       - Optionally add: `OPENAI_MODEL=gpt-4o-mini`
    
    2. **Required Files:**
       - `test_results_20250701_092437.csv` - Contains club data
       - `Introduction Email` - Email template file
    
    3. **Usage:**
       - Navigate to "Generate Email" to create personalized emails
       - Use "Club Status" to monitor progress and perform bulk actions
    """)

if __name__ == "__main__":
    main() 