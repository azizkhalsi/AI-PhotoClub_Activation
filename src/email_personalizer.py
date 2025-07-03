import openai
import pandas as pd
import os
from datetime import datetime
import json
from typing import Dict, Optional, Tuple
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
    
    def add_content_cost(self, input_tokens: int, output_tokens: int, cached_tokens: int = 0):
        """Add cost for GPT-4.1-nano content generation"""
        cost = self.calculate_token_cost(CONTENT_MODEL, input_tokens, output_tokens, cached_tokens)
        self.costs['content_cost'] += cost
        self.costs['total_cost'] += cost
    
    def add_web_search_cost(self, num_queries: int = 1):
        """Add cost for web search operations"""
        cost = num_queries * WEB_SEARCH_COST_PER_QUERY
        self.costs['web_search_cost'] += cost
        self.costs['total_cost'] += cost
    
    def get_costs(self) -> Dict[str, float]:
        """Get all tracked costs"""
        return self.costs.copy()

class EmailPersonalizer:
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in environment variables or .env file")
        
        try:
            # Initialize OpenAI client with explicit parameters only
            self.openai_client = openai.OpenAI(
                api_key=OPENAI_API_KEY,
                timeout=60.0,
                max_retries=3,
            )
        except TypeError as e:
            # If there's a parameter issue, try with minimal parameters
            try:
                self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
            except Exception as e2:
                raise ValueError(f"Failed to initialize OpenAI client: {e2}")
        except Exception as e:
            raise ValueError(f"Failed to initialize OpenAI client: {e}")
        
        self.tracking_csv_path = 'sent_emails_tracking.csv'
        self._initialize_tracking_csv()
        
    def _initialize_tracking_csv(self):
        """Initialize CSV file to track sent emails and costs"""
        import os
        if not os.path.exists(self.tracking_csv_path):
            tracking_df = pd.DataFrame(columns=[
                'club_name', 'email_sent_date', 'personalized_content', 
                'generated_email', 'search_cost', 'content_cost', 
                'web_search_cost', 'total_cost', 'created_at'
            ])
            tracking_df.to_csv(self.tracking_csv_path, index=False)
    
    def load_clubs_data(self) -> pd.DataFrame:
        """Load clubs data from CSV file"""
        try:
            # Load CSV with more robust parsing
            df = pd.read_csv(
                CLUBS_CSV_PATH,
                encoding='utf-8',
                quotechar='"',
                escapechar='\\',
                on_bad_lines='skip',  # Skip malformed lines
                engine='python'  # Use Python engine for better error handling
            )
            
            print(f"✅ Loaded {len(df)} records from CSV")
            print(f"📊 Columns: {list(df.columns)}")
            
            # Get unique clubs (since CSV has multiple contacts per club)
            if 'Club' in df.columns:
                unique_clubs = df.groupby('Club').first().reset_index()
                print(f"✅ Found {len(unique_clubs)} unique clubs")
                return unique_clubs
            else:
                print(f"❌ 'Club' column not found in CSV. Available columns: {list(df.columns)}")
                return pd.DataFrame()
                
        except FileNotFoundError:
            print(f"❌ CSV file not found: {CLUBS_CSV_PATH}")
            return pd.DataFrame()
        except Exception as e:
            print(f"❌ Error loading clubs data: {e}")
            print(f"   Trying alternative parsing method...")
            
            # Fallback: try with different parameters
            try:
                df = pd.read_csv(
                    CLUBS_CSV_PATH,
                    encoding='utf-8',
                    on_bad_lines='skip',
                    engine='c',
                    low_memory=False
                )
                print(f"✅ Fallback method loaded {len(df)} records")
                unique_clubs = df.groupby('Club').first().reset_index()
                return unique_clubs
            except Exception as e2:
                print(f"❌ Fallback method also failed: {e2}")
                return pd.DataFrame()
    
    def load_email_template(self) -> str:
        """Load the base email template"""
        try:
            with open(EMAIL_TEMPLATE_PATH, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error loading email template: {e}")
            return ""
    
    def check_email_sent(self, club_name: str) -> Tuple[bool, Optional[Dict]]:
        """Check if email has already been sent to a club"""
        try:
            tracking_df = pd.read_csv(self.tracking_csv_path)
            club_record = tracking_df[tracking_df['club_name'] == club_name]
            
            if not club_record.empty:
                record = club_record.iloc[0]
                return True, {
                    'email_sent_date': record.get('email_sent_date', None),
                    'personalized_content': record.get('personalized_content', ''),
                    'generated_email': record.get('generated_email', ''),
                    'total_cost': record.get('total_cost', 0.0)
                }
            return False, None
        except FileNotFoundError:
            return False, None
        except Exception as e:
            print(f"Error checking email status for {club_name}: {e}")
            return False, None
    
    def research_club_with_o3(self, club_name: str, website: str = None, country: str = None) -> Tuple[str, Dict]:
        """Use O3 with web search to research club information"""
        
        cost_tracker = CostTracker()
        
        # Add web search cost (estimated)
        cost_tracker.add_web_search_cost(1)
        
        search_query = f"photography club '{club_name}'"
        if country:
            search_query += f" {country}"
        if website:
            search_query += f" site:{website}"
            
        # Create a search prompt for O3 (no temperature/max_tokens as requested)
        search_prompt = f"""
        You are a research assistant with web search capabilities. Research the photography club "{club_name}" and provide a comprehensive summary.

        Focus on finding:
        1. Their main activities and specialties
        2. Notable achievements, awards, or recognition
        3. Community involvement or special events they organize
        4. Unique characteristics that make them stand out
        5. Recent news or activities
        6. Their photography focus areas (landscape, portrait, street, etc.)
        
        Club details:
        - Name: {club_name}
        - Country: {country if country else 'Unknown'}
        - Website: {website if website else 'Not provided'}
        
        Please provide a detailed research summary that will be used to personalize an email. Include specific details that would show genuine knowledge of the club.
        
        If you cannot find specific information about this club, provide general information about photography clubs in that region and mention that you'd like to learn more about their specific activities.
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model=SEARCH_MODEL,
                messages=[
                    {"role": "system", "content": "You are a research assistant specializing in photography clubs and communities. Use web search to find accurate, current information about photography clubs."},
                    {"role": "user", "content": search_prompt}
                ]
            )
            
            # Extract and track costs from API response
            if hasattr(response, 'usage') and response.usage:
                usage = response.usage
                input_tokens = getattr(usage, 'prompt_tokens', 0)
                output_tokens = getattr(usage, 'completion_tokens', 0)
                cached_tokens = getattr(usage, 'prompt_tokens_cached', 0)
                
                print(f"🔍 {SEARCH_MODEL} API Response Usage:")
                print(f"   Raw input tokens: {input_tokens}")
                print(f"   Raw output tokens: {output_tokens}")
                print(f"   Raw cached tokens: {cached_tokens}")
                
                cost_tracker.add_search_cost(input_tokens, output_tokens, cached_tokens)
            else:
                print(f"⚠️ Warning: No usage information available from {SEARCH_MODEL} API response")
            
            research_result = response.choices[0].message.content.strip()
            
            return research_result, cost_tracker.get_costs()
            
        except Exception as e:
            print(f"Error researching club {club_name} with O3: {e}")
            fallback_result = f"I understand that {club_name} is an active photography community focused on developing photographic skills and fostering creativity among its members."
            return fallback_result, cost_tracker.get_costs()
    
    def generate_personalized_content_with_gpt4(self, club_name: str, club_research: str) -> Tuple[str, Dict]:
        """Generate personalized content using GPT-4.1-nano based on O3 research"""
        
        cost_tracker = CostTracker()
        
        personalization_prompt = f"""
        Based on the detailed research about "{club_name}", create a personalized and engaging sentence or two that will be inserted after "I'm Killian, part of the Partnerships team at DxO Labs, the creators of award-winning photo editing software like DxO PhotoLab and Nik Collection."

        Research findings:
        {club_research}

        Your task is to create a natural, conversational transition that:
        1. Shows genuine knowledge about their specific club
        2. Mentions something concrete about their activities, achievements, or specialties
        3. Connects how DxO's professional editing software can enhance their members' work
        4. Feels personal and authentic, not generic
        5. Is concise but impactful (1-2 sentences maximum)

        Examples of good personalization:
        - "I came across your recent landscape photography exhibition and was impressed by the technical quality of the work displayed. I believe DxO PhotoLab's advanced noise reduction and lens corrections could help your members achieve even more professional results in challenging lighting conditions."
        - "I noticed your club's focus on wildlife photography and the amazing shots from your recent field trips to [location]. Our Nik Collection's specialized filters could really enhance the dramatic impact of those nature captures your members are creating."

        Generate a personalized message that sounds like it comes from someone who has genuinely researched and understands this specific club.
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model=CONTENT_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert at writing personalized, genuine partnership outreach messages. Create content that demonstrates real knowledge and interest in the recipient's work."},
                    {"role": "user", "content": personalization_prompt}
                ],
                temperature=0.8,
                max_tokens=150
            )
            
            # Extract and track costs from API response
            if hasattr(response, 'usage') and response.usage:
                usage = response.usage
                input_tokens = getattr(usage, 'prompt_tokens', 0)
                output_tokens = getattr(usage, 'completion_tokens', 0)
                cached_tokens = getattr(usage, 'prompt_tokens_cached', 0)
                
                print(f"✨ {CONTENT_MODEL} API Response Usage:")
                print(f"   Raw input tokens: {input_tokens}")
                print(f"   Raw output tokens: {output_tokens}")
                print(f"   Raw cached tokens: {cached_tokens}")
                
                cost_tracker.add_content_cost(input_tokens, output_tokens, cached_tokens)
            else:
                print(f"⚠️ Warning: No usage information available from {CONTENT_MODEL} API response")
            
            personalized_content = response.choices[0].message.content.strip()
            
            return personalized_content, cost_tracker.get_costs()
            
        except Exception as e:
            print(f"Error generating personalized content for {club_name}: {e}")
            fallback_content = f"I heard about {club_name} and your commitment to advancing photography skills in your community. I think our professional-grade editing tools could really benefit your members' creative work."
            return fallback_content, cost_tracker.get_costs()
    
    def generate_personalized_email(self, club_name: str) -> Tuple[str, str, str, Dict]:
        """Generate complete personalized email for a club with cost tracking"""
        
        total_costs = {
            'search_cost': 0.0,
            'content_cost': 0.0,
            'web_search_cost': 0.0,
            'total_cost': 0.0
        }
        
        # Load clubs data to get club details
        clubs_df = self.load_clubs_data()
        club_data = clubs_df[clubs_df['Club'] == club_name]
        
        if club_data.empty:
            raise ValueError(f"Club '{club_name}' not found in database")
        
        club_info = club_data.iloc[0]
        website = club_info.get('Website', '')
        country = club_info.get('Country', '')
        
        # Step 1: Research the club with O3
        print(f"🔍 Researching {club_name} with O3...")
        club_research, search_costs = self.research_club_with_o3(club_name, website, country)
        
        # Add search costs to total
        for cost_type, cost_value in search_costs.items():
            total_costs[cost_type] += cost_value
        
        # Step 2: Generate personalized content with GPT-4.1-nano
        print(f"✨ Generating personalized content with GPT-4.1-nano...")
        personalized_content, content_costs = self.generate_personalized_content_with_gpt4(club_name, club_research)
        
        # Add content costs to total
        for cost_type, cost_value in content_costs.items():
            total_costs[cost_type] += cost_value
        
        # Step 3: Load and modify email template
        template = self.load_email_template()
        if not template:
            raise ValueError("Could not load email template")
        
        # Replace placeholders
        personalized_email = template.replace("{{Company name}}", club_name)
        
        # Insert personalized content after the Killian introduction
        killian_line = "I'm Killian, part of the Partnerships team at DxO Labs, the creators of award-winning photo editing software like DxO PhotoLab and Nik Collection."
        
        if killian_line in personalized_email:
            insertion_point = personalized_email.find(killian_line) + len(killian_line)
            personalized_email = (
                personalized_email[:insertion_point] + 
                f"\n\n{personalized_content}" + 
                personalized_email[insertion_point:]
            )
        
        print(f"💰 Total cost for {club_name}: ${total_costs['total_cost']:.4f}")
        
        return personalized_email, personalized_content, club_research, total_costs
    
    def save_generated_email(self, club_name: str, personalized_content: str, generated_email: str, costs: Dict, mark_as_sent: bool = False):
        """Save generated email to CSV with cost tracking"""
        try:
            tracking_df = pd.read_csv(self.tracking_csv_path)
        except FileNotFoundError:
            tracking_df = pd.DataFrame(columns=[
                'club_name', 'email_sent_date', 'personalized_content', 
                'generated_email', 'search_cost', 'content_cost', 
                'web_search_cost', 'total_cost', 'created_at'
            ])
        
        email_sent_date = datetime.now().isoformat() if mark_as_sent else None
        created_at = datetime.now().isoformat()
        
        # Remove existing record if it exists
        tracking_df = tracking_df[tracking_df['club_name'] != club_name]
        
        # Add new record
        new_record = pd.DataFrame([{
            'club_name': club_name,
            'email_sent_date': email_sent_date,
            'personalized_content': personalized_content,
            'generated_email': generated_email,
            'search_cost': costs['search_cost'],
            'content_cost': costs['content_cost'],
            'web_search_cost': costs['web_search_cost'],
            'total_cost': costs['total_cost'],
            'created_at': created_at
        }])
        
        tracking_df = pd.concat([tracking_df, new_record], ignore_index=True)
        tracking_df.to_csv(self.tracking_csv_path, index=False)
        
        print(f"💾 Email saved for {club_name} (Cost: ${costs['total_cost']:.4f})" + (" and marked as sent" if mark_as_sent else ""))
    
    def mark_email_as_sent(self, club_name: str):
        """Mark an email as sent"""
        try:
            tracking_df = pd.read_csv(self.tracking_csv_path)
            tracking_df.loc[tracking_df['club_name'] == club_name, 'email_sent_date'] = datetime.now().isoformat()
            tracking_df.to_csv(self.tracking_csv_path, index=False)
            print(f"📤 Email marked as sent for {club_name}")
        except Exception as e:
            print(f"Error marking email as sent for {club_name}: {e}")
    
    def get_all_clubs_status(self) -> pd.DataFrame:
        """Get status of all clubs with cost information"""
        clubs_df = self.load_clubs_data()
        
        try:
            tracking_df = pd.read_csv(self.tracking_csv_path)
            tracking_df['status'] = tracking_df['email_sent_date'].apply(
                lambda x: 'Sent' if pd.notna(x) else 'Generated'
            )
        except FileNotFoundError:
            tracking_df = pd.DataFrame(columns=['club_name', 'email_sent_date', 'total_cost', 'status'])
        
        # Merge with clubs data
        status_df = clubs_df.merge(
            tracking_df[['club_name', 'email_sent_date', 'total_cost', 'status']], 
            left_on='Club', 
            right_on='club_name', 
            how='left'
        )
        
        status_df['status'] = status_df['status'].fillna('Not Generated')
        status_df['total_cost'] = status_df['total_cost'].fillna(0.0)
        status_df = status_df.drop('club_name', axis=1, errors='ignore')
        
        return status_df[['Club', 'Country', 'Website', 'status', 'total_cost']]
    
    def get_total_costs(self) -> Dict[str, float]:
        """Get total costs across all generated emails"""
        try:
            tracking_df = pd.read_csv(self.tracking_csv_path)
            
            return {
                'search_cost': tracking_df['search_cost'].sum(),
                'content_cost': tracking_df['content_cost'].sum(),
                'web_search_cost': tracking_df['web_search_cost'].sum(),
                'total_cost': tracking_df['total_cost'].sum(),
                'total_emails': len(tracking_df)
            }
        except FileNotFoundError:
            return {
                'search_cost': 0.0,
                'content_cost': 0.0,
                'web_search_cost': 0.0,
                'total_cost': 0.0,
                'total_emails': 0
            }


if __name__ == "__main__":
    # Example usage
    personalizer = EmailPersonalizer()
    
    # Test with a specific club
    test_club = "BOISE CAMERA CLUB"
    
    try:
        email, content, research, costs = personalizer.generate_personalized_email(test_club)
        print(f"\n=== Generated Email for {test_club} ===")
        print(email)
        print(f"\n=== Research Summary ===")
        print(research)
        print(f"\n=== Personalized Content ===")
        print(content)
        print(f"\n=== Costs ===")
        for cost_type, cost_value in costs.items():
            print(f"{cost_type}: ${cost_value:.4f}")
        
        # Save the generated email
        personalizer.save_generated_email(test_club, content, email, costs)
        
    except Exception as e:
        print(f"Error: {e}") 