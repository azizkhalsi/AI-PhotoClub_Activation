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
    from response_manager import ResponseManager
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
        response_manager = ResponseManager()
        
        try:
            brevo_service = BrevoEmailService()
            test_result = brevo_service.test_connection()
            brevo_available = test_result['success']
            if not brevo_available:
                brevo_service = None
        except:
            brevo_service = None
            brevo_available = False
            
        return email_personalizer, status_manager, response_manager, brevo_service, brevo_available
    except Exception as e:
        st.error(f"Error initializing services: {e}")
        return None, None, None, None, False

@st.cache_data(ttl=30)  # Cache for 30 seconds
def load_contacts_data():
    """Load and cache contacts data with custom CSV parsing to handle field count mismatches"""
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
    
    # Custom CSV parsing to handle field count mismatches (same as email generator)
    import csv
    contacts_data = []
    
    try:
        with open(contacts_file, 'r', encoding='utf-8') as f:
            # Read header properly
            header_line = f.readline().strip()
            header = header_line.split(',')
            expected_fields = len(header)
            
            # Read data rows
            reader = csv.reader(f, quotechar='"')
            for row_num, row in enumerate(reader, start=2):
                if len(row) >= expected_fields:
                    # Truncate to expected number of fields if there are extras
                    row_data = dict(zip(header, row[:expected_fields]))
                    contacts_data.append(row_data)
        
        return pd.DataFrame(contacts_data)
    except Exception as e:
        print(f"Error loading contacts data: {e}")
        return pd.DataFrame()

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
                try:
                    created_at = notif.get('created_at', '')
                    if isinstance(created_at, str) and created_at.strip():
                        created = datetime.fromisoformat(created_at).strftime("%H:%M")
                    else:
                        created = "unknown"
                except (ValueError, TypeError):
                    created = "unknown"
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
        
        if status and sent_date and isinstance(sent_date, str) and sent_date.strip():
            try:
                date_str = datetime.fromisoformat(sent_date).strftime("%m/%d")
            except (ValueError, TypeError):
                date_str = "unknown"
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
            st.markdown("**Quick Response:**")
            for email_type in response_emails:
                # Simple layout without nested columns
                st.markdown(f"*{email_type.title()} Email Response:*")
                
                # Create a container for the buttons
                with st.container():
                    if st.button(f"✅ Positive Response for {email_type.title()}", 
                               key=f"pos_{email_type}", 
                               use_container_width=True):
                        status_manager.record_response(selected_club, email_type, 
                                                     ResponseStatus.POSITIVE_RESPONSE.value,
                                                     f"Positive response on {datetime.now().strftime('%Y-%m-%d')}")
                        st.rerun()
                    
                    if st.button(f"❌ Negative Response for {email_type.title()}", 
                               key=f"neg_{email_type}", 
                               use_container_width=True):
                        status_manager.record_response(selected_club, email_type,
                                                     ResponseStatus.NEGATIVE_RESPONSE.value, 
                                                     f"Negative response on {datetime.now().strftime('%Y-%m-%d')}")
                        st.rerun()
                st.markdown("---")

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
    
    if created_at and isinstance(created_at, str) and created_at.strip():
        try:
            created_date = datetime.fromisoformat(created_at).strftime("%m/%d/%Y")
            st.text(f"📅 First Contact: {created_date}")
        except (ValueError, TypeError):
            st.text(f"📅 First Contact: {created_at}")
    
    if last_activity and isinstance(last_activity, str) and last_activity.strip():
        try:
            last_date = datetime.fromisoformat(last_activity).strftime("%m/%d/%Y")
            st.text(f"🕒 Last Activity: {last_date}")
        except (ValueError, TypeError):
            st.text(f"🕒 Last Activity: {last_activity}")
    


