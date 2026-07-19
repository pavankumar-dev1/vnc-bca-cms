"""Application factory for the VNC BCA college website CMS."""
import logging
import os

import click
from flask import Flask, render_template
from flask_wtf import CSRFProtect

from config import get_config

csrf = CSRFProtect()


def create_app(config_object=None):
    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "static"),
        template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates"),
        instance_relative_config=True,
    )

    app.config.from_object(config_object or get_config())

    _validate_required_config(app)

    csrf.init_app(app)

    os.makedirs(os.path.dirname(app.config["DATABASE_PATH"]), exist_ok=True) \
        if app.config["DATABASE_PATH"] != ":memory:" else None
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    from .models import init_db

    init_db(app)

    from .routes import public_bp, admin_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)

    _register_context_processors(app)
    _register_error_handlers(app)
    _register_security_headers(app)
    _register_cli(app)

    with app.app_context():
        from .seed import seed_if_empty
        seed_if_empty(app)

    if not app.debug and not app.testing:
        logging.basicConfig(level=logging.INFO)

    return app


def _validate_required_config(app: Flask) -> None:
    """Fail fast (in production) if critical secrets are missing."""
    missing = []
    if not app.config.get("SECRET_KEY"):
        missing.append("SECRET_KEY")

    if missing and not (app.debug or app.testing):
        raise RuntimeError(
            "Missing required environment variable(s): "
            f"{', '.join(missing)}. See .env.example."
        )

    if not app.config.get("SECRET_KEY"):
        # Only reachable in debug/testing - generate an ephemeral key so the
        # app can still boot locally without a .env file.
        app.config["SECRET_KEY"] = os.urandom(32).hex()


def _register_context_processors(app: Flask) -> None:
    @app.context_processor
    def inject_site_settings():
        from .models import SiteSetting

        try:
            settings = SiteSetting.get()
        except Exception:
            settings = None
        return {"site_settings": settings}


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(400)
    def bad_request(_error):
        return render_template("errors/400.html"), 400

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(_error):
        return render_template("errors/500.html"), 500


def _register_security_headers(app: Flask) -> None:
    @app.after_request
    def set_secure_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return response


def _register_cli(app: Flask) -> None:
    @app.cli.command("seed-db")
    def seed_db_command():
        """Populate the database with initial/demo CMS content."""
        from .seed import seed_all

        seed_all(app, force=True)
        print("Database seeded.")

    @app.cli.command("migrate-legacy")
    @click.argument("legacy_path", required=False)
    def migrate_legacy_command(legacy_path):
        """Import notices/messages from the old instance/database.db schema."""
        from .migrate_legacy import migrate_legacy_db

        legacy_path = legacy_path or os.path.join(app.instance_path, "database.db")
        if not os.path.exists(legacy_path):
            print(f"No legacy database found at {legacy_path} - nothing to migrate.")
            return
        result = migrate_legacy_db(legacy_path)
        print(f"Imported {result['notices']} notice(s) and {result['messages']} message(s).")

    @app.cli.command("create-admin")
    def create_admin_command():
        """Create (or update) an admin or developer user."""
        from werkzeug.security import generate_password_hash
        import getpass

        from .models import AdminUser, db

        username = input("Username [admin]: ").strip() or "admin"
        role = input("Role - 'admin' or 'developer' [admin]: ").strip().lower() or "admin"
        if role not in ("admin", "developer"):
            print("Role must be 'admin' or 'developer'.")
            return
        password = getpass.getpass("Password: ")
        if not password:
            print("Password cannot be empty.")
            return

        user = AdminUser.query.filter_by(username=username).first()
        if user is None:
            user = AdminUser(username=username, password_hash=generate_password_hash(password), role=role)
            db.session.add(user)
        else:
            user.password_hash = generate_password_hash(password)
            user.role = role
        db.session.commit()
        print(f"User '{username}' saved with role '{role}'.")
