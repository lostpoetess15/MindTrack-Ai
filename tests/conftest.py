# Shared pytest configuration
import pytest
import os

def pytest_configure(config):
    """Print the API URL being tested."""
    url = os.getenv("API_URL", "http://localhost:5000")
    print(f"\n  Testing against: {url}\n")