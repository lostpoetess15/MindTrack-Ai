import os
import uuid
import logging
from datetime import datetime, timezone, timedelta
from functools import wraps
from typing import Optional 

import bcrypt
import jwt
from flask import request, jsonify, g

from auth.models import User, TokenBlacklist

log = logging.getLogger(__name__)

SECRET_KEY    = os.getenv('JWT_SECRET_KEY', 'dev-secret-change-in-production')
EXPIRY_HOURS  = int(os.getenv('JWT_EXPIRY_HOURS', 24))
BCRYPT_ROUNDS = int(os.getenv('BCRYPT_ROUNDS', 12))

# ── Password ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """Returns a bcrypt hash string. Cost factor from env (default 12)."""
    return bcrypt.hashpw(
        plain.encode('utf-8'),
        bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    ).decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    """Constant-time comparison — immune to timing attacks."""
    try:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False


# ── JWT ───────────────────────────────────────────────────────────────

def create_token(user_id: int, email: str) -> str:
    """
    Creates a signed JWT.
    jti = unique token ID used for blacklisting on logout.
    """
    payload = {
        'sub' : str(user_id),
        'email': email,
        'jti' : str(uuid.uuid4()),
        'iat' : datetime.now(timezone.utc),
        'exp' : datetime.now(timezone.utc) + timedelta(hours=EXPIRY_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')


def decode_token(token: str) -> dict:
    """
    Decodes and validates a JWT.
    Raises jwt.ExpiredSignatureError or jwt.InvalidTokenError on failure.
    """
    return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])


def _extract_bearer_token() -> Optional[str]:
    """Pulls the token from Authorization: Bearer <token> header."""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:].strip()
    return None


# ── Decorator ─────────────────────────────────────────────────────────

def require_auth(f):
    """
    Route decorator that enforces JWT authentication.

    On success  : sets g.user_id and g.token_jti, calls the route
    On failure  : returns 401 JSON with a clear message

    Usage:
        @app.route('/predict/text', methods=['POST'])
        @require_auth
        def predict_text_endpoint():
            user_id = g.user_id   # available inside the route
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_bearer_token()

        if not token:
            return jsonify({
                'status' : 'error',
                'message': 'Authentication required. '
                           'Include Authorization: Bearer <token> header.',
                'code'   : 'missing_token',
            }), 401

        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({
                'status' : 'error',
                'message': 'Your session has expired. Please log in again.',
                'code'   : 'token_expired',
            }), 401
        except jwt.InvalidTokenError as e:
            return jsonify({
                'status' : 'error',
                'message': 'Invalid token.',
                'code'   : 'invalid_token',
            }), 401

        # Check blacklist (logout revocation)
        jti = payload.get('jti', '')
        if TokenBlacklist.is_revoked(jti):
            return jsonify({
                'status' : 'error',
                'message': 'Token has been revoked. Please log in again.',
                'code'   : 'token_revoked',
            }), 401

        # Check user still exists and is active
        user = User.query.get(int(payload['sub']))
        if not user or not user.is_active:
            return jsonify({
                'status' : 'error',
                'message': 'Account not found or deactivated.',
                'code'   : 'user_inactive',
            }), 401

        # Store in Flask's request context
        g.user_id  = user.id
        g.user     = user
        g.token_jti = jti

        return f(*args, **kwargs)
    return decorated


# ── Input validation ──────────────────────────────────────────────────

def validate_email(email: str) -> bool:
    """Basic RFC-5321 email check — no external library needed."""
    import re
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email)) and len(email) <= 254


def validate_password(password: str) -> tuple[bool, str]:
    """
    Password policy:
    - 8+ characters
    - At least one uppercase letter
    - At least one digit
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter."
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit."
    return True, ""