import streamlit as st
import sys
import os

def email_generator_page(personalizer):
    """Email generation page with cost tracking"""
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
            
            # Show cost and status
            col1, col2 = st.columns(2)
            with col1:
                if email_data['email_sent_date']:
                    st.info(f"📤 **Status:** Sent on {email_data['email_sent_date'][:10]}")
                else:
                    st.warning("📝 **Status:** Generated but not sent")
            
            with col2:
                if email_data.get('total_cost'):
                    st.metric("💰 Generation Cost", f"${email_data['total_cost']:.4f}")
                else:
                    st.info("💰 Cost not tracked")
            
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
                if st.button("📋 Copy Email", type="secondary"):
                    st.code(email_data['generated_email'])
                    st.info("📋 Email content displayed above for copying!")
        
        else:
            st.info("🆕 No email generated yet for this club.")
            
            # Estimated cost display
            st.markdown("### 💰 Estimated Costs")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("O3 Search", "~$0.001-0.005")
            with col2:
                st.metric("GPT-4o-mini Content", "~$0.0001-0.0005")
            with col3:
                st.metric("Web Search", "$0.001")
            with col4:
                st.metric("Total Est.", "~$0.0021-0.0056")
            
            # Generate new email
            if st.button("🚀 Generate Personalized Email", type="primary"):
                generate_new_email(personalizer, selected_club)

def generate_new_email(personalizer, club_name):
    """Generate a new personalized email with cost tracking"""
    try:
        with st.spinner(f"🔍 Step 1/3: Researching {club_name} with O3..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("🔍 Researching club with O3 and web search...")
            progress_bar.progress(33)
            
            email, content, research, costs = personalizer.generate_personalized_email(club_name)
            
            status_text.text("✨ Generated personalized content with GPT-4o-mini...")
            progress_bar.progress(66)
            
            personalizer.save_generated_email(club_name, content, email, costs)
            
            status_text.text("💾 Saving email to database...")
            progress_bar.progress(100)
        
        st.success("✅ Email generated successfully!")
        
        # Show cost breakdown
        st.markdown("### 💰 Generation Costs")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🔍 O3 Search", f"${costs['search_cost']:.6f}")
        with col2:
            st.metric("✨ GPT-4o-mini Content", f"${costs['content_cost']:.6f}")
        with col3:
            st.metric("🌐 Web Search", f"${costs['web_search_cost']:.6f}")
        with col4:
            st.metric("📊 Total Cost", f"${costs['total_cost']:.6f}")
        
        # Show the generated email
        st.subheader("📧 Generated Email")
        st.text_area("Email Content:", value=email, height=400, disabled=True)
        
        # Show research and personalization details
        col1, col2 = st.columns(2)
        
        with col1:
            with st.expander("🔍 O3 Research Summary"):
                st.write(research)
        
        with col2:
            with st.expander("✨ GPT-4o-mini Personalized Content"):
                st.write(content)
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📤 Mark as Sent", key="mark_sent_new"):
                personalizer.mark_email_as_sent(club_name)
                st.success("Email marked as sent!")
        
        with col2:
            if st.button("📋 Copy Email", key="copy_new"):
                st.code(email)
                st.info("📋 Email content displayed above for copying!")
        
        # Refresh the page to show updated status
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error generating email: {e}")
        if "model" in str(e).lower():
            st.info("💡 Note: Make sure you have access to the O3 model. You can update the models in the .env file.")

def regenerate_email(personalizer, club_name):
    """Regenerate email for a club"""
    try:
        with st.spinner(f"🔄 Regenerating email for {club_name}..."):
            email, content, research, costs = personalizer.generate_personalized_email(club_name)
            personalizer.save_generated_email(club_name, content, email, costs, mark_as_sent=False)
        
        st.success("✅ Email regenerated successfully!")
        st.info(f"💰 New generation cost: ${costs['total_cost']:.6f}")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error regenerating email: {e}") 