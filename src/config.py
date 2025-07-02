import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SEARCH_MODEL = os.getenv('SEARCH_MODEL', 'o3')  # O3 for web search research
CONTENT_MODEL = os.getenv('CONTENT_MODEL', 'gpt-4.1-nano')  # GPT-4.1-nano for content generation

# Database Configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', 'email_tracking.db')

# CSV Configuration
CLUBS_CSV_PATH = os.getenv('CLUBS_CSV_PATH', 'test_results_20250701_092437.csv')

# Email Template Configuration
EMAIL_TEMPLATE_PATH = os.getenv('EMAIL_TEMPLATE_PATH', 'Introduction Email')

# Streamlit Configuration
APP_TITLE = "Photo Club Email Personalization Tool"
APP_DESCRIPTION = "Generate personalized emails for photography clubs using AI with cost tracking"

# Cost Tracking Configuration (pricing per 1M tokens)
PRICING = {
    'o3-mini': {
        'input': 2.00,   
        'output': 8.00  
    },
    'gpt-4o-mini': {
        'input': 0.40, 
        'output': 1.60  
    }
}

# Web Search Tool Cost (estimated)
WEB_SEARCH_COST_PER_QUERY = 0.001  # $0.001 per search query 