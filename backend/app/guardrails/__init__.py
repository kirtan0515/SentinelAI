"""
NVIDIA NeMo Guardrails Integration

Provides input and output guardrails using NeMo's Colang runtime.
Guardrails are applied:
- BEFORE prompts reach the LLM (input rails)
- AFTER LLM responses are generated (output rails)
"""

from app.guardrails.manager import GuardrailsManager

__all__ = ["GuardrailsManager"]
