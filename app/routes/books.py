import sqlite3

from flask import Blueprint, request

from app.db import get_connection
from app.models.book import Book
from app.utils.auth_utils import require_auth
from app.utils.pagination import get_pagination, page_info

bp = Blueprint("books", __name__, url_prefix="/books")

COLUMNS = "id, title, author, isbn, quantity"


def _row_to_dict(row) -> dict:
    return Book(id=row[0], title=row[1], author=row[2], isbn=row[3], quantity=row[4]).to_dict()


def _book_from_request(book_id=None):
    """Parse and validate a Book from the JSON body. Returns (book, error_response)."""
    data = request.get_json(silent=True)
    if not data:
        return None, ({"error": "No data provided"}, 400)
    if book_id is not None:
        data["id"] = book_id
    try:
        book = Book.from_dict(data)
    except KeyError as e:
        return None, ({"error": f"Missing required field: {e.args[0]}"}, 400)
    except (TypeError, ValueError):
        return None, ({"error": "Quantity must be an integer"}, 400)
    error = book.validate()
    if error:
        return None, ({"error": error}, 400)
    return book, None


@bp.route("", methods=["GET"])
@require_auth
def list_books():
    page, per_page = get_pagination()
    conn = get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
        rows = conn.execute(
            f"SELECT {COLUMNS} FROM books ORDER BY id LIMIT ? OFFSET ?",
            (per_page, (page - 1) * per_page),
        ).fetchall()
    finally:
        conn.close()
    return {"books": [_row_to_dict(r) for r in rows], **page_info(total, page, per_page)}, 200


@bp.route("/search", methods=["GET"])
@require_auth
def search_books():
    query = request.args.get("q", "").strip()
    if not query:
        return {"error": "Search query required"}, 400
    page, per_page = get_pagination()
    pattern = f"%{query}%"
    conn = get_connection()
    try:
        total = conn.execute(
            "SELECT COUNT(*) FROM books WHERE title LIKE ? OR author LIKE ?", (pattern, pattern)
        ).fetchone()[0]
        rows = conn.execute(
            f"SELECT {COLUMNS} FROM books WHERE title LIKE ? OR author LIKE ? "
            "ORDER BY id LIMIT ? OFFSET ?",
            (pattern, pattern, per_page, (page - 1) * per_page),
        ).fetchall()
    finally:
        conn.close()
    return {"books": [_row_to_dict(r) for r in rows], **page_info(total, page, per_page)}, 200


@bp.route("/<int:id>", methods=["GET"])
@require_auth
def get_book(id: int):
    conn = get_connection()
    try:
        row = conn.execute(f"SELECT {COLUMNS} FROM books WHERE id = ?", (id,)).fetchone()
    finally:
        conn.close()
    if row is None:
        return {"error": "Book not found"}, 404
    return _row_to_dict(row), 200


@bp.route("", methods=["POST"])
@require_auth
def create_book():
    book, error = _book_from_request()
    if error:
        return error
    conn = get_connection()
    try:
        c = conn.execute(
            "INSERT INTO books (title, author, isbn, quantity) VALUES (?, ?, ?, ?)",
            (book.title, book.author, book.isbn, book.quantity),
        )
        book.id = c.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        return {"error": "ISBN already exists"}, 400
    finally:
        conn.close()
    return book.to_dict(), 201


@bp.route("/<int:id>", methods=["PUT"])
@require_auth
def update_book(id: int):
    book, error = _book_from_request(book_id=id)
    if error:
        return error
    conn = get_connection()
    try:
        c = conn.execute(
            "UPDATE books SET title = ?, author = ?, isbn = ?, quantity = ? WHERE id = ?",
            (book.title, book.author, book.isbn, book.quantity, id),
        )
        if c.rowcount == 0:
            return {"error": "Book not found"}, 404
        conn.commit()
    except sqlite3.IntegrityError:
        return {"error": "ISBN already exists"}, 400
    finally:
        conn.close()
    return book.to_dict(), 200


@bp.route("/<int:id>", methods=["DELETE"])
@require_auth
def delete_book(id: int):
    conn = get_connection()
    try:
        c = conn.execute("DELETE FROM books WHERE id = ?", (id,))
        if c.rowcount == 0:
            return {"error": "Book not found"}, 404
        conn.commit()
    finally:
        conn.close()
    return {"message": "Book deleted successfully"}, 200
