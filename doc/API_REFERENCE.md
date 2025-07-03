# API Reference - Photo Club Email Personalization Tool

## Overview

This document provides detailed API reference for the Photo Club Email Personalization Tool, which uses O3 for research and GPT-4o-mini for content generation with comprehensive cost tracking.

## Core Classes

### `EmailPersonalizer`

Main class for handling email personalization with AI models.

#### Methods

##### `__init__()`
Initialize the email personalizer with database connection.

**Returns:** `EmailPersonalizer` instance

##### `generate_personalized_email(club_name: str) -> Tuple[str, str, str, Dict]`
Generate a complete personalized email for a photography club.

**Parameters:**
- `club_name` (str): Name of the photography club

**Returns:**
- `str`: Complete personalized email content
- `str`: Personalized content snippet added to template
- `str`: Research summary from O3
- `Dict`: Cost breakdown with keys:
  - `search_cost`: Cost for O3 research
  - `content_cost`: Cost for GPT-4o-mini content generation
  - `web_search_cost`: Cost for web search operations
  - `total_cost`: Combined total cost

**Example:**
```python
personalizer = EmailPersonalizer()
email, content, research, costs = personalizer.generate_personalized_email("BOISE CAMERA CLUB")
print(f"Generated email cost: ${costs['total_cost']:.4f}")
```

##### `research_club_with_o3(club_name: str, website: str = None, country: str = None) -> Tuple[str, Dict]`
Research club information using O3 model with web search capabilities.

**Parameters:**
- `club_name` (str): Name of the photography club
- `website` (str, optional): Club website URL
- `country` (str, optional): Club's country

**Returns:**
- `str`: Research summary
- `Dict`: Cost information for O3 usage

##### `generate_personalized_content_with_gpt4(club_name: str, club_research: str) -> Tuple[str, Dict]`
Generate personalized content using GPT-4o-mini based on research.

**Parameters:**
- `club_name` (str): Name of the photography club
- `club_research` (str): Research summary from O3

**Returns:**
- `str`: Personalized content for email
- `Dict`: Cost information for GPT-4o-mini usage

##### `save_generated_email(club_name: str, personalized_content: str, generated_email: str, costs: Dict, mark_as_sent: bool = False)`
Save generated email to database with cost tracking.

**Parameters:**
- `club_name` (str): Name of the photography club
- `personalized_content` (str): Generated personalized content
- `generated_email` (str): Complete email content
- `costs` (Dict): Cost breakdown dictionary
- `mark_as_sent` (bool): Whether to mark email as sent immediately

##### `get_total_costs() -> Dict[str, float]`
Get total costs across all generated emails.

**Returns:**
Dictionary with keys:
- `search_cost`: Total O3 search costs
- `content_cost`: Total GPT-4o-mini content costs
- `web_search_cost`: Total web search costs
- `total_cost`: Combined total costs
- `total_emails`: Number of emails generated

### `CostTracker`

Class for tracking costs across different AI models and operations.

#### Methods

##### `__init__()`
Initialize cost tracker with zero costs.

##### `calculate_token_cost(model: str, input_tokens: int, output_tokens: int) -> float`
Calculate cost based on token usage for specific model.

**Parameters:**
- `model` (str): Model name ('o3-mini' or 'gpt-4o-mini')
- `input_tokens` (int): Number of input tokens
- `output_tokens` (int): Number of output tokens

**Returns:**
- `float`: Calculated cost in USD

##### `add_search_cost(input_tokens: int, output_tokens: int)`
Add cost for O3 search operation.

##### `add_content_cost(input_tokens: int, output_tokens: int)`
Add cost for GPT-4o-mini content generation.

##### `add_web_search_cost(num_queries: int = 1)`
Add cost for web search operations.

## Configuration

### Environment Variables

