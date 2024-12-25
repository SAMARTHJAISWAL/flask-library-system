import pytest
import os
import tempfile
import sqlite3
from app import create_app, init_db
from config import Config

@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()
    class TestConfig(Config):
        DATABASE_PATH = db_path
        TESTING = True
        SECRET_KEY = 'test-key'
    
    app = create_app(TestConfig())
    
    with app.app_context():
        init_db()
    
    yield app
    
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_token(client):
    # Register a user
    response = client.post('/auth/register', json={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'password123'
    })
    return response.get_json()['token']

def clear_db(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('DELETE FROM books')
    c.execute('DELETE FROM members')
    conn.commit()
    conn.close()

@pytest.fixture(autouse=True)
def setup_db(app):
    with app.app_context():
        clear_db(app.config['DATABASE_PATH'])
    yield

def test_register(client):
    response = client.post('/auth/register', json={
        'name': 'John Doe',
        'email': 'john@example.com',
        'password': 'password123'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert 'member' in data
    assert data['member']['email'] == 'john@example.com'

def test_login(client):
    client.post('/auth/register', json={
        'name': 'John Doe',
        'email': 'john@example.com',
        'password': 'password123'
    })
    response = client.post('/auth/login', json={
        'email': 'john@example.com',
        'password': 'password123'
    })
    assert response.status_code == 200
    assert 'token' in response.get_json()

def test_create_book(client, auth_token):
    response = client.post(
        '/books',
        json={
            'title': 'Test Book',
            'author': 'Test Author',
            'isbn': '1234567890',
            'quantity': 5
        },
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data['title'] == 'Test Book'

def test_get_books(client, auth_token):
    client.post(
        '/books',
        json={
            'title': 'Test Book',
            'author': 'Test Author',
            'isbn': '1234567890',
            'quantity': 5
        },
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    response = client.get(
        '/books',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['books']) == 1

def test_search_books(client, auth_token):
    client.post(
        '/books',
        json={
            'title': 'Python Programming',
            'author': 'John Smith',
            'isbn': '1111111111',
            'quantity': 5
        },
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    client.post(
        '/books',
        json={
            'title': 'Java Programming',
            'author': 'Jane Doe',
            'isbn': '2222222222',
            'quantity': 3
        },
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    response = client.get(
        '/books/search?q=Python',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['books']) == 1
    assert data['books'][0]['title'] == 'Python Programming'

def test_pagination(client, auth_token):
    for i in range(3):
        client.post(
            '/books',
            json={
                'title': f'Book {i}',
                'author': f'Author {i}',
                'isbn': f'ISBN{i}',
                'quantity': i + 1
            },
            headers={'Authorization': f'Bearer {auth_token}'}
        )
    
    response = client.get(
        '/books?per_page=2',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['books']) == 2
    assert data['total'] == 3
    assert data['total_pages'] == 2

