import sqlite3

from flask import Blueprint, request

from app.db import get_connection
from app.models.member import Member
from app.utils.auth_utils import create_token

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)
    if not data:
        return {"error": "No data provided"}, 400

    for field in ("name", "email", "password"):
        if field not in data:
            return {"error": f"Missing required field: {field}"}, 400

    # Validate the plain-text password before it is hashed.
    error = Member.validate_password(data["password"])
    if error:
        return {"error": error}, 400

    member = Member.from_dict(data)
    error = member.validate()
    if error:
        return {"error": error}, 400

    conn = get_connection()
    try:
        c = conn.execute(
            "INSERT INTO members (name, email, password) VALUES (?, ?, ?)",
            (member.name, member.email, member.password),
        )
        member.id = c.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        return {"error": "Email already exists"}, 400
    finally:
        conn.close()

    return {
        "message": "Registration successful",
        "token": create_token(member.id),
        "member": member.to_dict(),
    }, 201


@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if not data or "email" not in data or "password" not in data:
        return {"error": "Email and password required"}, 400

    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, name, email, password FROM members WHERE email = ?", (data["email"],)
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return {"error": "Invalid email or password"}, 401

    member = Member(id=row[0], name=row[1], email=row[2], password=row[3])
    if not member.check_password(str(data["password"])):
        return {"error": "Invalid email or password"}, 401

    return {"token": create_token(member.id), "member": member.to_dict()}, 200