All configuration is managed through environment variables loaded from `.env` file:

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `SEARCH_MODEL`: Model for research (default: 'o3-mini')
- `CONTENT_MODEL`: Model for content generation (default: 'gpt-4o-mini')
- `DATABASE_PATH`: SQLite database path (default: 'email_tracking.db')
- `CLUBS_CSV_PATH`: Path to clubs CSV file
- `EMAIL_TEMPLATE_PATH`: Path to email template file

### Pricing Configuration

Costs are configured in `src/config.py`:

```python
PRICING = {
    'o3-mini': {
        'input': 3.00,   # $3 per 1M input tokens
        'output': 12.00  # $12 per 1M output tokens
    },
    'gpt-4o-mini': {
        'input': 0.15,   # $0.15 per 1M input tokens
        'output': 0.60   # $0.60 per 1M output tokens
    }
}

WEB_SEARCH_COST_PER_QUERY = 0.001  # $0.001 per search query
```

## Database Schema

### `sent_emails` Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-incrementing ID |
| club_name | TEXT UNIQUE | Photography club name |
| email_sent_date | TEXT | ISO timestamp when marked as sent |
| personalized_content | TEXT | Generated personalized content |
| generated_email | TEXT | Complete email content |
| search_cost | REAL | Cost for O3 research |
| content_cost | REAL | Cost for GPT-4o-mini content |
| web_search_cost | REAL | Cost for web search |
| total_cost | REAL | Combined total cost |
| created_at | TEXT | ISO timestamp of creation |

## Usage Examples

### Basic Email Generation

```python
from src.email_personalizer import EmailPersonalizer

# Initialize
personalizer = EmailPersonalizer()

# Generate email
email, content, research, costs = personalizer.generate_personalized_email("BOISE CAMERA CLUB")

# Save to database
personalizer.save_generated_email("BOISE CAMERA CLUB", content, email, costs)

print(f"Email generated for ${costs['total_cost']:.6f}")
```

### Cost Analysis

```python
# Get total costs
total_costs = personalizer.get_total_costs()
print(f"Total spent: ${total_costs['total_cost']:.4f}")
print(f"Average per email: ${total_costs['total_cost'] / total_costs['total_emails']:.4f}")

# Get club status with costs
status_df = personalizer.get_all_clubs_status()
print(status_df[['Club', 'status', 'total_cost']])
```

### Bulk Processing

```python
clubs = ["CLUB_ONE", "CLUB_TWO", "CLUB_THREE"]
total_cost = 0

for club in clubs:
    try:
        email, content, research, costs = personalizer.generate_personalized_email(club)
        personalizer.save_generated_email(club, content, email, costs)
        total_cost += costs['total_cost']
        print(f"✅ {club}: ${costs['total_cost']:.6f}")
    except Exception as e:
        print(f"❌ {club}: {e}")

print(f"Total cost for batch: ${total_cost:.4f}")
```

## Error Handling

### Common Exceptions

- `ValueError`: Raised when club not found in database
- `openai.APIError`: OpenAI API related errors
- `sqlite3.Error`: Database operation errors

### Error Handling Example

```python
try:
    email, content, research, costs = personalizer.generate_personalized_email("INVALID_CLUB")
except ValueError as e:
    print(f"Club not found: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Performance Considerations

### Cost Optimization

- **Prompt Engineering**: Keep prompts concise but specific
- **Token Management**: Monitor token usage in cost analytics
- **Batch Processing**: Use bulk operations for multiple clubs
- **Caching**: Consider caching research results for similar clubs

### Memory Management

- **Database Connections**: Connections are properly closed after operations
- **Large Datasets**: Process clubs in batches for large CSV files
- **Cleanup**: Regularly backup and clean old test data

## API Rate Limits

Be aware of OpenAI API rate limits:
- O3 models may have different rate limits than GPT-4 models
- Implement proper error handling for rate limit responses
- Consider adding delays between bulk operations if needed

## Security

- **API Keys**: Never commit API keys to version control
- **Environment Variables**: Use `.env` file for sensitive configuration
- **Database**: SQLite database contains generated emails - secure appropriately
- **Logs**: Avoid logging sensitive information like full API keys 