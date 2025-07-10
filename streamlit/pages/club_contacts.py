import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

try:
    from brevo_email_service import BrevoEmailService
    from email_personalizer import EmailPersonalizer
    from club_status_manager import ClubStatusManager, ResponseStatus
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()

# Cache managers to improve performance
@st.cache_resource
def get_managers():
    """Cache managers for better performance"""
    try:
        email_personalizer = EmailPersonalizer()
        status_manager = ClubStatusManager()
        
        try:
            brevo_service = BrevoEmailService()
            test_result = brevo_service.test_connection()
            brevo_available = test_result['success']
            if not brevo_available:
                brevo_service = None
        except:
            brevo_service = None
            brevo_available = False
            
        return email_personalizer, status_manager, brevo_service, brevo_available
    except Exception as e:
        st.error(f"Error initializing services: {e}")
        return None, None, None, False

@st.cache_data(ttl=30)  # Cache for 30 seconds
def load_contacts_data():
    """Load and cache contacts data"""
    possible_paths = [
        "test_results_20250701_092437.csv",
        "../test_results_20250701_092437.csv", 
        os.path.join(os.path.dirname(__file__), "..", "..", "test_results_20250701_092437.csv"),
    ]
    
    contacts_file = None
    for path in possible_paths:
        if os.path.exists(path):
            contacts_file = path
            break
    
    if not contacts_file:
        return pd.DataFrame()
    
    return pd.read_csv(
        contacts_file,
        encoding='utf-8',
        quotechar='"',
        escapechar='\\',
        on_bad_lines='skip',
        engine='python',
        skipinitialspace=True,
        doublequote=True,
        sep=','
    )

def show_notification_bell(status_manager):
    """Compact notification bell in header"""
    notifications = status_manager.get_unread_notifications()
    count = len(notifications)
    
    # Create compact header with bell
    col1, col2, col3 = st.columns([0.7, 0.2, 0.1])
    
    with col1:
        st.markdown("# 👥 Club Contacts")
    
    with col3:
        bell_emoji = "🔔" if count == 0 else f"🔔({count})"
        
        if st.button(bell_emoji, key="notification_bell", help=f"{count} notifications"):
            st.session_state['show_notifications'] = not st.session_state.get('show_notifications', False)
    
    # Show notification popup if toggled
    if st.session_state.get('show_notifications', False) and notifications:
        with st.expander("🔔 Recent Notifications", expanded=True):
            for notif in notifications[-3:]:  # Show only last 3
                created = datetime.fromisoformat(notif['created_at']).strftime("%H:%M")
                st.info(f"📮 {notif['club_name']} - {notif['email_type']} ({created})")
            
            col_close, col_read = st.columns(2)
            with col_close:
                if st.button("Close", key="close_notifications"):
                    st.session_state['show_notifications'] = False
                    st.rerun()
            with col_read:
                if st.button("Mark All Read", key="mark_all_read"):
                    for notif in notifications:
                        status_manager.mark_notification_read(notif['notification_id'])
                    st.session_state['show_notifications'] = False
                    st.rerun()

def show_quick_stats(status_manager):
    """Show compact dashboard stats"""
    stats = status_manager.get_dashboard_stats()
    
    if stats.get('total_clubs', 0) > 0:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📊 Total Clubs", stats.get('total_clubs', 0))
        with col2:
            st.metric("✅ Positive Responses", stats.get('positive_responses', 0))
        with col3:
            st.metric("⏳ Awaiting Response", stats.get('awaiting_response', 0))

def show_filters(status_manager):
    """Simplified response-based filters"""
    st.markdown("### 🔍 Email Response Filters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📧 Emails with Responses:**")
        introduction_responded = st.checkbox("Introduction → Got Response", key="intro_responded")
        checkup_responded = st.checkbox("Checkup → Got Response", key="checkup_responded") 
        acceptance_responded = st.checkbox("Acceptance → Got Response", key="acceptance_responded")
    
    with col2:
        st.markdown("**⏳ Emails without Responses:**")
        introduction_no_response = st.checkbox("Introduction → No Response", key="intro_no_response")
        checkup_no_response = st.checkbox("Checkup → No Response", key="checkup_no_response")
        acceptance_no_response = st.checkbox("Acceptance → No Response", key="acceptance_no_response")
    
    col3, col4 = st.columns(2)
    
    with col3:
        never_contacted = st.checkbox("📭 Never Contacted", key="never_contacted")
    
    with col4:
        if st.button("🔄 Clear All Filters", key="clear_filters"):
            # Clear all filter states
            for key in ['intro_responded', 'checkup_responded', 'acceptance_responded',
                       'intro_no_response', 'checkup_no_response', 'acceptance_no_response', 'never_contacted']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    return {
        'introduction_responded': introduction_responded,
        'checkup_responded': checkup_responded,
        'acceptance_responded': acceptance_responded,
        'introduction_no_response': introduction_no_response,
        'checkup_no_response': checkup_no_response,
        'acceptance_no_response': acceptance_no_response,
        'never_contacted': never_contacted
    }

