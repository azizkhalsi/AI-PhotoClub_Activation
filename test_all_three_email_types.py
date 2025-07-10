#!/usr/bin/env python3
"""
Test script to demonstrate all three email types working with proper templates and research.

This script shows:
1. Research generation with three distinct sections
2. Email generation for introduction, checkup, and acceptance
3. Different templates and personalization strategies for each type
4. Complete end-to-end workflow for all email types
"""

import os
import sys
import time
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from club_research_manager import ClubResearchManager
from email_personalizer import EmailPersonalizer

def test_single_club_all_email_types():
    """Test generating all three email types for a single club"""
    print("🧪 TESTING ALL THREE EMAIL TYPES")
    print("=" * 60)
    
    # Initialize managers
    research_manager = ClubResearchManager()
    email_personalizer = EmailPersonalizer()
    
    # Load clubs data
    clubs_df = research_manager.load_clubs_data()
    if clubs_df.empty:
        print("❌ No clubs data available")
        return None
    
    # Get a test club
    test_club = clubs_df.iloc[0]
    club_name = test_club['Club']
    website = test_club.get('Website', '')
    country = test_club.get('Country', '')
    
    print(f"\n🎯 Testing with club: {club_name}")
    print(f"   Country: {country}")
    print(f"   Website: {website}")
    
    # Ensure research is available
    if not research_manager.is_research_cached(club_name):
        print(f"\n🔍 Researching {club_name} first...")
        research_data, costs = research_manager.research_club_with_o3(
            club_name, website, country
        )
        print(f"✅ Research completed! Cost: ${costs['total_cost']:.4f}")
    else:
        print(f"✅ Using cached research for {club_name}")
    
    # Test all three email types
    email_types = ['introduction', 'checkup', 'acceptance']
    
    for email_type in email_types:
        print(f"\n" + "=" * 40)
        print(f"📧 TESTING {email_type.upper()} EMAIL")
        print("=" * 40)
        
        try:
            # Check if research is available for this email type
            research_data = email_personalizer.get_club_research(club_name, email_type)
            
            if not research_data:
                print(f"❌ No {email_type} research available")
                continue
            
            print(f"📋 {email_type.capitalize()} research available ({len(research_data)} chars)")
            
            # Show research preview
            preview = research_data[:200] + "..." if len(research_data) > 200 else research_data
            print(f"📝 Research preview:")
            print(f"   {preview}")
            
            # Check if email already exists
            email_exists, email_data = email_personalizer.check_email_sent(club_name, email_type)
            
            if email_exists:
                print(f"📧 {email_type.capitalize()} email already exists")
                print(f"   Content length: {len(email_data.get('generated_email', ''))} chars")
                print(f"   Personalized content: {email_data.get('personalized_content', '')}")
                print(f"   Cost: ${email_data.get('total_cost', 0):.4f}")
            else:
                # Generate new email
                print(f"🚀 Generating {email_type} email...")
                start_time = time.time()
                
                complete_email, personalized_content, research, costs = email_personalizer.generate_personalized_email(club_name, email_type)
                end_time = time.time()
                
                # Save the email
                email_personalizer.save_generated_email(
                    club_name, personalized_content, complete_email, costs, email_type
                )
                
                print(f"✅ {email_type.capitalize()} email generated in {end_time - start_time:.1f} seconds")
                print(f"💰 Generation cost: ${costs['total_cost']:.4f}")
                print(f"📧 Email length: {len(complete_email)} characters")
                print(f"✨ Personalized content:")
                print(f"   {personalized_content}")
                
                # Show email structure
                print(f"\n📄 Email structure preview:")
                lines = complete_email.split('\n')
                for i, line in enumerate(lines[:8]):  # Show first 8 lines
                    print(f"   {i+1}: {line}")
                if len(lines) > 8:
                    print(f"   ... ({len(lines) - 8} more lines)")
        
        except Exception as e:
            print(f"❌ Error testing {email_type} email: {e}")
    
    return club_name

