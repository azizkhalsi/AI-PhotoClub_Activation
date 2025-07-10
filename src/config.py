import os
from dotenv import load_dotenv

# Load environment variables from .env file
# Look for .env in current directory first, then parent directory
if os.path.exists('.env'):
    load_dotenv('.env')
elif os.path.exists('../.env'):
    load_dotenv('../.env')
else:
    load_dotenv()  # Try default locations

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SEARCH_MODEL = os.getenv('SEARCH_MODEL', 'o3')  # O3 for web search research
CONTENT_MODEL = os.getenv('CONTENT_MODEL', 'gpt-4.1-nano')  # GPT-4.1-nano for content generation

# CSV Configuration - check multiple possible paths
def _find_csv_path(filename: str) -> str:
    """Find CSV file in multiple possible locations"""
    possible_paths = [
        filename,  # Current directory
        f"../{filename}",  # Parent directory
        os.path.join(os.path.dirname(__file__), "..", filename),  # Relative to src directory
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Return default if not found
    return filename

CLUBS_CSV_PATH = os.getenv('CLUBS_CSV_PATH', _find_csv_path('test_results_20250701_092437.csv'))
CLUBS_RESEARCH_CSV_PATH = _find_csv_path('club_research_results.csv')

# Email Template Configuration
EMAIL_TEMPLATE_PATH = os.getenv('EMAIL_TEMPLATE_PATH', 'Introduction Email')

# Database Configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', 'email_tracking.db')

# Streamlit Configuration
APP_TITLE = "Photo Club Email Personalization Tool"
APP_DESCRIPTION = "Generate personalized emails for photography clubs using AI with cost tracking"

# Cost Tracking Configuration (pricing per 1M tokens)
PRICING = {
    'o3': {
        'input': 2.00,           # $2.00 per 1M tokens
        'cached_input': 0.50,    # $0.50 per 1M cached tokens
        'output': 8.00           # $8.00 per 1M tokens
    },
    'gpt-4.1-nano': {
        'input': 0.100,          # $0.100 per 1M tokens
        'cached_input': 0.025,   # $0.025 per 1M cached tokens
        'output': 0.400          # $0.400 per 1M tokens
    }
}

# Web Search Tool Cost for O3 models
WEB_SEARCH_COST_PER_1K_CALLS = 10.00  # $10.00 per 1K calls
WEB_SEARCH_COST_PER_QUERY = WEB_SEARCH_COST_PER_1K_CALLS / 1000  # $0.01 per search query 