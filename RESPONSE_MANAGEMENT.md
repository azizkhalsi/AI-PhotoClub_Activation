# Email Response Management System

The response management system automatically detects and permanently saves email responses from photography clubs, ensuring no responses are lost over time.

## 🚀 Quick Start

### 1. Automatic Response Detection
```bash
# Check for new responses manually
python check_responses.py

# Check for new responses every 30 minutes (cron)
*/30 * * * * cd /path/to/project && python check_responses.py
```

### 2. Manual Response Entry
Use the Club Contacts page → Response Manager section to manually add responses you receive outside the system.

## 📁 Data Storage

The system creates permanent CSV files that won't be deleted:

- **`data/email_responses.csv`** - All responses with full content
- **`data/email_tracking.csv`** - Email send/receive tracking  
- **`data/email_conversations.csv`** - Conversation threads

## 🛠️ Features

### Automatic Detection
- **Brevo API Integration**: Fetches email events (opens, clicks, deliveries)
- **Response Simulation**: Detects potential responses based on email opens
- **Webhook Support**: Can be configured for real-time response detection

### Manual Entry
- **Club Contacts Page**: Add responses through the Response Manager section
- **Response Types**: Positive, Negative, Neutral responses
- **Full Content**: Save complete response text for reference

### Permanent Storage
- **CSV Persistence**: All data saved to CSV files that persist between sessions
- **No Data Loss**: Responses are never deleted or overwritten
- **Duplicate Prevention**: System prevents saving the same response twice

## 🎯 How It Works

### 1. Email Sending
When you send an email via Brevo:
```
Club Email Sent → Brevo API → Tracking CSV → Status Manager
```

### 2. Response Detection
The system checks for responses:
```
Brevo API Events → Response Detection → CSV Storage → Status Update
```

### 3. Manual Addition
For responses received outside the system:
```
Manual Entry → Response Manager → CSV Storage → Status Update
```

## 📊 Club Contacts Integration

The **Response Manager** section in Club Contacts provides:

### Check New Responses
- **🔍 Check New Responses** button fetches latest from Brevo API
- Shows count of new responses found
- Updates all tracking systems automatically

### Response Statistics
- **Total Responses**: Count of all responses in system
- **Unprocessed**: Responses that need attention
- **Warning alerts** for unprocessed responses

### Manual Response Entry
- **📝 Add Manual Response** expander for manual entry
- **Email Type**: Introduction, Checkup, or Acceptance
- **Response Type**: Positive, Negative, or Neutral
- **Full Content**: Complete response text

### Response History
- **📋 Existing Responses** shows last 3 responses for selected club
- Date, type, and preview of response content
- Quick visual overview of club communication

## 🔧 Configuration

### Brevo API Setup
1. Ensure `BREVO_API_KEY` is set in `.env`
2. Verify API permissions include email events
3. Test connection using the Club Contacts page

### Automated Checking
Set up cron job for automatic response checking:
```bash
# Every 30 minutes
*/30 * * * * cd /path/to/project && python check_responses.py

# Daily at 9 AM
0 9 * * * cd /path/to/project && python check_responses.py
```

## 📈 Response Types

### Positive Response
- Club is interested in partnership
- Wants to learn more
- Ready to move to next step

### Negative Response  
- Club declines partnership
- Not interested at this time
- Has existing partnerships

### Neutral Response
- Acknowledgment without commitment
- Request for more information
- Needs time to consider

## 🔍 Monitoring

### CLI Monitoring
```bash
# Check current status
python check_responses.py

# Get help
python check_responses.py --help
```

### Web Interface
- Use Club Contacts page Response Manager
- Check response statistics
- View conversation history with full content

## 📝 Data Format

### Response CSV Structure
```csv
response_id,club_name,contact_name,contact_email,email_type,response_type,response_content,response_date,detection_method,processed,created_at
CLUB_intro_1641234567,Sample Club,John Doe,john@club.com,introduction,positive_response,"Thank you for reaching out...",2024-01-01T10:00:00,manual,false,2024-01-01T10:00:00
```

### Response Fields
- **response_id**: Unique identifier
- **club_name**: Photography club name
- **contact_name**: Person who responded
- **email_type**: introduction/checkup/acceptance
- **response_type**: positive/negative/neutral
- **response_content**: Full response text
- **detection_method**: manual/brevo_api/webhook
- **processed**: Whether response has been handled

## 🚨 Troubleshooting

### No Responses Detected
1. Check Brevo API key configuration
2. Verify clubs have been sent emails
3. Ensure email events are enabled in Brevo

### Duplicate Responses
- System automatically prevents duplicates
- Based on club + email type combination
- Manual entries check existing responses

### Missing Response Data
- Check `data/` directory permissions
- Verify CSV files are not corrupted
- Run response checker to rebuild data

## 🎉 Benefits

### Never Lose Responses
- **Permanent Storage**: All responses saved to CSV files
- **Backup Safe**: Data persists even if application restarts
- **Historical Record**: Complete communication history

### Automated Workflow
- **API Integration**: Automatically detects responses
- **Status Updates**: Updates club tracking automatically  
- **Time Saving**: Reduces manual response tracking

### Complete Visibility
- **Full Conversation**: See entire email exchange
- **Response Analytics**: Track response rates by email type
- **Club Progress**: Monitor partnership progress over time

---

**Ready to use?** Check for responses by running `python check_responses.py` or use the Response Manager in Club Contacts! 