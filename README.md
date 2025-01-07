# Library Management System API

A Flask-based REST API for managing a library system, featuring CRUD operations for books and members, search functionality, pagination, and authentication.

## Features

- CRUD operations for books and members
- Search functionality for books by title or author
- Pagination support
- Custom token-based authentication
- Type hints throughout the codebase
- Comprehensive test suite

## Project Structure

```
library_system/
├── README.md
├── config.py
├── run.py
├── app/
│   ├── __init__.py
│   ├── models/
│   │   ├── book.py
│   │   └── member.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── books.py
│   │   └── members.py
│   └── utils/
│       └── auth_utils.py
└── tests/
    └── test_api.py
```

## Setup and Installation

1. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install Flask:
```bash
pip install flask
```

3. Initialize the database:
```bash
python3 run.py init-db
```

4. Run the application:
```bash
python3 run.py
```

## API Endpoints

### Authentication
- POST /auth/register - Register a new user
- POST /auth/login - Login and get access token

### Books
- GET /books - List all books (with pagination)
- GET /books/<id> - Get a specific book
- POST /books - Create a new book
- PUT /books/<id> - Update a book
- DELETE /books/<id> - Delete a book
- GET /books/search - Search books by title or author

### Members
- GET /members - List all members
- GET /members/<id> - Get a specific member
- POST /members - Create a new member
- PUT /members/<id> - Update a member
- DELETE /members/<id> - Delete a member

## Design Choices

1. **Minimalist Dependencies**: 
   - Uses only Flask without additional third-party libraries
   - Custom implementation of token-based authentication
   - SQLite for simple, file-based database storage

2. **Code Organization**:
   - Modular structure separating models, routes, and utilities
   - Type hints for better code documentation and IDE support
   - Blueprint-based route organization

3. **Security**:
   - Custom token implementation using HMAC-SHA256
   - Password hashing using SHA-256
   - Token expiration mechanism

4. **Database**:
   - SQLite for simplicity and zero-configuration
   - Proper indexing on frequently queried fields
   - Unique constraints on ISBN and email

## Running Tests

Run the test suite using pytest:
```bash
python3 -m pytest tests/
```
