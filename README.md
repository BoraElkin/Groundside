# Ground Operations Intelligence Platform

An AI-powered platform for predicting and preventing aircraft turnaround delays at airports.

## Overview

This B2B SaaS platform ingests data from multiple sources (airport operational databases, ground handler apps, vehicle GPS, and radio transcripts) to predict aircraft turnaround delays before they happen, providing real-time visibility and prescriptive recommendations.

### Key Features

- **Predictive Analytics**: ML-powered delay prediction before they cascade
- **Real-time Monitoring**: Live turnaround status for all flights
- **LLM-Powered Insights**: Natural language processing of radio chatter and operational logs
- **Intelligent Alerting**: Proactive notifications with recommended actions
- **Root Cause Analysis**: AI-driven analysis of delay patterns and causes

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, Celery
- **ML/AI**: scikit-learn, pandas, numpy, OpenAI/Anthropic APIs
- **Data**: PostgreSQL, Redis, Azure Blob Storage
- **Frontend**: React 18, TypeScript, Tailwind CSS, Vite
- **Infrastructure**: Docker, Docker Compose

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 18+
- API keys for OpenAI/Anthropic (for LLM features)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ground-ops-platform
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

3. Start the platform using Docker Compose:
```bash
docker-compose up -d
```

4. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Local Development

#### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

#### Running Celery Workers

```bash
cd backend
celery -A workers.celery_app worker --loglevel=info
```

## Project Structure

```
ground-ops-platform/
├── backend/           # FastAPI backend application
│   ├── api/          # REST API routes
│   ├── models/       # Database models and schemas
│   ├── services/     # Business logic services
│   └── workers/      # Celery background tasks
├── frontend/         # React frontend application
│   └── src/
│       ├── components/  # Reusable UI components
│       ├── pages/       # Page components
│       └── services/    # API client services
├── ml/               # Machine learning notebooks and models
└── docs/             # Documentation
```

## API Documentation

Once the backend is running, visit http://localhost:8000/docs for interactive API documentation (Swagger UI).

## Key Components

### Data Ingestion

- **AODB Connector**: Integrates with Airport Operational Database
- **Ground Handler API**: Real-time data from ground handling operations
- **GPS Tracker**: Vehicle location and movement data
- **FlightAware**: Flight status and schedule information

### Prediction Engine

- **Delay Predictor**: ML model predicting turnaround delays
- **Turnaround Estimator**: Duration estimation for turnaround activities
- **Cascade Analyzer**: Predicts downstream impact of delays

### LLM Services

- **Transcript Parser**: Extracts insights from radio communications
- **Alert Generator**: Creates natural language alerts and recommendations
- **Root Cause Analyzer**: AI-powered delay root cause analysis

## Sample Data

The platform includes sample data for Istanbul Airport (IST):
- Airlines: Turkish Airlines (TK), Pegasus (PC), AnadoluJet
- Aircraft: A321, B737-800, A330, B777
- Ground Handlers: TGS, Çelebi, Havaş

## Configuration

Key configuration options in `.env`:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection for caching and Celery
- `ANTHROPIC_API_KEY`: Claude API key for LLM features
- `DEFAULT_AIRPORT_CODE`: Airport IATA code (default: IST)

## Monitoring and Alerts

The platform supports multiple notification channels:
- Email (SMTP)
- Slack webhooks
- Microsoft Teams webhooks
- Custom webhooks

## Development

### Running Tests

```bash
cd backend
pytest
```

### Code Style

```bash
# Backend
black backend/
flake8 backend/

# Frontend
cd frontend
npm run lint
```

## Deployment

See [docs/deployment.md](docs/deployment.md) for production deployment guidelines.

## Documentation

- [Architecture Overview](docs/architecture.md)
- [API Reference](docs/api-reference.md)
- [Deployment Guide](docs/deployment.md)

## License

Proprietary - All rights reserved

## Support

For support and questions, contact: support@groundops.example.com
