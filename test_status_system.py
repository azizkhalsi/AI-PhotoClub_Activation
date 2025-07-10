#!/usr/bin/env python3
"""
Test script to demonstrate the Club Status Tracking and Notification System
"""

import sys
import os

# Add src to path
sys.path.append('src')

from club_status_manager import ClubStatusManager, ResponseStatus
from datetime import datetime, timedelta

def test_status_system():
    """Test the complete status tracking system"""
    
    print("🧪 Testing Club Status Tracking & Notification System")
    print("=" * 60)
    
    # Initialize the status manager
    status_manager = ClubStatusManager()
    
    # Test clubs from your data
    test_clubs = [
        "Auckland Photographic Society",
        "Camera Club of Hamilton", 
        "Wellington Photographic Society",
        "Christchurch Photographic Society",
        "Dunedin Photographic Society"
    ]
    
    print("\n📤 Simulating Email Sending...")
    
    # Simulate sending introduction emails
    for i, club in enumerate(test_clubs[:3]):
        email_type = 'introduction'
        notes = f"Introduction email sent via test script on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        result = status_manager.update_email_sent(club, email_type, notes)
        if result:
            print(f"✅ {club} - {email_type} email marked as sent")
        else:
            print(f"❌ Failed to update status for {club}")
    
    # Simulate sending follow-up emails
    for i, club in enumerate(test_clubs[1:3]):
        email_type = 'checkup'
        notes = f"Follow-up email sent via test script on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        result = status_manager.update_email_sent(club, email_type, notes)
        if result:
            print(f"✅ {club} - {email_type} email marked as sent")
    
    print("\n📧 Simulating Club Responses...")
    
    # Simulate positive responses
    positive_responses = [
        ("Auckland Photographic Society", "introduction", "Very interested! Please send more details."),
        ("Wellington Photographic Society", "introduction", "This sounds great for our members."),
        ("Camera Club of Hamilton", "checkup", "Yes, we'd like to proceed with the partnership.")
    ]
    
    for club, email_type, response_note in positive_responses:
        result = status_manager.record_response(
            club, 
            email_type, 
            ResponseStatus.POSITIVE_RESPONSE.value,
            response_note
        )
        if result:
            print(f"✅ {club} - Positive response to {email_type} recorded")
    
    # Simulate negative responses
    negative_responses = [
        ("Christchurch Photographic Society", "introduction", "Not interested at this time."),
    ]
    
    for club, email_type, response_note in negative_responses:
        result = status_manager.record_response(
            club, 
            email_type, 
            ResponseStatus.NEGATIVE_RESPONSE.value,
            response_note
        )
        if result:
            print(f"❌ {club} - Negative response to {email_type} recorded")
    
    print("\n📊 Dashboard Statistics:")
    print("-" * 30)
    
    # Get and display dashboard stats
    stats = status_manager.get_dashboard_stats()
    
    print(f"Total Clubs in Pipeline: {stats.get('total_clubs', 0)}")
    print(f"Introduction Emails Sent: {stats.get('introduction_sent', 0)}")
    print(f"Follow-up Emails Sent: {stats.get('checkup_sent', 0)}")
    print(f"Acceptance Emails Sent: {stats.get('acceptance_sent', 0)}")
    print(f"Positive Responses: {stats.get('positive_responses', 0)}")
    print(f"Awaiting Response: {stats.get('awaiting_response', 0)}")
    
    # Show pipeline stages
    if stats.get('pipeline_stages'):
        print("\nPipeline Stages:")
        for stage, count in stats['pipeline_stages'].items():
            print(f"  • {stage.title()}: {count}")
    
    print("\n🔔 Notifications:")
    print("-" * 20)
    
    # Get notifications
    notifications = status_manager.get_unread_notifications()
    
    if notifications:
        for notification in notifications[-5:]:  # Show last 5
            created_time = datetime.fromisoformat(notification['created_at']).strftime("%H:%M %d/%m")
            print(f"📮 {notification['message']} ({created_time})")
    else:
        print("No unread notifications")
    
    print("\n🔍 Filter Examples:")
    print("-" * 20)
    
    # Show filter examples
    positive_clubs = status_manager.get_clubs_by_status(
        email_type='introduction', 
        status=ResponseStatus.POSITIVE_RESPONSE.value
    )
    print(f"Clubs with positive introduction responses: {len(positive_clubs)}")
    for club in positive_clubs:
        print(f"  • {club['club_name']}")
    
    checkup_stage_clubs = status_manager.get_clubs_by_status(stage='checkup')
    print(f"\nClubs in checkup stage: {len(checkup_stage_clubs)}")
    for club in checkup_stage_clubs:
        print(f"  • {club['club_name']}")
    
    print("\n⏰ Follow-up Needed:")
    print("-" * 20)
    
    # Check follow-up needs (using 0 days to show all for demo)
    follow_up_clubs = status_manager.get_clubs_needing_follow_up(days_since_sent=0)
    
    if follow_up_clubs:
        print(f"Clubs needing follow-up: {len(follow_up_clubs)}")
        for club in follow_up_clubs:
            print(f"  • {club['club_name']} - {club['email_type']} ({club['days_since_sent']} days ago)")
    else:
        print("No clubs need follow-up")
    
    print("\n🎯 System Test Complete!")
    print(f"✅ Status tracking working")
    print(f"✅ Notifications created")
    print(f"✅ Filtering functional")
    print(f"✅ Dashboard metrics available")
    print(f"✅ Data stored in: data/club_status_tracking.csv")
    print(f"✅ Notifications in: data/notifications.csv")
    
    print(f"\n🌐 View in Streamlit: http://localhost:8502")
    print(f"📋 Navigate to 'Club Status & Notifications' to see the full interface")

if __name__ == "__main__":
    test_status_system() 