import openai
import pandas as pd
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import *

class CostTracker:
    """Track costs for different AI models and operations"""
    
    def __init__(self):
        self.costs = {
            'search_cost': 0.0,
            'content_cost': 0.0,
            'web_search_cost': 0.0,
            'total_cost': 0.0
        }
    
    def calculate_token_cost(self, model: str, input_tokens: int, output_tokens: int, cached_tokens: int = 0) -> float:
        """Calculate cost based on token usage including cached tokens"""
        if model not in PRICING:
            print(f"⚠️ Warning: Model '{model}' not found in pricing configuration")
            return 0.0
        
        # Calculate regular input cost (exclude cached tokens from regular input)
        regular_input_tokens = max(0, input_tokens - cached_tokens)
        input_cost = (regular_input_tokens / 1_000_000) * PRICING[model]['input']
        
        # Calculate cached input cost if applicable
        cached_cost = 0.0
        if cached_tokens > 0 and 'cached_input' in PRICING[model]:
            cached_cost = (cached_tokens / 1_000_000) * PRICING[model]['cached_input']
        
        # Calculate output cost
        output_cost = (output_tokens / 1_000_000) * PRICING[model]['output']
        
        total_cost = input_cost + cached_cost + output_cost
        
        # Log detailed token usage and costs
        print(f"📊 Token Usage for {model}:")
        print(f"   Input tokens: {input_tokens:,}")
        print(f"   Regular input tokens: {regular_input_tokens:,} (${input_cost:.6f})")
        if cached_tokens > 0:
            print(f"   Cached input tokens: {cached_tokens:,} (${cached_cost:.6f})")
        print(f"   Output tokens: {output_tokens:,} (${output_cost:.6f})")
        print(f"   Total cost: ${total_cost:.6f}")
        
        return total_cost
    
    def add_search_cost(self, input_tokens: int, output_tokens: int, cached_tokens: int = 0):
        """Add cost for O3 search operation"""
        cost = self.calculate_token_cost(SEARCH_MODEL, input_tokens, output_tokens, cached_tokens)
        self.costs['search_cost'] += cost
        self.costs['total_cost'] += cost
    
    def add_web_search_cost(self, num_queries: int = 1):
        """Add cost for web search operations"""
        cost = num_queries * WEB_SEARCH_COST_PER_QUERY
        self.costs['web_search_cost'] += cost
        self.costs['total_cost'] += cost
    
    def get_costs(self) -> Dict[str, float]:
        """Get all tracked costs"""
        return self.costs.copy()