def get_filtered_clubs(status_manager, filters):
    """Get clubs based on response filters"""
    # If no filters are active, return empty list (show all clubs)
    if not any(filters.values()):
        return []
    
    try:
        # Read the status tracking data
        import pandas as pd
        df = pd.read_csv(status_manager.status_csv_path)
        
        if df.empty:
            return []
        
        filtered_clubs = set()
        
        # Introduction filters
        if filters['introduction_responded']:
            intro_responded = df[df['introduction_status'] == 'positive_response']['club_name'].tolist()
            filtered_clubs.update(intro_responded)
        
        if filters['introduction_no_response']:
            intro_no_response = df[df['introduction_status'] == 'email_sent']['club_name'].tolist()
            filtered_clubs.update(intro_no_response)
        
        # Checkup filters  
        if filters['checkup_responded']:
            checkup_responded = df[df['checkup_status'] == 'positive_response']['club_name'].tolist()
            filtered_clubs.update(checkup_responded)
        
        if filters['checkup_no_response']:
            checkup_no_response = df[df['checkup_status'] == 'email_sent']['club_name'].tolist()
            filtered_clubs.update(checkup_no_response)
        
        # Acceptance filters
        if filters['acceptance_responded']:
            acceptance_responded = df[df['acceptance_status'] == 'positive_response']['club_name'].tolist()
            filtered_clubs.update(acceptance_responded)
        
        if filters['acceptance_no_response']:
            acceptance_no_response = df[df['acceptance_status'] == 'email_sent']['club_name'].tolist()
            filtered_clubs.update(acceptance_no_response)
        
        # Never contacted filter
        if filters['never_contacted']:
            # Clubs with no email activity at all
            never_contacted = df[
                (pd.isna(df['introduction_status']) | (df['introduction_status'] == '')) &
                (pd.isna(df['checkup_status']) | (df['checkup_status'] == '')) &
                (pd.isna(df['acceptance_status']) | (df['acceptance_status'] == ''))
            ]['club_name'].tolist()
            filtered_clubs.update(never_contacted)
        
        return list(filtered_clubs)
        
    except Exception as e:
        print(f"Error in filtering: {e}")
        return []

def show_club_selector(contacts_df, status_manager, filtered_clubs):
    """Show club selector with status badges"""
    all_clubs = sorted(contacts_df['Club'].dropna().unique())
    
    if filtered_clubs:
        available_clubs = [club for club in all_clubs if club in filtered_clubs]
        if not available_clubs:
            st.warning("No clubs match filters")
            available_clubs = all_clubs
    else:
        available_clubs = all_clubs
    
    # Create display options with status badges
    options = ["Select a club..."]
    values = [""]
    
    for club in available_clubs:
        club_status = status_manager.get_club_status(club)
        if club_status:
            stage = club_status.get('current_stage', 'new')
            badge = stage.upper()[:4]
            options.append(f"{club} [{badge}]")
        else:
            options.append(f"{club} [NEW]")
        values.append(club)
    
    selected_idx = st.selectbox("Choose club", range(len(options)), format_func=lambda x: options[x], key="club_select")
    return values[selected_idx] if selected_idx > 0 else ""

