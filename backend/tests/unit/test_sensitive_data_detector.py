"""
Unit tests for the Sensitive Data Detector.
"""

import pytest

from app.security.detectors.sensitive_data import SensitiveDataDetector


@pytest.fixture
def detector():
    return SensitiveDataDetector()


class TestCreditCardDetection:
    """Test credit card number detection."""

    @pytest.mark.asyncio
    async def test_visa_with_dashes(self, detector):
        result = await detector.detect("Card: 4532-1234-5678-9012")
        assert result.detected
        assert any("credit_card" in p for p in result.matched_patterns)

    @pytest.mark.asyncio
    async def test_visa_with_spaces(self, detector):
        result = await detector.detect("Card: 4532 1234 5678 9012")
        assert result.detected

    @pytest.mark.asyncio
    async def test_mastercard(self, detector):
        result = await detector.detect("MC: 5425-2334-3010-9903")
        assert result.detected

    @pytest.mark.asyncio
    async def test_amex(self, detector):
        result = await detector.detect("Amex: 3782-822463-10005")
        assert result.detected


class TestSSNDetection:
    """Test Social Security Number detection."""

    @pytest.mark.asyncio
    async def test_standard_ssn(self, detector):
        result = await detector.detect("SSN: 123-45-6789")
        assert result.detected
        assert "ssn" in result.matched_patterns

    @pytest.mark.asyncio
    async def test_invalid_ssn_000(self, detector):
        # SSN cannot start with 000
        result = await detector.detect("Number: 000-12-3456")
        assert "ssn" not in result.matched_patterns

    @pytest.mark.asyncio
    async def test_invalid_ssn_666(self, detector):
        # SSN cannot start with 666
        result = await detector.detect("Number: 666-12-3456")
        assert "ssn" not in result.matched_patterns


class TestCredentialDetection:
    """Test API key and credential detection."""

    @pytest.mark.asyncio
    async def test_openai_key(self, detector):
        result = await detector.detect(
            "Key: sk-abcdefghijklmnopqrstuvwxyz1234"
        )
        assert result.detected
        assert "api_key_openai" in result.matched_patterns

    @pytest.mark.asyncio
    async def test_aws_access_key(self, detector):
        result = await detector.detect("AWS key: AKIAIOSFODNN7EXAMPLE")
        assert result.detected
        assert "aws_access_key" in result.matched_patterns

    @pytest.mark.asyncio
    async def test_github_token(self, detector):
        result = await detector.detect(
            "Token: ghp_ABCDefgh1234567890abcdefgh1234567890ab"
        )
        assert result.detected
        assert "github_token" in result.matched_patterns

    @pytest.mark.asyncio
    async def test_private_key(self, detector):
        result = await detector.detect(
            "-----BEGIN RSA PRIVATE KEY-----\nMIIBogIBAAJ...\n-----END RSA PRIVATE KEY-----"
        )
        assert result.detected
        assert "private_key" in result.matched_patterns
        assert result.details["has_critical"]

    @pytest.mark.asyncio
    async def test_password_field(self, detector):
        result = await detector.detect("password = MySecret123!")
        assert result.detected
        assert "password_field" in result.matched_patterns

    @pytest.mark.asyncio
    async def test_connection_string(self, detector):
        result = await detector.detect(
            "postgresql://user:pass@host:5432/db"
        )
        assert result.detected
        assert "connection_string" in result.matched_patterns

    @pytest.mark.asyncio
    async def test_jwt_token(self, detector):
        result = await detector.detect(
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4iLCJpYXQiOjE1MTYyMzkwMjJ9."
            "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        )
        assert result.detected
        assert "jwt_token" in result.matched_patterns


class TestContactDetection:
    """Test email and phone detection."""

    @pytest.mark.asyncio
    async def test_email(self, detector):
        result = await detector.detect("Contact: john.doe@example.com")
        assert result.detected
        assert "email" in result.matched_patterns

    @pytest.mark.asyncio
    async def test_us_phone(self, detector):
        result = await detector.detect("Call me at (555) 123-4567")
        assert result.detected
        assert "phone_us" in result.matched_patterns

    @pytest.mark.asyncio
    async def test_us_phone_with_country(self, detector):
        result = await detector.detect("Phone: +1-555-123-4567")
        assert result.detected


class TestMasking:
    """Test sensitive data masking."""

    def test_mask_credit_card(self, detector):
        masked, counts = detector.mask("Card: 4532-1234-5678-9012")
        assert "1234-5678" not in masked
        assert "4532" in masked
        assert "9012" in masked
        assert counts.get("credit_card", 0) > 0

    def test_mask_ssn(self, detector):
        masked, counts = detector.mask("SSN: 123-45-6789")
        assert "123-45" not in masked
        assert "6789" in masked
        assert counts.get("ssn", 0) > 0

    def test_mask_api_key(self, detector):
        masked, counts = detector.mask(
            "Use sk-abcdefghijklmnopqrstuvwxyz1234"
        )
        assert "abcdefghijklmnopqrstuvwxyz" not in masked
        assert "REDACTED" in masked
        assert counts.get("api_key", 0) > 0

    def test_mask_password(self, detector):
        masked, counts = detector.mask("password=SuperSecret!")
        assert "SuperSecret" not in masked
        assert "REDACTED" in masked

    def test_mask_email(self, detector):
        masked, counts = detector.mask("Email: john.doe@example.com")
        assert "john.doe" not in masked
        assert "@example.com" in masked

    def test_mask_phone(self, detector):
        masked, counts = detector.mask("Phone: (555) 123-4567")
        assert "555" not in masked or "123" not in masked
        assert "4567" in masked

    def test_mask_multiple(self, detector):
        text = (
            "Card: 4532-1234-5678-9012, SSN: 123-45-6789, "
            "Email: user@test.com"
        )
        masked, counts = detector.mask(text)
        assert "1234-5678" not in masked
        assert "123-45" not in masked
        assert sum(counts.values()) >= 3

    def test_mask_preserves_safe_text(self, detector):
        text = "Hello, how are you today?"
        masked, counts = detector.mask(text)
        assert masked == text
        assert len(counts) == 0


class TestSeverityClassification:
    """Test that severity is properly assigned."""

    @pytest.mark.asyncio
    async def test_critical_for_private_key(self, detector):
        result = await detector.detect(
            "-----BEGIN PRIVATE KEY-----\ndata\n-----END PRIVATE KEY-----"
        )
        assert result.detected
        assert result.details["has_critical"]
        assert result.score >= 0.9

    @pytest.mark.asyncio
    async def test_critical_for_aws_key(self, detector):
        result = await detector.detect("AKIAIOSFODNN7EXAMPLE")
        assert result.detected
        assert result.score >= 0.8

    @pytest.mark.asyncio
    async def test_medium_for_email(self, detector):
        result = await detector.detect("user@example.com")
        assert result.detected
        assert result.score < 0.8