class ClubResearchManager:
    """
    Manages club research using O3 web search and stores results in CSV format.
    Generates three distinct research sections for different email types.
    """
    
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in environment variables or .env file")
        
        try:
            self.openai_client = openai.OpenAI(
                api_key=OPENAI_API_KEY,
                timeout=60.0,
                max_retries=3,
            )
        except Exception as e:
            raise ValueError(f"Failed to initialize OpenAI client: {e}")
        
        self.research_csv_path = CLUBS_RESEARCH_CSV_PATH
        self.cache_expiry_days = 30
        self._initialize_research_csv()
    
    def _initialize_research_csv(self):
        """Initialize CSV file to store club research results"""
        if not os.path.exists(self.research_csv_path):
            research_df = pd.DataFrame(columns=[
                'club_name', 'country', 'website',
                'introduction_research', 'checkup_research', 'acceptance_research',
                'full_research_data', 'search_cost', 'web_search_cost', 'total_cost',
                'researched_at', 'expires_at', 'is_valid'
            ])
            research_df.to_csv(self.research_csv_path, index=False)
    
    def load_clubs_data(self) -> pd.DataFrame:
        """Load clubs data from CSV file"""
        try:
            df = pd.read_csv(
                CLUBS_CSV_PATH,
                encoding='utf-8',
                quotechar='"',
                escapechar='\\',
                on_bad_lines='skip',
                engine='python',
                skipinitialspace=True,
                doublequote=True,
                sep=','
            )
            
            print(f"✅ Loaded {len(df)} records from CSV")
            
            if 'Club' in df.columns:
                unique_clubs = df.groupby('Club').first().reset_index()
                print(f"✅ Found {len(unique_clubs)} unique clubs")
                return unique_clubs
            else:
                print(f"❌ 'Club' column not found in CSV. Available columns: {list(df.columns)}")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ Error loading clubs data: {e}")
            return pd.DataFrame()
    
    def is_research_cached(self, club_name: str) -> bool:
        """Check if club research is cached and still valid"""
        try:
            research_df = pd.read_csv(self.research_csv_path)
            club_research = research_df[research_df['club_name'] == club_name]
            
            if not club_research.empty:
                research_entry = club_research.iloc[0]
                expires_at = pd.to_datetime(research_entry['expires_at'])
                return datetime.now() < expires_at
            
            return False
        except:
            return False
    
    def get_cached_research(self, club_name: str) -> Optional[Dict]:
        """Get cached research for a club if valid"""
        try:
            research_df = pd.read_csv(self.research_csv_path)
            club_research = research_df[research_df['club_name'] == club_name]
            
            if not club_research.empty:
                research_entry = club_research.iloc[0]
                expires_at = pd.to_datetime(research_entry['expires_at'])
                
                if datetime.now() < expires_at:
                    print(f"🎯 Using cached research for {club_name}")
                    return {
                        'introduction_research': research_entry['introduction_research'],
                        'checkup_research': research_entry['checkup_research'],
                        'acceptance_research': research_entry['acceptance_research'],
                        'full_research_data': research_entry['full_research_data'],
                        'search_cost': research_entry.get('search_cost', 0.0),
                        'web_search_cost': research_entry.get('web_search_cost', 0.0),
                        'total_cost': research_entry.get('total_cost', 0.0),
                        'researched_at': research_entry['researched_at'],
                        'from_cache': True
                    }
                else:
                    print(f"⏰ Research expired for {club_name}")
                    # Clean up expired entry
                    research_df = research_df[research_df['club_name'] != club_name]
                    research_df.to_csv(self.research_csv_path, index=False)
            
            return None
        except Exception as e:
            print(f"⚠️ Error checking cached research: {e}")
            return None
    
    def research_club_with_o3(self, club_name: str, website: str = None, country: str = None) -> Tuple[Dict, Dict]:
        """Research club using O3 and return structured research data"""
        
        # Check cache first
        cached_research = self.get_cached_research(club_name)
        if cached_research:
            return cached_research, {
                'search_cost': cached_research['search_cost'],
                'web_search_cost': cached_research['web_search_cost'],
                'total_cost': cached_research['total_cost']
            }
        
        print(f"🔍 Performing new research for {club_name}")
        cost_tracker = CostTracker()
        cost_tracker.add_web_search_cost(1)
        
        search_query = f"photography club '{club_name}'"
        if country:
            search_query += f" {country}"
        if website:
            search_query += f" site:{website}"
        
        search_prompt = f"""
        You are a research assistant with web search capabilities. I need you to search the web and find specific, current information about the photography club "{club_name}".

        **IMPORTANT: Use web search to find real, current information about this specific club.**

        Search for and provide specific details about:
        1. **Recent Activities:** Latest exhibitions, photo walks, workshops, or competitions they've organized (with dates if possible)
        2. **Upcoming Events:** Any announced future events, meetings, or special projects
        3. **Photography Specialties:** What types of photography they focus on (landscape, portrait, street, wildlife, macro, etc.)
        4. **Notable Achievements:** Recent awards, recognition, or member accomplishments
        5. **Unique Characteristics:** What makes this club special or different from others
        6. **Community Projects:** Any community involvement, charity work, or local partnerships
        7. **Member Highlights:** Featured photographers or notable member work
        8. **Club History:** Founding date, milestones, or significant moments
        9. **Active Engagement:** Social media presence, online galleries, member participation
        10. **Educational Focus:** Workshops, tutorials, skill development programs
        11. **Club Structure:** Leadership, membership size, organization
        12. **Communication Channels:** How they reach members, preferred platforms
        
        Club details to help your search:
        - Name: {club_name}
        - Country: {country if country else 'Unknown'}
        - Website: {website if website else 'Not provided'}
        
        **CRITICAL:** Please search the web for this specific club and provide concrete findings. Don't provide generic information - I need specific details that prove genuine knowledge of this particular club.
        
        **FORMAT YOUR RESPONSE WITH THREE DISTINCT SECTIONS:**

        === INTRODUCTION EMAIL RESEARCH ===
        [Information for first contact email offering DxO discount]
        - Recent impressive activities or achievements that would catch their attention
        - Photography specialties that align with DxO software benefits
        - Unique club characteristics that show we've done our research
        - Community engagement that demonstrates their active membership
        - Specific recent events or projects that show their current activity level

        === CHECK-UP EMAIL RESEARCH ===
        [Information for follow-up email when they don't respond to introduction]
        - Upcoming events or deadlines where DxO tools could be valuable
        - Current challenges in their photography work that DxO solves
        - Seasonal activities or competitions coming up
        - Member growth or expansion activities
        - Time-sensitive opportunities that create urgency

        === ACCEPTANCE EMAIL RESEARCH ===
        [Information for when they accept our offer - explaining discount process]
        - Club structure and leadership contact information
        - Membership size and how members typically communicate
        - Existing partnerships or vendor relationships they have
        - How they typically handle member benefits or discounts
        - Best communication channels to reach all members
        - Member skill levels and most used photography techniques

        If you cannot find specific information about this exact club, clearly state that in each section and provide what general information you can find about photography clubs in their region, but be honest about the limitations.
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model=SEARCH_MODEL,
                messages=[
                    {"role": "system", "content": "You are a research assistant with web search capabilities. You must search the internet to find specific, current information about photography clubs and communities. Always use web search to find real, up-to-date information rather than relying on training data. Focus on finding concrete details like recent events, specific activities, and unique characteristics of each club. Structure your response with three distinct sections for different email types."},
                    {"role": "user", "content": search_prompt}
                ]
            )
            
            # Track costs
            if hasattr(response, 'usage') and response.usage:
                usage = response.usage
                input_tokens = getattr(usage, 'prompt_tokens', 0)
                output_tokens = getattr(usage, 'completion_tokens', 0)
                cached_tokens = getattr(usage, 'prompt_tokens_cached', 0)
                
                print(f"🔍 {SEARCH_MODEL} API Response Usage:")
                print(f"   Input tokens: {input_tokens}")
                print(f"   Output tokens: {output_tokens}")
                print(f"   Cached tokens: {cached_tokens}")
                
                cost_tracker.add_search_cost(input_tokens, output_tokens, cached_tokens)
            
            full_research = response.choices[0].message.content.strip()
            
            # Parse the research into sections
            research_sections = self._parse_research_sections(full_research)
            
            # Save to CSV
            costs = cost_tracker.get_costs()
            self._save_research_to_csv(club_name, country or '', website or '', 
                                     research_sections, full_research, costs)
            
            return research_sections, costs
            
        except Exception as e:
            print(f"Error researching club {club_name} with O3: {e}")
            
            # Create fallback research
            fallback_sections = {
                'introduction_research': f"Unable to find specific current information about {club_name} due to research limitations. General photography club activities assumed based on location: {country if country else 'Unknown region'}. Focus on general photography community support and learning more about their specific activities.",
                'checkup_research': f"No specific upcoming events or challenges found for {club_name}. Suggest focusing on general photography season activities and mention common photography club needs and DxO benefits.",
                'acceptance_research': f"No specific club structure information found for {club_name}. Assume standard photography club structure with leadership team. Recommend standard member communication approach and focus on general DxO software benefits for club members.",
                'full_research_data': f"Research failed for {club_name}. Using fallback information.",
                'from_cache': False
            }
            
            costs = cost_tracker.get_costs()
            self._save_research_to_csv(club_name, country or '', website or '', 
                                     fallback_sections, fallback_sections['full_research_data'], costs)
            
            return fallback_sections, costs
    
    def _parse_research_sections(self, full_research: str) -> Dict:
        """Parse the full research into three distinct sections"""
        sections = {
            'introduction_research': '',
            'checkup_research': '',
            'acceptance_research': '',
            'full_research_data': full_research,
            'from_cache': False
        }
        
        try:
            # Extract introduction section
            intro_start = full_research.find("=== INTRODUCTION EMAIL RESEARCH ===")
            checkup_start = full_research.find("=== CHECK-UP EMAIL RESEARCH ===")
            
            if intro_start != -1:
                if checkup_start != -1:
                    intro_content = full_research[intro_start:checkup_start].strip()
                else:
                    intro_content = full_research[intro_start:].strip()
                sections['introduction_research'] = intro_content.replace("=== INTRODUCTION EMAIL RESEARCH ===", "").strip()
            
            # Extract checkup section
            if checkup_start != -1:
                acceptance_start = full_research.find("=== ACCEPTANCE EMAIL RESEARCH ===")
                if acceptance_start != -1:
                    checkup_content = full_research[checkup_start:acceptance_start].strip()
                else:
                    checkup_content = full_research[checkup_start:].strip()
                sections['checkup_research'] = checkup_content.replace("=== CHECK-UP EMAIL RESEARCH ===", "").strip()
            
            # Extract acceptance section
            acceptance_start = full_research.find("=== ACCEPTANCE EMAIL RESEARCH ===")
            if acceptance_start != -1:
                acceptance_content = full_research[acceptance_start:].strip()
                sections['acceptance_research'] = acceptance_content.replace("=== ACCEPTANCE EMAIL RESEARCH ===", "").strip()
                
        except Exception as e:
            print(f"⚠️ Error parsing research sections: {e}")
            # Fallback: use full research for all sections
            sections['introduction_research'] = full_research
            sections['checkup_research'] = full_research
            sections['acceptance_research'] = full_research
        
        return sections
    
    def _save_research_to_csv(self, club_name: str, country: str, website: str, 
                            research_sections: Dict, full_research: str, costs: Dict):
        """Save research results to CSV"""
        try:
            # Load existing research
            try:
                research_df = pd.read_csv(self.research_csv_path)
            except FileNotFoundError:
                research_df = pd.DataFrame(columns=[
                    'club_name', 'country', 'website',
                    'introduction_research', 'checkup_research', 'acceptance_research',
                    'full_research_data', 'search_cost', 'web_search_cost', 'total_cost',
                    'researched_at', 'expires_at', 'is_valid'
                ])
            
            # Remove existing entry for this club
            research_df = research_df[research_df['club_name'] != club_name]
            
            # Prepare new entry
            researched_at = datetime.now()
            expires_at = researched_at + timedelta(days=self.cache_expiry_days)
            
            new_entry = pd.DataFrame([{
                'club_name': club_name,
                'country': country,
                'website': website,
                'introduction_research': research_sections['introduction_research'],
                'checkup_research': research_sections['checkup_research'],
                'acceptance_research': research_sections['acceptance_research'],
                'full_research_data': full_research,
                'search_cost': costs.get('search_cost', 0.0),
                'web_search_cost': costs.get('web_search_cost', 0.0),
                'total_cost': costs.get('total_cost', 0.0),
                'researched_at': researched_at.isoformat(),
                'expires_at': expires_at.isoformat(),
                'is_valid': True
            }])
            
            # Add to research data
            research_df = pd.concat([research_df, new_entry], ignore_index=True)
            research_df.to_csv(self.research_csv_path, index=False)
            
            print(f"💾 Research saved for {club_name} (expires: {expires_at.strftime('%Y-%m-%d')})")
            print(f"💰 Research cost: ${costs.get('total_cost', 0.0):.4f}")
            
        except Exception as e:
            print(f"⚠️ Error saving research: {e}")
    
    def get_research_statistics(self) -> Dict:
        """Get statistics about research data"""
        try:
            research_df = pd.read_csv(self.research_csv_path)
            
            if research_df.empty:
                return {
                    'total_researched_clubs': 0,
                    'valid_research_count': 0,
                    'expired_research_count': 0,
                    'total_research_cost': 0.0
                }
            
            now = datetime.now()
            research_df['is_currently_valid'] = research_df['expires_at'].apply(
                lambda x: pd.to_datetime(x) > now
            )
            
            valid_count = research_df['is_currently_valid'].sum()
            expired_count = len(research_df) - valid_count
            total_cost = research_df['total_cost'].sum()
            
            return {
                'total_researched_clubs': len(research_df),
                'valid_research_count': valid_count,
                'expired_research_count': expired_count,
                'total_research_cost': total_cost
            }
            
        except Exception as e:
            print(f"⚠️ Error getting research statistics: {e}")
            return {
                'total_researched_clubs': 0,
                'valid_research_count': 0,
                'expired_research_count': 0,
                'total_research_cost': 0.0
            }
    
    def get_all_researched_clubs(self) -> List[Dict]:
        """Get list of all researched clubs with status"""
        try:
            research_df = pd.read_csv(self.research_csv_path)
            
            if research_df.empty:
                return []
            
            now = datetime.now()
            result = []
            
            for _, row in research_df.iterrows():
                expires_at = pd.to_datetime(row['expires_at'])
                is_valid = expires_at > now
                
                result.append({
                    'club_name': row['club_name'],
                    'country': row['country'],
                    'website': row['website'],
                    'researched_at': row['researched_at'],
                    'expires_at': row['expires_at'],
                    'is_valid': is_valid,
                    'days_until_expiry': (expires_at - now).days if is_valid else 0,
                    'research_cost': row.get('total_cost', 0.0)
                })
            
            return result
            
        except Exception as e:
            print(f"⚠️ Error getting researched clubs: {e}")
            return []

# Command line interface for research management
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Club Research Manager')
    parser.add_argument('--club', type=str, help='Research specific club')
    parser.add_argument('--stats', action='store_true', help='Show research statistics')
    parser.add_argument('--list', action='store_true', help='List all researched clubs')
    
    args = parser.parse_args()
    
    manager = ClubResearchManager()
    
    if args.stats:
        stats = manager.get_research_statistics()
        print("📊 Research Statistics:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
    
    elif args.list:
        clubs = manager.get_all_researched_clubs()
        print(f"🗂️ Researched Clubs ({len(clubs)}):")
        for club in clubs:
            status = "✅ Valid" if club['is_valid'] else "❌ Expired"
            print(f"   - {club['club_name']} ({club['country']}) - {status}")
    
    elif args.club:
        clubs_df = manager.load_clubs_data()
        club_data = clubs_df[clubs_df['Club'] == args.club]
        
        if not club_data.empty:
            club_info = club_data.iloc[0]
            website = club_info.get('Website', '')
            country = club_info.get('Country', '')
            
            print(f"🔍 Researching {args.club}...")
            research, costs = manager.research_club_with_o3(args.club, website, country)
            
            print(f"✅ Research completed!")
            print(f"💰 Cost: ${costs['total_cost']:.4f}")
        else:
            print(f"❌ Club '{args.club}' not found in database")
    
    else:
        print("Club Research Manager")
        print("Use --help for options") 