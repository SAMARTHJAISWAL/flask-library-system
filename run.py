from app import create_app, init_db
import sys
from flask import jsonify

app = create_app()

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "message": "Library Management System API",
        "status": "running",
        "endpoints": {
            "auth": ["/auth/register", "/auth/login"],
            "books": ["/books", "/books/<id>", "/books/search"],
            "members": ["/members", "/members/<id>"]
        }
    })

@app.route('/test', methods=['GET'])
def test():
    return jsonify({"message": "Test endpoint working"})

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'init-db':
        with app.app_context():
            init_db()
            print("Database initialized successfully!")
    else:
        # Added host='0.0.0.0' to ensure the server is accessible
        app.run(host='0.0.0.0', debug=True, port=5001)