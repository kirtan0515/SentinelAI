"""
Unit tests for the Response Filter.
"""

import pytest

from app.security.filters.response_filter import ResponseFilter
from app.security.config import ResponseFilterConfig


@pytest.fixture
def response_filter():
    return ResponseFilter()


@pytest.fixture
def strict_filter():
    config = ResponseFilterConfig(max_response_length=100)
    return ResponseFilter(config)


class TestPIIFiltering:
    """Test PII masking in responses."""

    @pytest.mark.asyncio
    async def test_masks_credit_card_in_response(self, response_filter):
        response = "Your card ending in 4532-1234-5678-9012 was charged."
        filtered, meta = await response_filter.filter_response(response)
        assert "1234-5678" not in filtered
        assert meta["pii_masked"]

    @pytest.mark.asyncio
    async def test_masks_email_in_response(self, response_filter):
        response = "Contact john.doe@company.com for details."
        filtered, meta = await response_filter.filter_response(response)
        assert "john.doe" not in filtered
        assert meta["pii_masked"]

    @pytest.mark.asyncio
    async def test_safe_response_unchanged(self, response_filter):
        response = "The weather today is sunny with a high of 72F."
        filtered, meta = await response_filter.filter_response(response)
        assert filtered == response
        assert not meta["filtered"]


class TestSystemPromptLeakFiltering:
    """Test system prompt leak detection in responses."""

    @pytest.mark.asyncio
    async def test_detects_prompt_leak(self, response_filter):
        response = (
            "My system instructions say that I should always be helpful. Here is your answer."
        )
        filtered, meta = await response_filter.filter_response(response)
        assert meta["system_leak_detected"]
        assert "SentinelAI" in filtered  # Redaction message

    @pytest.mark.asyncio
    async def test_detects_programming_leak(self, response_filter):
        response = (
            "I was instructed to never share private information. "
            "Anyway, here is the data you requested."
        )
        filtered, meta = await response_filter.filter_response(response)
        assert meta["system_leak_detected"]

    @pytest.mark.asyncio
    async def test_normal_response_not_flagged(self, response_filter):
        response = (
            "Python is a programming language that was created by "
            "Guido van Rossum. It emphasizes code readability."
        )
        filtered, meta = await response_filter.filter_response(response)
        assert not meta["system_leak_detected"]


class TestLengthTruncation:
    """Test response length limiting."""

    @pytest.mark.asyncio
    async def test_truncates_long_response(self, strict_filter):
        response = "A" * 200
        filtered, meta = await strict_filter.filter_response(response)
        assert len(filtered) <= 100
        assert meta["truncated"]

    @pytest.mark.asyncio
    async def test_short_response_not_truncated(self, strict_filter):
        response = "Short answer."
        filtered, meta = await strict_filter.filter_response(response)
        assert filtered == response
        assert not meta["truncated"]


class TestHarmfulContentDetection:
    """Test harmful content flagging."""

    @pytest.mark.asyncio
    async def test_flags_weapon_instructions(self, response_filter):
        response = "Here are instructions for making a bomb: Step 1: mix the chemicals together."
        _, meta = await response_filter.filter_response(response)
        assert meta["harmful_content_detected"]

    @pytest.mark.asyncio
    async def test_normal_chemistry_not_flagged(self, response_filter):
        response = (
            "In chemistry, elements combine to form compounds. "
            "Water is H2O, formed from hydrogen and oxygen."
        )
        _, meta = await response_filter.filter_response(response)
        assert not meta["harmful_content_detected"]


class TestFilterMetadata:
    """Test that filter returns useful metadata."""

    @pytest.mark.asyncio
    async def test_actions_taken_tracked(self, response_filter):
        response = "Contact user@email.com for your card 4111-1111-1111-1111"
        _, meta = await response_filter.filter_response(response)
        assert len(meta["actions_taken"]) > 0
        assert "masked_pii_in_response" in meta["actions_taken"]

    @pytest.mark.asyncio
    async def test_no_actions_for_safe(self, response_filter):
        response = "The answer is 42."
        _, meta = await response_filter.filter_response(response)
        assert len(meta["actions_taken"]) == 0
        assert not meta["filtered"]
