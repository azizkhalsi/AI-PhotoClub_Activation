# Brevo API Key Troubleshooting

## Solutions to Try:

### 1. Verify API Key in Brevo Dashboard
- Go to [Brevo Dashboard](https://app.brevo.com/)
- Navigate to **Settings** > **API Keys**
- Check if your API key exists and is **Active**
- Verify the key matches exactly (copy-paste to be sure)

### 2. Check API Key Permissions
Your API key needs specific permissions:
- ✅ **Send emails** (required)
- ✅ **View email campaigns** (recommended)
- ✅ **Manage contacts** (optional)

### 3. Verify Account Status
- Ensure your Brevo account is active
- Check if there are any billing issues
- Verify email sending limits haven't been exceeded

### 4. Generate New API Key
If the current key isn't working:
1. Delete the existing API key in Brevo dashboard
2. Create a new API key with required permissions
3. Update your `.env` file with the new key

### 5. Test with Postman/curl
Test your API key directly:
```bash
curl -X GET "https://api.brevo.com/v3/account" \
  -H "accept: application/json" \
  -H "api-key: YOUR_API_KEY_HERE"
```

## Sender Email Configuration
You'll also need to set up a verified sender email:

1. Add to `.env` file:
```
BREVO_SENDER_EMAIL=your-verified-email@yourdomain.com
BREVO_SENDER_NAME=Your Name
```

2. Verify the sender email in Brevo dashboard:
   - Go to **Settings** > **Sender Addresses**
   - Add and verify your email address

## Current Workaround
The application will continue to work without Brevo:
- Email generation still works
- Conversation viewing works (for existing data)
- Only sending new emails is disabled

## Contact Support
If issues persist, contact Brevo support with:
- Your account email
- The API key causing issues
- Screenshots of any error messages 
