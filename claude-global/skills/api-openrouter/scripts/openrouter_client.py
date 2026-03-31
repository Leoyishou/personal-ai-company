#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenRouter API client helpers.
"""

import os

import requests

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


if load_dotenv:
    dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    load_dotenv(dotenv_path, override=False)


DEFAULT_OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-3-pro-preview")
DEFAULT_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def resolve_api_key(api_key=None):
    """Resolve API key from argument or environment."""
    resolved_key = api_key or os.getenv("OPENROUTER_API_KEY")
    if not resolved_key:
        raise ValueError("Missing OPENROUTER_API_KEY")
    return resolved_key


def build_headers(api_key, app_name=None, site_url=None):
    """Build OpenRouter request headers."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    resolved_site_url = site_url or os.getenv("OPENROUTER_SITE_URL")
    resolved_app_name = app_name or os.getenv("OPENROUTER_APP_NAME", "openrouter-chat")
    if resolved_site_url:
        headers["HTTP-Referer"] = resolved_site_url
    if resolved_app_name:
        headers["X-Title"] = resolved_app_name
    return headers


def normalize_messages(messages):
    """Validate and normalize OpenRouter message list."""
    if not isinstance(messages, list) or not messages:
        raise ValueError("Messages must be a non-empty list")

    normalized = []
    for message in messages:
        if not isinstance(message, dict):
            raise ValueError("Each message must be a dict with role/content")
        role = message.get("role")
        content = message.get("content")
        if not role or content is None:
            raise ValueError("Message missing role/content")
        normalized.append({"role": role, "content": content})
    return normalized


def request_openrouter(
    model,
    messages,
    api_key=None,
    base_url=None,
    temperature=0.7,
    max_tokens=None,
    timeout=90,
    extra_payload=None,
):
    """
    Call OpenRouter chat completions API.

    Returns:
        tuple: (content, raw_json)
    """
    resolved_key = resolve_api_key(api_key)
    resolved_url = base_url or os.getenv("OPENROUTER_BASE_URL", DEFAULT_OPENROUTER_URL)

    payload = {
        "model": model or DEFAULT_OPENROUTER_MODEL,
        "messages": normalize_messages(messages),
        "temperature": temperature,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if extra_payload:
        payload.update(extra_payload)

    response = requests.post(
        resolved_url,
        json=payload,
        headers=build_headers(resolved_key),
        timeout=timeout,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"OpenRouter request failed ({response.status_code}): {response.text}"
        )

    data = response.json()
    choices = data.get("choices")
    if not choices:
        raise RuntimeError(f"OpenRouter response missing choices: {data}")

    return choices[0]["message"]["content"], data
