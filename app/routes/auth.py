from flask import Blueprint, request, jsonify
from app.models.member import Member
from app.utils.auth_utils import create_token
from typing import Tuple, Dict, Any
import sqlite3
from config import Config

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=['POST'])
def register() -> Tuple[Dict[str, Any], int]:
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        required_fields = ['name', 'email', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        member = Member.from_dict(data)
        
        error = member.validate()
        if error:
            return jsonify({"error": error}), 400
        
        conn = sqlite3.connect(Config.DATABASE_PATH)
        c = conn.cursor()
        
        try:
            c.execute(
                'INSERT INTO members (name, email, password) VALUES (?, ?, ?)',
                (member.name, member.email, member.password)
            )
            member.id = c.lastrowid
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({"error": "Email already exists"}), 400
        finally:
            conn.close()
        
        token = create_token(member.id)
        
        return jsonify({
            "message": "Registration successful",
            "token": token,
            "member": member.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/login', methods=['POST'])
def login() -> Tuple[Dict[str, Any], int]:
    try:
        data = request.get_json()
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({"error": "Email and password required"}), 400
        
        conn = sqlite3.connect(Config.DATABASE_PATH)
        c = conn.cursor()
        
        c.execute('SELECT * FROM members WHERE email = ?', (data['email'],))
        member_data = c.fetchone()
        conn.close()
        
        if member_data is None:
            return jsonify({"error": "Invalid email or password"}), 401
        
        member = Member(
            id=member_data[0],
            name=member_data[1],
            email=member_data[2],
            password=member_data[3]
        )
        
        if not member.check_password(data['password']):
            return jsonify({"error": "Invalid email or password"}), 401
        
        token = create_token(member.id)
        
        return jsonify({
            "token": token,
            "member": member.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

