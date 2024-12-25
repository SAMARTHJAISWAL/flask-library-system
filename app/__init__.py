from flask import Flask
from typing import Optional
import sqlite3
import os
from config import Config

def create_app(config: Optional[Config] = None) -> Flask:
    app = Flask(__name__)
    if config is None:
        config = Config()
    app.config.from_object(config)
    with app.app_context():
        init_db()
    from app.routes import auth, books, members
    app.register_blueprint(auth.bp)
    app.register_blueprint(books.bp)
    app.register_blueprint(members.bp)
    return app

def init_db() -> None:
    os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(Config.DATABASE_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT UNIQUE NOT NULL,
            quantity INTEGER NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