def show_contact_selector(contacts_df, selected_club):
    """Show contact selector for selected club"""
    if not selected_club:
        st.selectbox("Contact Person", ["Select club first"], disabled=True)
        return None
    
    club_contacts = contacts_df[contacts_df['Club'] == selected_club]
    
    contact_options = []
    for _, contact in club_contacts.iterrows():
        name = contact.get('Name', 'Unknown')
        role = contact.get('Role', 'Unknown')
        email = contact.get('Email', '')
        
        if pd.notna(name) and pd.notna(email) and email.strip():
            contact_options.append({
                'display': f"{name} ({role})",
                'name': name,
                'role': role,
                'email': email,
                'phone': contact.get('Phone', ''),
                'country': contact.get('Country', ''),
                'website': contact.get('Website', '')
            })
    
    if not contact_options:
        st.selectbox("Contact Person", ["No contacts found"], disabled=True)
        return None
    
    contact_idx = st.selectbox("Contact Person", range(len(contact_options)), 
                              format_func=lambda x: contact_options[x]['display'], key="contact_select")
    return contact_options[contact_idx]

def show_current_stage_and_activity(selected_club, status_manager):
    """Show current stage and email activity"""
    if not selected_club:
        st.info("Select a club to view current stage")
        return
    
    club_status = status_manager.get_club_status(selected_club)
    
    if not club_status:
        st.info("New club - no activity yet")
        return
    
    # Show current stage and priority
    stage = club_status.get('current_stage', 'unknown')
    priority = club_status.get('priority_level', 'medium')
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Current Stage", stage.title())
    with col2:
        priority_colors = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        color = priority_colors.get(priority, "⚪")
        st.metric("Priority", f"{color} {priority.title()}")
    
    # Show email activity timeline
    st.markdown("**Email Activity:**")
    
    activities = []
    for email_type in ['introduction', 'checkup', 'acceptance']:
        status = club_status.get(f'{email_type}_status')
        sent_date = club_status.get(f'{email_type}_sent_date')
        
        if status and sent_date:
            date_str = datetime.fromisoformat(sent_date).strftime("%m/%d")
            if status == 'email_sent':
                activities.append(f"📤 {email_type.title()} sent ({date_str})")
            elif status == 'positive_response':
                activities.append(f"✅ {email_type.title()} positive ({date_str})")
            elif status == 'negative_response':
                activities.append(f"❌ {email_type.title()} negative ({date_str})")
    
    if activities:
        for activity in activities:
            st.text(activity)
    else:
        st.text("No email activity yet")
    
    # Response recording buttons (keep this functionality)
    if club_status:
        st.markdown("**Record Response:**")
        
        response_emails = []
        for email_type in ['introduction', 'checkup', 'acceptance']:
            if club_status.get(f'{email_type}_status') == 'email_sent':
                response_emails.append(email_type)
        
        if response_emails:
            cols = st.columns(len(response_emails))
            for i, email_type in enumerate(response_emails):
                with cols[i]:
                    col_pos, col_neg = st.columns(2)
                    with col_pos:
                        if st.button("✅", key=f"pos_{email_type}", help=f"Positive {email_type}"):
                            status_manager.record_response(selected_club, email_type, 
                                                         ResponseStatus.POSITIVE_RESPONSE.value,
                                                         f"Positive response on {datetime.now().strftime('%Y-%m-%d')}")
                            st.rerun()
                    with col_neg:
                        if st.button("❌", key=f"neg_{email_type}", help=f"Negative {email_type}"):
                            status_manager.record_response(selected_club, email_type,
                                                         ResponseStatus.NEGATIVE_RESPONSE.value, 
                                                         f"Negative response on {datetime.now().strftime('%Y-%m-%d')}")
                            st.rerun()

def show_club_status(selected_club, status_manager):
    """Show club status information"""
    if not selected_club:
        st.info("Select a club to view status")
        return
    
    club_status = status_manager.get_club_status(selected_club)
    
    if not club_status:
        st.info("New club - no status information yet")
        return
    
    # Show additional club information if available
    st.markdown("**Club Information:**")
    
    created_at = club_status.get('created_at', '')
    updated_at = club_status.get('updated_at', '')
    last_activity = club_status.get('last_activity_date', '')
    
    if created_at:
        created_date = datetime.fromisoformat(created_at).strftime("%m/%d/%Y")
        st.text(f"📅 First Contact: {created_date}")
    
    if last_activity:
        last_date = datetime.fromisoformat(last_activity).strftime("%m/%d/%Y")
        st.text(f"🕒 Last Activity: {last_date}")
    
    # Show any additional notes or information
    intro_notes = club_status.get('introduction_notes', '')
    checkup_notes = club_status.get('checkup_notes', '')
    acceptance_notes = club_status.get('acceptance_notes', '')
    
    all_notes = [intro_notes, checkup_notes, acceptance_notes]
    notes_text = ' | '.join([note for note in all_notes if note])
    
    if notes_text:
        st.markdown("**Notes:**")
        st.text(notes_text)

