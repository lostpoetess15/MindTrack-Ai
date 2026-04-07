from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    db.init_app(app)
    # Import models here so they are registered before create_all
    import auth.models   # noqa: F401 — registers User, Prediction, TokenBlacklist
    with app.app_context():
        db.create_all()