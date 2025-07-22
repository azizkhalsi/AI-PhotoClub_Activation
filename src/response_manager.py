import pandas as pd
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
from brevo_email_service import BrevoEmailService
from club_status_manager import ClubStatusManager, ResponseStatus

class ResponseManager:
    """
    Manages email responses detection and storage.
    Integrates with Brevo API and status tracking.
    """
    
    def __init__(self):
        self.brevo_service = None
        self.status_manager = ClubStatusManager()
        self.responses_csv_path = 'data/email_responses.csv'
        
        # Initialize Brevo service if available
        try:
            self.brevo_service = BrevoEmailService()
            test_result = self.brevo_service.test_connection()
            self.brevo_available = test_result['success']
        except:
            self.brevo_available = False
            
        self._initialize_responses_csv()
    
    def _initialize_responses_csv(self):
        """Initialize CSV file for response tracking"""
        os.makedirs('data', exist_ok=True)
        
        if not os.path.exists(self.responses_csv_path):
            responses_df = pd.DataFrame(columns=[
                'response_id', 'club_name', 'contact_name', 'contact_email', 
                'email_type', 'response_type', 'response_content', 'response_date',
                'detection_method', 'processed', 'created_at'
            ])
            responses_df.to_csv(self.responses_csv_path, index=False)
    
    def check_for_new_responses(self) -> List[Dict]:
        """Check for new responses from multiple sources"""
        new_responses = []
        
        # 1. Check Brevo API for events
        if self.brevo_available:
            brevo_responses = self.brevo_service.check_for_new_responses()
            new_responses.extend(brevo_responses)
        
        # 2. Save detected responses
        for response in new_responses:
            self.save_response(
                club_name=response['club_name'],
                contact_email=response['contact_email'],
                email_type=response['email_type'],
                response_content=response['response_content'],
                response_type='positive_response',  # Default assumption
                detection_method='brevo_api'
            )
        
        return new_responses
    
    def save_response(self, club_name: str, contact_email: str, email_type: str, 
                     response_content: str, response_type: str = 'positive_response',
                     detection_method: str = 'manual') -> bool:
        """Save a response permanently"""
        try:
            # Generate response ID
            response_id = f"{club_name}_{email_type}_{int(time.time())}"
            
            # Get contact name from contacts data
            contact_name = self._get_contact_name(club_name, contact_email)
            
            # Load existing responses
            responses_df = pd.read_csv(self.responses_csv_path)
            
            # Check if this response already exists
            existing = responses_df[
                (responses_df['club_name'] == club_name) & 
                (responses_df['email_type'] == email_type) &
                (responses_df['contact_email'] == contact_email)
            ]
            
            if not existing.empty:
                print(f"Response already exists for {club_name} - {email_type}")
                return False
            
            # Add new response
            new_response = pd.DataFrame([{
                'response_id': response_id,
                'club_name': club_name,
                'contact_name': contact_name,
                'contact_email': contact_email,
                'email_type': email_type,
                'response_type': response_type,
                'response_content': response_content,
                'response_date': datetime.now().isoformat(),
                'detection_method': detection_method,
                'processed': False,
                'created_at': datetime.now().isoformat()
            }])
            
            responses_df = pd.concat([responses_df, new_response], ignore_index=True)
            responses_df.to_csv(self.responses_csv_path, index=False)
            
            # Update status manager
            self.status_manager.record_response(
                club_name=club_name,
                email_type=email_type,
                response_type=response_type,
                notes=f"Response: {response_content[:100]}..."
            )
            
            # Save to Brevo conversation if available
            if self.brevo_available:
                self.brevo_service.add_reply(
                    club_name=club_name,
                    contact_email=contact_email,
                    subject=f"Re: {email_type.title()} Email",
                    content=response_content
                )
            
            print(f"✅ Response saved for {club_name} - {email_type}")
            return True
            
        except Exception as e:
            print(f"Error saving response: {e}")
            return False
    
    def _get_contact_name(self, club_name: str, contact_email: str) -> str:
        """Get contact name from contacts CSV"""
        try:
            # Try to load contacts data
            possible_paths = [
                "test_results_20250701_092437.csv",
                "../test_results_20250701_092437.csv", 
                os.path.join(os.path.dirname(__file__), "..", "test_results_20250701_092437.csv"),
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    contacts_df = pd.read_csv(path, encoding='utf-8', on_bad_lines='skip')
                    contact = contacts_df[
                        (contacts_df['Club'] == club_name) & 
                        (contacts_df['Email'] == contact_email)
                    ]
                    if not contact.empty:
                        return contact.iloc[0].get('Name', 'Unknown')
                    break
            
            return 'Unknown'
            
        except Exception as e:
            return 'Unknown'
    
    def get_all_responses(self, club_name: str = None) -> List[Dict]:
        """Get all saved responses"""
        try:
            responses_df = pd.read_csv(self.responses_csv_path)
            
            if club_name:
                responses_df = responses_df[responses_df['club_name'] == club_name]
            
            return responses_df.to_dict('records')
            
        except Exception as e:
            print(f"Error getting responses: {e}")
            return []
    
    def get_unprocessed_responses(self) -> List[Dict]:
        """Get responses that haven't been processed yet"""
        try:
            responses_df = pd.read_csv(self.responses_csv_path)
            unprocessed = responses_df[responses_df['processed'] == False]
            return unprocessed.to_dict('records')
            
        except Exception as e:
            print(f"Error getting unprocessed responses: {e}")
            return []
    
    def mark_response_processed(self, response_id: str) -> bool:
        """Mark a response as processed"""
        try:
            responses_df = pd.read_csv(self.responses_csv_path)
            mask = responses_df['response_id'] == response_id
            
            if mask.any():
                responses_df.loc[mask, 'processed'] = True
                responses_df.to_csv(self.responses_csv_path, index=False)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error marking response processed: {e}")
            return False
    
    def get_response_stats(self) -> Dict:
        """Get response statistics"""
        try:
            responses_df = pd.read_csv(self.responses_csv_path)
            
            if responses_df.empty:
                return {'total_responses': 0}
            
            stats = {
                'total_responses': len(responses_df),
                'by_email_type': responses_df['email_type'].value_counts().to_dict(),
                'by_response_type': responses_df['response_type'].value_counts().to_dict(),
                'by_club': responses_df['club_name'].value_counts().to_dict(),
                'recent_responses': responses_df.tail(5).to_dict('records'),
                'unprocessed_count': len(responses_df[responses_df['processed'] == False])
            }
            
            return stats
            
        except Exception as e:
            print(f"Error getting response stats: {e}")
            return {}
    
    def run_response_check(self) -> Dict:
        """Run a complete response check cycle"""
        print("🔍 Starting response check...")
        
        start_time = time.time()
        
        # Check for new responses
        new_responses = self.check_for_new_responses()
        
        # Get stats
        stats = self.get_response_stats()
        
        end_time = time.time()
        
        result = {
            'success': True,
            'new_responses_found': len(new_responses),
            'total_responses': stats.get('total_responses', 0),
            'unprocessed_count': stats.get('unprocessed_count', 0),
            'duration': end_time - start_time,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"✅ Response check completed:")
        print(f"   New responses: {result['new_responses_found']}")
        print(f"   Total responses: {result['total_responses']}")
        print(f"   Duration: {result['duration']:.2f}s")
        
        return result


def main():
    """Main function for running response manager"""
    response_manager = ResponseManager()
    
    # Run response check
    result = response_manager.run_response_check()
    
    # Show unprocessed responses
    unprocessed = response_manager.get_unprocessed_responses()
    if unprocessed:
        print(f"\n📋 {len(unprocessed)} unprocessed responses:")
        for response in unprocessed[:5]:  # Show first 5
            print(f"   {response['club_name']} - {response['email_type']} ({response['response_date'][:10]})")


if __name__ == "__main__":
    main() 