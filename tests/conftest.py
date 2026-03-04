import pytest
from flask import Flask
from flask_jwt_extended import JWTManager
from app_crud import app as flask_app
from models.health_models import CommunityHealthWorker, Patient, HealthVisit
from models.user import User
from datetime import datetime, timedelta
import tempfile
import os

@pytest.fixture
def app():
    """Create and configure a test Flask application"""
    # Create a test config
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    flask_app.config['JWT_COOKIE_CSRF_PROTECT'] = False
    flask_app.config['JWT_TOKEN_LOCATION'] = ['headers']
    
    # Create a test client
    with flask_app.test_client() as testing_client:
        with flask_app.app_context():
            yield testing_client

@pytest.fixture
def test_user():
    """Create a test user"""
    return User(
        id="TEST001",
        email="test@example.com",
        password_hash=User.hash_password("Test123!"),
        full_name="Test User",
        role="viewer"
    )

@pytest.fixture
def test_chw():
    """Create a test Community Health Worker"""
    return CommunityHealthWorker(
        id="CHW001",
        name="John Doe",
        village="Test Village",
        district="Test District",
        phone="+254700000000",
        is_active=True
    )

@pytest.fixture
def test_patient():
    """Create a test patient"""
    return Patient(
        id="PAT001",
        name="Jane Smith",
        age=30,
        village="Test Village",
        chw_id="CHW001",
        is_pregnant=False,
        has_chronic_condition=True,
        last_visit_date=datetime.now() - timedelta(days=45)
    )

@pytest.fixture
def test_visit():
    """Create a test health visit"""
    return HealthVisit(
        id="VIS001",
        patient_id="PAT001",
        chw_id="CHW001",
        visit_date=datetime.now(),
        visit_type="routine",
        notes="Regular checkup",
        is_offline_sync=False
    )