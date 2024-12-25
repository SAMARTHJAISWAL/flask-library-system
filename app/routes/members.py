from flask import Blueprint, request, jsonify
from app.models.member import Member
from app.utils.auth_utils import require_auth
from typing import Tuple, Dict, Any, List
import sqlite3
from config import Config

bp = Blueprint('members', __name__, url_prefix='/members')

@bp.route('', methods=['GET'])
@require_auth
def list_members() -> Tuple[Dict[str, Any], int]:
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', Config.PAGE_SIZE, type=int)
        conn = sqlite3.connect(Config.DATABASE_PATH)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM members')
        total = c.fetchone()[0]
        offset = (page - 1) * per_page
        c.execute('SELECT id, name, email FROM members LIMIT ? OFFSET ?', 
                 (per_page, offset))
        members = []
        for row in c.fetchall():
            members.append({
                "id": row[0],
                "name": row[1],
                "email": row[2]
            })
        conn.close()
        return {
            "members": members,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }, 200
    except Exception as e:
        return {"error": str(e)}, 500
@bp.route('/<int:id>', methods=['GET'])
@require_auth
def get_member(id: int) -> Tuple[Dict[str, Any], int]:
    try:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        c = conn.cursor()
        c.execute('SELECT id, name, email FROM members WHERE id = ?', (id,))
        row = c.fetchone()
        conn.close()
        if row is None:
            return {"error": "Member not found"}, 404
        return {
            "id": row[0],
            "name": row[1],
            "email": row[2]
        }, 200
    except Exception as e:
        return {"error": str(e)}, 500
@bp.route('/<int:id>', methods=['PUT'])
@require_auth
def update_member(id: int) -> Tuple[Dict[str, Any], int]:
    try:
        data = request.get_json()
        if not data:
            return {"error": "No data provided"}, 400
        if 'email' in data:
            return {"error": "Email cannot be updated"}, 400
        updates = []
        values = []
        if 'name' in data:
            updates.append('name = ?')
            values.append(data['name'])
        if 'password' in data:
            updates.append('password = ?')
            values.append(Member.hash_password(data['password']))
        if not updates:
            return {"error": "No valid fields to update"}, 400
        values.append(id)
        conn = sqlite3.connect(Config.DATABASE_PATH)
        c = conn.cursor()
        query = f"UPDATE members SET {', '.join(updates)} WHERE id = ?"
        c.execute(query, values)
        if c.rowcount == 0:
            conn.close()
            return {"error": "Member not found"}, 404
        conn.commit()
        c.execute('SELECT id, name, email FROM members WHERE id = ?', (id,))
        row = c.fetchone()
        conn.close()
        return {
            "id": row[0],
            "name": row[1],
            "email": row[2]
        }, 200
    except Exception as e:
        return {"error": str(e)}, 500
@bp.route('/<int:id>', methods=['DELETE'])
@require_auth
def delete_member(id: int) -> Tuple[Dict[str, Any], int]:
    try:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        c = conn.cursor()
        c.execute('DELETE FROM members WHERE id = ?', (id,))
        if c.rowcount == 0:
            conn.close()
            return {"error": "Member not found"}, 404
        conn.commit()
        conn.close()
        return {"message": "Member deleted successfully"}, 200
    except Exception as e:
        return {"error": str(e)}, 500

