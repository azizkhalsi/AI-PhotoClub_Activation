import pandas as pd
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum

class ResponseStatus(Enum):
    """Enum for different response statuses"""
    NO_EMAIL_SENT = "no_email_sent"
    EMAIL_SENT = "email_sent"
    POSITIVE_RESPONSE = "positive_response"
    NEGATIVE_RESPONSE = "negative_response"
    NO_RESPONSE = "no_response"
    FOLLOW_UP_NEEDED = "follow_up_needed"

class EmailType(Enum):
    """Enum for email types"""
    INTRODUCTION = "introduction"
    CHECKUP = "checkup" 
    ACCEPTANCE = "acceptance"

class ClubStatusManager:
    """Manages club statuses, responses, and notifications"""
    
    def __init__(self):
        self.status_csv_path = 'data/club_status_tracking.csv'
        self.notifications_csv_path = 'data/notifications.csv'
        self._initialize_csv_files()
    
    def _initialize_csv_files(self):
        """Initialize CSV files for club status tracking and notifications"""
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Initialize club status tracking CSV
        if not os.path.exists(self.status_csv_path):
            status_df = pd.DataFrame({
                'club_name': pd.Series(dtype='str'),
                'country': pd.Series(dtype='str'), 
                'website': pd.Series(dtype='str'),
                # Introduction email tracking
                'introduction_sent_date': pd.Series(dtype='str'),
                'introduction_status': pd.Series(dtype='str'),
                'introduction_response_date': pd.Series(dtype='str'),
                'introduction_response_type': pd.Series(dtype='str'),
                'introduction_notes': pd.Series(dtype='str'),
                # Checkup email tracking  
                'checkup_sent_date': pd.Series(dtype='str'),
                'checkup_status': pd.Series(dtype='str'),
                'checkup_response_date': pd.Series(dtype='str'),
                'checkup_response_type': pd.Series(dtype='str'),
                'checkup_notes': pd.Series(dtype='str'),
                # Acceptance email tracking
                'acceptance_sent_date': pd.Series(dtype='str'),
                'acceptance_status': pd.Series(dtype='str'),
                'acceptance_response_date': pd.Series(dtype='str'),
                'acceptance_response_type': pd.Series(dtype='str'),
                'acceptance_notes': pd.Series(dtype='str'),
                # Overall status
                'current_stage': pd.Series(dtype='str'),
                'priority_level': pd.Series(dtype='str'),
                'last_activity_date': pd.Series(dtype='str'),
                'created_at': pd.Series(dtype='str'),
                'updated_at': pd.Series(dtype='str')
            })
            status_df.to_csv(self.status_csv_path, index=False)
        
        # Initialize notifications CSV
        if not os.path.exists(self.notifications_csv_path):
            notifications_df = pd.DataFrame(columns=[
                'notification_id', 'club_name', 'email_type', 'notification_type',
                'message', 'is_read', 'created_at', 'read_at'
            ])
            notifications_df.to_csv(self.notifications_csv_path, index=False)
    
    def update_email_sent(self, club_name: str, email_type: str, notes: str = ""):
        """Update status when an email is sent"""
        try:
            df = pd.read_csv(self.status_csv_path)
            
            # Find or create club record
            club_idx = df[df['club_name'] == club_name].index
            if len(club_idx) == 0:
                # Create new record
                new_record = {
                    'club_name': club_name,
                    'current_stage': email_type,
                    'priority_level': 'medium',
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'last_activity_date': datetime.now().isoformat()
                }
                df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
                club_idx = [len(df) - 1]
            
            # Update email sent information
            idx = club_idx[0]
            df.loc[idx, f'{email_type}_sent_date'] = datetime.now().isoformat()
            df.loc[idx, f'{email_type}_status'] = ResponseStatus.EMAIL_SENT.value
            df.loc[idx, f'{email_type}_notes'] = notes
            df.loc[idx, 'current_stage'] = email_type
            df.loc[idx, 'last_activity_date'] = datetime.now().isoformat()
            df.loc[idx, 'updated_at'] = datetime.now().isoformat()
            
            df.to_csv(self.status_csv_path, index=False)
            
            # Create notification
            self._create_notification(
                club_name, 
                email_type, 
                'email_sent',
                f"{email_type.title()} email sent to {club_name}"
            )
            
            return True
            
        except Exception as e:
            print(f"Error updating email sent status: {e}")
            return False
    
    def record_response(self, club_name: str, email_type: str, response_type: str, notes: str = ""):
        """Record a response from a club"""
        try:
            df = pd.read_csv(self.status_csv_path)
            
            club_idx = df[df['club_name'] == club_name].index
            if len(club_idx) == 0:
                return False
            
            idx = club_idx[0]
            df.loc[idx, f'{email_type}_response_date'] = datetime.now().isoformat()
            df.loc[idx, f'{email_type}_response_type'] = response_type
            df.loc[idx, f'{email_type}_status'] = response_type
            df.loc[idx, f'{email_type}_notes'] = notes
            df.loc[idx, 'last_activity_date'] = datetime.now().isoformat()
            df.loc[idx, 'updated_at'] = datetime.now().isoformat()
            
            # Update current stage based on response
            if response_type == ResponseStatus.POSITIVE_RESPONSE.value:
                if email_type == 'introduction':
                    df.loc[idx, 'current_stage'] = 'checkup'
                elif email_type == 'checkup':
                    df.loc[idx, 'current_stage'] = 'acceptance'
                elif email_type == 'acceptance':
                    df.loc[idx, 'current_stage'] = 'partnership_active'
                df.loc[idx, 'priority_level'] = 'high'
            elif response_type == ResponseStatus.NEGATIVE_RESPONSE.value:
                df.loc[idx, 'current_stage'] = 'not_interested'
                df.loc[idx, 'priority_level'] = 'low'
            
            df.to_csv(self.status_csv_path, index=False)
            
            # Create notification for new response
            self._create_notification(
                club_name,
                email_type, 
                'response_received',
                f"New {response_type.replace('_', ' ')} response from {club_name}"
            )
            
            return True
            
        except Exception as e:
            print(f"Error recording response: {e}")
            return False
    
    def _create_notification(self, club_name: str, email_type: str, notification_type: str, message: str):
        """Create a new notification"""
        try:
            df = pd.read_csv(self.notifications_csv_path)
            
            new_notification = {
                'notification_id': f"{club_name}_{email_type}_{notification_type}_{int(datetime.now().timestamp())}",
                'club_name': club_name,
                'email_type': email_type,
                'notification_type': notification_type,
                'message': message,
                'is_read': False,
                'created_at': datetime.now().isoformat(),
                'read_at': None
            }
            
            df = pd.concat([df, pd.DataFrame([new_notification])], ignore_index=True)
            df.to_csv(self.notifications_csv_path, index=False)
            
        except Exception as e:
            print(f"Error creating notification: {e}")
    
    def get_club_status(self, club_name: str) -> Optional[Dict]:
        """Get complete status information for a club"""
        try:
            df = pd.read_csv(self.status_csv_path)
            club_data = df[df['club_name'] == club_name]
            
            if club_data.empty:
                return None
            
            return club_data.iloc[0].to_dict()
            
        except Exception as e:
            print(f"Error getting club status: {e}")
            return None
    
    def get_clubs_by_status(self, email_type: str = None, status: str = None, stage: str = None) -> List[Dict]:
        """Get clubs filtered by status criteria"""
        try:
            df = pd.read_csv(self.status_csv_path)
            
            if df.empty:
                return []
            
            # Apply filters
            if email_type and status:
                df = df[df[f'{email_type}_status'] == status]
            
            if stage:
                df = df[df['current_stage'] == stage]
            
            return df.to_dict('records')
            
        except Exception as e:
            print(f"Error getting clubs by status: {e}")
            return []
    
    def get_unread_notifications(self) -> List[Dict]:
        """Get all unread notifications"""
        try:
            df = pd.read_csv(self.notifications_csv_path)
            unread = df[df['is_read'] == False].sort_values('created_at', ascending=False)
            return unread.to_dict('records')
            
        except Exception as e:
            print(f"Error getting notifications: {e}")
            return []
    
    def mark_notification_read(self, notification_id: str):
        """Mark a notification as read"""
        try:
            df = pd.read_csv(self.notifications_csv_path)
            
            notification_idx = df[df['notification_id'] == notification_id].index
            if len(notification_idx) > 0:
                idx = notification_idx[0]
                df.loc[idx, 'is_read'] = True
                df.loc[idx, 'read_at'] = datetime.now().isoformat()
                df.to_csv(self.notifications_csv_path, index=False)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error marking notification as read: {e}")
            return False
    
    def get_dashboard_stats(self) -> Dict:
        """Get statistics for the dashboard"""
        try:
            df = pd.read_csv(self.status_csv_path)
            
            if df.empty:
                return {
                    'total_clubs': 0,
                    'introduction_sent': 0,
                    'checkup_sent': 0,
                    'acceptance_sent': 0,
                    'positive_responses': 0,
                    'awaiting_response': 0,
                    'pipeline_stages': {}
                }
            
            stats = {
                'total_clubs': len(df),
                'introduction_sent': len(df[df['introduction_status'] == ResponseStatus.EMAIL_SENT.value]),
                'checkup_sent': len(df[df['checkup_status'] == ResponseStatus.EMAIL_SENT.value]),
                'acceptance_sent': len(df[df['acceptance_status'] == ResponseStatus.EMAIL_SENT.value]),
                'positive_responses': len(df[
                    (df['introduction_status'] == ResponseStatus.POSITIVE_RESPONSE.value) |
                    (df['checkup_status'] == ResponseStatus.POSITIVE_RESPONSE.value) |
                    (df['acceptance_status'] == ResponseStatus.POSITIVE_RESPONSE.value)
                ]),
                'awaiting_response': len(df[
                    (df['introduction_status'] == ResponseStatus.EMAIL_SENT.value) |
                    (df['checkup_status'] == ResponseStatus.EMAIL_SENT.value) |
                    (df['acceptance_status'] == ResponseStatus.EMAIL_SENT.value)
                ])
            }
            
            # Pipeline stages
            if 'current_stage' in df.columns:
                stage_counts = df['current_stage'].value_counts().to_dict()
                stats['pipeline_stages'] = stage_counts
            else:
                stats['pipeline_stages'] = {}
            
            return stats
            
        except Exception as e:
            print(f"Error getting dashboard stats: {e}")
            return {}
    
    def get_clubs_needing_follow_up(self, days_since_sent: int = 7) -> List[Dict]:
        """Get clubs that need follow-up (no response after X days)"""
        try:
            df = pd.read_csv(self.status_csv_path)
            
            if df.empty:
                return []
            
            cutoff_date = datetime.now() - timedelta(days=days_since_sent)
            follow_up_needed = []
            
            for _, club in df.iterrows():
                # Check each email type for follow-up needs
                for email_type in ['introduction', 'checkup', 'acceptance']:
                    sent_date_col = f'{email_type}_sent_date'
                    status_col = f'{email_type}_status'
                    
                    if pd.notna(club.get(sent_date_col)) and club.get(status_col) == ResponseStatus.EMAIL_SENT.value:
                        sent_date = datetime.fromisoformat(club[sent_date_col])
                        if sent_date < cutoff_date:
                            follow_up_needed.append({
                                'club_name': club['club_name'],
                                'email_type': email_type,
                                'sent_date': sent_date.isoformat(),
                                'days_since_sent': (datetime.now() - sent_date).days
                            })
            
            return follow_up_needed
            
        except Exception as e:
            print(f"Error getting follow-up clubs: {e}")
            return [] 