def handle_email_generation(status_manager, email_personalizer, brevo_service):
    """Handle email generation and sending"""
    if st.session_state.get('generating_email', False):
        club = st.session_state.get('send_club')
        contact = st.session_state.get('send_contact')
        
        if club and contact:
            with st.spinner("Generating and sending email..."):
                try:
                    # Generate email - returns (complete_email, personalized_content, club_research, total_costs)
                    complete_email, personalized_content, club_research, total_costs = email_personalizer.generate_personalized_email(
                        club, 'introduction', auto_research=True
                    )
                    
                    # Send via Brevo
                    send_result = brevo_service.send_email(
                        to_email=contact['email'],
                        to_name=contact['name'], 
                        subject=f"DxO Labs Partnership - {contact['name']}",
                        content=complete_email,
                        club_name=club,
                        contact_role=contact['role'],
                        email_type='introduction'
                    )
                    
                    if send_result['success']:
                        # Track status
                        status_manager.update_email_sent(club, 'introduction', 
                                                       f"Email sent to {contact['name']} on {datetime.now().strftime('%Y-%m-%d')}")
                        st.success(f"✅ Email sent to {contact['name']}!")
                        st.info(f"💰 Generation cost: ${total_costs.get('total_cost', 0):.4f}")
                    else:
                        st.error(f"❌ Send failed: {send_result['error']}")
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                
                finally:
                    st.session_state['generating_email'] = False

