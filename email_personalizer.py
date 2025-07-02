import openai
import pandas as pd
import sqlite3
import os
from datetime import datetime
import json
from typing import Dict, Optional, Tuple
import config

class EmailPersonalizer:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        self.db_path = config.DATABASE_PATH
        self._initialize_database()
        
    def _initialize_database(self):
        """Initialize SQLite database to track sent emails"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sent_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                club_name TEXT UNIQUE NOT NULL,
                email_sent_date TEXT,
                personalized_content TEXT,
                generated_email TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def load_clubs_data(self) -> pd.DataFrame:
        """Load clubs data from CSV file"""
        try:
            df = pd.read_csv(config.CLUBS_CSV_PATH)
            # Get unique clubs (since CSV has multiple contacts per club)
            unique_clubs = df.groupby('Club').first().reset_index()
            return unique_clubs
        except Exception as e:
            print(f"Error loading clubs data: {e}")
            return pd.DataFrame()
    
    def load_email_template(self) -> str:
        """Load the base email template"""
        try:
            with open(config.EMAIL_TEMPLATE_PATH, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error loading email template: {e}")
            return ""
    
    def check_email_sent(self, club_name: str) -> Tuple[bool, Optional[Dict]]:
        """Check if email has already been sent to a club"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT email_sent_date, personalized_content, generated_email 
            FROM sent_emails 
            WHERE club_name = ?
        ''', (club_name,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return True, {
                'email_sent_date': result[0],
                'personalized_content': result[1],
                'generated_email': result[2]
            }
        return False, None
    
    def research_club(self, club_name: str, website: str = None, country: str = None) -> str:
        """Use OpenAI with web search to research club information"""
        
        search_query = f"photography club '{club_name}'"
        if country:
            search_query += f" {country}"
        if website:
            search_query += f" site:{website}"
            
        # Create a search prompt for OpenAI
        search_prompt = f"""
        Research the photography club "{club_name}" and provide a brief summary focusing on:
        1. Their main activities and specialties
        2. Notable achievements or awards
        3. Community involvement or events they organize
        4. Any unique characteristics that make them stand out
        
        Club details:
        - Name: {club_name}
        - Country: {country if country else 'Unknown'}
        - Website: {website if website else 'Not provided'}
        
        Please provide a concise summary in 2-3 sentences that highlights what makes this club special.
        If you cannot find specific information, provide a general response about photography clubs in that region.
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a research assistant specializing in photography clubs and communities. Provide accurate, concise information."},
                    {"role": "user", "content": search_prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error researching club {club_name}: {e}")
            return f"I understand that {club_name} is an active photography community focused on developing photographic skills and fostering creativity among its members."
    
    def generate_personalized_content(self, club_name: str, club_research: str) -> str:
        """Generate personalized content for the email based on club research"""
        
        personalization_prompt = f"""
        Based on the research about "{club_name}", create a personalized sentence or two that can be inserted after "I'm Killian, part of the Partnerships team at DxO Labs, the creators of award-winning photo editing software like DxO PhotoLab and Nik Collection."

        Club research:
        {club_research}

        Generate a brief, natural transition that:
        1. Shows you've heard about their club
        2. Mentions something specific about their activities/achievements
        3. Connects how DxO's software can help their members
        4. Keeps it conversational and genuine

        Example format: "I heard about [specific detail about club] and was impressed by [their achievement/activity]. I think our applications could really benefit your members who are [relevant activity]."

        Keep it to 1-2 sentences maximum, natural and conversational.
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a partnership specialist writing personalized, genuine outreach messages to photography clubs. Keep it conversational and specific."},
                    {"role": "user", "content": personalization_prompt}
                ],
                temperature=0.8,
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating personalized content for {club_name}: {e}")
            return f"I heard about {club_name} and your commitment to advancing photography skills in your community."
    
    def generate_personalized_email(self, club_name: str) -> Tuple[str, str, str]:
        """Generate complete personalized email for a club"""
        
        # Load clubs data to get club details
        clubs_df = self.load_clubs_data()
        club_data = clubs_df[clubs_df['Club'] == club_name]
        
        if club_data.empty:
            raise ValueError(f"Club '{club_name}' not found in database")
        
        club_info = club_data.iloc[0]
        website = club_info.get('Website', '')
        country = club_info.get('Country', '')
        
        # Research the club
        print(f"Researching {club_name}...")
        club_research = self.research_club(club_name, website, country)
        
        # Generate personalized content
        print(f"Generating personalized content for {club_name}...")
        personalized_content = self.generate_personalized_content(club_name, club_research)
        
        # Load and modify email template
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
        
        return personalized_email, personalized_content, club_research
    
    def save_generated_email(self, club_name: str, personalized_content: str, generated_email: str, mark_as_sent: bool = False):
        """Save generated email to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        email_sent_date = datetime.now().isoformat() if mark_as_sent else None
        
        cursor.execute('''
            INSERT OR REPLACE INTO sent_emails 
            (club_name, email_sent_date, personalized_content, generated_email)
            VALUES (?, ?, ?, ?)
        ''', (club_name, email_sent_date, personalized_content, generated_email))
        
        conn.commit()
        conn.close()
        
        print(f"Email saved for {club_name}" + (" and marked as sent" if mark_as_sent else ""))
    
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
        
        print(f"Email marked as sent for {club_name}")
    
    def get_all_clubs_status(self) -> pd.DataFrame:
        """Get status of all clubs (sent/not sent)"""
        clubs_df = self.load_clubs_data()
        
        conn = sqlite3.connect(self.db_path)
        sent_emails_df = pd.read_sql_query('''
            SELECT club_name, email_sent_date, 
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
        status_df = status_df.drop('club_name', axis=1, errors='ignore')
        
        return status_df[['Club', 'Country', 'Website', 'status']]


if __name__ == "__main__":
    # Example usage
    personalizer = EmailPersonalizer()
    
    # Test with a specific club
    test_club = "BOISE CAMERA CLUB"
    
    try:
        email, content, research = personalizer.generate_personalized_email(test_club)
        print(f"\n=== Generated Email for {test_club} ===")
        print(email)
        print(f"\n=== Research Summary ===")
        print(research)
        print(f"\n=== Personalized Content ===")
        print(content)
        
        # Save the generated email
        personalizer.save_generated_email(test_club, content, email)
        
    except Exception as e:
        print(f"Error: {e}") 