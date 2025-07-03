import streamlit as st
import pandas as pd
import sqlite3
from src.config import *

def cost_analytics_page(personalizer):
    """Cost analytics and visualization page"""
    st.header("💰 Cost Analytics Dashboard")
    
    try:
        # Get total costs
        total_costs = personalizer.get_total_costs()
        
        if total_costs['total_emails'] == 0:
            st.info("📊 No emails generated yet. Generate some emails to see cost analytics.")
            return
        
        # Summary metrics
        st.subheader("📈 Overall Cost Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("💰 Total Spent", f"${total_costs['total_cost']:.6f}")
        with col2:
            st.metric("📧 Total Emails", total_costs['total_emails'])
        with col3:
            avg_cost = total_costs['total_cost'] / total_costs['total_emails']
            st.metric("📊 Avg Cost/Email", f"${avg_cost:.6f}")
        with col4:
            # Estimate remaining cost for all clubs
            status_df = personalizer.get_all_clubs_status()
            remaining_clubs = len(status_df[status_df['status'] == 'Not Generated'])
            est_remaining = remaining_clubs * avg_cost
            st.metric("📈 Est. Remaining", f"${est_remaining:.4f}")
        
        # Cost breakdown
        st.subheader("🔍 Cost Breakdown by Model")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🔍 O3 Search Costs", f"${total_costs['search_cost']:.6f}")
            if total_costs['total_cost'] > 0:
                search_percentage = (total_costs['search_cost'] / total_costs['total_cost']) * 100
                st.caption(f"{search_percentage:.1f}% of total cost")
        
        with col2:
            st.metric("✨ GPT-4.1-nano Content", f"${total_costs['content_cost']:.6f}")
            if total_costs['total_cost'] > 0:
                content_percentage = (total_costs['content_cost'] / total_costs['total_cost']) * 100
                st.caption(f"{content_percentage:.1f}% of total cost")
        
        with col3:
            st.metric("🌐 Web Search Costs", f"${total_costs['web_search_cost']:.6f}")
            if total_costs['total_cost'] > 0:
                web_percentage = (total_costs['web_search_cost'] / total_costs['total_cost']) * 100
                st.caption(f"{web_percentage:.1f}% of total cost")
        
        # Model pricing information
        st.subheader("💡 Model Pricing Information")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**O3 Pricing:**")
            st.info(f"• Input: ${PRICING['o3']['input']:.2f} per 1M tokens\n• Cached Input: ${PRICING['o3']['cached_input']:.2f} per 1M tokens\n• Output: ${PRICING['o3']['output']:.2f} per 1M tokens")
        
        with col2:
            st.markdown("**GPT-4.1-nano Pricing:**")
            st.info(f"• Input: ${PRICING['gpt-4.1-nano']['input']:.3f} per 1M tokens\n• Cached Input: ${PRICING['gpt-4.1-nano']['cached_input']:.3f} per 1M tokens\n• Output: ${PRICING['gpt-4.1-nano']['output']:.3f} per 1M tokens")
        
        st.info(f"🌐 **Web Search Cost:** ${WEB_SEARCH_COST_PER_QUERY:.3f} per query (${WEB_SEARCH_COST_PER_1K_CALLS:.2f} per 1K calls)")
        
        # Detailed cost analysis from database
        st.subheader("📋 Detailed Cost Analysis")
        
        conn = sqlite3.connect(personalizer.db_path)
        detailed_df = pd.read_sql_query('''
            SELECT 
                club_name,
                search_cost,
                content_cost,
                web_search_cost,
                total_cost,
                email_sent_date,
                created_at
            FROM sent_emails
            ORDER BY total_cost DESC
        ''', conn)
        conn.close()
        
        if not detailed_df.empty:
            # Format for display
            display_df = detailed_df.copy()
            display_df['search_cost'] = display_df['search_cost'].apply(lambda x: f"${x:.6f}")
            display_df['content_cost'] = display_df['content_cost'].apply(lambda x: f"${x:.6f}")
            display_df['web_search_cost'] = display_df['web_search_cost'].apply(lambda x: f"${x:.6f}")
            display_df['total_cost'] = display_df['total_cost'].apply(lambda x: f"${x:.6f}")
            display_df['status'] = display_df['email_sent_date'].apply(
                lambda x: "📤 Sent" if x else "📝 Generated"
            )
            display_df = display_df.drop(['email_sent_date'], axis=1)
            
            # Rename columns for better display
            display_df.columns = [
                'Club Name', 'O3 Search Cost', 'GPT-4.1-nano Cost', 
                'Web Search Cost', 'Total Cost', 'Created At', 'Status'
            ]
            
            st.dataframe(display_df, use_container_width=True)
            
            # Cost distribution analysis
            st.subheader("📊 Cost Distribution Analysis")
            
            cost_data = detailed_df['total_cost']
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("💹 Highest Cost", f"${cost_data.max():.6f}")
                highest_club = detailed_df.loc[cost_data.idxmax(), 'club_name']
                st.caption(f"Club: {highest_club}")
            
            with col2:
                st.metric("💰 Lowest Cost", f"${cost_data.min():.6f}")
                lowest_club = detailed_df.loc[cost_data.idxmin(), 'club_name']
                st.caption(f"Club: {lowest_club}")
            
            with col3:
                st.metric("📈 Median Cost", f"${cost_data.median():.6f}")
                std_dev = cost_data.std()
                st.caption(f"Std Dev: ${std_dev:.6f}")
        
        # Cost projections
        st.subheader("🔮 Cost Projections")
        
        # Get remaining clubs count
        status_df = personalizer.get_all_clubs_status()
        remaining_clubs = len(status_df[status_df['status'] == 'Not Generated'])
        
        if remaining_clubs > 0:
            st.markdown(f"**Remaining clubs to process:** {remaining_clubs}")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Conservative Estimate**")
                conservative_cost = remaining_clubs * 0.001  # $0.001 per email
                st.metric("Est. Cost", f"${conservative_cost:.4f}")
                st.caption("Based on minimum expected cost")
            
            with col2:
                st.markdown("**Average-based Estimate**")
                avg_based_cost = remaining_clubs * avg_cost
                st.metric("Est. Cost", f"${avg_based_cost:.4f}")
                st.caption("Based on current average")
            
            with col3:
                st.markdown("**High-end Estimate**")
                high_end_cost = remaining_clubs * 0.01  # $0.01 per email
                st.metric("Est. Cost", f"${high_end_cost:.4f}")
                st.caption("Worst-case scenario")
        
        # Cost optimization tips
        st.subheader("💡 Cost Optimization Tips")
        
        # Calculate efficiency metrics
        if total_costs['total_cost'] > 0:
            search_ratio = total_costs['search_cost'] / total_costs['total_cost']
            content_ratio = total_costs['content_cost'] / total_costs['total_cost']
            web_ratio = total_costs['web_search_cost'] / total_costs['total_cost']
            
            tips = []
            
            if search_ratio > 0.7:
                tips.append("🔍 **O3 Search costs are high** - Consider optimizing search prompts for efficiency")
            
            if content_ratio > 0.3:
                tips.append("✨ **GPT-4.1-nano costs are significant** - Review content generation prompts for conciseness")
            
            if web_ratio > 0.2:
                tips.append("🌐 **Web search costs are notable** - Consider caching search results for similar clubs")
            
            if avg_cost > 0.005:
                tips.append("💰 **Average cost per email is high** - Review prompt engineering to reduce token usage")
            
            if not tips:
                tips.append("✅ **Cost distribution looks optimal** - Current configuration is cost-efficient")
            
            for tip in tips:
                st.info(tip)
        
        # Export option
        st.subheader("📤 Export Cost Data")
        if st.button("📊 Download Cost Report as CSV"):
            csv_data = detailed_df.to_csv(index=False)
            st.download_button(
                label="💾 Download CSV",
                data=csv_data,
                file_name=f"email_cost_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
    except Exception as e:
        st.error(f"Error loading cost analytics: {e}")
        st.info("💡 Make sure you have generated some emails to see cost analytics.") 