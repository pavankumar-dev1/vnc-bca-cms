"""Application configuration loaded from environment variables.

Never commit real secrets. Copy `.env.example` to `.env` and fill in
real values for local development; on Railway, set the same variables
in the project's Variables tab.
"""
import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    """Base configuration shared by all environments."""

    # --- Core ---
    SECRET_KEY = os.environ.get("SECRET_KEY")
    DATABASE_PATH = os.environ.get(
        "DATABASE_PATH", os.path.join(BASE_DIR, "instance", "app.db")
    )
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{DATABASE_PATH}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")

    # --- Admin bootstrap credentials (all optional) ---
    # The app creates a default admin account (admin / Admin@123) the very
    # first time it runs if no admin exists yet - no setup required. These
    # two variables let you override that default username/password hash
    # instead, but you never have to set them.
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME")
    # A Werkzeug PBKDF2 hash, e.g. produced by:
    #   python -c "from werkzeug.security import generate_password_hash as g; print(g('yourpassword'))"
    ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH")

    # --- Developer bootstrap credentials (used only to seed the developer account) ---
    # The developer account has everything the admin account has, plus exclusive
    # control over whether the "developer" credit button shows on the site.
    DEVELOPER_USERNAME = os.environ.get("DEVELOPER_USERNAME", "developer")
    DEVELOPER_PASSWORD_HASH = os.environ.get("DEVELOPER_PASSWORD_HASH")

    # --- Session / cookie security ---
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", default=True)
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)

    # --- CSRF ---
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # tokens tied to the session, not a fixed timeout

    # --- Misc ---
    DEBUG = False
    TESTING = False
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB upload/body cap


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", default=False)


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    DATABASE_PATH = ":memory:"
    SQLALCHEMY_DATABASE_URI = "sqlite://"


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config():
    env_name = os.environ.get("FLASK_ENV", "production")
    return config_by_name.get(env_name, ProductionConfig)
