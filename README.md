# News Agent Web

A modern web-based news analysis platform with AI-powered critical analysis, built with Flask, MongoDB, and HTMX.

## Features

- **📰 RSS Feed Aggregation**: Automatically fetch news from multiple RSS sources
- **🧠 AI-Powered Analysis**: Critical analysis using OpenAI, Anthropic, or local Ollama
- **🌐 Web Interface**: Modern UI with Tabler CSS and HTMX for dynamic interactions
- **📊 MongoDB Storage**: Persistent storage for articles and analysis results
- **🔧 Modular Architecture**: Blueprint-based Flask application
- **🐳 Docker Support**: Easy deployment with Docker and docker-compose
- **🔌 MCP Ready**: Prepared adapter stub for Model Context Protocol integration

## Screenshots

![News Agent Web - Main Interface](immagini/1.png)
![News Agent Web - Article Analysis](immagini/2.png)
![News Agent Web - Settings Configuration](immagini/3.png)
![News Agent Web - MCP Integration](immagini/4.png)
![News Agent Web - Analysis Results](immagini/5.png)

## Tech Stack

- **Backend**: Python 3.12, Flask 3
- **Database**: MongoDB (pymongo)
- **UI**: Tabler CSS (via CDN) + HTMX (zero build)
- **AI Providers**: OpenAI, Anthropic, Ollama
- **Scraping**: BeautifulSoup4, markdownify
- **RSS**: feedparser
- **Containerization**: Docker + docker-compose

## 🐳 Docker Quick Start (Recommended)

### Prerequisites
- Docker & Docker Compose
- Ollama running locally (`ollama serve`)
- MongoDB locale (opzionale)

### Scenario 1: Hai già MongoDB e Ollama locali
```bash
git clone <your-repo>
cd news_agent_web
docker-compose up news-agent-standalone --build
```
Vai su http://localhost:8080

### Scenario 2: Vuoi MongoDB in Docker
```bash
git clone <your-repo>
cd news_agent_web
# Modifica docker-compose.yml: decommenta la sezione mongodb
docker-compose --profile full up --build
```

### Scenario 3: Solo MongoDB in Docker
```bash
docker-compose --profile mongodb-only up -d  # Solo MongoDB
docker-compose up news-agent-standalone --build  # Poi l'app
```

### Configurazione API Keys (opzionale)
```bash
cp env.example .env
# Modifica .env con le tue chiavi API
```

---

## Manual Installation

### Prerequisites

### Prerequisites

- Python 3.12+
- MongoDB (or Docker)
- Ollama (optional, for local AI)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd news_agent_web
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

4. **Start MongoDB** (if not using Docker)
   ```bash
   # Install and start MongoDB locally
   # Or use Docker: docker run -d -p 27017:27017 mongo:7.0
   ```

5. **Run the application**
   ```bash
   python run.py
   ```

   The application will be available at `http://localhost:8080`

### Docker Deployment

1. **Build and run with docker-compose**
   ```bash
   docker-compose up --build
   ```

2. **Access the application**
   - Web UI: `http://localhost:8080`
   - MongoDB: `localhost:27017`

## Configuration

### Environment Variables

Copy `env.example` to `.env` and configure:

```env
# Flask Configuration
FLASK_APP=app
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017/news_agent_web

# Ollama Configuration
OLLAMA_URL=http://localhost:11434

# News Sources Configuration
DEFAULT_LANGUAGE=it
ENABLE_MULTILINGUAL=true
ARTICLES_PER_PAGE=15

# RSS Sources (comma-separated)
RSS_SOURCES=https://www.ansa.it/sito/ansait_rss.xml,https://www.repubblica.it/rss/homepage/rss2.0.xml

# MCP Configuration (for future use)
MCP_ENABLED=false
MCP_SERVER_URL=http://localhost:3000
```

**Note**: API keys for AI providers (OpenAI, Anthropic, ScrapingDog) are managed through the web interface and stored securely in the MongoDB database. No need to configure them in environment variables.

## Usage

### 1. News Aggregation

- Navigate to `/news` to view aggregated articles
- Click "Aggiorna" to fetch fresh news from RSS feeds
- Filter by language (IT/EN)
- View article details and perform analysis

### 2. Critical Analysis

- **Article Analysis**: Click "Analizza" on any article
- **Text Analysis**: Use the "Analizza Testo" feature for custom content
- **URL Analysis**: Analyze articles directly from URLs
- View detailed analysis results with credibility scores

### 3. Settings Management

- Configure AI providers and models through the web interface
- Set language preferences
- Manage RSS sources
- Configure and test AI provider connections
- **API Keys**: Securely stored in MongoDB database, managed via web UI

### 4. MCP Integration (Future)

- Access MCP status at `/mcp`
- Filesystem, HTTP, and search adapters (stub implementation)
- Ready for Model Context Protocol integration

## API Endpoints

### News API
- `GET /news/api/articles` - Get articles
- `GET /news/api/sources` - Get available sources
- `GET /news/fetch` - Fetch fresh news
- `GET /news/api/articles/<id>` - Get specific article

### Analysis API
- `POST /analysis/api/analyze` - Analyze article
- `POST /analysis/api/analyze-text` - Analyze custom text
- `POST /analysis/api/analyze-url` - Analyze URL
- `GET /analysis/api/analyses` - Get analysis history

### Settings API
- `GET /settings/api/settings` - Get current settings
- `POST /settings/api/settings` - Update settings
- `GET /settings/api/providers` - Get AI providers
- `POST /settings/api/test-provider` - Test provider

### MCP API
- `GET /mcp/api/status` - Get MCP status
- `POST /mcp/api/filesystem` - Filesystem operations
- `POST /mcp/api/http` - HTTP operations
- `POST /mcp/api/search` - Search operations

## Architecture

```
news_agent_web/
├── app/
│   ├── blueprints/          # Flask blueprints
│   │   ├── news.py         # News management
│   │   ├── analysis.py     # Analysis features
│   │   ├── settings.py     # Configuration
│   │   └── mcp.py          # MCP adapter
│   ├── models/             # MongoDB models
│   │   ├── article.py      # Article model
│   │   ├── analysis.py     # Analysis model
│   │   └── settings.py     # Settings model
│   ├── services/           # Business logic
│   │   ├── news_service.py # RSS aggregation
│   │   ├── ai_service.py   # AI providers
│   │   ├── analysis_service.py # Critical analysis
│   │   └── scraping_service.py # Web scraping
│   ├── templates/          # Jinja2 templates
│   └── static/             # Static assets
├── docker-compose.yml      # Docker configuration
├── Dockerfile             # Container definition
├── requirements.txt       # Python dependencies
└── run.py                # Application entry point
```

## Development

### Project Structure

The application follows a modular architecture:

- **Blueprints**: Separate Flask modules for different features
- **Models**: MongoDB document models with validation
- **Services**: Business logic and external integrations
- **Templates**: Jinja2 templates with Tabler CSS
- **Static**: CSS, JS, and image assets

### Adding New Features

1. **Create a new blueprint** in `app/blueprints/`
2. **Add models** if needed in `app/models/`
3. **Implement services** in `app/services/`
4. **Create templates** in `app/templates/`
5. **Register blueprint** in `app/__init__.py`

### Testing

```bash
# Run tests (when implemented)
python -m pytest

# Run with coverage
python -m pytest --cov=app
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- **Tabler**: Modern UI components
- **HTMX**: Dynamic web interactions
- **Flask**: Web framework
- **MongoDB**: Database
- **Ollama**: Local AI inference