def show_response_manager(selected_club, selected_contact, response_manager, status_manager):
    """Show response management interface"""
    if not selected_club:
        st.info("Select a club to manage responses")
        return
    
    # Check for new responses button
    col_check, col_stats = st.columns(2)
    
    with col_check:
        if st.button("🔍 Check New Responses", use_container_width=True):
            with st.spinner("Checking for responses..."):
                result = response_manager.run_response_check()
                if result['new_responses_found'] > 0:
                    st.success(f"✅ Found {result['new_responses_found']} new responses!")
                else:
                    st.info("📭 No new responses found")
    
    with col_stats:
        # Show response stats
        stats = response_manager.get_response_stats()
        total_responses = stats.get('total_responses', 0)
        unprocessed = stats.get('unprocessed_count', 0)
        
        if total_responses > 0:
            st.metric("Total Responses", f"{total_responses}")
            if unprocessed > 0:
                st.warning(f"⚠️ {unprocessed} unprocessed")
        else:
            st.info("No responses yet")
    
    # Manual response entry
    if selected_contact:
        with st.expander("📝 Add Manual Response"):
            email_type = st.selectbox(
                "Email Type",
                ["introduction", "checkup", "acceptance"],
                key="response_email_type"
            )
            
            response_type = st.selectbox(
                "Response Type",
                ["positive_response", "negative_response", "neutral_response"],
                key="response_type",
                format_func=lambda x: x.replace('_', ' ').title()
            )
            
            response_content = st.text_area(
                "Response Content",
                placeholder="Enter the actual response content from the club...",
                height=100,
                key="response_content"
            )
            
            if st.button("💾 Save Response", type="primary"):
                if response_content.strip():
                    success = response_manager.save_response(
                        club_name=selected_club,
                        contact_email=selected_contact['email'],
                        email_type=email_type,
                        response_content=response_content,
                        response_type=response_type,
                        detection_method='manual'
                    )
                    
                    if success:
                        st.success("✅ Response saved successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to save response (may already exist)")
                else:
                    st.warning("Please enter response content")
    
    # Show existing responses for this club
    club_responses = response_manager.get_all_responses(selected_club)
    if club_responses:
        st.markdown("**📋 Existing Responses:**")
        for response in club_responses[-3:]:  # Show last 3
            response_date = response['response_date'][:10]
            response_type = response['response_type'].replace('_', ' ').title()
            email_type = response['email_type'].title()
            
            st.markdown(f"""
            <div style="background: #f0f0f0; padding: 8px; border-radius: 4px; margin: 4px 0;">
            <small><strong>{email_type}</strong> - {response_type} ({response_date})</small><br>
            <small>{response['response_content'][:80]}...</small>
            </div>
            """, unsafe_allow_html=True)


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
    
    email_personalizer, status_manager, response_manager, brevo_service, brevo_available = managers
    
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
        
        # Response management
        st.markdown("---")
        st.markdown("### 📥 Response Manager")
        show_response_manager(selected_club, selected_contact, response_manager, status_manager)
    
    with col_right:
        st.markdown("### 📊 Club Status")
        
        # Club status
        show_club_status(selected_club, status_manager)
        
        # Show conversation if available
        if selected_club and selected_contact:
            st.markdown("---")
            st.markdown(f"### 💬 Email Conversation with {selected_contact['name']}")
            
            # Get contact-specific email conversation from Brevo tracking
            try:
                # Load Brevo email tracking data (contact-specific)
                brevo_tracking_df = pd.read_csv('data/email_tracking.csv')
                
                # Filter for this specific contact
                contact_emails = brevo_tracking_df[
                    (brevo_tracking_df['club_name'] == selected_club) & 
                    (brevo_tracking_df['contact_email'] == selected_contact['email'])
                ]
                
                # Also load conversation data if available
                try:
                    conversation_df = pd.read_csv('data/email_conversations.csv')
                    contact_conversation = conversation_df[
                        (conversation_df['club_name'] == selected_club) &
                        (conversation_df['contact_email'] == selected_contact['email'])
                    ]
                except FileNotFoundError:
                    contact_conversation = pd.DataFrame()
                
                if not contact_emails.empty or not contact_conversation.empty:
                    # Combine tracking and conversation data
                    all_messages = []
                    
                    # Add sent emails from tracking
                    for _, email in contact_emails.iterrows():
                        all_messages.append({
                            'type': 'sent',
                            'email_type': email.get('email_type', 'unknown'),
                            'date': email.get('sent_datetime', ''),
                            'subject': email.get('subject', ''),
                            'content': email.get('content', ''),
                            'status': 'sent',
                            'delivery_status': email.get('delivery_status', 'unknown'),
                            'opened': bool(email.get('opened_datetime', '')),
                            'clicked': bool(email.get('clicked_datetime', '')),
                            'replied': bool(email.get('replied_datetime', ''))
                        })
                    
                    # Add conversation messages (sent/received)
                    for _, msg in contact_conversation.iterrows():
                        message_type = msg.get('message_type', 'unknown')
                        sender = msg.get('sender', 'unknown')
                        
                        all_messages.append({
                            'type': message_type,
                            'email_type': 'conversation',
                            'date': msg.get('message_datetime', ''),
                            'subject': msg.get('subject', ''),
                            'content': msg.get('content', ''),
                            'status': msg.get('status', 'unknown'),
                            'sender': sender
                        })
                    
                    # Sort by date
                    def safe_date_key(message):
                        date_value = message.get('date', '')
                        if pd.isna(date_value) or not date_value:
                            return '1900-01-01'
                        return str(date_value)
                    
                    all_messages.sort(key=safe_date_key)
                    
                    if all_messages:
                        for i, message in enumerate(all_messages):
                            try:
                                message_date = message.get('date', '')
                                if isinstance(message_date, str) and message_date.strip():
                                    date_str = datetime.fromisoformat(message_date).strftime("%m/%d %H:%M")
                                else:
                                    date_str = "unknown"
                            except (ValueError, TypeError):
                                date_str = "unknown"
                            
                            email_type = message.get('email_type', 'unknown').title()
                            subject = message.get('subject', '')
                            content = message.get('content', '')
                            
                            if message['type'] == 'sent':
                                # Show sent emails with status indicators
                                status_indicators = ""
                                if message.get('delivery_status') == 'sent':
                                    status_indicators += "📤 "
                                if message.get('opened'):
                                    status_indicators += "👁️ "
                                if message.get('clicked'):
                                    status_indicators += "🖱️ "
                                if message.get('replied'):
                                    status_indicators += "💬 "
                                
                                # Create preview (first 2 lines)
                                preview = ""
                                if content:
                                    lines = content.split('\n')
                                    preview_lines = [line.strip() for line in lines[:2] if line.strip()]
                                    preview = ' '.join(preview_lines)
                                    if len(preview) > 100:
                                        preview = preview[:100] + "..."
                                
                                st.markdown(f"""
                                <div style="background: #e3f2fd; padding: 10px; border-radius: 8px; margin: 8px 0; border-left: 4px solid #2196f3;">
                                📤 <strong>Sent to {selected_contact['name']}</strong> {status_indicators}<br>
                                <strong>{subject}</strong><br>
                                <small style="color: #666;">{date_str}</small><br>
                                <small style="color: #888; font-style: italic;">{preview}</small>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Expandable full email content
                                if content:
                                    with st.expander(f"📄 View Full Email"):
                                        st.text_area(
                                            "Email Content",
                                            value=content,
                                            height=400,
                                            disabled=True,
                                            label_visibility="collapsed",
                                            key=f"email_content_{i}_{selected_contact['email']}"
                                        )
                                        
                                        # Copy button
                                        if st.button(f"📋 Copy Email", key=f"copy_{i}"):
                                            st.code(content, language="text")
                                            st.success("📋 Email content displayed above - select all and copy!")
                            
                            elif message['type'] == 'received':
                                # Show received responses
                                with st.container():
                                    st.markdown(f"""
                                    <div style="background: #f1f8e9; padding: 10px; border-radius: 8px; margin: 8px 0 16px 40px; border-left: 4px solid #4caf50;">
                                    📥 <strong>Response from {selected_contact['name']}</strong><br>
                                    <strong>{subject}</strong><br>
                                    <small style="color: #666;">{date_str}</small><br>
                                    <em>{content[:200]}{'...' if len(content) > 200 else ''}</em>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    # Show full response if longer
                                    if len(content) > 200:
                                        with st.expander(f"📄 View Full Response"):
                                            st.text_area(
                                                "Response Content",
                                                value=content,
                                                height=200,
                                                disabled=True,
                                                label_visibility="collapsed",
                                                key=f"response_content_{i}_{selected_contact['email']}"
                                            )
                    else:
                        st.info(f"No email conversation found with {selected_contact['name']}")
                else:
                    st.info(f"No emails sent to {selected_contact['name']} yet")
                    
            except FileNotFoundError:
                st.warning("⚠️ Email tracking files not found. Start sending emails via the Email Generator to see conversation history here.")
            except Exception as e:
                st.error(f"❌ Error loading email conversation: {e}")
                # Fallback to old system
                st.info("Using fallback email tracking...")

if __name__ == "__main__":
    st.set_page_config(
        page_title="Club Contacts", 
        page_icon="👥",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    club_contacts_page() 