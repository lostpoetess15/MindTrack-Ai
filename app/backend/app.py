# ══════════════════════════════════════════════════════════════════════
#  MINDTRACK AI — Phase 7 (secured)
#  Added: auth blueprint, JWT protection on predict routes,
#         rate limiting, security headers, prediction history logging
# ══════════════════════════════════════════════════════════════════════
# mian directory for backend
import os
import time
import logging
import traceback
from pathlib import Path
from datetime import datetime

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import joblib

from database import db, init_db
from auth.routes import auth as auth_blueprint
from auth.utils  import require_auth
from auth.models import Prediction
from pipelines.text_pipeline  import predict_text
from pipelines.audio_pipeline import predict_audio
from utils.validators          import validate_text, validate_audio

load_dotenv()

logging.basicConfig(
    level   = logging.INFO,
    format  = '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt = '%H:%M:%S'
)
log = logging.getLogger('mindtrack')

# ── App factory ───────────────────────────────────────────────────────
app = Flask(__name__)

# Database config
DB_PATH = Path(os.getenv('DB_PATH', './mindtrack.db'))
app.config['SQLALCHEMY_DATABASE_URI']        = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY']                     = os.getenv('JWT_SECRET_KEY', 'dev')

# Initialise database
init_db(app)

# CORS — restrict to your frontend origin in production
CORS(app, resources={r"/*": {"origins": os.getenv("ALLOWED_ORIGINS", "*")}})

# Rate limiter — uses in-memory storage for development
limiter = Limiter(
    app            = app,
    key_func       = get_remote_address,
    default_limits = ["200 per minute"],
    storage_uri    = "memory://",
)

# Register auth blueprint
app.register_blueprint(auth_blueprint)

PORT       = int(os.getenv('FLASK_PORT', 5000))
MODELS_DIR = Path(os.getenv('MODELS_DIR', '../../models'))

# ── Security headers — applied to every response ──────────────────────
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options']        = 'DENY'
    response.headers['X-XSS-Protection']       = '1; mode=block'
    response.headers['Referrer-Policy']        = 'strict-origin-when-cross-origin'
    response.headers['Cache-Control']          = 'no-store'
    return response

# ── Load models ───────────────────────────────────────────────────────
models = {}

def load_models():
    required = {
        'text_model'    : MODELS_DIR / 'best_text_model.pkl',
        'audio_pipeline': MODELS_DIR / 'best_audio_model.pkl',
        'tfidf'         : MODELS_DIR / 'tfidf_vectorizer.pkl',
        'le_text'       : MODELS_DIR / 'label_encoder_text.pkl',
        'le_audio'      : MODELS_DIR / 'label_encoder_audio.pkl',
    }
    loaded, failed = {}, []
    for key, path in required.items():
        if path.exists():
            try:
                loaded[key] = joblib.load(path)
                log.info(f"  Loaded  {key:20s} <- {path.name}")
            except Exception as e:
                log.error(f"  FAILED  {key}: {e}")
                failed.append(key)
        else:
            log.error(f"  MISSING {key}: {path}")
            failed.append(key)
    return loaded, failed

log.info("=" * 55)
log.info("  MindTrack AI — Backend (secured) starting")
models, failed_models = load_models()
startup_time = datetime.utcnow().isoformat() + 'Z'
log.info(f"  Models ready: {len(models)}/{len(models)+len(failed_models)}")
log.info("=" * 55)


# ── Helpers ───────────────────────────────────────────────────────────
def success(data, status=200): return jsonify({'status':'success',**data}), status
def error(msg, status, details=None):
    body = {'status':'error','message':msg}
    if details: body['details'] = details
    return jsonify(body), status

def _save_prediction(user_id, modality, risk_level, confidence, preview=None):
    """Persist a prediction to the user's history. Silent on failure."""
    try:
        pred = Prediction(
            user_id      = user_id,
            modality     = modality,
            risk_level   = risk_level,
            confidence   = confidence,
            input_preview= (preview or '')[:120],
        )
        db.session.add(pred)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        log.warning(f"Could not save prediction history: {e}")


