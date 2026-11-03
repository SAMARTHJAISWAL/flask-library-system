import pytest

from app import create_app
from config import Config

@pytest.fixture
def app(tmp_path):
    class TestConfig(Config):
        DATABASE_PATH = str(tmp_path / 'test.db')
        TESTING = True
        SECRET_KEY = 'test-key'

    return create_app(TestConfig())

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



# --- Additional coverage -------------------------------------------------

import base64
import json
import sqlite3
import time

from app.models.member import Member
from app.utils.auth_utils import verify_token


def _auth(token):
    return {'Authorization': f'Bearer {token}'}


def test_uses_configured_database(app, client, auth_token):
    """Routes must write to the app's DATABASE_PATH, not the default path."""
    conn = sqlite3.connect(app.config['DATABASE_PATH'])
    assert conn.execute('SELECT email FROM members').fetchall() == [('test@example.com',)]
    conn.close()


def test_short_password_rejected(client):
    r = client.post('/auth/register', json={'name': 'A', 'email': 'a@example.com', 'password': 'short'})
    assert r.status_code == 400
    assert 'at least 8' in r.get_json()['error']


def test_duplicate_email_rejected(client, auth_token):
    r = client.post('/auth/register', json={'name': 'X', 'email': 'test@example.com', 'password': 'password123'})
    assert r.status_code == 400


def test_login_wrong_password(client, auth_token):
    r = client.post('/auth/login', json={'email': 'test@example.com', 'password': 'wrong-password'})
    assert r.status_code == 401


def test_passwords_are_salted_hashes(app, auth_token):
    conn = sqlite3.connect(app.config['DATABASE_PATH'])
    stored = conn.execute('SELECT password FROM members').fetchone()[0]
    conn.close()
    assert stored != 'password123'
    assert stored.startswith(('scrypt:', 'pbkdf2:'))


def test_legacy_sha256_password_still_works():
    import hashlib
    member = Member(id=1, name='Old', email='old@example.com',
                    password=hashlib.sha256(b'password123').hexdigest())
    assert member.check_password('password123')
    assert not member.check_password('nope')


def test_requires_auth(client):
    assert client.get('/books').status_code == 401
    assert client.get('/books', headers={'Authorization': 'Bearer garbage'}).status_code == 401
    assert client.get('/books', headers={'Authorization': 'Token abc'}).status_code == 401


def test_tampered_and_expired_tokens(app, auth_token):
    payload_b64, sig = auth_token.split('.')
    forged = base64.urlsafe_b64encode(json.dumps({'user_id': 999, 'exp': 9999999999}).encode()).decode()
    with app.app_context():
        with pytest.raises(ValueError, match='Invalid token'):
            verify_token(f'{forged}.{sig}')
        app.config['TOKEN_EXPIRATION'] = -10
        from app.utils.auth_utils import create_token
        expired = create_token(1)
        with pytest.raises(ValueError, match='expired'):
            verify_token(expired)


def test_book_crud(client, auth_token):
    h = _auth(auth_token)
    book = {'title': 'Dune', 'author': 'Frank Herbert', 'isbn': '9780441013593', 'quantity': 2}
    book_id = client.post('/books', json=book, headers=h).get_json()['id']

    assert client.get(f'/books/{book_id}', headers=h).get_json()['title'] == 'Dune'
    updated = client.put(f'/books/{book_id}', json={**book, 'quantity': 7}, headers=h)
    assert updated.status_code == 200 and updated.get_json()['quantity'] == 7
    assert client.post('/books', json=book, headers=h).status_code == 400  # duplicate ISBN
    assert client.delete(f'/books/{book_id}', headers=h).status_code == 200
    assert client.get(f'/books/{book_id}', headers=h).status_code == 404
    assert client.delete(f'/books/{book_id}', headers=h).status_code == 404


def test_book_validation(client, auth_token):
    h = _auth(auth_token)
    base = {'title': 'T', 'author': 'A', 'isbn': '1', 'quantity': 1}
    assert client.post('/books', json={**base, 'quantity': 'many'}, headers=h).status_code == 400
    assert client.post('/books', json={**base, 'quantity': -1}, headers=h).status_code == 400
    assert client.post('/books', json={'title': 'T'}, headers=h).status_code == 400


def test_pagination_bounds(client, auth_token):
    h = _auth(auth_token)
    assert client.get('/books?per_page=0', headers=h).status_code == 200
    assert client.get('/books?page=-3', headers=h).get_json()['page'] == 1


def test_member_endpoints(client, auth_token):
    h = _auth(auth_token)
    members = client.get('/members', headers=h).get_json()
    assert members['total'] == 1
    member_id = members['members'][0]['id']
    assert 'password' not in members['members'][0]

    r = client.put(f'/members/{member_id}', json={'name': 'Renamed'}, headers=h)
    assert r.get_json()['name'] == 'Renamed'
    assert client.put(f'/members/{member_id}', json={'password': 'short'}, headers=h).status_code == 400
    assert client.put(f'/members/{member_id}', json={'email': 'x@y.com'}, headers=h).status_code == 400
    assert client.delete(f'/members/{member_id}', headers=h).status_code == 200
    assert client.get(f'/members/{member_id}', headers=h).status_code == 404
