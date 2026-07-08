# Developer Guide

## Development Environment Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp ../.env.example .env

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Full Stack with Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop all services
docker-compose down
```

## Project Conventions

### Backend

- **Code Style**: Ruff for linting and formatting
- **Type Hints**: Required for all function signatures
- **Documentation**: Docstrings for all public functions
- **Testing**: pytest with async support
- **Naming**: snake_case for functions/variables, PascalCase for classes

### Frontend

- **Code Style**: ESLint + Prettier
- **Components**: Functional components with TypeScript
- **State**: Zustand for global state
- **Styling**: Tailwind CSS + shadcn/ui components
- **Naming**: camelCase for functions/variables, PascalCase for components

### Git Workflow

- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - Feature branches
- `fix/*` - Bug fix branches
- `release/*` - Release preparation

### Commit Messages

Follow Conventional Commits:
```
feat: add prompt injection detection
fix: correct token refresh logic
docs: update API documentation
test: add security service unit tests
chore: update dependencies
```

## API Development

### Adding a New Endpoint

1. Create schema in `app/schemas/`
2. Create/update model in `app/models/`
3. Create repository method in `app/repositories/`
4. Create service method in `app/services/`
5. Add endpoint in `app/api/v1/endpoints/`
6. Register in router

### Running Tests

```bash
cd backend

# All tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/unit/test_security_service.py -v

# Security tests only
pytest tests/security/ -v
```
