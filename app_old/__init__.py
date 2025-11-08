import os
from flask import Flask

from .config import Config
from .extensions import db, migrate
from .routes.admin import admin_bp
from .routes.api import api_bp
from .routes.public import public_bp
from .seed import ensure_seed_data


def create_app(config_class: type[Config] | None = None) -> Flask:
    """Application factory used by both the CLI and the WSGI entry point."""
    app = Flask(
        __name__,
        instance_relative_config=True,
        static_folder="../static",
        template_folder="../templates",
    )

    app.config.from_object(config_class or Config)

    os.makedirs(app.instance_path, exist_ok=True)

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    with app.app_context():
        db.create_all()
        ensure_seed_data()

    return app
