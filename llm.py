"""
LLM interaction layer for PEACE_COM.
"""

import warnings
from typing import TypeVar

import litellm
from pydantic import BaseModel

from config import MODEL

# Suppress Pydantic serialization warnings from LiteLLM
warnings.filterwarnings("ignore", message="Pydantic serializer warnings")

T = TypeVar("T", bound=BaseModel)


def get_response(messages: list[dict]) -> str:
    """Get a response from the LLM."""
    response = litellm.completion(
        model=MODEL,
        messages=messages,
    )
    return response.choices[0].message.content


def get_structured_response(messages: list[dict], response_model: type[T]) -> T:
    """Get a structured response from the LLM, validated against a Pydantic model."""
    response = litellm.completion(
        model=MODEL,
        messages=messages,
        response_format=response_model,
    )
    content = response.choices[0].message.content
    return response_model.model_validate_json(content)
