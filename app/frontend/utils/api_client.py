import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv('API_URL', 'http://localhost:5000')
TIMEOUT = 30


def _auth_headers() -> dict:
    """Returns Authorization header if a token is in session state."""
    token = st.session_state.get('token')
    if token:
        return {'Authorization': f'Bearer {token}'}
    return {}


def check_health() -> dict:
    r = requests.get(f"{API_URL}/health", timeout=5)
    r.raise_for_status()
    return r.json()


def register(email: str, password: str, display_name: str = '') -> dict:
    r = requests.post(
        f"{API_URL}/auth/register",
        json    = {'email': email, 'password': password,
                   'display_name': display_name},
        timeout = TIMEOUT
    )
    r.raise_for_status()
    return r.json()


def login(email: str, password: str) -> dict:
    r = requests.post(
        f"{API_URL}/auth/login",
        json    = {'email': email, 'password': password},
        timeout = TIMEOUT
    )
    r.raise_for_status()
    return r.json()


def logout() -> dict:
    r = requests.post(
        f"{API_URL}/auth/logout",
        headers = _auth_headers(),
        timeout = TIMEOUT
    )
    r.raise_for_status()
    return r.json()


def get_me() -> dict:
    r = requests.get(
        f"{API_URL}/auth/me",
        headers = _auth_headers(),
        timeout = TIMEOUT
    )
    r.raise_for_status()
    return r.json()


def get_history(page: int = 1, limit: int = 20) -> dict:
    r = requests.get(
        f"{API_URL}/auth/history",
        headers = _auth_headers(),
        params  = {'page': page, 'limit': limit},
        timeout = TIMEOUT
    )
    r.raise_for_status()
    return r.json()


def predict_text(text: str) -> dict:
    r = requests.post(
        f"{API_URL}/predict/text",
        headers = _auth_headers(),
        json    = {'text': text},
        timeout = TIMEOUT
    )
    r.raise_for_status()
    return r.json()


def predict_audio(audio_bytes: bytes, filename: str) -> dict:
    r = requests.post(
        f"{API_URL}/predict/audio",
        headers = _auth_headers(),
        files   = {'file': (filename, audio_bytes, 'audio/wav')},
        timeout = TIMEOUT
    )
    r.raise_for_status()
    return r.json()