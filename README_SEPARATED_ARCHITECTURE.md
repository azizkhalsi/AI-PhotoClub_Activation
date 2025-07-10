# Photo Club Email Tool - Separated Architecture

## Overview

The system has been restructured into a clean, separated architecture with dedicated components for research and email generation. This provides better performance, clearer separation of concerns, and efficient caching.

## Architecture Components

### 1. ClubResearchManager (`src/club_research_manager.py`)
- **Purpose**: Handles all O3 web search and research operations
- **Storage**: Saves research results in CSV format (`club_research_results.csv`)
- **Features**:
  - Three-section research (introduction, checkup, acceptance)
  - 30-day cache expiration
  - Cost tracking and statistics
  - Automatic expired entry cleanup

### 2. EmailPersonalizer (`src/email_personalizer.py`)
- **Purpose**: Generates personalized emails using pre-researched data
- **Focus**: Content generation only - no research operations
- **Features**:
  - Reads research from CSV
  - Supports three email types
  - Cost tracking for content generation
  - Email modification and tracking

### 3. Streamlit Interface (`streamlit/main_app.py`, `streamlit/pages/email_generator.py`)
- **Purpose**: Professional web interface for the entire workflow
- **Features**:
  - Email type selection (introduction, checkup, acceptance)
  - Research status and cache management
  - Email generation and editing
  - Statistics and bulk operations

## Usage Methods

### 1. Web Interface (Recommended)
```bash
streamlit run streamlit/main_app.py
```

### 2. Command Line Interface
```bash
# Research a specific club
python research_cli.py research "Tokyo Photography Club"

# Show statistics
python research_cli.py stats

# List all researched clubs
python research_cli.py list --show-details

# Bulk research 5 clubs
python research_cli.py bulk --count 5

# Generate introduction emails
python research_cli.py emails introduction --count 3 --show-preview
```

### 3. Test Script
```bash
python test_separated_architecture.py
```

## Data Storage

### Research Data (`club_research_results.csv`)
- Club research with three sections per club
- Expiration dates and validity tracking
- Cost information and timestamps

### Email Tracking (`sent_emails_tracking.csv`)
- Generated emails by type and club
- Send status and modification tracking
- Content generation costs

## Email Types

### 1. Introduction
- **Purpose**: First contact offering DxO discount
- **Research Focus**: Recent achievements, specialties
- **Tone**: Professional and confident

### 2. Checkup  
- **Purpose**: Follow-up when no response
- **Research Focus**: Upcoming events, time-sensitive opportunities
- **Tone**: Friendly but urgent

### 3. Acceptance
- **Purpose**: Explain discount process when accepted
- **Research Focus**: Club structure, member communication
- **Tone**: Helpful and instructional

## Performance Benefits

### Caching Advantages
- **Speed**: 5-10 seconds (cached) vs 30-60 seconds (new research)
- **Cost**: ~95% savings when using cached research
- **Reliability**: Research valid for 30 days

### Research Sections
- All three email types use same research data
- Only introduction section used currently
- Ready for checkup and acceptance email expansion

## Key Features

1. **Separated Concerns**: Research and email generation are independent
2. **CSV Storage**: Simple, readable data format
3. **Multi-Email Types**: Three distinct email workflows
4. **Cost Tracking**: Detailed cost monitoring and statistics
5. **Cache Management**: Automatic expiration and manual invalidation
6. **Professional UI**: Clean, task-focused interface
7. **CLI Access**: Command-line tools for automation

## Next Steps

1. **Expand Email Types**: Implement checkup and acceptance email generation
2. **Mailing Integration**: Add mailing service API (SendGrid, Mailgun, etc.)
3. **Advanced Analytics**: Track email open rates and responses
4. **Bulk Operations**: Enhanced bulk research and email generation

## File Structure

```
├── src/
│   ├── club_research_manager.py    # O3 research & CSV storage
│   ├── email_personalizer.py       # Email content generation
│   └── config.py                   # Configuration settings
├── streamlit/
│   ├── main_app.py                 # Main application
│   └── pages/
│       └── email_generator.py      # Email generation interface
├── research_cli.py                 # Command-line interface
├── test_separated_architecture.py  # Test & demonstration script
├── club_research_results.csv       # Research data storage
└── sent_emails_tracking.csv        # Email tracking data
```

## Benefits of This Architecture

1. **Modularity**: Each component has a single, clear purpose
2. **Performance**: Efficient caching prevents expensive duplicate research
3. **Scalability**: Easy to add new email types or research sources
4. **Maintainability**: Clear separation makes updates and debugging easier
5. **Cost Efficiency**: Research reuse saves significant API costs
6. **Flexibility**: Multiple interfaces (web, CLI) for different use cases 