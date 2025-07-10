import requests
import json
import pandas as pd
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
from dotenv import load_dotenv

# Load environment variables from .env file
# Look for .env in current directory first, then parent directory
if os.path.exists('.env'):
    load_dotenv('.env')
elif os.path.exists('../.env'):
    load_dotenv('../.env')
else:
    load_dotenv()  # Try default locations

class BrevoEmailService:
    """
    Brevo (formerly Sendinblue) email service for sending and tracking emails
    """
    
    def __init__(self, api_key: str = None):
        """Initialize Brevo service with API key"""
        self.api_key = api_key or os.getenv('BREVO_API_KEY')
        if not self.api_key:
            raise ValueError("Brevo API key is required. Set BREVO_API_KEY environment variable.")
        
        self.base_url = "https://api.brevo.com/v3"
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "api-key": self.api_key
        }
        
        # Initialize email tracking CSV
        self.email_tracking_file = "data/email_tracking.csv"
        self.conversation_file = "data/email_conversations.csv"
        self._ensure_tracking_files()
    
    def _ensure_tracking_files(self):
        """Ensure tracking CSV files exist with proper headers"""
        os.makedirs("data", exist_ok=True)
        
        # Email tracking file
        if not os.path.exists(self.email_tracking_file):
            tracking_df = pd.DataFrame(columns=[
                'email_id', 'club_name', 'contact_name', 'contact_email', 'contact_role',
                'email_type', 'subject', 'content', 'sent_datetime', 'delivery_status',
                'opened_datetime', 'clicked_datetime', 'replied_datetime', 'brevo_message_id',
                'response_content', 'conversation_id'
            ])
            tracking_df.to_csv(self.email_tracking_file, index=False)
        
        # Conversation file
        if not os.path.exists(self.conversation_file):
            conversation_df = pd.DataFrame(columns=[
                'conversation_id', 'club_name', 'contact_name', 'contact_email',
                'message_datetime', 'message_type', 'subject', 'content', 
                'sender', 'message_id', 'status'
            ])
            conversation_df.to_csv(self.conversation_file, index=False)
    
    def send_email(self, to_email: str, to_name: str, subject: str, content: str, 
                   club_name: str, contact_role: str, email_type: str) -> Dict:
        """
        Send email via Brevo API
        
        Args:
            to_email: Recipient email address
            to_name: Recipient name
            subject: Email subject
            content: Email content (HTML)
            club_name: Photography club name
            contact_role: Contact's role in the club
            email_type: Type of email (introduction, checkup, acceptance)
            
        Returns:
            Dict with success status and message details
        """
        try:
            # Create email payload
            sender_email = os.getenv('BREVO_SENDER_EMAIL', 'noreply@yourdomain.com')
            sender_name = os.getenv('BREVO_SENDER_NAME', 'Photo Club Partnerships')
            
            payload = {
                "sender": {
                    "name": sender_name,
                    "email": sender_email  # Configure via BREVO_SENDER_EMAIL environment variable
                },
                "to": [
                    {
                        "email": to_email,
                        "name": to_name
                    }
                ],
                "subject": subject,
                "htmlContent": self._format_html_content(content),
                "textContent": self._strip_html(content),
                "tags": [f"club:{club_name}", f"type:{email_type}", f"role:{contact_role}"],
                "headers": {
                    "X-Mailin-custom": json.dumps({
                        "club_name": club_name,
                        "email_type": email_type,
                        "contact_role": contact_role
                    })
                }
            }
            
            # Send email via Brevo API
            response = requests.post(
                f"{self.base_url}/smtp/email",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 201:
                result = response.json()
                message_id = result.get('messageId')
                
                # Save to tracking
                self._save_email_tracking(
                    club_name=club_name,
                    contact_name=to_name,
                    contact_email=to_email,
                    contact_role=contact_role,
                    email_type=email_type,
                    subject=subject,
                    content=content,
                    brevo_message_id=message_id
                )
                
                return {
                    'success': True,
                    'message_id': message_id,
                    'message': 'Email sent successfully'
                }
            else:
                error_msg = response.json().get('message', 'Unknown error')
                return {
                    'success': False,
                    'error': f"Failed to send email: {error_msg}",
                    'status_code': response.status_code
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Email sending error: {str(e)}"
            }
    
    def _format_html_content(self, content: str) -> str:
        """Convert plain text content to HTML format"""
        if not content.startswith('<html>'):
            # Convert line breaks to HTML
            html_content = content.replace('\n', '<br>')
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    {html_content}
                </div>
            </body>
            </html>
            """
            return html_content
        return content
    
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags for plain text version"""
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', html_content)
    
    def _save_email_tracking(self, club_name: str, contact_name: str, contact_email: str,
                           contact_role: str, email_type: str, subject: str, content: str,
                           brevo_message_id: str):
        """Save email tracking information"""
        try:
            # Generate unique email ID and conversation ID
            email_id = f"{club_name}_{contact_email}_{int(time.time())}"
            conversation_id = f"{club_name}_{contact_email}"
            
            # Load existing tracking data
            tracking_df = pd.read_csv(self.email_tracking_file)
            
            # Add new email record
            new_record = {
                'email_id': email_id,
                'club_name': club_name,
                'contact_name': contact_name,
                'contact_email': contact_email,
                'contact_role': contact_role,
                'email_type': email_type,
                'subject': subject,
                'content': content,
                'sent_datetime': datetime.now().isoformat(),
                'delivery_status': 'sent',
                'opened_datetime': '',
                'clicked_datetime': '',
                'replied_datetime': '',
                'brevo_message_id': brevo_message_id,
                'response_content': '',
                'conversation_id': conversation_id
            }
            
            tracking_df = pd.concat([tracking_df, pd.DataFrame([new_record])], ignore_index=True)
            tracking_df.to_csv(self.email_tracking_file, index=False)
            
            # Add to conversation
            self._add_to_conversation(
                conversation_id=conversation_id,
                club_name=club_name,
                contact_name=contact_name,
                contact_email=contact_email,
                subject=subject,
                content=content,
                message_type='sent',
                sender='us'
            )
            
        except Exception as e:
            print(f"Error saving email tracking: {e}")
    
    def _add_to_conversation(self, conversation_id: str, club_name: str, contact_name: str,
                           contact_email: str, subject: str, content: str, message_type: str,
                           sender: str, message_id: str = None):
        """Add message to conversation history"""
        try:
            conversation_df = pd.read_csv(self.conversation_file)
            
            new_message = {
                'conversation_id': conversation_id,
                'club_name': club_name,
                'contact_name': contact_name,
                'contact_email': contact_email,
                'message_datetime': datetime.now().isoformat(),
                'message_type': message_type,
                'subject': subject,
                'content': content,
                'sender': sender,
                'message_id': message_id or '',
                'status': 'delivered' if message_type == 'sent' else 'received'
            }
            
            conversation_df = pd.concat([conversation_df, pd.DataFrame([new_message])], ignore_index=True)
            conversation_df.to_csv(self.conversation_file, index=False)
            
        except Exception as e:
            print(f"Error adding to conversation: {e}")
    
    def get_conversation(self, club_name: str, contact_email: str) -> List[Dict]:
        """Get conversation history for a specific club contact"""
        try:
            conversation_df = pd.read_csv(self.conversation_file)
            conversation_id = f"{club_name}_{contact_email}"
            
            messages = conversation_df[conversation_df['conversation_id'] == conversation_id]
            messages = messages.sort_values('message_datetime')
            
            return messages.to_dict('records')
        except Exception as e:
            print(f"Error getting conversation: {e}")
            return []
    
    def get_email_metrics(self, club_name: str = None) -> Dict:
        """Get email metrics and statistics"""
        try:
            tracking_df = pd.read_csv(self.email_tracking_file)
            
            if club_name:
                tracking_df = tracking_df[tracking_df['club_name'] == club_name]
            
            metrics = {
                'total_sent': len(tracking_df),
                'total_opened': len(tracking_df[tracking_df['opened_datetime'] != '']),
                'total_clicked': len(tracking_df[tracking_df['clicked_datetime'] != '']),
                'total_replied': len(tracking_df[tracking_df['replied_datetime'] != '']),
                'by_email_type': tracking_df['email_type'].value_counts().to_dict(),
                'by_club': tracking_df['club_name'].value_counts().to_dict() if not club_name else {},
                'recent_activity': tracking_df.tail(10).to_dict('records')
            }
            
            # Calculate rates
            if metrics['total_sent'] > 0:
                metrics['open_rate'] = (metrics['total_opened'] / metrics['total_sent']) * 100
                metrics['click_rate'] = (metrics['total_clicked'] / metrics['total_sent']) * 100
                metrics['reply_rate'] = (metrics['total_replied'] / metrics['total_sent']) * 100
            else:
                metrics['open_rate'] = metrics['click_rate'] = metrics['reply_rate'] = 0
            
            return metrics
        except Exception as e:
            print(f"Error getting metrics: {e}")
            return {}
    
    def update_email_status(self, brevo_message_id: str, status_type: str, timestamp: str = None):
        """Update email status (opened, clicked, replied)"""
        try:
            tracking_df = pd.read_csv(self.email_tracking_file)
            mask = tracking_df['brevo_message_id'] == brevo_message_id
            
            if mask.any():
                timestamp = timestamp or datetime.now().isoformat()
                
                if status_type == 'opened':
                    tracking_df.loc[mask, 'opened_datetime'] = timestamp
                elif status_type == 'clicked':
                    tracking_df.loc[mask, 'clicked_datetime'] = timestamp
                elif status_type == 'replied':
                    tracking_df.loc[mask, 'replied_datetime'] = timestamp
                
                tracking_df.to_csv(self.email_tracking_file, index=False)
                return True
            return False
        except Exception as e:
            print(f"Error updating email status: {e}")
            return False
    
    def add_reply(self, club_name: str, contact_email: str, subject: str, content: str):
        """Add a received reply to the conversation"""
        conversation_id = f"{club_name}_{contact_email}"
        
        # Get contact details
        tracking_df = pd.read_csv(self.email_tracking_file)
        contact_info = tracking_df[
            (tracking_df['club_name'] == club_name) & 
            (tracking_df['contact_email'] == contact_email)
        ].iloc[-1] if len(tracking_df) > 0 else {}
        
        contact_name = contact_info.get('contact_name', 'Unknown')
        
        self._add_to_conversation(
            conversation_id=conversation_id,
            club_name=club_name,
            contact_name=contact_name,
            contact_email=contact_email,
            subject=subject,
            content=content,
            message_type='received',
            sender='contact'
        )
        
        # Update reply status in tracking
        mask = (tracking_df['club_name'] == club_name) & (tracking_df['contact_email'] == contact_email)
        if mask.any():
            tracking_df.loc[mask, 'replied_datetime'] = datetime.now().isoformat()
            tracking_df.loc[mask, 'response_content'] = content[:500]  # Store first 500 chars
            tracking_df.to_csv(self.email_tracking_file, index=False)
    
    def test_connection(self) -> Dict:
        """Test Brevo API connection"""
        try:
            response = requests.get(
                f"{self.base_url}/account",
                headers=self.headers
            )
            
            if response.status_code == 200:
                account_info = response.json()
                return {
                    'success': True,
                    'message': 'Brevo connection successful',
                    'account': account_info.get('email', 'Unknown')
                }
            else:
                return {
                    'success': False,
                    'error': f"Connection failed: {response.status_code}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': f"Connection error: {str(e)}"
            } 