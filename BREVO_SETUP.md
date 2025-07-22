# Brevo Email Service Setup

## 🚀 Quick Setup

### 1. Get Brevo API Key
1. Sign up at [Brevo.com](https://www.brevo.com) (formerly Sendinblue)
2. Go to **Settings > API Keys**
3. Create a new API key with **Send emails** permission
4. Copy the API key

### 2. Environment Configuration
Add your API key and sender configuration to environment variables:

```bash
# Option 1: Set environment variables
export BREVO_API_KEY="your-api-key-here"
export BREVO_SENDER_EMAIL="akhalsi@dxo.com"
export BREVO_SENDER_NAME="Aziz Khalsi - DxO Labs Partnerships"

# Option 2: Add to .env file
echo "BREVO_API_KEY=your-api-key-here" >> .env
echo "BREVO_SENDER_EMAIL=akhalsi@dxo.com" >> .env
echo "BREVO_SENDER_NAME=Aziz Khalsi - DxO Labs Partnerships" >> .env
```

### 3. Sender Email Configuration ✅ **Already Configured**
The sender email is now set to **akhalsi@dxo.com** by default. You can override this by setting the `BREVO_SENDER_EMAIL` environment variable if needed.

**Current Configuration:**
- **Email**: akhalsi@dxo.com  
- **Name**: Aziz Khalsi - DxO Labs Partnerships

**Important**: Make sure `akhalsi@dxo.com` is verified in your Brevo account dashboard under **Senders & IP** section.

## 📧 Features

### Email Sending
- Send personalized emails via Brevo API
- HTML and plain text versions
- Custom headers and tags for tracking

### Email Tracking
- Delivery status monitoring
- Open and click tracking
- Reply detection and conversation threading

### Conversation Management
- Full email history per contact
- Sent/received message threading
- Manual reply addition

### Analytics & Metrics
- Club-level email statistics
- Open rates and reply rates
- Email type performance tracking

## 📱 Pages

### Email Generator
- **Purpose**: Generate personalized emails with AI
- **Features**: Auto-research, email editing, basic sending
- **Best for**: Creating email content and templates

### Club Contacts
- **Purpose**: Targeted email sending to specific contacts
- **Features**: Person selection, Brevo sending, conversation view
- **Best for**: Managing ongoing relationships with clubs

## 📊 Data Storage

### Email Tracking (`data/email_tracking.csv`)
Stores all sent emails with metadata:
- Email ID, club name, contact details
- Send timestamps, delivery status
- Open/click/reply tracking
- Brevo message IDs

### Conversation History (`data/email_conversations.csv`)
Stores conversation threads:
- Message timeline
- Sent vs received messages
- Subject and content history
- Sender identification

## 🛠️ API Usage

### Test Connection
```python
from src.brevo_email_service import BrevoEmailService

brevo = BrevoEmailService()
result = brevo.test_connection()
print(result)  # Should show success if configured correctly
```

### Send Email
```python
result = brevo.send_email(
    to_email="contact@club.com",
    to_name="Club President",
    subject="Partnership Opportunity",
    content="Your email content here...",
    club_name="Sample Camera Club",
    contact_role="President",
    email_type="introduction"
)
```

### Get Metrics
```python
metrics = brevo.get_email_metrics("Sample Camera Club")
print(f"Reply rate: {metrics['reply_rate']:.1f}%")
```

## 🔧 Troubleshooting

### API Key Issues
- Ensure key has **Send emails** permission
- Verify environment variable is set correctly
- Check `.env` file is in project root

### Sender Email
- **akhalsi@dxo.com** must be verified in Brevo dashboard
- Check **Senders & IP** section in Brevo to verify this email
- DxO domain should provide excellent deliverability
- If using a different sender email, set `BREVO_SENDER_EMAIL` environment variable

### File Permissions
- Ensure `data/` directory is writable
- CSV files will be created automatically

### Testing
```bash
# Test without sending emails
python -c "
from src.brevo_email_service import BrevoEmailService
try:
    service = BrevoEmailService()
    print('✅ Brevo service initialized successfully')
    result = service.test_connection()
    print(f'Connection: {result}')
except Exception as e:
    print(f'❌ Error: {e}')
"
```

## 📈 Best Practices

### Email Content
- Keep subjects under 50 characters
- Include clear call-to-action
- Personalize with club-specific details

### Tracking
- Allow 24-48 hours for accurate metrics
- Monitor reply rates by email type
- Use conversation view for follow-ups

### Data Management
- Backup CSV files regularly
- Clean old conversation data periodically
- Monitor API usage in Brevo dashboard

## 🎯 Workflow

1. **Research Phase**: Use Email Generator to create content
2. **Targeting Phase**: Use Club Contacts to select specific people
3. **Sending Phase**: Send via Brevo with tracking
4. **Follow-up Phase**: Monitor conversations and reply rates
5. **Analytics Phase**: Review metrics and optimize

---

**Need Help?** Check the Brevo documentation or contact support. 