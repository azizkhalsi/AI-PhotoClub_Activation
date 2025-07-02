import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

# Database Configuration
DATABASE_PATH = 'email_tracking.db'

# CSV Configuration
CLUBS_CSV_PATH = 'test_results_20250701_092437.csv'

# Email Template Configuration
EMAIL_TEMPLATE_PATH = 'Introduction Email'

# Streamlit Configuration
APP_TITLE = "Photo Club Email Personalization Tool"
APP_DESCRIPTION = "Generate personalized emails for photography clubs using AI" 