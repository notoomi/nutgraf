# 🥜 Nutgraf: Your AI-Powered Article Summarizer

Tired of reading long articles? Let Nutgraf do the heavy lifting! This nifty web tool takes URLs, extracts the good stuff, and whips up AI-powered summaries that are just the right length and tone for you. Think of it as your personal reading assistant that never gets tired! 

## ✨ What's in the Box?

- **URL Processing Magic**: Drop in URLs any way you like - paste them, upload them, or even pull them from RSS feeds!
- **Smart Article Extraction**: We'll grab the content for you, even if it's hiding behind a paywall (shh, our little secret! 🤫)
- **AI Brainpower**: Powered by the latest and greatest from OpenAI GPT and Anthropic Claude
- **Customizable Goodness**: Want it short and sweet? Long and detailed? Professional or casual? You got it!
- **User-Friendly Features**: Secure login, API key storage, and a history that won't forget your favorite summaries
- **Tag & Search**: Organize your summaries like a pro
- **Works Everywhere**: Desktop, tablet, phone - we've got you covered!

## Quick Start

### 🐳 Docker Way (The Easy Path)

1. Clone the repository:
```bash
git clone <repository-url>
cd nutgraf
```

2. Set up your environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Fire it up:
```bash
docker-compose up -d
```

4. Point your browser to http://localhost:5001 and let the magic begin!

### 🛠️ Manual Installation (For the DIY Enthusiasts)

1. **Prerequisites**:
   - Python 3.9+
   - Virtual environment (recommended)

2. **Installation**:
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

3. **Configuration**:
```bash
# Copy environment file
cp .env.example .env

# Generate a secret key (it's like a password for your passwords!)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Copy the output and paste it as ENCRYPTION_KEY in your .env file

# Edit .env file with your settings (especially ENCRYPTION_KEY)
```

4. **Launch Time**:
```bash
python app.py
```

5. Visit http://localhost:5001 and start summarizing!

## Configuration

### Environment Variables

- `SECRET_KEY`: Flask secret key for sessions
- `DATABASE_URL`: Database connection string (default: SQLite)
- `ENCRYPTION_KEY`: Key for encrypting stored API keys
- `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`: Email configuration

### API Keys

You'll need these to make the magic happen:
- **OpenAI**: Grab one from [OpenAI Platform](https://platform.openai.com/api-keys)
- **Anthropic**: Get yours from [Anthropic Console](https://console.anthropic.com/)

Don't worry - we keep these safe and sound with encryption!

## Usage

1. **Get Started**: Sign up or log in
2. **Set Up**: Add your AI API keys in Settings
3. **Feed It URLs**: 
   - Paste them directly
   - Upload a file
   - Import from RSS
4. **Pick Your Articles**: Choose what you want to summarize
5. **Make It Yours**: Set the length, tone, and format
6. **Generate**: Watch the magic happen!
7. **Organize**: Tag and search your summaries

## 🏗️ Under the Hood

### Backend (Python/Flask)
- **Flask**: Web framework with SQLAlchemy ORM
- **Authentication**: Flask-Login with password hashing
- **Database**: SQLite (default) or PostgreSQL
- **Article Extraction**: BeautifulSoup + Readability
- **AI Integration**: OpenAI and Anthropic APIs

### Frontend (HTML/CSS/JS)
- **Responsive Design**: CSS Grid/Flexbox
- **Vanilla JavaScript**: No framework dependencies
- **Progressive Enhancement**: Works without JavaScript

### Security
- HTTPS enforcement (production)
- Encrypted API key storage
- CSRF protection
- Input validation and sanitization

## Development

### Project Structure
```
nutgraf/
├── app.py                 # Main Flask application
├── models.py             # Database models
├── requirements.txt      # Python dependencies
├── .env.example         # Environment template
├── routes/              # Route handlers
│   ├── auth.py         # Authentication routes
│   ├── main.py         # Main application routes
│   └── api.py          # API endpoints
├── services/            # Business logic
│   ├── article_extractor.py
│   ├── llm_service.py
│   └── url_processor.py
├── templates/           # Jinja2 templates
│   ├── base.html
│   ├── auth/           # Authentication templates
│   └── main/           # Main application templates
├── static/              # Static assets
│   ├── css/            # Stylesheets
│   └── js/             # JavaScript
└── tests/              # Test suite
```

### 🧪 Testing
```bash
# Install test dependencies
pip install pytest pytest-flask

# Run the tests
pytest
```

### Code Quality
```bash
# Install linting tools
pip install black flake8 isort

# Format code
black .
isort .

# Lint code
flake8 .
```

## Deployment

### Local Docker
```bash
docker-compose up -d
```

### Production Considerations
- Use PostgreSQL for better performance
- Set strong SECRET_KEY and ENCRYPTION_KEY
- Configure proper email settings
- Enable HTTPS/SSL
- Set up monitoring and logging
- Consider rate limiting for API endpoints

### Cloud Deployment
The application is designed to be easily deployable to:
- AWS (EC2, ECS, Elastic Beanstalk)
- Google Cloud Platform
- Azure
- DigitalOcean
- Heroku

## API Reference

### Authentication Required Endpoints
- `POST /api/process-urls`: Process URL list/file/RSS
- `POST /api/extract-article`: Extract article content
- `POST /api/generate-summary`: Generate AI summary
- `POST /api/add-tags`: Add tags to summary
- `POST /api/remove-tag`: Remove tag from summary
- `GET /api/get-tag-suggestions`: Get tag suggestions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

Found a bug? Want a new feature? Hit us up on the GitHub issue tracker!