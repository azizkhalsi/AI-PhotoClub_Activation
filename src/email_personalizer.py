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
            
        # Create a detailed search prompt for O3 with web search capabilities
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
        
        Club details to help your search:
        - Name: {club_name}
        - Country: {country if country else 'Unknown'}
        - Website: {website if website else 'Not provided'}
        
        **CRITICAL:** Please search the web for this specific club and provide concrete findings. Don't provide generic information - I need specific details that prove genuine knowledge of this particular club.
        
        Format your response as:
        **SPECIFIC FINDINGS:**
        [List concrete facts you found about this club]
        
        **RECENT ACTIVITIES:**
        [Recent events, exhibitions, or activities with dates]
        
        **CLUB SPECIALTIES:**
        [Their photography focus areas and unique characteristics]
        
        **PERSONALIZATION ANGLE:**
        [Specific aspect that would make a good personalization hook for an email]
        
        If you cannot find specific information about this exact club, clearly state that and provide what general information you can find about photography clubs in their region, but be honest about the limitations.
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model=SEARCH_MODEL,
                messages=[
                    {"role": "system", "content": "You are a research assistant with web search capabilities. You must search the internet to find specific, current information about photography clubs and communities. Always use web search to find real, up-to-date information rather than relying on training data. Focus on finding concrete details like recent events, specific activities, and unique characteristics of each club."},
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
                print(f"   Input tokens: {input_tokens}")
                print(f"   Output tokens: {output_tokens}")
                print(f"   Cached tokens: {cached_tokens}")
                
                cost_tracker.add_search_cost(input_tokens, output_tokens, cached_tokens)
            else:
                print(f"⚠️ Warning: No usage information available from {SEARCH_MODEL} API response")
            
            research_result = response.choices[0].message.content.strip()
            
            return research_result, cost_tracker.get_costs()
            
        except Exception as e:
            print(f"Error researching club {club_name} with O3: {e}")
            fallback_result = f"""
            **SPECIFIC FINDINGS:**
            Unable to find specific current information about {club_name} due to research limitations.
            
            **RECENT ACTIVITIES:**
            No specific recent activities found.
            
            **CLUB SPECIALTIES:**
            General photography club activities assumed based on location: {country if country else 'Unknown region'}
            
            **PERSONALIZATION ANGLE:**
            Focus on general photography community support and learning more about their specific activities.
            """
            return fallback_result, cost_tracker.get_costs()
    
    def generate_personalized_content(self, club_name: str, club_research: str) -> Tuple[str, Dict]:
        """Generate ONLY the personalized addition (1-2 sentences) using GPT-4.1-nano"""
        
        cost_tracker = CostTracker()
        
        content_prompt = f"""
        You are writing a personalized addition for a professional marketing email from DxO Labs to a photography club.

        **CLUB RESEARCH:**
        {club_research}

        **YOUR TASK:**
        Generate ONLY 1-2 personalized sentences that will be inserted after this line in the email:
        "I'm Killian, part of the Partnerships team at DxO Labs, the creators of award-winning photo editing software like DxO PhotoLab and Nik Collection."

        **REQUIREMENTS:**
        - Start with "I read about..." or "I came across..." or "I noticed..." or "I was impressed by..."
        - Reference specific research findings about {club_name}
        - Connect to DxO's software benefits naturally
        - Be professional and confident
        - Maximum 2 sentences
        - Return ONLY the personalized sentences, nothing else

        **EXAMPLE OUTPUT:**
        "I read about your recent 'Urban Nights' exhibition and was impressed by the technical challenges your members tackled with low-light street photography. I believe DxO PhotoLab's industry-leading noise reduction could help your photographers push those ISO limits even further."

        **GENERATE ONLY THE PERSONALIZED SENTENCES:**
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model=CONTENT_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional marketing specialist for DxO Labs creating personalized content for photography club outreach. Generate ONLY the requested personalized sentences, nothing else. Do not include any email template or other content."},
                    {"role": "user", "content": content_prompt}
                ],
                temperature=0.8,
                max_tokens=200
            )
            
            # Track costs
            if hasattr(response, 'usage') and response.usage:
                usage = response.usage
                input_tokens = getattr(usage, 'prompt_tokens', 0)
                output_tokens = getattr(usage, 'completion_tokens', 0)
                cached_tokens = getattr(usage, 'prompt_tokens_cached', 0)
                
                cost_tracker.add_content_cost(input_tokens, output_tokens, cached_tokens)
            
            personalized_content = response.choices[0].message.content.strip()
            print(f"✨ Generated personalized content for {club_name}: {len(personalized_content)} characters")
            
            return personalized_content, cost_tracker.get_costs()
            
        except Exception as e:
            print(f"❌ Error generating personalized content for {club_name}: {e}")
            fallback_content = f"I came across {club_name} and was impressed by your photography community's dedication to advancing the art of photography. I'd love to explore how DxO's professional editing tools could support your members' creative work."
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
        personalized_content, content_costs = self.generate_personalized_content(club_name, club_research)
        
        # Add content costs to total
        for cost_type, cost_value in content_costs.items():
            total_costs[cost_type] += cost_value
        
        # Step 3: Load email template and combine
        print(f"📧 Combining template with personalized content...")
        template = self.load_email_template()
        if not template:
            raise ValueError("Could not load email template")
        
        # Combine template with personalized content
        complete_email = self.combine_email_with_personalization(template, personalized_content, club_name)
        
        print(f"✅ Email generation completed for {club_name}")
        print(f"📝 Personalized content: {personalized_content[:100]}...")
        print(f"📧 Complete email length: {len(complete_email)} characters")
        print(f"💰 Total cost: ${total_costs['total_cost']:.4f}")
        
        return complete_email, personalized_content, club_research, total_costs
    
    def combine_email_with_personalization(self, template: str, personalized_content: str, club_name: str) -> str:
        """Combine the email template with personalized content"""
        
        # Replace club name placeholder
        email = template.replace("{{Company name}}", club_name)
        
        # Look for the exact pattern from the template
        killian_line = "I'm Killian, part of the Partnerships team at DxO Labs, the creators of award-winning photo editing software like DxO PhotoLab and Nik Collection."
        
        killian_position = email.find(killian_line)
        
        if killian_position != -1:
            # Find the end of this line
            killian_end = killian_position + len(killian_line)
            
            # Look for the pattern after Killian's line: should be "\n\nWe're offering"
            next_section_start = email.find("\n\nWe're offering", killian_end)
            
            if next_section_start != -1:
                # Insert personalized content between Killian's line and "We're offering..."
                combined_email = (
                    email[:killian_end] + 
                    f"\n\n{personalized_content}" + 
                    email[next_section_start:]
                )
                print(f"✅ Successfully inserted personalized content after Killian's introduction")
                return combined_email
            else:
                # Fallback: look for any double newline after Killian's line
                next_paragraph = email.find("\n\n", killian_end)
                if next_paragraph != -1:
                    combined_email = (
                        email[:killian_end] + 
                        f"\n\n{personalized_content}" + 
                        email[next_paragraph:]
                    )
                    print(f"✅ Inserted personalized content at next paragraph break")
                    return combined_email
        
        # Enhanced fallback with more precise insertion
        print(f"⚠️ Could not find exact Killian line, trying partial match...")
        
        # Try to find just the start of Killian's introduction
        killian_start = email.find("I'm Killian, part of the Partnerships team")
        if killian_start != -1:
            # Find the end of the sentence (look for period followed by space or newline)
            sentence_end = email.find(".", killian_start)
            while sentence_end != -1 and sentence_end < len(email) - 1:
                if email[sentence_end + 1] in [' ', '\n']:
                    break
                sentence_end = email.find(".", sentence_end + 1)
            
            if sentence_end != -1:
                # Look for next paragraph after this sentence
                next_paragraph = email.find("\n\n", sentence_end)
                if next_paragraph != -1:
                    combined_email = (
                        email[:sentence_end + 1] + 
                        f"\n\n{personalized_content}" + 
                        email[next_paragraph:]
                    )
                    print(f"✅ Inserted personalized content after partial Killian match")
                    return combined_email
        
        # Final fallback: Insert after the first paragraph that contains "DxO Labs"
        dxo_mention = email.find("DxO Labs")
        if dxo_mention != -1:
            next_paragraph = email.find("\n\n", dxo_mention)
            if next_paragraph != -1:
                combined_email = (
                    email[:next_paragraph] + 
                    f"\n\n{personalized_content}" + 
                    email[next_paragraph:]
                )
                print(f"✅ Inserted personalized content after DxO Labs mention")
                return combined_email
        
        # Last resort: append at the end
        print(f"❌ All insertion attempts failed, appending at end")
        return email + f"\n\n{personalized_content}"
    
    def save_generated_email(self, club_name: str, personalized_content: str, generated_email: str, costs: Dict, mark_as_sent: bool = False):
        """Save generated email to CSV with cost tracking"""
        
        print(f"💾 Saving email for {club_name}...")
        
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
            'personalized_content': personalized_content,  # Only the personalized addition
            'generated_email': generated_email,  # Complete email with personalization
            'search_cost': costs['search_cost'],
            'content_cost': costs['content_cost'],
            'web_search_cost': costs['web_search_cost'],
            'total_cost': costs['total_cost'],
            'created_at': created_at
        }])
        
        tracking_df = pd.concat([tracking_df, new_record], ignore_index=True)
        tracking_df.to_csv(self.tracking_csv_path, index=False)
        
        print(f"✅ Email saved for {club_name} (Cost: ${costs['total_cost']:.4f})" + (" and marked as sent" if mark_as_sent else ""))
        print(f"📝 Personalized content saved: {len(personalized_content)} characters")
        print(f"📧 Complete email saved: {len(generated_email)} characters")
    

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
    
    # Test with AUSTRALIAN PHOTOGRAPHIC SOCIETY
    test_club = "AUSTRALIAN PHOTOGRAPHIC SOCIETY"
    
    print(f"🚀 Running email generation for: {test_club}")
    print("=" * 60)
    
    try:
        email, content, research, costs = personalizer.generate_personalized_email(test_club)
        
        print(f"\n=== RESULTS FOR {test_club} ===")
        print(f"\n📝 Personalized Content Generated:")
        print(f"'{content}'")
        print(f"\n📧 Complete Email (first 500 chars):")
        print(email[:500] + "..." if len(email) > 500 else email)
        print(f"\n🔍 Research Summary:")
        print(research[:300] + "..." if len(research) > 300 else research)
        print(f"\n💰 Costs Breakdown:")
        for cost_type, cost_value in costs.items():
            print(f"  {cost_type}: ${cost_value:.4f}")
        
        # Save the generated email
        personalizer.save_generated_email(test_club, content, email, costs)
        
        print(f"\n✅ Email generation and saving completed for {test_club}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc() 