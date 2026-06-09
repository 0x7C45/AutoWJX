# Autowjx - 自动问卷星填写系统

An automated questionnaire filling system powered by AI, designed for non-technical users who need quick, high-quality survey data.

## Overview

Autowjx automatically fills questionnaires on Wenjuanxing (问卷星) using AI-powered population inference and intelligent data generation. The system analyzes questionnaire constraints, performs demographic stratification, and generates realistic responses across multiple dimensions (gender, age, location, occupation, income).

## Architecture

- **Backend:** FastAPI + Python 3.11
- **Task Queue:** Celery + Redis
- **Database:** PostgreSQL 15
- **Frontend:** Vue 3 + Element Plus
- **LLM:** Claude API (primary) / OpenAI API (fallback)
- **Deployment:** Docker Compose

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)

### 1. Clone Repository

```bash
git clone <repository-url>
cd Autowjx
```

### 2. Configure Environment

```bash
cd backend
cp .env.example .env
# Edit .env and add your API keys
```

Required environment variables:
- `CLAUDE_API_KEY` - Your Claude API key
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string

### 3. Start Services

```bash
# Start all services with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f
```

Services will be available at:
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### 4. Initialize Database

```bash
# Run migrations
docker-compose exec backend alembic upgrade head
```

## Development

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

## Project Structure

```
Autowjx/
├── backend/
│   ├── app/
│   │   ├── config.py           # Configuration management
│   │   ├── models/             # Database models
│   │   ├── services/           # Business logic
│   │   └── routes/             # API endpoints
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   └── package.json
├── docker-compose.yml
└── README.md
```

## API Endpoints

- `POST /api/parse` - Parse questionnaire from URL
- `POST /api/stratify` - Perform demographic stratification
- `POST /api/execute` - Execute questionnaire filling
- `GET /api/status/:id` - Get task status
- `GET /api/result/:id` - Get task results
- `WS /ws/:id` - WebSocket for real-time updates

## Testing

```bash
# Run backend tests
cd backend
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

## Deployment

For production deployment, ensure you:
- Set strong values for `SECRET_KEY` and database credentials
- Use Docker service names (e.g., `postgres`, `redis`) in connection strings
- Configure appropriate `ALLOWED_ORIGINS` for your domain
- Set `ENVIRONMENT=production` and adjust `LOG_LEVEL` as needed

## License

MIT

## Support

For issues and questions, please open an issue on GitHub.
