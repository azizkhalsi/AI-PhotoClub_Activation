import streamlit as st
import sys
import os

def email_generator_page(personalizer):
    """Email generation page focused on core functionality"""
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
    
    # Club selection with enhanced info
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
            st.info(f"🌍 **Country:** {club_info.get('Country', 'N/A')}")
            if club_info.get('Website'):
                st.info(f"🌐 **Website:** {club_info['Website']}")
    
    # Check if email already exists
    if selected_club:
        email_exists, email_data = personalizer.check_email_sent(selected_club)
        
        if email_exists:
            st.success("✅ Email already generated for this club!")
            
            # Show status with proper date handling
            if email_data.get('email_sent_date') and str(email_data['email_sent_date']) != 'nan':
                # Safely handle the date formatting
                date_str = str(email_data['email_sent_date'])
                if len(date_str) >= 10:
                    st.info(f"📤 **Status:** Sent on {date_str[:10]}")
                else:
                    st.info(f"📤 **Status:** Sent on {date_str}")
            else:
                # Show generation date instead of "up to date" message
                if email_data.get('created_at'):
                    creation_date = str(email_data['created_at'])
                    if len(creation_date) >= 10:
                        st.info(f"📝 **Generated on:** {creation_date[:10]}")
                    else:
                        st.info(f"📝 **Generated on:** {creation_date}")
                else:
                    st.warning("📝 **Status:** Generated but not sent")
            
            # Email editing section
            st.markdown("### 📝 Email Content")
            
            # Initialize session state for email editing
            if f"email_content_{selected_club}" not in st.session_state:
                st.session_state[f"email_content_{selected_club}"] = email_data['generated_email']
                st.session_state[f"original_email_{selected_club}"] = email_data['generated_email']
            
            # Check if email has been modified
            is_modified = st.session_state[f"email_content_{selected_club}"] != st.session_state[f"original_email_{selected_club}"]
            
            # Email editor with modification indicator
            if is_modified:
                st.warning("✏️ **Email has been modified** - Don't forget to save your changes!")
            
            edited_email = st.text_area(
                "Email Content:",
                value=st.session_state[f"email_content_{selected_club}"],
                height=400,
                key=f"email_editor_{selected_club}",
                help="Edit the email content as needed."
            )
            
            # Update session state when text area changes
            st.session_state[f"email_content_{selected_club}"] = edited_email
            
            # Action buttons with better layout (removed "✅ Sent" button)
            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
            
            with col1:
                if st.button("💾 Save Changes", type="primary", disabled=not is_modified, help="Save your email modifications"):
                    save_email_changes(personalizer, selected_club, edited_email)
            
            with col2:
                if st.button("↩️ Undo", type="secondary", disabled=not is_modified, help="Revert to original email"):
                    st.session_state[f"email_content_{selected_club}"] = st.session_state[f"original_email_{selected_club}"]
                    st.rerun()
            
            with col3:
                if st.button("🗑️ Delete", type="secondary", help="Delete this email record"):
                    delete_email_record(personalizer, selected_club)
            
            with col4:
                if st.button("🔄 Regenerate", type="secondary", help="Generate a completely new email"):
                    regenerate_email(personalizer, selected_club)
            
            # Mark as sent button (only show if not already sent)
            if not email_data.get('email_sent_date') or str(email_data.get('email_sent_date')) == 'nan':
                if st.button("📤 Mark as Sent", type="primary", help="Mark email as sent"):
                    personalizer.mark_email_as_sent(selected_club)
                    st.success("✅ Email marked as sent!")
                    st.rerun()
            
            # Copy section
            if st.button("📋 Copy to Clipboard", help="Copy email content for external use"):
                st.code(edited_email, language="text")
                st.success("📋 Email content displayed above - you can now copy it!")
        
        else:
            st.info("🆕 No email generated yet for this club.")
            
            # Generate new email
            if st.button("🚀 Generate Personalized Email", type="primary"):
                generate_new_email(personalizer, selected_club)

