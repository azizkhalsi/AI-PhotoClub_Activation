import streamlit as st
import pandas as pd

def club_status_page(personalizer):
    """Club status dashboard with cost tracking"""
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
        
        # Cost metrics
        total_cost = status_df['total_cost'].sum()
        avg_cost = status_df[status_df['total_cost'] > 0]['total_cost'].mean() if len(status_df[status_df['total_cost'] > 0]) > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("💰 Total Cost", f"${total_cost:.4f}")
        with col2:
            st.metric("💰 Avg Cost/Email", f"${avg_cost:.4f}")
        with col3:
            emails_with_cost = len(status_df[status_df['total_cost'] > 0])
            st.metric("📊 Emails with Cost Data", emails_with_cost)
        with col4:
            if emails_with_cost > 0:
                est_remaining_cost = (total_clubs - emails_with_cost) * avg_cost
                st.metric("📈 Est. Remaining Cost", f"${est_remaining_cost:.4f}")
        
        # Progress bar
        progress = (sent_count + generated_count) / total_clubs if total_clubs > 0 else 0
        st.progress(progress, text=f"Progress: {progress:.1%} of clubs have emails generated")
        
        # Filter options
        st.subheader("🔍 Filter Clubs")
        col1, col2, col3 = st.columns(3)
        
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
        
        with col3:
            cost_filter = st.selectbox(
                "Filter by Cost:",
                options=["All", "With Cost Data", "No Cost Data", "High Cost (>$0.01)", "Low Cost (<$0.001)"]
            )
        
        # Apply filters
        filtered_df = status_df.copy()
        
        if status_filter != "All":
            filtered_df = filtered_df[filtered_df['status'] == status_filter]
        
        if country_filter != "All":
            filtered_df = filtered_df[filtered_df['Country'] == country_filter]
        
        if cost_filter != "All":
            if cost_filter == "With Cost Data":
                filtered_df = filtered_df[filtered_df['total_cost'] > 0]
            elif cost_filter == "No Cost Data":
                filtered_df = filtered_df[filtered_df['total_cost'] == 0]
            elif cost_filter == "High Cost (>$0.01)":
                filtered_df = filtered_df[filtered_df['total_cost'] > 0.01]
            elif cost_filter == "Low Cost (<$0.001)":
                filtered_df = filtered_df[(filtered_df['total_cost'] > 0) & (filtered_df['total_cost'] < 0.001)]
        
        # Display filtered data
        st.subheader(f"Clubs ({len(filtered_df)} of {total_clubs})")
        
        # Style the dataframe
        def style_status(val):
            if val == 'Sent':
                return 'background-color: #d4edda; color: #155724'
            elif val == 'Generated':
                return 'background-color: #fff3cd; color: #856404'
            else:
                return 'background-color: #f8d7da; color: #721c24'
        
        def style_cost(val):
            if val > 0.01:
                return 'background-color: #f8d7da; color: #721c24'  # High cost - red
            elif val > 0.001:
                return 'background-color: #fff3cd; color: #856404'  # Medium cost - yellow
            elif val > 0:
                return 'background-color: #d4edda; color: #155724'  # Low cost - green
            else:
                return ''  # No cost data
        
        # Format the dataframe for display
        display_df = filtered_df.copy()
        display_df['total_cost'] = display_df['total_cost'].apply(lambda x: f"${x:.6f}" if x > 0 else "No data")
        
        styled_df = display_df.style.applymap(style_status, subset=['status'])
        
        # Show styled dataframe
        st.dataframe(styled_df, use_container_width=True)
        
        # Bulk actions
        if not filtered_df.empty:
            st.subheader("⚡ Bulk Actions")
            
            # Show cost estimate for bulk generation
            not_generated_clubs = filtered_df[filtered_df['status'] == 'Not Generated']
            if not not_generated_clubs.empty:
                estimated_cost = len(not_generated_clubs) * avg_cost if avg_cost > 0 else len(not_generated_clubs) * 0.003  # fallback estimate
                st.info(f"💰 Estimated cost for generating {len(not_generated_clubs)} remaining emails: ${estimated_cost:.4f}")
            
            selected_clubs = st.multiselect(
                "Select clubs for bulk actions:",
                options=filtered_df['Club'].tolist(),
                help="Select multiple clubs to perform bulk actions"
            )
            
            if selected_clubs:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("🚀 Generate Emails for Selected Clubs"):
                        generate_bulk_emails(personalizer, selected_clubs)
                
                with col2:
                    if st.button("📤 Mark Selected as Sent"):
                        mark_bulk_as_sent(personalizer, selected_clubs)
                
                with col3:
                    # Show estimated cost for selected clubs
                    selected_not_generated = [club for club in selected_clubs 
                                            if club in filtered_df[filtered_df['status'] == 'Not Generated']['Club'].values]
                    if selected_not_generated:
                        est_cost = len(selected_not_generated) * (avg_cost if avg_cost > 0 else 0.003)
                        st.metric("💰 Est. Cost", f"${est_cost:.4f}")
        
    except Exception as e:
        st.error(f"Error loading club status: {e}")

def generate_bulk_emails(personalizer, club_names):
    """Generate emails for multiple clubs with cost tracking"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_clubs = len(club_names)
    total_cost = 0.0
    successful_generations = 0
    
    for i, club_name in enumerate(club_names):
        try:
            status_text.text(f"Processing {club_name}... ({i+1}/{total_clubs})")
            
            # Check if email already exists
            email_exists, _ = personalizer.check_email_sent(club_name)
            
            if not email_exists:
                email, content, research, costs = personalizer.generate_personalized_email(club_name)
                personalizer.save_generated_email(club_name, content, email, costs)
                total_cost += costs['total_cost']
                successful_generations += 1
                st.success(f"✅ Generated email for {club_name} (Cost: ${costs['total_cost']:.4f})")
            else:
                st.info(f"ℹ️ Email already exists for {club_name}")
            
            progress_bar.progress((i + 1) / total_clubs)
            
        except Exception as e:
            st.error(f"❌ Error generating email for {club_name}: {e}")
    
    status_text.text("Bulk generation completed!")
    st.success(f"✅ Processed {total_clubs} clubs")
    st.info(f"💰 Total cost for {successful_generations} new emails: ${total_cost:.4f}")
    
    if successful_generations > 0:
        avg_cost = total_cost / successful_generations
        st.info(f"📊 Average cost per email: ${avg_cost:.4f}")

def mark_bulk_as_sent(personalizer, club_names):
    """Mark multiple emails as sent"""
    success_count = 0
    for club_name in club_names:
        try:
            personalizer.mark_email_as_sent(club_name)
            success_count += 1
        except Exception as e:
            st.error(f"Error marking {club_name} as sent: {e}")
    
    if success_count > 0:
        st.success(f"📤 Marked {success_count} emails as sent!")
    
    if success_count < len(club_names):
        st.warning(f"⚠️ {len(club_names) - success_count} emails could not be marked as sent") 