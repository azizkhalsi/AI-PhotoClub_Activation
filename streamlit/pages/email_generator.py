import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime, timedelta
import time
from typing import Dict, Optional

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

try:
    from club_research_manager import ClubResearchManager
    from email_personalizer import EmailPersonalizer
    from brevo_email_service import BrevoEmailService
    from club_status_manager import ClubStatusManager
except ImportError as e:
    st.error(f"Import error: {e}")
    st.error("Please make sure all dependencies are installed and files are in the correct location.")
    st.stop()

def email_generator_page():
    """Clean, full-width email generator interface"""
    
    # Custom CSS for better design and info icons
    st.markdown("""
    <style>
    /* Hide sidebar completely */
    .css-1d391kg {display: none !important;}
    .css-1cypcdb {display: none !important;}
    section[data-testid="stSidebar"] {display: none !important;}
    
    .info-tooltip {
        cursor: pointer;
        color: #007AFF;
        font-size: 16px;
        padding: 4px;
        border-radius: 50%;
        border: 1px solid #007AFF;
        width: 20px;
        height: 20px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: white;
        margin-left: 8px;
    }
    .info-tooltip:hover {
        background: #007AFF;
        color: white;
    }
    .save-notification {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        color: #155724;
    }
    .conversation-message {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
    }
    .sent-message {
        background: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .received-message {
        background: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    .metrics-container {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 16px;
        margin: 16px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    try:
        # Initialize managers
        email_personalizer = EmailPersonalizer()
        status_manager = ClubStatusManager()
        
        # Initialize Brevo service (optional)
        try:
            brevo_service = BrevoEmailService()
            # Test connection
            test_result = brevo_service.test_connection()
            if test_result['success']:
                brevo_available = True
                st.success("✅ Brevo email service connected successfully!")
            else:
                brevo_available = False
                st.error(f"❌ Brevo connection failed: {test_result['error']}")
                st.error("📧 Email sending disabled. Please check your API key in Brevo dashboard.")
                brevo_service = None
        except ValueError as e:
            st.warning("⚠️ Brevo API key not found. Email sending disabled. Set BREVO_API_KEY environment variable to enable.")
            brevo_service = None
            brevo_available = False
        except Exception as e:
            st.error(f"❌ Brevo service error: {str(e)}")
            brevo_service = None
            brevo_available = False
        
        # Load clubs data
        clubs_df = email_personalizer.load_clubs_data()
        
        if clubs_df.empty:
            st.error("No clubs data found. Please check the CSV file.")
            return
        
        # Full width layout - Left side: Selection, Right side: Email content
        col_selection, col_content = st.columns([1, 2.5])
        
        with col_selection:
            # Club Selection Section
            header_col, info_col = st.columns([4, 1])
            with header_col:
                st.markdown("### 📍 Club Selection")
            with info_col:
                if st.button("?", key="club_info", help="Click for help", 
                           type="secondary", use_container_width=False):
                    st.session_state['show_club_help'] = not st.session_state.get('show_club_help', False)
            
            if st.session_state.get('show_club_help', False):
                st.info("💡 Select a photography club from the list. The system will automatically research the club if needed (first time takes ~60s).")
            
            club_names = sorted(clubs_df['Club'].unique())
            selected_club = st.selectbox(
                "Choose a photography club",
                [""] + club_names,
                key="club_selection",
                label_visibility="collapsed"
            )
            
            if selected_club:
                st.markdown("---")
                
                # Email Type Selection
                header_col2, info_col2 = st.columns([4, 1])
                with header_col2:
                    st.markdown("### ✉️ Email Type")
                with info_col2:
                    if st.button("?", key="email_type_info", help="Click for help", 
                               type="secondary", use_container_width=False):
                        st.session_state['show_email_help'] = not st.session_state.get('show_email_help', False)
                
                if st.session_state.get('show_email_help', False):
                    st.info("""
                    💡 **Email Types:**  
                    📩 **Introduction**: First contact with new clubs  
                    📞 **Follow-up**: Check progress with existing contacts  
                    🤝 **Partnership**: Formal partnership proposals
                    """)
                
                email_types = {
                    "introduction": "📩 Introduction Email",
                    "checkup": "📞 Follow-up Email", 
                    "acceptance": "🤝 Partnership Email"
                }
                
                email_type = st.selectbox(
                    "Select email type",
                    list(email_types.keys()),
                    format_func=lambda x: email_types[x],
                    key="email_type_selection",
                    label_visibility="collapsed"
                )
                
                st.markdown("---")
                
                # Generation Status Info
                research_data = email_personalizer.get_club_research(selected_club, email_type)
                if research_data:
                    st.success("⚡ Ready for fast generation (research cached)")
                else:
                    st.warning("🔍 First generation includes research (~60 seconds)")
                
                # Check if email already exists
                email_exists, existing_email_data = email_personalizer.check_email_sent(selected_club, email_type)
                
                # Main Generate Button - only show if email doesn't exist
                if not email_exists:
                    if st.button(
                        f"🚀 Generate {email_types[email_type]}",
                        type="primary",
                        use_container_width=True,
                        key=f"generate_{selected_club}_{email_type}"
                    ):
                        st.session_state['generating'] = True
                        st.rerun()
                else:
                    st.success("✅ Email already generated!")
                    if st.button(
                        f"🔄 Regenerate {email_types[email_type]}",
                        type="secondary",
                        use_container_width=True,
                        key=f"regenerate_{selected_club}_{email_type}"
                    ):
                        st.session_state['generating'] = True
                        st.rerun()
                
                # Send via Brevo Section (under generate section)
                if email_exists or f'email_content_{selected_club}_{email_type}' in st.session_state:
                    if brevo_available and brevo_service:
                        st.markdown("---")
                        st.markdown("### 📤 Send Email")
                        
                        # Load contacts data for club
                        try:
                            # Custom CSV parsing to handle field count mismatches
                            import csv
                            contacts_data = []
                            
                            with open('test_results_20250701_092437.csv', 'r', encoding='utf-8') as f:
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
                            
                            contacts_df = pd.DataFrame(contacts_data)
                            club_contacts = contacts_df[contacts_df['Club'] == selected_club]
                            
                            if not club_contacts.empty:
                                contact_options = []
                                for _, contact in club_contacts.iterrows():
                                    # Skip rows with missing email or name
                                    if pd.isna(contact['Email']) or pd.isna(contact['Name']) or contact['Email'] == '' or contact['Name'] == '':
                                        continue
                                    
                                    contact_display = f"{contact['Name']} ({contact['Role']}) - {contact['Email']}"
                                    contact_options.append({
                                        'display': contact_display,
                                        'name': contact['Name'],
                                        'email': contact['Email'],
                                        'role': contact['Role']
                                    })
                                
                                if contact_options:
                                    selected_contact_idx = st.selectbox(
                                        "Select contact to send to:",
                                        range(len(contact_options)),
                                        format_func=lambda x: contact_options[x]['display'],
                                        key=f"contact_select_{selected_club}_{email_type}"
                                    )
                                    
                                    selected_contact = contact_options[selected_contact_idx]
                                else:
                                    st.warning("⚠️ No valid contacts found for this club (missing email addresses).")
                                    selected_contact = None
                                
                                if selected_contact:
                                    col_send, col_info = st.columns([1, 2])
                                    with col_send:
                                        if st.button("📤 Send via Brevo", 
                                                   type="primary", 
                                                   use_container_width=True,
                                                   key=f"send_brevo_{selected_club}_{email_type}"):
                                            # Get current email content
                                            if email_exists and existing_email_data:
                                                email_content = existing_email_data.get('generated_email', '')
                                            else:
                                                email_content = st.session_state.get(f'email_content_{selected_club}_{email_type}', '')
                                            
                                            if email_content:
                                                with st.spinner("Sending email..."):
                                                    try:
                                                        send_result = brevo_service.send_email(
                                                            to_email=selected_contact['email'],
                                                            to_name=selected_contact['name'],
                                                            subject=f"DxO Labs Partnership - {email_type.title()}",
                                                            content=email_content,
                                                            club_name=selected_club,
                                                            contact_role=selected_contact['role'],
                                                            email_type=email_type
                                                        )
                                                        
                                                        if send_result['success']:
                                                            st.success(f"✅ Email sent successfully to {selected_contact['name']}!")
                                                            # Update status manager
                                                            status_manager.update_email_sent(
                                                                selected_club, 
                                                                email_type, 
                                                                f"Email sent to {selected_contact['name']} via Brevo on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                                                            )
                                                            # Mark as sent in email personalizer
                                                            email_personalizer.mark_email_as_sent(selected_club, email_type)
                                                        else:
                                                            st.error(f"❌ Failed to send email: {send_result['error']}")
                                                    except Exception as e:
                                                        st.error(f"❌ Error sending email: {e}")
                                            else:
                                                st.error("❌ No email content found to send")
                                    
                                    with col_info:
                                        st.info(f"📧 Will send to: {selected_contact['name']} ({selected_contact['email']})")
                            
                            else:
                                st.warning("⚠️ No contacts found for this club in the contacts database.")
                        
                        except FileNotFoundError:
                            st.warning("⚠️ Contacts data file not found. Please ensure 'test_results_20250701_092437.csv' exists.")
                        except Exception as e:
                            st.error(f"❌ Error loading contacts: {e}")
                    
                    elif not brevo_available:
                        st.markdown("---")
                        st.info("📧 **Email sending disabled.** Set BREVO_API_KEY environment variable to enable direct sending.")
        
        with col_content:
            # Always show email section header
            header_col3, info_col3 = st.columns([4, 1])
            with header_col3:
                st.markdown("### 📧 Your Email")
            with info_col3:
                if st.button("?", key="email_edit_info", help="Click for help", 
                           type="secondary", use_container_width=False):
                    st.session_state['show_edit_help'] = not st.session_state.get('show_edit_help', False)
            
            if st.session_state.get('show_edit_help', False):
                st.info("💡 Edit the email content below, save changes, and mark as sent when you've sent it to the club.")
            
            # Determine current email content
            current_email = ""
            email_data = None
            
            if selected_club and email_type:
                # Check if we're in generation mode
                if st.session_state.get('generating', False):
                    with st.spinner("Generating your personalized email..."):
                        try:
                            start_time = time.time()
                            complete_email, personalized_content, research, costs = email_personalizer.generate_personalized_email(
                                selected_club, email_type, auto_research=True
                            )
                            end_time = time.time()
                            
                            # Save the generated email
                            email_personalizer.save_generated_email(
                                selected_club, personalized_content, complete_email, costs, email_type
                            )
                            
                            # Store in session state
                            st.session_state[f'email_content_{selected_club}_{email_type}'] = complete_email
                            st.session_state['generation_time'] = end_time - start_time
                            st.session_state['generating'] = False
                            st.session_state['just_generated'] = True
                            st.success(f"✅ Email generated in {end_time - start_time:.1f} seconds!")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Generation failed: {e}")
                            st.session_state['generating'] = False
                
                # Check for existing email
                email_sent, email_data = email_personalizer.check_email_sent(selected_club, email_type)
                
                if email_sent and email_data:
                    current_email = email_data.get('generated_email', '')
                elif f'email_content_{selected_club}_{email_type}' in st.session_state:
                    current_email = st.session_state[f'email_content_{selected_club}_{email_type}']
            
            # Show email status only if we have content
            if current_email:
                if email_data and email_data.get('email_sent_date') and str(email_data.get('email_sent_date')) not in ['nan', 'None', '']:
                    st.success("✅ Email has been sent")
                elif st.session_state.get('just_generated', False):
                    st.info("📝 New email generated - ready to send!")
                    st.session_state['just_generated'] = False
                    
                # Show save notification if just saved
                if st.session_state.get('email_just_saved', False):
                    st.markdown("""
                    <div class="save-notification">
                        ✅ <strong>Email saved successfully!</strong> Your changes have been stored.
                    </div>
                    """, unsafe_allow_html=True)
                    st.session_state['email_just_saved'] = False
            
            # Use a unique key that doesn't depend on club/email type selection
            editor_key = "main_email_editor"
            if selected_club and email_type:
                editor_key = f"email_editor_{selected_club}_{email_type}"
            
            # Email editor - much taller to see full email without scrolling
            edited_email = st.text_area(
                "Email content",
                value=current_email,
                height=800,  # Much taller to see full email
                key=editor_key,
                label_visibility="collapsed",
                placeholder="Your personalized email will appear here once you select a club and generate..."
            )
            
            # Action Buttons - only show if we have content and selections
            if current_email and selected_club and email_type:
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    # Save button (only show if content changed)
                    if edited_email != current_email:
                        if st.button("💾 Save Changes", use_container_width=True, 
                                   key=f"save_{selected_club}_{email_type}", type="primary"):
                            if email_personalizer.save_email_modification(selected_club, edited_email, email_type):
                                st.session_state['email_just_saved'] = True
                                st.session_state[f'email_content_{selected_club}_{email_type}'] = edited_email
                                st.rerun()
                            else:
                                st.error("❌ Failed to save changes")
                
                with col_b:
                    if st.button("🔄 Regenerate", use_container_width=True, 
                               key=f"regen_{selected_club}_{email_type}"):
                        st.session_state['generating'] = True
                        st.rerun()
                
                with col_c:
                    if st.button("📋 Copy Email", use_container_width=True, 
                               key=f"copy_{selected_club}_{email_type}"):
                        st.code(edited_email, language="text")
                        st.info("📋 Email content displayed above - select all and copy!")
                
                # Mark as sent button - separate row if needed
                if not (email_data and email_data.get('email_sent_date')):
                    if st.button("📤 Mark as Sent", use_container_width=True, 
                               key=f"mark_sent_{selected_club}_{email_type}", type="secondary"):
                        email_personalizer.mark_email_as_sent(selected_club, email_type)
                        # Track in status manager
                        status_manager.update_email_sent(selected_club, email_type, f"Email sent via email generator on {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                        st.success("✅ Marked as sent and tracked!")
                        st.rerun()
                
                # Generation time info
                if 'generation_time' in st.session_state:
                    gen_time = st.session_state['generation_time']
                    if gen_time > 30:
                        st.caption(f"⚡ Generated in {gen_time:.1f}s (included club research)")
                    else:
                        st.caption(f"⚡ Generated in {gen_time:.1f}s (used cached research)")
                
                # Email metrics and conversation (if Brevo is available)
                if brevo_available and brevo_service:
                    st.markdown("---")
                    
                    # Get club metrics
                    club_metrics = brevo_service.get_email_metrics(selected_club)
                    
                    if club_metrics.get('total_sent', 0) > 0:
                        st.markdown('<div class="metrics-container">', unsafe_allow_html=True)
                        st.markdown("#### 📊 Email Metrics for " + selected_club)
                        
                        # Metrics display
                        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                        with col_m1:
                            st.metric("📤 Sent", club_metrics.get('total_sent', 0))
                        with col_m2:
                            st.metric("👀 Opened", club_metrics.get('total_opened', 0))
                        with col_m3:
                            st.metric("💬 Replied", club_metrics.get('total_replied', 0))
                        with col_m4:
                            reply_rate = club_metrics.get('reply_rate', 0)
                            st.metric("📈 Reply Rate", f"{reply_rate:.1f}%")
                        
                        # Email type breakdown
                        if club_metrics.get('by_email_type'):
                            st.markdown("**📋 By Email Type:**")
                            for email_t, count in club_metrics['by_email_type'].items():
                                st.write(f"• {email_t.title()}: {count}")
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Show recent activity
                    if club_metrics.get('recent_activity'):
                        with st.expander("📜 Recent Email Activity", expanded=False):
                            for activity in club_metrics['recent_activity'][-5:]:  # Last 5 activities
                                sent_time = activity.get('sent_datetime', '')
                                if sent_time:
                                    try:
                                        sent_time = datetime.fromisoformat(sent_time).strftime("%Y-%m-%d %H:%M")
                                    except:
                                        pass
                                
                                st.markdown(f"**📧 {activity.get('email_type', 'Unknown').title()}** to {activity.get('contact_name', 'Unknown')} ({sent_time})")
                                if activity.get('replied_datetime'):
                                    st.markdown("  ✅ *Replied*")
                                elif activity.get('opened_datetime'):
                                    st.markdown("  👀 *Opened*")
                                else:
                                    st.markdown("  📤 *Sent*")
                
                elif brevo_available:
                    st.info("📊 Send emails via the 'Club Contacts' page to see metrics and conversation history!")
            
            elif not selected_club:
                st.info("👈 Select a club and email type to get started")
            elif not current_email:
                st.info("🚀 Click 'Generate' to create your personalized email")
    
    except Exception as e:
        st.error(f"❌ Application error: {e}")
        st.error("Please check your configuration and try again.")

if __name__ == "__main__":
    # Set page config for full width
    st.set_page_config(
        page_title="Email Generator",
        page_icon="📧",
        layout="wide",  # Full width layout
        initial_sidebar_state="collapsed"  # No sidebar
    )
    
    email_generator_page() 