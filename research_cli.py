#!/usr/bin/env python3
"""
Command-line interface for Club Research Manager.

This script provides easy access to research functionality:
- Research specific clubs
- View research statistics
- List all researched clubs
- Bulk research operations
"""

import argparse
import os
import sys
import time
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from club_research_manager import ClubResearchManager
from email_personalizer import EmailPersonalizer

def research_club(args):
    """Research a specific club"""
    manager = ClubResearchManager()
    
    print(f"🔍 Researching club: {args.club}")
    
    # Load clubs data to get club details
    clubs_df = manager.load_clubs_data()
    club_data = clubs_df[clubs_df['Club'].str.contains(args.club, case=False, na=False)]
    
    if club_data.empty:
        print(f"❌ Club '{args.club}' not found in database")
        print("Available clubs (first 10):")
        for club in clubs_df['Club'].head(10):
            print(f"   - {club}")
        return
    
    # Use first match if multiple found
    club_info = club_data.iloc[0]
    club_name = club_info['Club']
    website = club_info.get('Website', '')
    country = club_info.get('Country', '')
    
    print(f"📋 Club found: {club_name}")
    print(f"   Country: {country}")
    print(f"   Website: {website}")
    
    # Check if already researched
    if manager.is_research_cached(club_name):
        print(f"✅ Research already cached for {club_name}")
        if not args.force:
            print("Use --force to re-research this club")
            return
        else:
            print("🔄 Forcing new research...")
    
    # Perform research
    start_time = time.time()
    try:
        research_data, costs = manager.research_club_with_o3(club_name, website, country)
        end_time = time.time()
        
        print(f"✅ Research completed in {end_time - start_time:.1f} seconds")
        print(f"💰 Cost: ${costs['total_cost']:.4f}")
        
        # Show research sections
        print(f"\n📄 Research sections:")
        print(f"   Introduction: {len(research_data['introduction_research'])} chars")
        print(f"   Checkup: {len(research_data['checkup_research'])} chars")
        print(f"   Acceptance: {len(research_data['acceptance_research'])} chars")
        
        if args.show_preview:
            print(f"\n📝 Introduction research preview:")
            preview = research_data['introduction_research'][:300]
            print(f"{preview}...")
        
    except Exception as e:
        print(f"❌ Research failed: {e}")

def show_statistics(args):
    """Show research statistics"""
    manager = ClubResearchManager()
    stats = manager.get_research_statistics()
    
    print("📊 Research Statistics")
    print("=" * 40)
    print(f"Total researched clubs: {stats['total_researched_clubs']}")
    print(f"Valid research: {stats['valid_research_count']}")
    print(f"Expired research: {stats['expired_research_count']}")
    print(f"Total research cost: ${stats['total_research_cost']:.4f}")
    
    if stats['total_researched_clubs'] > 0:
        hit_rate = (stats['valid_research_count'] / stats['total_researched_clubs']) * 100
        print(f"Cache hit rate: {hit_rate:.1f}%")

def list_clubs(args):
    """List all researched clubs"""
    manager = ClubResearchManager()
    researched_clubs = manager.get_all_researched_clubs()
    
    if not researched_clubs:
        print("📭 No research data found")
        return
    
    print(f"📋 Researched Clubs ({len(researched_clubs)})")
    print("=" * 60)
    
    # Sort by validity and then by name
    researched_clubs.sort(key=lambda x: (not x['is_valid'], x['club_name']))
    
    for club in researched_clubs:
        status_icon = "✅" if club['is_valid'] else "❌"
        status_text = "Valid" if club['is_valid'] else "Expired"
        days_left = club['days_until_expiry'] if club['is_valid'] else 0
        
        print(f"{status_icon} {club['club_name']} ({club['country']})")
        print(f"   Status: {status_text} ({days_left} days left)")
        print(f"   Cost: ${club['research_cost']:.4f}")
        print(f"   Researched: {club['researched_at'][:10]}")
        
        if args.show_details:
            # Show email generation status
            personalizer = EmailPersonalizer()
            for email_type in ['introduction', 'checkup', 'acceptance']:
                email_exists, _ = personalizer.check_email_sent(club['club_name'], email_type)
                status = "✅" if email_exists else "❌"
                print(f"   {email_type.capitalize()} email: {status}")
        
        print()