def generate_new_email(personalizer, club_name):
    """Generate a new personalized email with simplified progress tracking"""
    try:
        with st.spinner(f"🔍 Researching {club_name} and generating email..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("🔍 Researching club...")
            progress_bar.progress(33)
            
            email, content, research, costs = personalizer.generate_personalized_email(club_name)
            
            status_text.text("✨ Generating personalized content...")
            progress_bar.progress(66)
            
            personalizer.save_generated_email(club_name, content, email, costs)
            
            status_text.text("💾 Saving email...")
            progress_bar.progress(100)
        
        st.success("✅ Email generated successfully!")
        
        # Initialize session state for the new email
        st.session_state[f"email_content_{club_name}"] = email
        st.session_state[f"original_email_{club_name}"] = email
        
        # Show the generated email with editing capabilities
        st.markdown("### 📧 Generated Email")
        
        edited_new_email = st.text_area(
            "Email Content:",
            value=email,
            height=400,
            key=f"new_email_editor_{club_name}",
            help="You can edit the generated email before marking it as sent."
        )
        
        # Update session state
        st.session_state[f"email_content_{club_name}"] = edited_new_email
        
        # Action buttons for new email
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Save Changes", key="save_new", type="primary"):
                save_email_changes(personalizer, club_name, edited_new_email)
        
        with col2:
            if st.button("📋 Copy Email", key="copy_new"):
                st.code(edited_new_email, language="text")
                st.success("📋 Email content displayed above!")
        
        with col3:
            if st.button("📤 Mark as Sent", key="mark_sent_new", type="primary"):
                personalizer.mark_email_as_sent(club_name)
                st.success("✅ Email marked as sent!")
                st.rerun()
        
        st.rerun()
        
    except Exception as e:
        st.error(f"Error generating email: {e}")

def save_email_changes(personalizer, club_name, modified_email, show_success=True):
    """Save modified email content"""
    try:
        # Update the email content in the database
        result = personalizer.save_email_modification(club_name, modified_email)
        
        if result:
            # Update the session state to reflect saved changes
            st.session_state[f"original_email_{club_name}"] = modified_email
            if show_success:
                st.success("✅ Email changes saved successfully!")
        else:
            st.error("❌ Failed to save email changes")
            
    except Exception as e:
        st.error(f"Error saving email changes: {e}")

def delete_email_record(personalizer, club_name):
    """Delete email record with confirmation"""
    # Show confirmation dialog
    if st.button("⚠️ Confirm Delete", type="secondary", key="confirm_delete"):
        try:
            success = personalizer.delete_email_record(club_name)
            if success:
                # Clear session state for this club
                keys_to_remove = [key for key in st.session_state.keys() if club_name in key]
                for key in keys_to_remove:
                    del st.session_state[key]
                
                st.success("✅ Email record deleted successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to delete email record")
        except Exception as e:
            st.error(f"Error deleting email record: {e}")
    
    else:
        st.warning("⚠️ Click 'Confirm Delete' to permanently delete this email record")

def regenerate_email(personalizer, club_name):
    """Regenerate email with confirmation"""
    # Show confirmation dialog
    if st.button("⚠️ Confirm Regenerate", type="secondary", key="confirm_regen"):
        try:
            # Delete existing email first
            personalizer.delete_email_record(club_name)
            
            # Clear session state
            keys_to_remove = [key for key in st.session_state.keys() if club_name in key]
            for key in keys_to_remove:
                del st.session_state[key]
            
            st.success("✅ Existing email deleted. Generating new email...")
            
            # Generate new email
            generate_new_email(personalizer, club_name)
            
        except Exception as e:
            st.error(f"Error regenerating email: {e}")
    
    else:
        st.warning("⚠️ Click 'Confirm Regenerate' to create a completely new email (this will delete the current one)") 