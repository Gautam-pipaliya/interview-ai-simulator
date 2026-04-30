import os
import logging
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, request
from flask_caching import Cache

from .extensions import db, login_manager
from .migrations import run_startup_migrations
from .routes import register_blueprints
from .seed import seed_questions


def create_app():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    # Load .env before importing Config so class-level env reads are up to date.
    project_root = Path(__file__).resolve().parent.parent
    load_dotenv(project_root / ".env", override=True)

    from .config import Config

    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config.from_object(Config)

    # Configure caching
    app.config['CACHE_TYPE'] = 'SimpleCache'
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # 5 minutes
    cache = Cache(app)

    db.init_app(app)
    login_manager.init_app(app)

    @app.after_request
    def apply_response_headers(response):
        if request.path.startswith('/static/'):
            response.headers['Cache-Control'] = 'public, max-age=604800, immutable'
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'DENY')
        response.headers.setdefault('Referrer-Policy', 'no-referrer-when-downgrade')
        response.headers.setdefault('X-Accel-Buffering', 'no')
        return response

    register_blueprints(app)

    with app.app_context():
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        db.create_all()
        run_startup_migrations()
        seed_questions()
        logger.info("Application initialized successfully")

    return app