# ══════════════════════════════════════════════════════════════════════
#  GET /health  — public, no auth required
# ══════════════════════════════════════════════════════════════════════
@app.route('/health', methods=['GET'])
def health():
    return success({
        'server'       : 'online',
        'started_at'   : startup_time,
        'timestamp'    : datetime.utcnow().isoformat() + 'Z',
        'models'       : {k: True for k in models},
        'failed_models': failed_models,
        'auth'         : 'enabled',
        'version'      : '2.0.0',
    })


# ══════════════════════════════════════════════════════════════════════
#  POST /predict/text  — REQUIRES AUTH
#  Rate limited: 30/minute per IP
# ══════════════════════════════════════════════════════════════════════
@app.route('/predict/text', methods=['POST'])
@limiter.limit("30 per minute")
@require_auth
def predict_text_endpoint():
    t0 = time.perf_counter()

    missing = [k for k in ['text_model','tfidf','le_text'] if k not in models]
    if missing:
        return error(f"Text prediction unavailable — missing: {missing}", 503)

    if not request.is_json:
        return error("Content-Type must be application/json", 400)

    body = request.get_json(silent=True) or {}
    text = body.get('text', '')

    is_valid, err_msg = validate_text(text)
    if not is_valid:
        return error(err_msg, 400)

    try:
        result = predict_text(text, models['text_model'],
                              models['tfidf'], models['le_text'])
    except ValueError as e:
        return error(str(e), 400)
    except Exception as e:
        log.error(traceback.format_exc())
        return error("Prediction failed.", 500, str(e))

    # Save to user's history
    _save_prediction(
        user_id    = g.user_id,
        modality   = 'text',
        risk_level = result['risk_level'],
        confidence = result['confidence'],
        preview    = text[:120],
    )

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    log.info(f"TEXT  | user={g.user_id} | risk={result['risk_level']} | "
             f"conf={result['confidence']:.3f} | {elapsed}ms")

    return success({
        'risk_level' : result['risk_level'],
        'confidence' : result['confidence'],
        'sentiment'  : result['sentiment'],
        'class_probs': result['class_probs'],
        'elapsed_ms' : elapsed,
    })


# ══════════════════════════════════════════════════════════════════════
#  POST /predict/audio  — REQUIRES AUTH
#  Rate limited: 10/minute per IP (audio is heavier)
# ══════════════════════════════════════════════════════════════════════
@app.route('/predict/audio', methods=['POST'])
@limiter.limit("10 per minute")
@require_auth
def predict_audio_endpoint():
    t0 = time.perf_counter()

    missing = [k for k in ['audio_pipeline','le_audio'] if k not in models]
    if missing:
        return error(f"Audio prediction unavailable — missing: {missing}", 503)

    if 'file' not in request.files:
        return error("No file attached. Use multipart form with key 'file'.", 400)

    uploaded_file = request.files['file']
    is_valid, err_msg = validate_audio(uploaded_file)
    if not is_valid:
        return error(err_msg, 400)

    audio_bytes = uploaded_file.read()

    try:
        result = predict_audio(audio_bytes, models['audio_pipeline'],
                               models['le_audio'])
    except ValueError as e:
        return error(str(e), 400)
    except Exception as e:
        log.error(traceback.format_exc())
        return error("Prediction failed.", 500, str(e))

    _save_prediction(
        user_id    = g.user_id,
        modality   = 'audio',
        risk_level = result['risk_level'],
        confidence = result['confidence'],
        preview    = f"[audio] {uploaded_file.filename}",
    )

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    log.info(f"AUDIO | user={g.user_id} | risk={result['risk_level']} | "
             f"conf={result['confidence']:.3f} | {elapsed}ms")

    return success({
        'risk_level'      : result['risk_level'],
        'confidence'      : result['confidence'],
        'class_probs'     : result['class_probs'],
        'duration_seconds': result['duration_seconds'],
        'elapsed_ms'      : elapsed,
    })


# ── Error handlers ────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return error("Endpoint not found.", 404)

@app.errorhandler(405)
def method_not_allowed(e):
    return error("Wrong HTTP method.", 405)

@app.errorhandler(429)
def rate_limited(e):
    return error("Too many requests. Please slow down.", 429)

@app.errorhandler(413)
def too_large(e):
    return error("File too large.", 413)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT,
            debug=os.getenv('FLASK_ENV') == 'development')