def club_contacts_page():
    """Optimized club contacts page"""
    
    # Custom CSS (simplified)
    st.markdown("""
    <style>
    .css-1d391kg {display: none !important;}
    .css-1cypcdb {display: none !important;}
    section[data-testid="stSidebar"] {display: none !important;}
    
    .contact-card {
        background: #f8f9fa;
        padding: 12px;
        border-radius: 6px;
        margin: 8px 0;
        border-left: 3px solid #007bff;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize managers (cached)
    managers = get_managers()
    if not managers[0]:
        st.error("Failed to initialize services")
        return
    
    email_personalizer, status_manager, brevo_service, brevo_available = managers
    
    # Load data (cached)
    contacts_df = load_contacts_data()
    if contacts_df.empty:
        st.error("❌ No contacts data found")
        return
    
    # Header with notification bell
    show_notification_bell(status_manager)
    
    # Quick stats
    show_quick_stats(status_manager)
    
    st.markdown("---")
    
    # Filters
    filters = show_filters(status_manager)
    filtered_clubs = get_filtered_clubs(status_manager, filters)
    
    st.markdown("---")
    
    # Main layout - more compact
    col_left, col_right = st.columns([1, 2])
    
    with col_left:
        st.markdown("### 🏛️ Selection")
        
        # Club selector
        selected_club = show_club_selector(contacts_df, status_manager, filtered_clubs)
        
        # Contact selector  
        selected_contact = show_contact_selector(contacts_df, selected_club)
        
        # Show contact card if selected
        if selected_contact:
            st.markdown('<div class="contact-card">', unsafe_allow_html=True)
            st.markdown(f"**{selected_contact['name']}**")
            st.markdown(f"*{selected_contact['role']}*")
            st.markdown(f"📧 {selected_contact['email']}")
            if selected_contact['country']:
                st.markdown(f"🌍 {selected_contact['country']}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Current stage and email activity
        st.markdown("### 📊 Current Stage")
        show_current_stage_and_activity(selected_club, status_manager)
    
    with col_right:
        st.markdown("### 📊 Club Status")
        
        # Club status
        show_club_status(selected_club, status_manager)
        
        # Show conversation if available
        if selected_club and selected_contact:
            st.markdown("---")
            st.markdown("### 💬 Email Conversation")
            
            # Get email exchanges from status manager and email content from tracking
            club_status = status_manager.get_club_status(selected_club)
            
            if club_status:
                email_exchanges = []
                
                # Load email content from tracking CSV
                try:
                    tracking_df = pd.read_csv('sent_emails_tracking.csv')
                    club_emails = tracking_df[tracking_df['club_name'] == selected_club]
                except:
                    club_emails = pd.DataFrame()
                
                # Create timeline from status data
                for email_type in ['introduction', 'checkup', 'acceptance']:
                    status = club_status.get(f'{email_type}_status')
                    sent_date = club_status.get(f'{email_type}_sent_date')
                    response_notes = club_status.get(f'{email_type}_response_notes', '')
                    
                    # Get email content if available
                    email_content = ""
                    if not club_emails.empty:
                        email_record = club_emails[club_emails['email_type'] == email_type]
                        if not email_record.empty:
                            email_content = email_record.iloc[0].get('generated_email', '')
                    
                    if status and sent_date:
                        # Add sent email
                        email_exchanges.append({
                            'type': 'sent',
                            'email_type': email_type,
                            'date': sent_date,
                            'status': status,
                            'notes': response_notes,
                            'content': email_content
                        })
                        
                        # Add response if we got one
                        if status in ['positive_response', 'negative_response']:
                            email_exchanges.append({
                                'type': 'received',
                                'email_type': email_type,
                                'date': sent_date,  # Use same date for now
                                'status': status,
                                'notes': response_notes,
                                'content': response_notes  # Use notes as response content
                            })
                
                # Sort by date
                email_exchanges.sort(key=lambda x: x['date'])
                
                if email_exchanges:
                    for i, exchange in enumerate(email_exchanges):
                        date_str = datetime.fromisoformat(exchange['date']).strftime("%m/%d %H:%M")
                        email_type = exchange['email_type'].title()
                        content = exchange.get('content', '')
                        
                        if exchange['type'] == 'sent':
                            # Show sent emails on the left with preview
                            with st.container():
                                # Create preview (first 2 lines)
                                preview = ""
                                if content:
                                    lines = content.split('\n')
                                    preview_lines = [line.strip() for line in lines[:2] if line.strip()]
                                    preview = ' '.join(preview_lines)
                                    if len(preview) > 100:
                                        preview = preview[:100] + "..."
                                
                                st.markdown(f"""
                                <div style="background: #e3f2fd; padding: 10px; border-radius: 8px; margin: 8px 0; border-left: 4px solid #2196f3; cursor: pointer;">
                                📤 <strong>Sent {email_type} Email</strong><br>
                                <small style="color: #666;">{date_str}</small><br>
                                <small style="color: #888; font-style: italic;">{preview}</small>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Expandable full email content
                                if content:
                                    with st.expander(f"📄 View Full {email_type} Email", key=f"email_{i}"):
                                        st.text_area(
                                            "Email Content",
                                            value=content,
                                            height=400,
                                            disabled=True,
                                            label_visibility="collapsed"
                                        )
                                        
                                        # Copy button
                                        if st.button(f"📋 Copy Email", key=f"copy_{i}"):
                                            st.code(content, language="text")
                                            st.success("📋 Email content displayed above - select all and copy!")
                        else:
                            # Show received responses on the right (indented)
                            with st.container():
                                response_color = "#4caf50" if exchange['status'] == 'positive_response' else "#f44336"
                                response_icon = "✅" if exchange['status'] == 'positive_response' else "❌"
                                response_text = "Positive Response" if exchange['status'] == 'positive_response' else "Negative Response"
                                
                                st.markdown(f"""
                                <div style="background: #f1f8e9; padding: 10px; border-radius: 8px; margin: 8px 0 16px 40px; border-left: 4px solid {response_color};">
                                📥 {response_icon} <strong>{response_text}</strong><br>
                                <small style="color: #666;">{date_str}</small>
                                {f'<br><em>{exchange["notes"]}</em>' if exchange["notes"] else ''}
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # If there's response content, show it expandable too
                                if content and content != exchange['notes']:
                                    with st.expander(f"📄 View Response Details", key=f"response_{i}"):
                                        st.text_area(
                                            "Response Content",
                                            value=content,
                                            height=200,
                                            disabled=True,
                                            label_visibility="collapsed"
                                        )
                else:
                    st.info("No email activity yet")
            else:
                st.info("No club status found")

if __name__ == "__main__":
    st.set_page_config(
        page_title="Club Contacts", 
        page_icon="👥",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    club_contacts_page() 