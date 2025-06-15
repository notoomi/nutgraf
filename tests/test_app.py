import pytest
import tempfile
import os
from app import app
from models import db, User

@pytest.fixture
def client():
    # Create a temporary database
    db_fd, temp_db_path = tempfile.mkstemp()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + temp_db_path
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            # Clean up database after each test
            db.session.remove()
            db.drop_all()

    os.close(db_fd)
    os.unlink(temp_db_path)

def test_home_redirect(client):
    """Test that home page redirects to login for unauthenticated users"""
    rv = client.get('/')
    assert rv.status_code == 302
    assert '/auth/login' in rv.location

def test_login_page(client):
    """Test that login page loads correctly"""
    rv = client.get('/auth/login')
    assert rv.status_code == 200
    assert b'Login' in rv.data

def test_register_page(client):
    """Test that registration page loads correctly"""
    rv = client.get('/auth/register')
    assert rv.status_code == 200
    assert b'Create Account' in rv.data

def test_user_registration(client):
    """Test user registration functionality"""
    rv = client.post('/auth/register', data={
        'email': 'test@example.com',
        'password': 'testpassword123',
        'password2': 'testpassword123'
    }, follow_redirects=True)
    
    assert rv.status_code == 200
    assert b'Dashboard' in rv.data or b'Welcome' in rv.data

def test_user_login(client):
    """Test user login functionality"""
    # First create a user
    with app.app_context():
        user = User(email='test@example.com')
        user.set_password('testpassword123')
        db.session.add(user)
        db.session.commit()
    
    # Then try to log in
    rv = client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'testpassword123'
    }, follow_redirects=True)
    
    assert rv.status_code == 200
    assert b'Dashboard' in rv.data or b'Welcome' in rv.data

def test_logout(client):
    """Test user logout functionality"""
    # Login first
    with app.app_context():
        user = User(email='test@example.com')
        user.set_password('testpassword123')
        db.session.add(user)
        db.session.commit()
    
    client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'testpassword123'
    })
    
    # Then logout
    rv = client.get('/auth/logout', follow_redirects=True)
    assert rv.status_code == 200
    assert b'Login' in rv.data

def test_protected_routes_require_login(client):
    """Test that protected routes redirect to login"""
    protected_routes = [
        '/dashboard',
        '/analyze',
        '/history',
        '/settings'
    ]
    
    for route in protected_routes:
        rv = client.get(route)
        assert rv.status_code == 302
        assert '/auth/login' in rv.location

def test_api_endpoints_require_login(client):
    """Test that API endpoints require authentication"""
    api_routes = [
        '/api/process-urls',
        '/api/extract-article',
        '/api/generate-summary'
    ]
    
    for route in api_routes:
        rv = client.post(route)
        assert rv.status_code == 302  # Redirect to login