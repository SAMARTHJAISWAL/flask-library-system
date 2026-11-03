# Library Management System API

[![tests](https://github.com/SAMARTHJAISWAL/flask-library-system/actions/workflows/tests.yml/badge.svg)](https://github.com/SAMARTHJAISWAL/flask-library-system/actions/workflows/tests.yml)

A Flask REST API for a small library: CRUD for books and members, book search, pagination, and token authentication. It deliberately uses only Flask (plus python-dotenv for config) and the standard library: SQLite via `sqlite3` and a hand-rolled HMAC-signed token instead of a JWT library.

## Features

- Register and log in; both return a signed bearer token (default lifetime 1 hour).
- Books: list, get, create, update, delete, and search by title or author (case-insensitive substring).
- Members: list, get, update name/password, delete. New members are created through `/auth/register`.
- Pagination on list and search endpoints (`page`, `per_page`, max 100).
- Input validation: required fields, email format, password length (8+), non-negative integer quantity, unique ISBN and email.
- Passwords stored as salted Werkzeug hashes. Accounts created by older versions (plain SHA-256) can still log in.

## Tech stack

Python 3.10+, Flask 3, SQLite (`sqlite3`), Werkzeug password hashing, pytest.

## Setup

```bash
git clone https://github.com/SAMARTHJAISWAL/flask-library-system.git
cd flask-library-system
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # set SECRET_KEY
python run.py init-db       # optional: tables are also created on startup
python run.py
```

The API runs at <http://127.0.0.1:5001>.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `dev-key-please-change-in-production` | Key used to sign tokens. Set your own outside local development |
| `DATABASE_PATH` | `./database/library.db` | SQLite file location |
| `TOKEN_EXPIRATION` | `3600` | Token lifetime in seconds |
| `HOST` / `PORT` | `127.0.0.1` / `5001` | Bind address for `python run.py` |
| `FLASK_DEBUG` | `0` | Set `1` to enable the Flask debugger (local use only) |

## API

All `/books` and `/members` routes require `Authorization: Bearer <token>`.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Service info and endpoint list |
| `POST` | `/auth/register` | Body `{name, email, password}`. Returns `token` and `member` (201) |
| `POST` | `/auth/login` | Body `{email, password}`. Returns `token` and `member` |
| `GET` | `/books?page=&per_page=` | List books |
| `GET` | `/books/search?q=&page=&per_page=` | Search by title or author |
| `GET` | `/books/<id>` | Get a book |
| `POST` | `/books` | Body `{title, author, isbn, quantity}` (201) |
| `PUT` | `/books/<id>` | Replace a book (all fields required) |
| `DELETE` | `/books/<id>` | Delete a book |
| `GET` | `/members?page=&per_page=` | List members (no passwords) |
| `GET` | `/members/<id>` | Get a member |
| `PUT` | `/members/<id>` | Body with `name` and/or `password`. Email cannot be changed |
| `DELETE` | `/members/<id>` | Delete a member |

Example:

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:5001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name": "Demo", "email": "demo@example.com", "password": "password123"}' \
  | python -c 'import sys, json; print(json.load(sys.stdin)["token"])')

curl -X POST http://127.0.0.1:5001/books -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Dune", "author": "Frank Herbert", "isbn": "9780441013593", "quantity": 3}'

curl "http://127.0.0.1:5001/books/search?q=dune" -H "Authorization: Bearer $TOKEN"
```

List responses look like:

```json
{"books": [...], "total": 1, "page": 1, "per_page": 10, "total_pages": 1}
```

Errors are returned as `{"error": "..."}` with status 400, 401 or 404.

## Project structure

```
config.py              # settings from env / .env
run.py                 # entry point (python run.py [init-db])
app/
  __init__.py          # create_app factory
  db.py                # schema + connection helper
  models/book.py       # Book dataclass + validation
  models/member.py     # Member dataclass, password hashing
  routes/auth.py       # /auth
  routes/books.py      # /books
  routes/members.py    # /members
  utils/auth_utils.py  # token create/verify, @require_auth
  utils/pagination.py
tests/test_api.py
```

## Design notes

- Tokens are `base64url(JSON {user_id, exp}) + "." + HMAC-SHA256(SECRET_KEY)`, checked with a constant-time comparison.
- Any authenticated user can manage any book or member. There are no roles.
- Indexes on book title and author; unique constraints on ISBN and email.

## Tests

Each test gets its own temporary SQLite database.

```bash
pip install -r requirements-dev.txt
python -m pytest
```
