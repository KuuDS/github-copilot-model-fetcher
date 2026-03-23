#!/usr/bin/env python3
"""Test different Copilot API configurations."""

import httpx
import json
from pathlib import Path

# Read token
token_file = Path.home() / ".copilot-fetcher" / "token.json"
token_data = json.loads(token_file.read_text())
access_token = token_data["access_token"]

print("Testing different API configurations...\n")

# Test 1: Current configuration
print("=== Test 1: Current config (basic headers) ===")
try:
    client = httpx.Client(
        base_url="https://api.githubcopilot.com",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        },
        timeout=30.0,
    )
    resp = client.get("/models")
    print(f"Status: {resp.status_code}")
    data = resp.json()
    print(f"Models count: {len(data.get('data', []))}")
    for m in data.get("data", [])[:3]:
        print(f"  - {m.get('id')}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: With editor version headers
print("\n=== Test 2: With editor version headers ===")
try:
    client = httpx.Client(
        base_url="https://api.githubcopilot.com",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Editor-Version": "vscode/1.85.0",
            "Copilot-Editor-Version": "vscode/1.85.0",
        },
        timeout=30.0,
    )
    resp = client.get("/models")
    print(f"Status: {resp.status_code}")
    data = resp.json()
    print(f"Models count: {len(data.get('data', []))}")
    for m in data.get("data", [])[:3]:
        print(f"  - {m.get('id')}")
except Exception as e:
    print(f"Error: {e}")

# Test 3: With OpenAI-compatible endpoint
print("\n=== Test 3: OpenAI-compatible /v1/models ===")
try:
    client = httpx.Client(
        base_url="https://api.githubcopilot.com",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        },
        timeout=30.0,
    )
    resp = client.get("/v1/models")
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Models count: {len(data.get('data', []))}")
        for m in data.get("data", [])[:3]:
            print(f"  - {m.get('id')}")
    else:
        print(f"Response: {resp.text[:200]}")
except Exception as e:
    print(f"Error: {e}")

# Test 4: Check if there's a query parameter
print("\n=== Test 4: With query parameters ===")
try:
    client = httpx.Client(
        base_url="https://api.githubcopilot.com",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        },
        timeout=30.0,
    )
    resp = client.get("/models", params={"include_all": "true"})
    print(f"Status: {resp.status_code}")
    data = resp.json()
    print(f"Models count: {len(data.get('data', []))}")
except Exception as e:
    print(f"Error: {e}")

# Test 5: Try chat/completions to see what models are available
print("\n=== Test 5: Check chat endpoint headers ===")
try:
    client = httpx.Client(
        base_url="https://api.githubcopilot.com",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        timeout=30.0,
    )
    # Try a simple request to see error message (which might list available models)
    resp = client.post(
        "/chat/completions",
        json={"model": "claude-sonnet-4", "messages": [{"role": "user", "content": "hi"}]},
    )
    print(f"Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"Response: {resp.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
