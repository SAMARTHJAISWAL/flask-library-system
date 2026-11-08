from typing import Optional

from flask import Flask

from app.db import init_db as _init_db
from config import Config


def create_app(config: Optional[object] = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config or Config())
    init_db(app)

    from app.routes import auth, books, members

    app.register_blueprint(auth.bp)
    app.register_blueprint(books.bp)
    app.register_blueprint(members.bp)
    return app


def init_db(app: Flask) -> None:
    """Create the tables for `app`'s database if they do not exist."""
    _init_db(app.config["DATABASE_PATH"])
