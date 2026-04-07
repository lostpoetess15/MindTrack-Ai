# ══════════════════════════════════════════════════════
#  Database models — User, Prediction, TokenBlacklist
# ══════════════════════════════════════════════════════
from datetime import datetime, timezone
from database import db          # db = SQLAlchemy() — no app bound yet, safe to import


class User(db.Model):
    __tablename__ = 'users'

    id            = db.Column(db.Integer,    primary_key=True)
    email         = db.Column(db.String(254), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(60),  nullable=False)
    display_name  = db.Column(db.String(80),  nullable=True)
    is_active     = db.Column(db.Boolean,     default=True, nullable=False)
    created_at    = db.Column(db.DateTime,    default=lambda: datetime.now(timezone.utc))
    last_login    = db.Column(db.DateTime,    nullable=True)

    predictions   = db.relationship(
        'Prediction', backref='user',
        lazy='dynamic', cascade='all, delete-orphan'
    )

    def to_safe_dict(self) -> dict:
        return {
            'id'          : self.id,
            'email'       : self.email,
            'display_name': self.display_name or self.email.split('@')[0],
            'created_at'  : self.created_at.isoformat() + 'Z',
            'last_login'  : self.last_login.isoformat() + 'Z' if self.last_login else None,
        }

    def __repr__(self):
        return f'<User {self.email}>'


class Prediction(db.Model):
    __tablename__ = 'predictions'

    id            = db.Column(db.Integer,    primary_key=True)
    user_id       = db.Column(db.Integer,    db.ForeignKey('users.id'), nullable=False, index=True)
    modality      = db.Column(db.String(10), nullable=False)
    risk_level    = db.Column(db.String(10), nullable=False)
    confidence    = db.Column(db.Float,      nullable=False)
    input_preview = db.Column(db.String(120),nullable=True)
    created_at    = db.Column(db.DateTime,   default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self) -> dict:
        return {
            'id'           : self.id,
            'modality'     : self.modality,
            'risk_level'   : self.risk_level,
            'confidence'   : round(self.confidence, 4),
            'input_preview': self.input_preview,
            'created_at'   : self.created_at.isoformat() + 'Z',
        }


class TokenBlacklist(db.Model):
    __tablename__ = 'token_blacklist'

    id         = db.Column(db.Integer,    primary_key=True)
    jti        = db.Column(db.String(36), unique=True, nullable=False, index=True)
    revoked_at = db.Column(db.DateTime,   default=lambda: datetime.now(timezone.utc))

    @staticmethod
    def is_revoked(jti: str) -> bool:
        return db.session.query(
            TokenBlacklist.query.filter_by(jti=jti).exists()
        ).scalar()