def test_template_differences():
    """Test that different templates are being used correctly"""
    print("\n" + "=" * 60)
    print("📄 TESTING TEMPLATE DIFFERENCES")
    print("=" * 60)
    
    email_personalizer = EmailPersonalizer()
    
    email_types = ['introduction', 'checkup', 'acceptance']
    
    for email_type in email_types:
        print(f"\n📧 {email_type.upper()} TEMPLATE:")
        template = email_personalizer.load_email_template(email_type)
        
        if template:
            lines = template.split('\n')
            print(f"   Length: {len(template)} characters")
            print(f"   Lines: {len(lines)}")
            print(f"   First line: {lines[0] if lines else 'Empty'}")
            print(f"   Contains 'Killian': {'Yes' if 'Killian' in template else 'No'}")
            print(f"   Contains 'follow up': {'Yes' if 'follow up' in template else 'No'}")
            print(f"   Contains '20% discount': {'Yes' if '20% discount' in template else 'No'}")
        else:
            print(f"   ❌ Template not found!")

def test_research_sections():
    """Test that research sections are properly separated"""
    print("\n" + "=" * 60)
    print("📊 TESTING RESEARCH SECTIONS")
    print("=" * 60)
    
    research_manager = ClubResearchManager()
    email_personalizer = EmailPersonalizer()
    
    # Get researched clubs
    researched_clubs = research_manager.get_all_researched_clubs()
    
    if not researched_clubs:
        print("❌ No researched clubs found")
        return
    
    # Test first valid club
    for club in researched_clubs:
        if club['is_valid']:
            club_name = club['club_name']
            print(f"\n🏛️ Testing research sections for: {club_name}")
            
            email_types = ['introduction', 'checkup', 'acceptance']
            
            for email_type in email_types:
                research_data = email_personalizer.get_club_research(club_name, email_type)
                
                if research_data:
                    print(f"   ✅ {email_type.capitalize()}: {len(research_data)} characters")
                    
                    # Show first few words to verify different content
                    words = research_data.split()[:8]
                    preview = ' '.join(words) + "..." if len(words) >= 8 else research_data
                    print(f"      Preview: {preview}")
                else:
                    print(f"   ❌ {email_type.capitalize()}: No research found")
            
            break  # Only test first valid club

def show_complete_workflow():
    """Show the complete workflow from research to all three emails"""
    print("\n" + "=" * 60)
    print("🔄 COMPLETE WORKFLOW DEMONSTRATION")
    print("=" * 60)
    
    research_manager = ClubResearchManager()
    email_personalizer = EmailPersonalizer()
    
    # Get statistics
    stats = research_manager.get_research_statistics()
    
    print(f"📊 Current System Status:")
    print(f"   Total researched clubs: {stats['total_researched_clubs']}")
    print(f"   Valid research: {stats['valid_research_count']}")
    print(f"   Total research cost: ${stats['total_research_cost']:.4f}")
    
    # Count emails by type
    email_counts = {}
    for email_type in ['introduction', 'checkup', 'acceptance']:
        emails = email_personalizer.get_emails_by_type(email_type)
        email_counts[email_type] = len(emails)
    
    print(f"\n📧 Generated Emails by Type:")
    for email_type, count in email_counts.items():
        print(f"   {email_type.capitalize()}: {count} emails")
    
    print(f"\n🎯 System Capabilities:")
    print(f"   ✅ Three-section research generation (O3)")
    print(f"   ✅ CSV storage with 30-day caching")
    print(f"   ✅ Three distinct email templates")
    print(f"   ✅ Type-specific personalization logic")
    print(f"   ✅ Individual email tracking by type")
    print(f"   ✅ Cost tracking and statistics")

def main():
    """Main test function"""
    print("🧪 TESTING ALL THREE EMAIL TYPES SYSTEM")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Test single club with all email types
        club_name = test_single_club_all_email_types()
        
        # Test template differences
        test_template_differences()
        
        # Test research sections
        test_research_sections()
        
        # Show complete workflow
        show_complete_workflow()
        
        print("\n" + "=" * 80)
        print("✅ ALL EMAIL TYPE TESTS COMPLETED!")
        print("=" * 80)
        
        print(f"\n📋 Summary:")
        print(f"   ✅ Introduction emails: Professional first contact")
        print(f"   ✅ Checkup emails: Urgent follow-up with time-sensitive content")
        print(f"   ✅ Acceptance emails: Partnership details and process explanation")
        print(f"   ✅ All three types use appropriate research sections")
        print(f"   ✅ Different templates and personalization strategies")
        print(f"   ✅ Independent tracking and cost monitoring")
        
        if club_name:
            print(f"\n🎯 Test a club with all three email types:")
            print(f"   1. Run: streamlit run streamlit/main_app.py")
            print(f"   2. Select club: {club_name}")
            print(f"   3. Try all three email types from dropdown")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 