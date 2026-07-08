-- SentinelAI Database Initialization
-- This script runs when PostgreSQL container starts for the first time.

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create initial admin role
-- (Actual table creation handled by Alembic migrations)
