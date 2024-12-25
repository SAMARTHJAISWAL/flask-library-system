from flask import Blueprint, request, jsonify
from app.models.book import Book
from app.utils.auth_utils import require_auth
from typing import Tuple, Dict, Any, List
import sqlite3
from config import Config

bp = Blueprint('books', __name__, url_prefix='/books')

@bp.route('', methods=['GET'])
@require_auth
def list_books() -> Tuple[Dict[str, Any], int]:
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', Config.PAGE_SIZE, type=int)
        conn = sqlite3.connect(Config.DATABASE_PATH)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM books')
        total = c.fetchone()[0]
        offset = (page - 1) * per_page
        c.execute('SELECT * FROM books LIMIT ? OFFSET ?', (per_page, offset))
        books = []
        for row in c.fetchall():
            books.append(Book(
                id=row[0],
                title=row[1],
                author=row[2],
                isbn=row[3],
                quantity=row[4]
            ).to_dict())
        conn.close()
        return {
            "books": books,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }, 200
    except Exception as e:
        return {"error": str(e)}, 500

@bp.route('/search', methods=['GET'])
@require_auth
def search_books() -> Tuple[Dict[str, Any], int]:
    try:
        query = request.args.get('q', '')
        if not query:
            return {"error": "Search query required"}, 400
        conn = sqlite3.connect(Config.DATABASE_PATH)
        c = conn.cursor()
        search_pattern = f"%{query}%"
        c.execute(
            'SELECT * FROM books WHERE title LIKE ? OR author LIKE ?',
            (search_pattern, search_pattern)
        )
        books = []
        for row in c.fetchall():
            books.append(Book(
                id=row[0],
                title=row[1],
                author=row[2],
                isbn=row[3],
                quantity=row[4]
            ).to_dict())
        conn.close()
        return {"books": books}, 200
    except Exception as e:
        return {"error": str(e)}, 500

@bp.route('/<int:id>', methods=['GET'])
@require_auth
def get_book(id: int) -> Tuple[Dict[str, Any], int]:
    try:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        c = conn.cursor()
        c.execute('SELECT * FROM books WHERE id = ?', (id,))
        row = c.fetchone()
        conn.close()
        if row is None:
            return {"error": "Book not found"}, 404
        book = Book(
            id=row[0],
            title=row[1],
            author=row[2],
            isbn=row[3],
            quantity=row[4]
        )
        return book.to_dict(), 200
    except Exception as e:
        return {"error": str(e)}, 500

@bp.route('', methods=['POST'])
@require_auth
def create_book() -> Tuple[Dict[str, Any], int]:
    try:
        data = request.get_json()
        if not data:
            return {"error": "No data provided"}, 400
        book = Book.from_dict(data)
        error = book.validate()
        if error:
            return {"error": error}, 400
        conn = sqlite3.connect(Config.DATABASE_PATH)
        c = conn.cursor()
        c.execute(
            'INSERT INTO books (title, author, isbn, quantity) VALUES (?, ?, ?, ?)',
            (book.title, book.author, book.isbn, book.quantity)
        )
        book.id = c.lastrowid
        conn.commit()
        conn.close()
        return book.to_dict(), 201
    except sqlite3.IntegrityError:
        return {"error": "ISBN already exists"}, 400
    except KeyError as e:
        return {"error": f"Missing required field: {str(e)}"}, 400
    except Exception as e:
        return {"error": str(e)}, 500

@bp.route('/<int:id>', methods=['PUT'])
@require_auth
def update_book(id: int) -> Tuple[Dict[str, Any], int]:
    try:
        data = request.get_json()
        if not data:
            return {"error": "No data provided"}, 400
        data['id'] = id
        book = Book.from_dict(data)
        error = book.validate()
        if error:
            return {"error": error}, 400
        conn = sqlite3.connect(Config.DATABASE_PATH)
        c = conn.cursor()
        c.execute(
            'UPDATE books SET title = ?, author = ?, isbn = ?, quantity = ? WHERE id = ?',
            (book.title, book.author, book.isbn, book.quantity, id)
        )
        if c.rowcount == 0:
            conn.close()
            return {"error": "Book not found"}, 404
        conn.commit()
        conn.close()
        return book.to_dict(), 200
    except sqlite3.IntegrityError:
        return {"error": "ISBN already exists"}, 400
    except KeyError as e:
        return {"error": f"Missing required field: {str(e)}"}, 400
    except Exception as e:
        return {"error": str(e)}, 500

@bp.route('/<int:id>', methods=['DELETE'])
@require_auth
def delete_book(id: int) -> Tuple[Dict[str, Any], int]:
    try:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        c = conn.cursor()
        c.execute('DELETE FROM books WHERE id = ?', (id,))
        if c.rowcount == 0:
            conn.close()
            return {"error": "Book not found"}, 404
        conn.commit()
        conn.close()
        return {"message": "Book deleted successfully"}, 200
    except Exception as e:
        return {"error": str(e)}, 500

