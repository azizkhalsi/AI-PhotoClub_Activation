# Configuration Setup Guide

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```bash
# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=your_openai_api_key_here

# Model Configuration (Optional - defaults provided)
SEARCH_MODEL=o3
CONTENT_MODEL=gpt-4.1-nano

# Data Configuration (Optional - defaults provided)
CLUBS_CSV_PATH=test_results_20250701_092437.csv
EMAIL_TEMPLATE_PATH=Introduction Email
```

## Getting Your OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Sign in to your OpenAI account
3. Click "Create new secret key"
4. Copy the API key and paste it in your `.env` file

## Data Source

The application uses the CSV file `test_results_20250701_092437.csv` as the source of photography club data. Email tracking is stored in `sent_emails_tracking.csv` which will be created automatically.

## Quick Start

1. Create your `.env` file with your OpenAI API key
2. Run: `source venv/bin/activate`
3. Run: `streamlit run app.py`
