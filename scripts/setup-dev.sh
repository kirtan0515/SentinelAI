#!/usr/bin/env bash
###############################################################################
# SentinelAI Developer Setup Script
# Sets up the local development environment from scratch
###############################################################################

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}"
echo "=============================================="
echo "  SentinelAI - Developer Setup"
echo "=============================================="
echo -e "${NC}"

# ---------------------------------------------------------------------------
# Check Prerequisites
# ---------------------------------------------------------------------------
echo -e "${YELLOW}Checking prerequisites...${NC}"

check_command() {
    if command -v "$1" &> /dev/null; then
        VERSION=$($1 --version 2>&1 | head -n 1)
        echo -e "  ${GREEN}✓${NC} $1: $VERSION"
        return 0
    else
        echo -e "  ${RED}✗${NC} $1: NOT FOUND"
        return 1
    fi
}

MISSING=0
check_command "docker" || MISSING=1
check_command "docker-compose" || check_command "docker" || MISSING=1
check_command "python3" || MISSING=1
check_command "node" || MISSING=1
check_command "npm" || MISSING=1
check_command "git" || MISSING=1

if [ $MISSING -eq 1 ]; then
    echo ""
    echo -e "${RED}Missing required tools. Please install them and try again.${NC}"
    echo "  - Docker: https://docs.docker.com/get-docker/"
    echo "  - Python 3.11+: https://www.python.org/downloads/"
    echo "  - Node.js 18+: https://nodejs.org/"
    exit 1
fi

echo ""

# ---------------------------------------------------------------------------
# Setup Backend
# ---------------------------------------------------------------------------
echo -e "${YELLOW}Setting up backend...${NC}"
cd "$PROJECT_ROOT/backend"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "  Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "  Installing Python dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Install dev/test dependencies if available
if [ -f "requirements-dev.txt" ]; then
    pip install -r requirements-dev.txt -q
fi

echo -e "  ${GREEN}✓${NC} Backend dependencies installed"

cd "$PROJECT_ROOT"

# ---------------------------------------------------------------------------
# Setup Frontend
# ---------------------------------------------------------------------------
echo -e "${YELLOW}Setting up frontend...${NC}"
cd "$PROJECT_ROOT/frontend"

if [ -f "package.json" ]; then
    echo "  Installing Node.js dependencies..."
    npm ci --silent 2>/dev/null || npm install --silent
    echo -e "  ${GREEN}✓${NC} Frontend dependencies installed"
else
    echo -e "  ${YELLOW}⚠${NC} No package.json found, skipping frontend setup"
fi

cd "$PROJECT_ROOT"

# ---------------------------------------------------------------------------
# Setup Environment File
# ---------------------------------------------------------------------------
echo -e "${YELLOW}Setting up environment...${NC}"

if [ -f ".env.example" ] && [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "  ${GREEN}✓${NC} Created .env from .env.example"
    echo -e "  ${YELLOW}⚠${NC} Edit .env with your API keys and configuration"
elif [ -f ".env" ]; then
    echo -e "  ${GREEN}✓${NC} .env already exists"
else
    echo -e "  ${YELLOW}⚠${NC} No .env.example found"
fi

# ---------------------------------------------------------------------------
# Start Docker Services (PostgreSQL + Redis)
# ---------------------------------------------------------------------------
echo -e "${YELLOW}Starting Docker services...${NC}"

if [ -f "docker-compose.yml" ] || [ -f "docker-compose.yaml" ]; then
    docker compose up -d postgres redis 2>/dev/null || docker-compose up -d postgres redis 2>/dev/null || {
        echo -e "  ${YELLOW}⚠${NC} Could not start docker services. Start manually with: docker compose up -d"
    }
    echo -e "  ${GREEN}✓${NC} Docker services started (PostgreSQL, Redis)"

    # Wait for PostgreSQL to be ready
    echo "  Waiting for PostgreSQL to be ready..."
    for i in {1..30}; do
        if docker compose exec -T postgres pg_isready -U sentinelai 2>/dev/null || \
           docker-compose exec -T postgres pg_isready -U sentinelai 2>/dev/null; then
            break
        fi
        sleep 1
    done
    echo -e "  ${GREEN}✓${NC} PostgreSQL is ready"
else
    echo -e "  ${YELLOW}⚠${NC} No docker-compose.yml found. Start PostgreSQL and Redis manually."
fi

# ---------------------------------------------------------------------------
# Run Database Migrations
# ---------------------------------------------------------------------------
echo -e "${YELLOW}Running database migrations...${NC}"
cd "$PROJECT_ROOT/backend"

if [ -f "alembic.ini" ]; then
    source venv/bin/activate
    alembic upgrade head 2>/dev/null && \
        echo -e "  ${GREEN}✓${NC} Database migrations applied" || \
        echo -e "  ${YELLOW}⚠${NC} Migration failed - database may not be ready yet"
else
    echo -e "  ${YELLOW}⚠${NC} No alembic.ini found, skipping migrations"
fi

cd "$PROJECT_ROOT"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo -e "${GREEN}=============================================="
echo "  ✓ Setup Complete!"
echo "==============================================${NC}"
echo ""
echo "  Next steps:"
echo "  1. Edit .env with your API keys (OpenAI, Anthropic, etc.)"
echo "  2. Start the backend:"
echo "     cd backend && source venv/bin/activate"
echo "     uvicorn app.main:app --reload --port 8000"
echo ""
echo "  3. Start the frontend:"
echo "     cd frontend && npm run dev"
echo ""
echo "  URLs:"
echo "    Backend API:   http://localhost:8000"
echo "    API Docs:      http://localhost:8000/docs"
echo "    Frontend:      http://localhost:3000"
echo "    PostgreSQL:    localhost:5432"
echo "    Redis:         localhost:6379"
echo ""
echo -e "  ${BLUE}Happy coding! 🚀${NC}"
