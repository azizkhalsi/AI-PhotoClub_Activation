import openai
import pandas as pd
import os
from datetime import datetime
import json
from typing import Dict, Optional, Tuple, List
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import *
from src.club_research_manager import ClubResearchManager

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
    
    def add_content_cost(self, input_tokens: int, output_tokens: int, cached_tokens: int = 0):
        """Add cost for GPT-4.1-nano content generation"""
        cost = self.calculate_token_cost(CONTENT_MODEL, input_tokens, output_tokens, cached_tokens)
        self.costs['content_cost'] += cost
        self.costs['total_cost'] += cost
    
    def get_costs(self) -> Dict[str, float]:
        """Get all tracked costs"""
        return self.costs.copy()

class EmailPersonalizer:
    """
    Handles email personalization using pre-researched club data.
    Research is handled separately by ClubResearchManager.
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
        
        self.tracking_csv_path = 'sent_emails_tracking.csv'
        self.research_csv_path = CLUBS_RESEARCH_CSV_PATH
        self.research_manager = ClubResearchManager()
        self._initialize_tracking_csv()
        
    def _initialize_tracking_csv(self):
        """Initialize CSV file to track sent emails and costs"""
        if not os.path.exists(self.tracking_csv_path):
            tracking_df = pd.DataFrame(columns=[
                'club_name', 'email_type', 'email_sent_date', 'personalized_content', 
                'generated_email', 'content_cost', 'total_cost', 'created_at'
            ])
            tracking_df.to_csv(self.tracking_csv_path, index=False)
    
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
    
    def load_email_template(self, email_type: str = 'introduction') -> str:
        """Load the base email template for specific email type"""
        # Get the project root directory (parent of src)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        template_files = {
            'introduction': 'introduction_email_template.txt',
            'checkup': 'checkup_email_template.txt',
            'acceptance': 'acceptance_email_template.txt'
        }
        
        template_filename = template_files.get(email_type, 'introduction_email_template.txt')
        
        # Try multiple possible locations for templates
        possible_paths = [
            os.path.join(project_root, 'templates', template_filename),  # Project root/templates/
            os.path.join('templates', template_filename),               # Current dir/templates/
            os.path.join('..', 'templates', template_filename),        # Parent dir/templates/
            os.path.join('..', '..', 'templates', template_filename),  # Two levels up/templates/
            template_filename                                           # Current dir/
        ]
        
        for template_path in possible_paths:
            try:
                if os.path.exists(template_path):
                    with open(template_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                        print(f"✅ Loaded {email_type} template from: {template_path}")
                        return content
            except Exception as e:
                continue
        
        # Fallback to the old template path
        try:
            with open(EMAIL_TEMPLATE_PATH, 'r', encoding='utf-8') as file:
                content = file.read()
                print(f"✅ Loaded fallback template")
                return content
        except Exception as e:
            print(f"❌ Could not load email template for {email_type}")
            return ""
    
    def get_club_research(self, club_name: str, email_type: str = 'introduction') -> Optional[str]:
        """Get research data for a club from CSV for specific email type"""
        try:
            research_df = pd.read_csv(self.research_csv_path)
            club_research = research_df[research_df['club_name'] == club_name]
            
            if not club_research.empty:
                research_entry = club_research.iloc[0]
                
                # Check if research is still valid
                expires_at = pd.to_datetime(research_entry['expires_at'])
                if datetime.now() > expires_at:
                    print(f"⏰ Research expired for {club_name}")
                    return None
                
                # Return research for specific email type
                research_columns = {
                    'introduction': 'introduction_research',
                    'checkup': 'checkup_research',
                    'acceptance': 'acceptance_research'
                }
                
                research_column = research_columns.get(email_type, 'introduction_research')
                research_data = research_entry.get(research_column, '')
                
                if research_data:
                    print(f"📋 Found {email_type} research for {club_name}")
                    return research_data
                else:
                    print(f"❌ No {email_type} research found for {club_name}")
                    return None
            
            print(f"❌ No research found for {club_name}")
            return None
            
        except FileNotFoundError:
            print(f"📁 Research file not found: {self.research_csv_path}")
            return None
        except Exception as e:
            print(f"⚠️ Error loading research for {club_name}: {e}")
            return None
    
    def is_club_research_available(self, club_name: str) -> bool:
        """Check if research is available for a club"""
        research = self.get_club_research(club_name)
        return research is not None
    
    def preview_club_research(self, club_name: str, email_type: str = 'introduction') -> Optional[str]:
        """Get research preview for a club"""
        return self.get_club_research(club_name, email_type)
    
    def check_email_sent(self, club_name: str, email_type: str = 'introduction') -> Tuple[bool, Optional[Dict]]:
        """Check if email has already been sent to a club for specific email type"""
        try:
            tracking_df = pd.read_csv(self.tracking_csv_path)
            club_record = tracking_df[
                (tracking_df['club_name'] == club_name) & 
                (tracking_df['email_type'] == email_type)
            ]
            
            if not club_record.empty:
                record = club_record.iloc[0]
                return True, {
                    'email_sent_date': record.get('email_sent_date', None),
                    'personalized_content': record.get('personalized_content', ''),
                    'generated_email': record.get('generated_email', ''),
                    'total_cost': record.get('total_cost', 0.0),
                    'created_at': record.get('created_at', None)
                }
            return False, None
        except FileNotFoundError:
            return False, None
        except Exception as e:
            print(f"Error checking email status for {club_name}: {e}")
            return False, None
    
    def generate_personalized_content(self, club_name: str, club_research: str, email_type: str = 'introduction') -> Tuple[str, Dict]:
        """Generate personalized content using research data for specific email type"""
        
        cost_tracker = CostTracker()
        
        # Email type specific prompts
        email_contexts = {
            'introduction': {
                'context': 'This is the FIRST email we\'re sending to this club. We are introducing ourselves and offering a discount for DxO products to their members.',
                'focus': 'catching their attention with recent achievements and specialties',
                'tone': 'professional and confident - this is our first impression'
            },
            'checkup': {
                'context': 'This is a FOLLOW-UP email because they didn\'t respond to our introduction. We need to create urgency and show value.',
                'focus': 'upcoming events, deadlines, and time-sensitive opportunities',
                'tone': 'friendly but urgent - showing we understand their needs'
            },
            'acceptance': {
                'context': 'This email is sent when they ACCEPT our offer. We need to explain how the discount process works.',
                'focus': 'club structure, member communication, and discount implementation',
                'tone': 'helpful and instructional - guiding them through the process'
            }
        }
        
        email_context = email_contexts.get(email_type, email_contexts['introduction'])
        
        # Different prompts for different email types
        if email_type == 'introduction':
            content_prompt = f"""
            You are writing a personalized addition for a professional marketing email from DxO Labs to a photography club.

            **EMAIL TYPE: INTRODUCTION EMAIL**
            **CONTEXT:** {email_context['context']}

            **CLUB RESEARCH FOR INTRODUCTION EMAIL:**
            {club_research}

            **YOUR TASK:**
            Generate ONLY 1-2 personalized sentences that will be inserted after this line in the email:
            "I'm Killian, part of the Partnerships team at DxO Labs, the creators of award-winning photo editing software like DxO PhotoLab and Nik Collection."

            **REQUIREMENTS:**
            - Start with "I read about..." or "I came across..." or "I noticed..." or "I was impressed by..."
            - Reference specific research findings about {club_name}
            - Focus on {email_context['focus']}
            - Connect to DxO's software benefits naturally for their specific photography focus
            - Be {email_context['tone']}
            - Maximum 2 sentences
            - Return ONLY the personalized sentences, nothing else

            **EXAMPLE OUTPUT:**
            "I read about your recent 'Urban Nights' exhibition and was impressed by the technical challenges your members tackled with low-light street photography. I believe DxO PhotoLab's industry-leading noise reduction could help your photographers push those ISO limits even further."

            **GENERATE ONLY THE PERSONALIZED SENTENCES FOR INTRODUCTION EMAIL:**
            """
        
        elif email_type == 'checkup':
            content_prompt = f"""
            You are writing a personalized addition for a follow-up email from DxO Labs to a photography club that didn't respond to the initial offer.

            **EMAIL TYPE: CHECKUP/FOLLOW-UP EMAIL**
            **CONTEXT:** {email_context['context']}

            **CLUB RESEARCH FOR CHECKUP EMAIL:**
            {club_research}

            **YOUR TASK:**
            Generate ONLY 1-2 personalized sentences that will be inserted after the greeting in a follow-up email.

            **REQUIREMENTS:**
            - Reference upcoming events, deadlines, or time-sensitive opportunities from research
            - Create urgency but remain friendly
            - Show you understand their current activities and needs
            - Connect timing to when DxO tools would be most valuable
            - Be {email_context['tone']}
            - Maximum 2 sentences
            - Return ONLY the personalized sentences, nothing else

            **EXAMPLE OUTPUT:**
            "I noticed you have your annual photography competition coming up in March and thought this might be perfect timing. Many clubs find DxO tools especially valuable when members are preparing their best work for competitions."

            **GENERATE ONLY THE PERSONALIZED SENTENCES FOR CHECKUP EMAIL:**
            """
        
        elif email_type == 'acceptance':
            content_prompt = f"""
            You are writing a personalized addition for an acceptance email from DxO Labs to a photography club that has shown interest in the partnership.

            **EMAIL TYPE: ACCEPTANCE/PARTNERSHIP EMAIL**
            **CONTEXT:** {email_context['context']}

            **CLUB RESEARCH FOR ACCEPTANCE EMAIL:**
            {club_research}

            **YOUR TASK:**
            Generate ONLY 1-2 personalized sentences that acknowledge their club structure and show understanding of how they communicate with members.

            **REQUIREMENTS:**
            - Reference their club size, organization, or communication methods from research
            - Show understanding of how they handle member benefits
            - Acknowledge their community or leadership structure
            - Be {email_context['tone']}
            - Maximum 2 sentences
            - Return ONLY the personalized sentences, nothing else

            **EXAMPLE OUTPUT:**
            "I understand you have about 50 active members and typically share benefits through your monthly newsletter. This partnership structure should work perfectly with your existing member communication process."

            **GENERATE ONLY THE PERSONALIZED SENTENCES FOR ACCEPTANCE EMAIL:**
            """
        
        else:
            # Default to introduction
            content_prompt = f"""
            You are writing a personalized addition for a professional marketing email from DxO Labs to a photography club.

            **CLUB RESEARCH:**
            {club_research}

            **YOUR TASK:**
            Generate ONLY 1-2 personalized sentences referencing specific research findings about {club_name}.

            **REQUIREMENTS:**
            - Reference specific research findings
            - Connect to DxO's software benefits
            - Maximum 2 sentences
            - Return ONLY the personalized sentences, nothing else

            **GENERATE PERSONALIZED CONTENT:**
            """
        
        try:
            response = self.openai_client.chat.completions.create(
                model=CONTENT_MODEL,
                messages=[
                    {"role": "system", "content": f"You are a professional marketing specialist for DxO Labs creating personalized content for photography club {email_type} emails. Generate ONLY the requested personalized sentences that show genuine knowledge of the club and connect to DxO software benefits. Do not include any email template or other content."},
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
            print(f"✨ Generated {email_type} personalized content for {club_name}: {len(personalized_content)} characters")
            
            return personalized_content, cost_tracker.get_costs()
            
        except Exception as e:
            print(f"❌ Error generating personalized content for {club_name}: {e}")
            fallback_content = f"I came across {club_name} and was impressed by your photography community's dedication to advancing the art of photography. I'd love to explore how DxO's professional editing tools could support your members' creative work."
            return fallback_content, cost_tracker.get_costs()
    
    def generate_personalized_email(self, club_name: str, email_type: str = 'introduction', auto_research: bool = True) -> Tuple[str, str, str, Dict]:
        """Generate complete personalized email for a club with automatic research if needed"""
        
        # Check if research is available
        club_research = self.get_club_research(club_name, email_type)
        total_costs = {'total_cost': 0.0, 'content_cost': 0.0, 'search_cost': 0.0}
        
        if not club_research and auto_research:
            print(f"🔍 No {email_type} research found for '{club_name}'. Auto-researching...")
            
            # Get club data for research
            clubs_df = self.load_clubs_data()
            club_data = clubs_df[clubs_df['Club'] == club_name]
            
            if club_data.empty:
                raise ValueError(f"Club '{club_name}' not found in clubs database")
            
            club_row = club_data.iloc[0]
            website = club_row.get('Website', '')
            country = club_row.get('Country', '')
            
            # Perform automatic research
            print(f"🔍 Researching {club_name} automatically...")
            research_results, research_costs = self.research_manager.research_club_with_o3(
                club_name, website, country
            )
            
            # Add research costs to total
            total_costs['search_cost'] += research_costs.get('total_cost', 0.0)
            total_costs['total_cost'] += research_costs.get('total_cost', 0.0)
            
            print(f"✅ Auto-research completed for {club_name}. Cost: ${research_costs.get('total_cost', 0.0):.4f}")
            
            # Now get the research we just generated
            club_research = self.get_club_research(club_name, email_type)
            
            if not club_research:
                raise ValueError(f"Auto-research failed to generate {email_type} research for '{club_name}'")
        
        elif not club_research:
            raise ValueError(f"No {email_type} research available for '{club_name}' and auto-research is disabled.")
        
        print(f"✨ Generating {email_type} email for {club_name} using available research...")
        
        # Generate personalized content
        personalized_content, content_costs = self.generate_personalized_content(club_name, club_research, email_type)
        
        # Add content costs to total
        total_costs['content_cost'] += content_costs.get('total_cost', 0.0)
        total_costs['total_cost'] += content_costs.get('total_cost', 0.0)
        
        # Load email template
        template = self.load_email_template(email_type)
        if not template:
            raise ValueError(f"Could not load email template for {email_type}")
        
        # Combine template with personalized content
        complete_email = self.combine_email_with_personalization(template, personalized_content, club_name, email_type)
        
        print(f"✅ {email_type.capitalize()} email generation completed for {club_name}")
        print(f"📝 Personalized content: {personalized_content[:100]}...")
        print(f"📧 Complete email length: {len(complete_email)} characters")
        print(f"💰 Total cost: ${total_costs['total_cost']:.4f} (Research: ${total_costs['search_cost']:.4f}, Content: ${total_costs['content_cost']:.4f})")
        
        return complete_email, personalized_content, club_research, total_costs
    
    def combine_email_with_personalization(self, template: str, personalized_content: str, club_name: str, email_type: str = 'introduction') -> str:
        """Combine the email template with personalized content based on email type"""
        
        # Replace club name placeholder
        email = template.replace("{{Company name}}", club_name)
        
        if email_type == 'introduction':
            return self._insert_introduction_personalization(email, personalized_content)
        elif email_type == 'checkup':
            return self._insert_checkup_personalization(email, personalized_content, club_name)
        elif email_type == 'acceptance':
            return self._insert_acceptance_personalization(email, personalized_content, club_name)
        else:
            # Fallback to introduction logic
            return self._insert_introduction_personalization(email, personalized_content)
    
    def _insert_introduction_personalization(self, email: str, personalized_content: str) -> str:
        """Insert personalization for introduction emails"""
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
                print(f"✅ Successfully inserted introduction personalization after Killian's introduction")
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
                    print(f"✅ Inserted introduction personalization at next paragraph break")
                    return combined_email
        
        # Fallback: append at the end before signature
        signature_start = email.find("Best regards,")
        if signature_start != -1:
            combined_email = (
                email[:signature_start] + 
                f"{personalized_content}\n\n" + 
                email[signature_start:]
            )
            print(f"✅ Inserted introduction personalization before signature")
            return combined_email
        
        return email + f"\n\n{personalized_content}"
    
    def _insert_checkup_personalization(self, email: str, personalized_content: str, club_name: str) -> str:
        """Insert personalization for checkup emails"""
        # For checkup emails, insert personalized content after the greeting
        greeting_end = email.find(f"Hello {{{{First name}}}}")
        if greeting_end == -1:
            greeting_end = email.find("Hello")
        
        if greeting_end != -1:
            # Find the end of the greeting line and next paragraph
            line_end = email.find("\n", greeting_end)
            if line_end != -1:
                next_paragraph = email.find("\n\n", line_end)
                if next_paragraph != -1:
                    # Insert personalized content after greeting
                    combined_email = (
                        email[:next_paragraph] + 
                        f"\n\n{personalized_content}" + 
                        email[next_paragraph:]
                    )
                    print(f"✅ Successfully inserted checkup personalization after greeting")
                    return combined_email
        
        # Fallback: insert before "I just wanted to follow up"
        followup_start = email.find("I just wanted to follow up")
        if followup_start != -1:
            combined_email = (
                email[:followup_start] + 
                f"{personalized_content}\n\n" + 
                email[followup_start:]
            )
            print(f"✅ Inserted checkup personalization before follow-up message")
            return combined_email
        
        # Last resort: after first paragraph
        first_paragraph_end = email.find("\n\n")
        if first_paragraph_end != -1:
            combined_email = (
                email[:first_paragraph_end] + 
                f"\n\n{personalized_content}" + 
                email[first_paragraph_end:]
            )
            print(f"✅ Inserted checkup personalization after first paragraph")
            return combined_email
        
        return email + f"\n\n{personalized_content}"
    
    def _insert_acceptance_personalization(self, email: str, personalized_content: str, club_name: str) -> str:
        """Insert personalization for acceptance emails"""
        # For acceptance emails, insert after the greeting and thank you line
        greeting_section = email.find("I hope you're doing well, and thank you again for your previous reply.")
        
        if greeting_section != -1:
            # Find the end of this sentence and insert after it
            sentence_end = email.find(".", greeting_section) + 1
            # Insert personalized content right after the greeting sentence
            combined_email = (
                email[:sentence_end] + 
                f"\n\n{personalized_content}\n\n" + 
                email[sentence_end:].lstrip()
            )
            print(f"✅ Successfully inserted acceptance personalization after greeting")
            return combined_email
        
        # Fallback: insert before the discount details
        discount_start = email.find("We'd love to offer your photography club")
        if discount_start != -1:
            combined_email = (
                email[:discount_start] + 
                f"{personalized_content}\n\n" + 
                email[discount_start:]
            )
            print(f"✅ Inserted acceptance personalization before discount details")
            return combined_email
        
        # Another fallback: after the greeting line
        greeting_line = email.find("Hello {{First name}}")
        if greeting_line == -1:
            greeting_line = email.find(f"Hello {club_name}")
        if greeting_line == -1:
            greeting_line = email.find("Hello")
        
        if greeting_line != -1:
            # Find the end of the greeting line
            line_end = email.find("\n", greeting_line)
            if line_end != -1:
                # Find the next paragraph break
                next_paragraph = email.find("\n\n", line_end)
                if next_paragraph != -1:
                    combined_email = (
                        email[:next_paragraph] + 
                        f"\n\n{personalized_content}" + 
                        email[next_paragraph:]
                    )
                    print(f"✅ Inserted acceptance personalization after greeting line")
                    return combined_email
        
        # Absolute last resort: append at the end before signature
        signature_start = email.find("Best regards,")
        if signature_start != -1:
            combined_email = (
                email[:signature_start] + 
                f"{personalized_content}\n\n" + 
                email[signature_start:]
            )
            print(f"✅ Inserted acceptance personalization before signature")
            return combined_email
        
        return email + f"\n\n{personalized_content}"
    
    def save_generated_email(self, club_name: str, personalized_content: str, generated_email: str, costs: Dict, email_type: str = 'introduction', mark_as_sent: bool = False):
        """Save generated email to CSV with cost tracking"""
        
        print(f"💾 Saving {email_type} email for {club_name}...")
        
        try:
            tracking_df = pd.read_csv(self.tracking_csv_path)
        except FileNotFoundError:
            tracking_df = pd.DataFrame(columns=[
                'club_name', 'email_type', 'email_sent_date', 'personalized_content', 
                'generated_email', 'content_cost', 'total_cost', 'created_at'
            ])
        
        email_sent_date = datetime.now().isoformat() if mark_as_sent else None
        created_at = datetime.now().isoformat()
        
        # Remove existing record if it exists
        tracking_df = tracking_df[
            ~((tracking_df['club_name'] == club_name) & (tracking_df['email_type'] == email_type))
        ]
        
        # Add new record
        new_record = pd.DataFrame([{
            'club_name': club_name,
            'email_type': email_type,
            'email_sent_date': email_sent_date,
            'personalized_content': personalized_content,
            'generated_email': generated_email,
            'content_cost': costs.get('content_cost', 0.0),
            'total_cost': costs.get('total_cost', 0.0),
            'created_at': created_at
        }])
        
        tracking_df = pd.concat([tracking_df, new_record], ignore_index=True)
        tracking_df.to_csv(self.tracking_csv_path, index=False)
        
        print(f"✅ {email_type.capitalize()} email saved for {club_name} (Cost: ${costs.get('total_cost', 0):.4f})" + (" and marked as sent" if mark_as_sent else ""))
    
    def mark_email_as_sent(self, club_name: str, email_type: str = 'introduction'):
        """Mark an email as sent"""
        try:
            tracking_df = pd.read_csv(self.tracking_csv_path)
            mask = (tracking_df['club_name'] == club_name) & (tracking_df['email_type'] == email_type)
            tracking_df.loc[mask, 'email_sent_date'] = datetime.now().isoformat()
            tracking_df.to_csv(self.tracking_csv_path, index=False)
            print(f"📤 {email_type.capitalize()} email marked as sent for {club_name}")
        except Exception as e:
            print(f"Error marking email as sent for {club_name}: {e}")
    
    def get_emails_by_type(self, email_type: str) -> List[Dict]:
        """Get all emails of specific type"""
        try:
            tracking_df = pd.read_csv(self.tracking_csv_path)
            type_emails = tracking_df[tracking_df['email_type'] == email_type]
            return type_emails.to_dict('records')
        except FileNotFoundError:
            return []
    
    def save_email_modification(self, club_name: str, modified_email: str, email_type: str = 'introduction') -> bool:
        """Save modified email content"""
        try:
            tracking_df = pd.read_csv(self.tracking_csv_path)
            mask = (tracking_df['club_name'] == club_name) & (tracking_df['email_type'] == email_type)
            tracking_df.loc[mask, 'generated_email'] = modified_email
            tracking_df.loc[mask, 'created_at'] = datetime.now().isoformat()
            tracking_df.to_csv(self.tracking_csv_path, index=False)
            return True
        except Exception as e:
            print(f"Error saving email modification: {e}")
            return False
    
    def delete_email_record(self, club_name: str, email_type: str = 'introduction') -> bool:
        """Delete email record"""
        try:
            tracking_df = pd.read_csv(self.tracking_csv_path)
            original_len = len(tracking_df)
            tracking_df = tracking_df[
                ~((tracking_df['club_name'] == club_name) & (tracking_df['email_type'] == email_type))
            ]
            tracking_df.to_csv(self.tracking_csv_path, index=False)
            return len(tracking_df) < original_len
        except Exception as e:
            print(f"Error deleting email record: {e}")
            return False 