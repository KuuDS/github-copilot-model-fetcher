#!/usr/bin/env python3
"""Test different Copilot API authentication methods."""

import httpx
import json
from pathlib import Path

# Read token
token_file = Path.home() / ".copilot-fetcher" / "token.json"
token_data = json.loads(token_file.read_text())
access_token = token_data["access_token"]

print("Testing different authentication methods...\n")

# Test 1: Try different token exchange URLs
exchange_urls = [
    "https://api.github.com/copilot_internal/v2/token",
    "https://api.github.com/copilot_internal/token",
    "https://github.com/copilot_internal/token",
    "https://api.github.com/copilot/token",
]

print("=== Testing token exchange URLs ===")
for url in exchange_urls:
    try:
        resp = httpx.get(
            url,
            headers={
                "Authorization": f"Token {access_token}",
                "Accept": "application/json",
            },
            timeout=10.0,
        )
        print(f"{url}: {resp.status_code}")
    except Exception as e:
        print(f"{url}: Error - {e}")

# Test 2: Try using gh CLI token format
print("\n=== Testing with different auth headers ===")
headers_variants = [
    {"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
    {"Authorization": f"Token {access_token}", "Accept": "application/json"},
]

for i, headers in enumerate(headers_variants, 1):
    try:
        resp = httpx.get(
            "https://api.githubcopilot.com/models",
            headers=headers,
            timeout=10.0,
        )
        print(f"Variant {i} ({list(headers.keys())[0]}): {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"  Models: {len(data.get('data', []))}")
    except Exception as e:
        print(f"Variant {i}: Error - {e}")

# Test 3: Check if gh CLI is available and get its token
print("\n=== Checking gh CLI ===")
import subprocess

try:
    result = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True, timeout=10)
    print(f"gh auth status: {result.returncode}")
    if result.stdout:
        print(result.stdout[:500])
except FileNotFoundError:
    print("gh CLI not found")
except Exception as e:
    print(f"Error: {e}")

# Test 4: Try to use gh copilot CLI to get models
print("\n=== Checking gh copilot extension ===")
try:
    result = subprocess.run(
        ["gh", "copilot", "--version"], capture_output=True, text=True, timeout=10
    )
    print(f"gh copilot version: {result.returncode}")
    if result.stdout:
        print(result.stdout.strip())
except FileNotFoundError:
    print("gh copilot not found")
except Exception as e:
    print(f"Error: {e}")