def bulk_research(args):
    """Perform bulk research on multiple clubs"""
    manager = ClubResearchManager()
    
    # Load clubs data
    clubs_df = manager.load_clubs_data()
    if clubs_df.empty:
        print("❌ No clubs data available")
        return
    
    # Find unresearched clubs
    unresearched_clubs = []
    for _, club_row in clubs_df.iterrows():
        club_name = club_row['Club']
        if not manager.is_research_cached(club_name):
            unresearched_clubs.append({
                'name': club_name,
                'website': club_row.get('Website', ''),
                'country': club_row.get('Country', '')
            })
    
    if not unresearched_clubs:
        print("✅ All clubs in database are already researched!")
        return
    
    # Limit to requested number
    clubs_to_research = unresearched_clubs[:args.count]
    
    print(f"🔍 Starting bulk research for {len(clubs_to_research)} clubs...")
    print(f"Total unresearched clubs available: {len(unresearched_clubs)}")
    
    total_cost = 0.0
    success_count = 0
    
    for i, club in enumerate(clubs_to_research, 1):
        print(f"\n[{i}/{len(clubs_to_research)}] Researching {club['name']}...")
        
        try:
            start_time = time.time()
            research_data, costs = manager.research_club_with_o3(
                club['name'], club['website'], club['country']
            )
            end_time = time.time()
            
            total_cost += costs['total_cost']
            success_count += 1
            
            print(f"   ✅ Completed in {end_time - start_time:.1f}s (${costs['total_cost']:.4f})")
            
            # Small delay to avoid rate limiting
            if i < len(clubs_to_research):
                time.sleep(2)
                
        except Exception as e:
            print(f"   ❌ Failed: {e}")
    
    print(f"\n📊 Bulk Research Summary:")
    print(f"   Successfully researched: {success_count}/{len(clubs_to_research)}")
    print(f"   Total cost: ${total_cost:.4f}")
    print(f"   Average cost per club: ${total_cost/success_count:.4f}" if success_count > 0 else "")

def generate_emails(args):
    """Generate emails for researched clubs"""
    personalizer = EmailPersonalizer()
    manager = ClubResearchManager()
    
    # Get clubs with valid research
    researched_clubs = manager.get_all_researched_clubs()
    valid_clubs = [club for club in researched_clubs if club['is_valid']]
    
    if not valid_clubs:
        print("❌ No clubs with valid research found")
        return
    
    clubs_to_process = valid_clubs[:args.count] if args.count else valid_clubs
    email_type = args.email_type
    
    print(f"📧 Generating {email_type} emails for {len(clubs_to_process)} clubs...")
    
    generated_count = 0
    total_cost = 0.0
    
    for i, club in enumerate(clubs_to_process, 1):
        club_name = club['club_name']
        print(f"\n[{i}/{len(clubs_to_process)}] Processing {club_name}...")
        
        # Check if email already exists
        email_exists, _ = personalizer.check_email_sent(club_name, email_type)
        if email_exists and not args.force:
            print(f"   ⏭️ {email_type.capitalize()} email already exists (use --force to regenerate)")
            continue
        
        try:
            # Generate email
            complete_email, personalized_content, research, costs = personalizer.generate_personalized_email(club_name, email_type)
            
            # Save email
            personalizer.save_generated_email(
                club_name, personalized_content, complete_email, costs, email_type
            )
            
            generated_count += 1
            total_cost += costs['total_cost']
            
            print(f"   ✅ Generated ({len(complete_email)} chars, ${costs['total_cost']:.4f})")
            
            if args.show_preview:
                print(f"   Preview: {personalized_content[:100]}...")
                
        except Exception as e:
            print(f"   ❌ Failed: {e}")
    
    print(f"\n📧 Email Generation Summary:")
    print(f"   Successfully generated: {generated_count}/{len(clubs_to_process)}")
    print(f"   Total generation cost: ${total_cost:.4f}")

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description='Club Research Manager CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s research "Tokyo Photography Club"
  %(prog)s research "Berlin" --show-preview
  %(prog)s stats
  %(prog)s list --show-details
  %(prog)s bulk --count 5
  %(prog)s emails introduction --count 3 --show-preview
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Research command
    research_parser = subparsers.add_parser('research', help='Research a specific club')
    research_parser.add_argument('club', help='Club name to research')
    research_parser.add_argument('--force', action='store_true', help='Force re-research even if cached')
    research_parser.add_argument('--show-preview', action='store_true', help='Show research preview')
    
    # Statistics command
    stats_parser = subparsers.add_parser('stats', help='Show research statistics')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all researched clubs')
    list_parser.add_argument('--show-details', action='store_true', help='Show detailed information')
    
    # Bulk research command
    bulk_parser = subparsers.add_parser('bulk', help='Bulk research multiple clubs')
    bulk_parser.add_argument('--count', type=int, default=5, help='Number of clubs to research (default: 5)')
    
    # Email generation command
    emails_parser = subparsers.add_parser('emails', help='Generate emails for researched clubs')
    emails_parser.add_argument('email_type', choices=['introduction', 'checkup', 'acceptance'], 
                             help='Type of email to generate')
    emails_parser.add_argument('--count', type=int, help='Number of emails to generate')
    emails_parser.add_argument('--force', action='store_true', help='Regenerate existing emails')
    emails_parser.add_argument('--show-preview', action='store_true', help='Show email preview')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    print(f"🚀 Club Research Manager CLI")
    print(f"Command: {args.command}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    try:
        if args.command == 'research':
            research_club(args)
        elif args.command == 'stats':
            show_statistics(args)
        elif args.command == 'list':
            list_clubs(args)
        elif args.command == 'bulk':
            bulk_research(args)
        elif args.command == 'emails':
            generate_emails(args)
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 