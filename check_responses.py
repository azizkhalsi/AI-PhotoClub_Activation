#!/usr/bin/env python3
"""
Email Response Checker
Checks for new email responses via Brevo API and saves them permanently.
Can be run manually or scheduled with cron.
"""

import sys
import os
import time
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from response_manager import ResponseManager
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

def main():
    """Main function to check for responses"""
    print("🔍 Photo Club Response Checker")
    print("=" * 40)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Initialize response manager
        response_manager = ResponseManager()
        
        # Check Brevo availability
        if response_manager.brevo_available:
            print("✅ Brevo API connection successful")
        else:
            print("⚠️ Brevo API not available - only manual responses will be processed")
        
        # Run response check
        result = response_manager.run_response_check()
        
        print("\n📊 Results:")
        print(f"   New responses found: {result['new_responses_found']}")
        print(f"   Total responses in system: {result['total_responses']}")
        print(f"   Unprocessed responses: {result['unprocessed_count']}")
        print(f"   Check duration: {result['duration']:.2f} seconds")
        
        # Show recent responses
        stats = response_manager.get_response_stats()
        recent_responses = stats.get('recent_responses', [])
        
        if recent_responses:
            print(f"\n📬 Recent Responses ({len(recent_responses)}):")
            for response in recent_responses:
                club_name = response['club_name']
                email_type = response['email_type']
                response_type = response['response_type'].replace('_', ' ').title()
                response_date = response['response_date'][:10]
                
                print(f"   • {club_name} - {email_type} ({response_type}) on {response_date}")
        
        # Show unprocessed responses
        unprocessed = response_manager.get_unprocessed_responses()
        if unprocessed:
            print(f"\n⚠️ Unprocessed Responses ({len(unprocessed)}):")
            for response in unprocessed[:5]:  # Show first 5
                club_name = response['club_name']
                email_type = response['email_type']
                response_date = response['response_date'][:10]
                
                print(f"   • {club_name} - {email_type} ({response_date})")
                
            if len(unprocessed) > 5:
                print(f"   ... and {len(unprocessed) - 5} more")
        
        print(f"\n✅ Response check completed successfully")
        
        # Return appropriate exit code
        return 0 if result['success'] else 1
        
    except Exception as e:
        print(f"\n❌ Error during response check: {e}")
        return 1

def show_help():
    """Show help information"""
    print("""
Photo Club Response Checker

USAGE:
    python check_responses.py

DESCRIPTION:
    Checks for new email responses from photography clubs via the Brevo API.
    Saves responses permanently to CSV files and updates club status tracking.

FEATURES:
    • Fetches email events from Brevo API
    • Detects potential responses based on email opens/clicks
    • Saves responses to data/email_responses.csv
    • Updates club status tracking automatically
    • Shows statistics and unprocessed responses

SCHEDULING:
    You can run this script periodically using cron:
    
    # Check for responses every 30 minutes
    */30 * * * * cd /path/to/project && python check_responses.py
    
    # Check for responses daily at 9 AM
    0 9 * * * cd /path/to/project && python check_responses.py

FILES CREATED:
    • data/email_responses.csv - Permanent response storage
    • data/email_tracking.csv - Email send/receive tracking
    • data/email_conversations.csv - Conversation threads
    
REQUIREMENTS:
    • Brevo API key configured in .env file
    • Contact and status CSV files present
    • Internet connection for API calls
""")

if __name__ == "__main__":
    # Check for help flag
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        show_help()
        sys.exit(0)
    
    # Run the response checker
    exit_code = main()
    sys.exit(exit_code) 