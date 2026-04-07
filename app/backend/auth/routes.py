# ══════════════════════════════════════════════════════
#  Auth blueprint
#  POST /auth/register
#  POST /auth/login
#  GET  /auth/me
#  POST /auth/logout
#  GET  /auth/history
# ══════════════════════════════════════════════════════
import logging
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify, g
from sqlalchemy.exc import IntegrityError

from database import db
from auth.models import User, Prediction, TokenBlacklist
from auth.utils import (
    hash_password, verify_password, create_token,
    require_auth, validate_email, validate_password
)

log    = logging.getLogger(__name__)
auth   = Blueprint('auth', __name__, url_prefix='/auth')


# ── Helper ─────────────────────────────────────────────────────────────

def _ok(data: dict, status: int = 200):
    return jsonify({'status': 'success', **data}), status

def _err(message: str, status: int, code: str = 'error'):
    return jsonify({'status': 'error', 'message': message, 'code': code}), status


# ── POST /auth/register ────────────────────────────────────────────────

@auth.route('/register', methods=['POST'])
def register():
    """
    Create a new account.

    Body (JSON):
        { "email": "...", "password": "...", "display_name": "..." }

    Returns:
        201 + { token, user } on success
        400 on validation failure
        409 if email already registered
    """
    if not request.is_json:
        return _err("Request must be JSON.", 400)

    body         = request.get_json(silent=True) or {}
    email        = (body.get('email')        or '').strip().lower()
    password     = (body.get('password')     or '').strip()
    display_name = (body.get('display_name') or '').strip()

    # ── Validate ──────────────────────────────────────────────────────
    if not email:
        return _err("Email is required.", 400)
    if not validate_email(email):
        return _err("Please enter a valid email address.", 400)
    if not password:
        return _err("Password is required.", 400)

    pw_ok, pw_msg = validate_password(password)
    if not pw_ok:
        return _err(pw_msg, 400)

    # ── Create user ───────────────────────────────────────────────────
    try:
        user = User(
            email        = email,
            password_hash= hash_password(password),
            display_name = display_name or None,
        )
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _err("An account with this email already exists.", 409, 'email_taken')

    token = create_token(user.id, user.email)
    log.info(f"New user registered: {email}")

    return _ok({
        'message': 'Account created successfully.',
        'token'  : token,
        'user'   : user.to_safe_dict(),
    }, 201)


# ── POST /auth/login ───────────────────────────────────────────────────

@auth.route('/login', methods=['POST'])
def login():
    """
    Authenticate and receive a JWT token.

    Body (JSON):
        { "email": "...", "password": "..." }

    Returns:
        200 + { token, user } on success
        401 on wrong credentials (intentionally vague — no user enumeration)
    """
    if not request.is_json:
        return _err("Request must be JSON.", 400)

    body     = request.get_json(silent=True) or {}
    email    = (body.get('email')    or '').strip().lower()
    password = (body.get('password') or '').strip()

    if not email or not password:
        return _err("Email and password are required.", 400)

    # Look up user — intentionally identical error for missing vs wrong password
    # This prevents user enumeration attacks
    user = User.query.filter_by(email=email, is_active=True).first()

    if not user or not verify_password(password, user.password_hash):
        return _err(
            "Incorrect email or password.",
            401,
            'invalid_credentials'
        )

    # Update last_login timestamp
    user.last_login = datetime.now(timezone.utc)
    db.session.commit()

    token = create_token(user.id, user.email)
    log.info(f"User logged in: {email}")

    return _ok({
        'message': 'Login successful.',
        'token'  : token,
        'user'   : user.to_safe_dict(),
    })


# ── GET /auth/me ───────────────────────────────────────────────────────

@auth.route('/me', methods=['GET'])
@require_auth
def me():
    """Returns the current user's profile. Requires valid JWT."""
    return _ok({'user': g.user.to_safe_dict()})


# ── POST /auth/logout ──────────────────────────────────────────────────

@auth.route('/logout', methods=['POST'])
@require_auth
def logout():
    """
    Revokes the current JWT by adding it to the blacklist.
    After this, the token is rejected on all future requests.
    """
    blacklisted = TokenBlacklist(jti=g.token_jti)
    db.session.add(blacklisted)
    db.session.commit()
    log.info(f"User logged out: {g.user.email}")
    return _ok({'message': 'Logged out successfully.'})


# ── GET /auth/history ──────────────────────────────────────────────────

@auth.route('/history', methods=['GET'])
@require_auth
def history():
    """
    Returns the authenticated user's last 20 predictions.
    Used by the frontend to populate the history panel on login.
    """
    page     = request.args.get('page',  1,  type=int)
    per_page = request.args.get('limit', 20, type=int)
    per_page = min(per_page, 50)   # cap at 50

    paginated = (
        Prediction.query
        .filter_by(user_id=g.user_id)
        .order_by(Prediction.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return _ok({
        'predictions' : [p.to_dict() for p in paginated.items],
        'total'       : paginated.total,
        'page'        : page,
        'pages'       : paginated.pages,
    })


# ── Empty __init__ ─────────────────────────────────────────────────────