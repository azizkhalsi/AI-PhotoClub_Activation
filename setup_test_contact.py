#!/usr/bin/env python3
"""
Setup Test Contact Script
Clean fake data and add Aziz Khalsi as test contact for email response testing
"""

import pandas as pd
import os
from datetime import datetime

def clean_fake_data():
    """Remove all fake data from data files"""
    print("🧹 Cleaning fake data...")
    
    # Clean club status tracking
    if os.path.exists("data/club_status_tracking.csv"):
        df = pd.read_csv("data/club_status_tracking.csv")
        # Remove fake clubs
        df = df[~df['club_name'].isin(['AUSTRALIAN PHOTOGRAPHIC SOCIETY', 'WELLINGTON PHOTOGRAPHY CLUB'])]
        df.to_csv("data/club_status_tracking.csv", index=False)
        print("  ✓ Cleaned club status tracking")
    
    # Clean email tracking
    if os.path.exists("data/email_tracking.csv"):
        df = pd.read_csv("data/email_tracking.csv")
        # Remove fake clubs
        df = df[~df['club_name'].isin(['AUSTRALIAN PHOTOGRAPHIC SOCIETY', 'WELLINGTON PHOTOGRAPHY CLUB'])]
        df.to_csv("data/email_tracking.csv", index=False)
        print("  ✓ Cleaned email tracking")
    
    # Clean email conversations
    if os.path.exists("data/email_conversations.csv"):
        df = pd.read_csv("data/email_conversations.csv")
        # Remove fake clubs
        df = df[~df['club_name'].isin(['AUSTRALIAN PHOTOGRAPHIC SOCIETY', 'WELLINGTON PHOTOGRAPHY CLUB'])]
        df.to_csv("data/email_conversations.csv", index=False)
        print("  ✓ Cleaned email conversations")
    
    # Clean notifications
    if os.path.exists("data/notifications.csv"):
        df = pd.read_csv("data/notifications.csv")
        # Remove fake clubs
        df = df[~df['club_name'].isin(['AUSTRALIAN PHOTOGRAPHIC SOCIETY', 'WELLINGTON PHOTOGRAPHY CLUB'])]
        df.to_csv("data/notifications.csv", index=False)
        print("  ✓ Cleaned notifications")

def add_test_contact():
    """Add Aziz Khalsi as a test contact to the contacts CSV"""
    print("👤 Adding Aziz Khalsi as test contact...")
    
    # Load existing contacts
    contacts_df = pd.read_csv("test_results_20250701_092437.csv")
    
    # Create new test contact entry
    test_contact = {
        'Club': 'DXO TEST PHOTOGRAPHY CLUB',
        'Country': 'France',
        'Website': 'https://dxo.com',
        'Name': 'Aziz Khalsi',
        'Role': 'President',
        'Email': 'akhalsi@dxo.com',
        'Phone': '',
        'Source': 'Test Setup',
        'Search_Summary': 'Test contact for email response verification',
        'search_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_cost': '$0.0000',
        'time_taken_seconds': '0.0'
    }
    
    # Remove any existing test contact first
    contacts_df = contacts_df[contacts_df['Club'] != 'DXO TEST PHOTOGRAPHY CLUB']
    
    # Add the new test contact
    new_row = pd.DataFrame([test_contact])
    contacts_df = pd.concat([contacts_df, new_row], ignore_index=True)
    
    # Save updated contacts
    contacts_df.to_csv("test_results_20250701_092437.csv", index=False)
    print("  ✓ Added DXO TEST PHOTOGRAPHY CLUB with Aziz Khalsi as contact")

def main():
    print("🚀 Setting up test contact and cleaning fake data...")
    print("=" * 50)
    
    # Clean up existing fake data
    clean_fake_data()
    
    print()
    
    # Add test contact
    add_test_contact()
    
    print()
    print("✅ Setup complete!")
    print("📧 You can now generate and send emails to akhalsi@dxo.com for testing")
    print("🧪 Test club: DXO TEST PHOTOGRAPHY CLUB")
    print("👤 Contact: Aziz Khalsi (President)")

if __name__ == "__main__":
    main()
