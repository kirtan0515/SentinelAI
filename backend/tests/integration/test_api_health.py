"""
Integration tests for health check and root endpoints.

Tests verify that core endpoints respond correctly and include
expected security headers.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.mark.asyncio
class TestHealthEndpoint:
    """Tests for /health endpoint."""

    async def test_health_returns_200(self, client: AsyncClient):
        """Health check should return 200 with status healthy."""
        response = await client.get("/health")
        assert response.status_code == 200

    async def test_health_response_body(self, client: AsyncClient):
        """Health check should return expected JSON structure."""
        response = await client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert data["service"] == "SentinelAI"
        assert "version" in data

    async def test_health_has_security_headers(self, client: AsyncClient):
        """Health check response should include security headers."""
        response = await client.get("/health")
        assert "x-content-type-options" in response.headers
        assert response.headers["x-content-type-options"] == "nosniff"
        assert "x-frame-options" in response.headers
        assert response.headers["x-frame-options"] == "DENY"
        assert "strict-transport-security" in response.headers


@pytest.mark.asyncio
class TestRootEndpoint:
    """Tests for / root endpoint."""

    async def test_root_returns_200(self, client: AsyncClient):
        """Root endpoint should return 200."""
        response = await client.get("/")
        assert response.status_code == 200

    async def test_root_response_body(self, client: AsyncClient):
        """Root endpoint should return welcome message with links."""
        response = await client.get("/")
        data = response.json()
        assert "message" in data
        assert "docs" in data
        assert "health" in data
        assert data["docs"] == "/docs"
        assert data["health"] == "/health"

    async def test_root_content_type(self, client: AsyncClient):
        """Root endpoint should return JSON content type."""
        response = await client.get("/")
        assert "application/json" in response.headers["content-type"]


@pytest.mark.asyncio
class TestDocsEndpoint:
    """Tests for /docs (Swagger UI) endpoint."""

    async def test_docs_returns_200(self, client: AsyncClient):
        """Docs endpoint should be accessible."""
        response = await client.get("/docs")
        assert response.status_code == 200

    async def test_docs_returns_html(self, client: AsyncClient):
        """Docs endpoint should return HTML (Swagger UI)."""
        response = await client.get("/docs")
        assert "text/html" in response.headers["content-type"]

    async def test_openapi_json_accessible(self, client: AsyncClient):
        """OpenAPI schema should be accessible."""
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "SentinelAI"


@pytest.mark.asyncio
class TestRedocEndpoint:
    """Tests for /redoc endpoint."""

    async def test_redoc_returns_200(self, client: AsyncClient):
        """ReDoc endpoint should be accessible."""
        response = await client.get("/redoc")
        assert response.status_code == 200

    async def test_redoc_returns_html(self, client: AsyncClient):
        """ReDoc endpoint should return HTML."""
        response = await client.get("/redoc")
        assert "text/html" in response.headers["content-type"]


@pytest.mark.asyncio
class TestMetricsEndpoint:
    """Tests for /metrics (Prometheus) endpoint."""

    async def test_metrics_returns_200(self, client: AsyncClient):
        """Metrics endpoint should be accessible."""
        response = await client.get("/metrics")
        assert response.status_code == 200

    async def test_metrics_content_type(self, client: AsyncClient):
        """Metrics endpoint should return prometheus text format."""
        response = await client.get("/metrics")
        content_type = response.headers["content-type"]
        assert "text/plain" in content_type or "text/html" in content_type
