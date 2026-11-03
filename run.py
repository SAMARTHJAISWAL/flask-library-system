import os
import sys

from flask import jsonify

from app import create_app, init_db

app = create_app()


@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "message": "Library Management System API",
        "status": "running",
        "endpoints": {
            "auth": ["/auth/register", "/auth/login"],
            "books": ["/books", "/books/<id>", "/books/search"],
            "members": ["/members", "/members/<id>"],
        },
    })


@app.route("/test", methods=["GET"])
def test():
    return jsonify({"message": "Test endpoint working"})


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "init-db":
        init_db(app)
        print(f"Database initialized at {app.config['DATABASE_PATH']}")
    else:
        app.run(
            host=os.environ.get("HOST", "127.0.0.1"),
            port=int(os.environ.get("PORT", "5001")),
            debug=os.environ.get("FLASK_DEBUG", "0") == "1",
        )
