import openai
import pandas as pd
import sqlite3
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
            return 0.0
        
        # Calculate regular input cost
        regular_input_tokens = max(0, input_tokens - cached_tokens)
        input_cost = (regular_input_tokens / 1_000_000) * PRICING[model]['input']
        
        # Calculate cached input cost if applicable
        cached_cost = 0.0
        if cached_tokens > 0 and 'cached_input' in PRICING[model]:
            cached_cost = (cached_tokens / 1_000_000) * PRICING[model]['cached_input']
        
        # Calculate output cost
        output_cost = (output_tokens / 1_000_000) * PRICING[model]['output']
        
        return input_cost + cached_cost + output_cost
    
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
        self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        self.db_path = DATABASE_PATH
        self._initialize_database()
        
    def _initialize_database(self):
        """Initialize SQLite database to track sent emails and costs"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sent_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                club_name TEXT UNIQUE NOT NULL,
                email_sent_date TEXT,
                personalized_content TEXT,
                generated_email TEXT,
                search_cost REAL DEFAULT 0.0,
                content_cost REAL DEFAULT 0.0,
                web_search_cost REAL DEFAULT 0.0,
                total_cost REAL DEFAULT 0.0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def load_clubs_data(self) -> pd.DataFrame:
        """Load clubs data from CSV file"""
        try:
            df = pd.read_csv(CLUBS_CSV_PATH)
            # Get unique clubs (since CSV has multiple contacts per club)
            unique_clubs = df.groupby('Club').first().reset_index()
            return unique_clubs
        except Exception as e:
            print(f"Error loading clubs data: {e}")
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT email_sent_date, personalized_content, generated_email, total_cost 
            FROM sent_emails 
            WHERE club_name = ?
        ''', (club_name,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return True, {
                'email_sent_date': result[0],
                'personalized_content': result[1],
                'generated_email': result[2],
                'total_cost': result[3]
            }
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
            
            # Track costs
            if hasattr(response, 'usage') and response.usage:
                cached_tokens = getattr(response.usage, 'prompt_tokens_cached', 0) if hasattr(response.usage, 'prompt_tokens_cached') else 0
                cost_tracker.add_search_cost(
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens,
                    cached_tokens
                )
            
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
            
            # Track costs
            if hasattr(response, 'usage') and response.usage:
                cached_tokens = getattr(response.usage, 'prompt_tokens_cached', 0) if hasattr(response.usage, 'prompt_tokens_cached') else 0
                cost_tracker.add_content_cost(
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens,
                    cached_tokens
                )
            
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
        """Save generated email to database with cost tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        email_sent_date = datetime.now().isoformat() if mark_as_sent else None
        
        cursor.execute('''
            INSERT OR REPLACE INTO sent_emails 
            (club_name, email_sent_date, personalized_content, generated_email, 
             search_cost, content_cost, web_search_cost, total_cost)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (club_name, email_sent_date, personalized_content, generated_email,
              costs['search_cost'], costs['content_cost'], costs['web_search_cost'], costs['total_cost']))
        
        conn.commit()
        conn.close()
        
        print(f"💾 Email saved for {club_name} (Cost: ${costs['total_cost']:.4f})" + (" and marked as sent" if mark_as_sent else ""))
    
    def mark_email_as_sent(self, club_name: str):
        """Mark an email as sent"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE sent_emails 
            SET email_sent_date = ? 
            WHERE club_name = ?
        ''', (datetime.now().isoformat(), club_name))
        
        conn.commit()
        conn.close()
        
        print(f"📤 Email marked as sent for {club_name}")
    
    def get_all_clubs_status(self) -> pd.DataFrame:
        """Get status of all clubs with cost information"""
        clubs_df = self.load_clubs_data()
        
        conn = sqlite3.connect(self.db_path)
        sent_emails_df = pd.read_sql_query('''
            SELECT club_name, email_sent_date, total_cost,
                   CASE WHEN email_sent_date IS NOT NULL THEN 'Sent' ELSE 'Generated' END as status
            FROM sent_emails
        ''', conn)
        conn.close()
        
        # Merge with clubs data
        status_df = clubs_df.merge(
            sent_emails_df, 
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                SUM(search_cost) as total_search_cost,
                SUM(content_cost) as total_content_cost,
                SUM(web_search_cost) as total_web_search_cost,
                SUM(total_cost) as total_cost,
                COUNT(*) as total_emails
            FROM sent_emails
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        return {
            'search_cost': result[0] or 0.0,
            'content_cost': result[1] or 0.0,
            'web_search_cost': result[2] or 0.0,
            'total_cost': result[3] or 0.0,
            'total_emails': result[4] or 0
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