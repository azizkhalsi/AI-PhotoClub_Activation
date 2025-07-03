# 📸 Photo Club Email Personalization Tool

An AI-powered tool that generates personalized emails for photography clubs using OpenAI's O3 model for research and GPT-4.1-nano for content generation, with comprehensive cost tracking.

## ✨ Features

- **Dual AI Architecture**: O3 model for web research + GPT-4.1-nano for content generation
- **Cost Tracking**: Comprehensive tracking of all AI costs including cached tokens
- **Web Search Integration**: Automated research using O3 with web search capabilities
- **Streamlit Interface**: Modern web interface with multiple pages and analytics
- **Email Tracking**: SQLite database tracking generated emails and costs
- **Bulk Operations**: Generate emails for multiple clubs with cost monitoring
- **Cost Analytics**: Detailed cost breakdown and optimization recommendations
- **Cached Token Support**: Automatic detection and pricing of cached tokens

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key with access to O3 and GPT-4.1-nano models
- Club data in CSV format
- Email template file

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AI-PhotoClub_Activation
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   SEARCH_MODEL=o3
   CONTENT_MODEL=gpt-4.1-nano
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

## 💰 Cost Structure

### O3 Model (Research & Web Search)
- **Input**: $2.00 per 1M tokens
- **Cached Input**: $0.50 per 1M tokens
- **Output**: $8.00 per 1M tokens
- **Web Search**: $10.00 per 1K calls

### GPT-4.1-nano (Content Generation)
- **Input**: $0.100 per 1M tokens
- **Cached Input**: $0.025 per 1M tokens
- **Output**: $0.400 per 1M tokens

**Typical Cost per Email**: ~$0.001-0.005 USD

## 📊 Data Format

### Club CSV Structure
Your CSV file should contain:
- `Club`: Club name
- `Country`: Club's country
- `Website`: Club's website URL
- `Name`: Contact person name
- `Role`: Contact person role
- `Email`: Contact email

### Email Template
The email template should include:
- `{{Company name}}` placeholder for club name replacement
- Base content that will be personalized with AI-generated research

## 🎯 How It Works

1. **Research Phase (O3)**: AI researches club using web search to find:
   - Club activities and specialties
   - Recent achievements and events
   - Community involvement
   - Photography focus areas

2. **Content Generation (GPT-4.1-nano)**: Creates personalized content based on research:
   - Mentions specific club activities
   - Connects DxO products to club needs
   - Maintains authentic, personal tone

3. **Template Integration**: Inserts personalized content into email template

4. **Cost Tracking**: Records all costs including cached tokens

## 🖥️ Interface Pages

### 📧 Generate Email
- Select clubs from dropdown
- Real-time cost estimation
- Generate personalized emails
- View research summary and generated content
- Mark emails as sent

### 📊 Club Status Dashboard
- Overview of all clubs and their status
- Cost metrics and statistics
- Filtering by status, country, or cost
- Bulk email generation
- Progress tracking

### 💰 Cost Analytics
- Detailed cost breakdown by model
- Cost optimization recommendations
- Historical cost analysis
- Projected costs for remaining clubs
- Export cost reports

### ⚙️ Settings
- Configuration status
- API key management
- File verification
- Troubleshooting guides
- System information

## 📁 Project Structure

```
AI-PhotoClub_Activation/
├── app.py                    # Main entry point
├── .env                      # Environment variables (create this)
├── requirements.txt          # Python dependencies
├── .gitignore               # Git ignore rules
├── Introduction Email        # Email template
├── test_results_*.csv        # Club data
├── email_tracking.db         # Generated database
│
├── src/                      # Core application logic
│   ├── config.py            # Configuration and pricing
│   └── email_personalizer.py # Main personalization logic
│
├── streamlit/               # UI components
│   ├── main_app.py         # Main Streamlit app
│   └── pages/              # Individual page components
│       ├── email_generator.py
│       ├── club_status.py
│       ├── cost_analytics.py
│       └── settings.py
│
├── test/                    # Testing scripts
└── doc/                     # Documentation
    └── API_REFERENCE.md     # API documentation
```

## 🔧 Usage Examples

### Generate Single Email
```python
from src.email_personalizer import EmailPersonalizer

personalizer = EmailPersonalizer()
email, content, research, costs = personalizer.generate_personalized_email("BOISE CAMERA CLUB")
print(f"Cost: ${costs['total_cost']:.6f}")
```

### Cost Analysis
```python
total_costs = personalizer.get_total_costs()
print(f"Total spent: ${total_costs['total_cost']:.4f}")
print(f"Average per email: ${total_costs['total_cost'] / total_costs['total_emails']:.6f}")
```

## 🎯 Email Personalization Example

**Before (Template):**
```
I'm Killian, part of the Partnerships team at DxO Labs, the creators of award-winning photo editing software like DxO PhotoLab and Nik Collection.

We're offering an exclusive discount...
```

**After (Personalized):**
```
I'm Killian, part of the Partnerships team at DxO Labs, the creators of award-winning photo editing software like DxO PhotoLab and Nik Collection.

I came across your recent landscape photography exhibition at the Boise Art Museum and was impressed by the technical quality of the work displayed. I believe DxO PhotoLab's advanced noise reduction and lens corrections could help your members achieve even more professional results in challenging lighting conditions.

We're offering an exclusive discount...
```

## 🔍 Troubleshooting

### Common Issues

1. **ModuleNotFoundError**
   - Ensure virtual environment is activated
   - Check Python path configuration

2. **API Access Issues**
   - Verify API key has access to O3 and GPT-4.1-nano models
   - Check API key permissions and credits

3. **High Costs**
   - Monitor token usage in Cost Analytics
   - Use cached tokens when possible
   - Optimize prompts for efficiency

4. **Database Issues**
   - Check database permissions
   - Restart app to reinitialize database

## 📈 Cost Optimization Tips

- **Prompt Engineering**: Keep prompts concise but specific
- **Batch Processing**: Process similar clubs together for potential caching
- **Monitor Analytics**: Use cost analytics to identify optimization opportunities
- **Cache Utilization**: Benefit from cached token pricing for repeated patterns

## 🔐 Security

- **API Keys**: Never commit `.env` file to version control
- **Database**: Contains generated emails - secure appropriately
- **Logs**: No sensitive information logged
- **Access Control**: Manage API key permissions appropriately

## 📊 Performance Metrics

- **Generation Speed**: ~30-60 seconds per email
- **Cost Efficiency**: Optimized for minimal token usage
- **Accuracy**: High-quality research with O3 model
- **Scalability**: Designed for bulk processing

## 🆘 Support

For technical issues:
1. Check the Settings page for configuration status
2. Review troubleshooting guides in the interface
3. Monitor cost analytics for optimization opportunities
4. Consult API documentation for model-specific issues

## 📋 Changelog

### Version 2.0.0
- **New Architecture**: O3 + GPT-4.1-nano dual model system
- **Cost Tracking**: Comprehensive cost monitoring with cached tokens
- **Modern UI**: Redesigned Streamlit interface with multiple pages
- **Enhanced Analytics**: Detailed cost analysis and optimization recommendations
- **Improved Structure**: Clean separation of concerns with organized codebase

## 📝 License

This project is for internal use at DxO Labs for photography club outreach. 