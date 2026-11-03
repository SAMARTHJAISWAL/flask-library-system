from flask import Blueprint, request

from app.db import get_connection
from app.models.member import Member
from app.utils.auth_utils import require_auth
from app.utils.pagination import get_pagination, page_info

bp = Blueprint("members", __name__, url_prefix="/members")


def _row_to_dict(row) -> dict:
    return {"id": row[0], "name": row[1], "email": row[2]}


@bp.route("", methods=["GET"])
@require_auth
def list_members():
    page, per_page = get_pagination()
    conn = get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) FROM members").fetchone()[0]
        rows = conn.execute(
            "SELECT id, name, email FROM members ORDER BY id LIMIT ? OFFSET ?",
            (per_page, (page - 1) * per_page),
        ).fetchall()
    finally:
        conn.close()
    return {"members": [_row_to_dict(r) for r in rows], **page_info(total, page, per_page)}, 200


@bp.route("/<int:id>", methods=["GET"])
@require_auth
def get_member(id: int):
    conn = get_connection()
    try:
        row = conn.execute("SELECT id, name, email FROM members WHERE id = ?", (id,)).fetchone()
    finally:
        conn.close()
    if row is None:
        return {"error": "Member not found"}, 404
    return _row_to_dict(row), 200


@bp.route("/<int:id>", methods=["PUT"])
@require_auth
def update_member(id: int):
    data = request.get_json(silent=True)
    if not data:
        return {"error": "No data provided"}, 400
    if "email" in data:
        return {"error": "Email cannot be updated"}, 400

    updates, values = [], []
    if "name" in data:
        error = Member.validate_name(data["name"])
        if error:
            return {"error": error}, 400
        updates.append("name = ?")
        values.append(data["name"])
    if "password" in data:
        error = Member.validate_password(data["password"])
        if error:
            return {"error": error}, 400
        updates.append("password = ?")
        values.append(Member.hash_password(data["password"]))
    if not updates:
        return {"error": "No valid fields to update"}, 400

    conn = get_connection()
    try:
        c = conn.execute(f"UPDATE members SET {', '.join(updates)} WHERE id = ?", (*values, id))
        if c.rowcount == 0:
            return {"error": "Member not found"}, 404
        conn.commit()
        row = conn.execute("SELECT id, name, email FROM members WHERE id = ?", (id,)).fetchone()
    finally:
        conn.close()
    return _row_to_dict(row), 200


@bp.route("/<int:id>", methods=["DELETE"])
@require_auth
def delete_member(id: int):
    conn = get_connection()
    try:
        c = conn.execute("DELETE FROM members WHERE id = ?", (id,))
        if c.rowcount == 0:
            return {"error": "Member not found"}, 404
        conn.commit()
    finally:
        conn.close()
    return {"message": "Member deleted successfully"}, 200
