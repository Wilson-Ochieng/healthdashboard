import pytest
import json
from models.user import User

class TestAuthentication:
    """Test cases for authentication endpoints"""
    
    def test_register(self, app):
        """Test user registration"""
        response = app.post('/auth/api/register', json={
            'email': 'newuser@example.com',
            'password': 'Test123!',
            'full_name': 'New User'
        })
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['message'] == 'Registration successful'
        assert 'user' in data
        assert data['user']['email'] == 'newuser@example.com'
    
    def test_register_invalid_email(self, app):
        """Test registration with invalid email"""
        response = app.post('/auth/api/register', json={
            'email': 'invalid-email',
            'password': 'Test123!',
            'full_name': 'New User'
        })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_register_weak_password(self, app):
        """Test registration with weak password"""
        response = app.post('/auth/api/register', json={
            'email': 'test@example.com',
            'password': 'weak',
            'full_name': 'New User'
        })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_login_success(self, app):
        """Test successful login"""
        # First register a user
        app.post('/auth/api/register', json={
            'email': 'login@example.com',
            'password': 'Test123!',
            'full_name': 'Login User'
        })
        
        # Then try to login
        response = app.post('/auth/api/login', json={
            'email': 'login@example.com',
            'password': 'Test123!',
            'remember': False
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Login successful'
        assert 'user' in data
    
    def test_login_invalid_credentials(self, app):
        """Test login with invalid credentials"""
        response = app.post('/auth/api/login', json={
            'email': 'nonexistent@example.com',
            'password': 'WrongPass123!',
            'remember': False
        })
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data