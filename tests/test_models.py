import pytest
from datetime import datetime, timedelta
from models.user import User
from models.health_models import CommunityHealthWorker, Patient, HealthVisit

class TestUserModel:
    """Test cases for User model"""
    
    def test_user_creation(self):
        """Test user creation"""
        user = User(
            id="USR001",
            email="test@example.com",
            password_hash=User.hash_password("Test123!"),
            full_name="Test User",
            role="viewer"
        )
        
        assert user.id == "USR001"
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.role == "viewer"
        assert user.is_active == True
        assert user.verify_password("Test123!") == True
        assert user.verify_password("WrongPassword") == False
    
    def test_user_role_permissions(self, test_user):
        """Test role-based permissions"""
        # Test viewer permissions
        assert test_user.has_permission('read') == True
        assert test_user.has_permission('create') == False
        assert test_user.has_permission('update') == False
        assert test_user.has_permission('delete') == False
        
        # Test manager permissions
        test_user.role = 'manager'
        assert test_user.has_permission('read') == True
        assert test_user.has_permission('create') == True
        assert test_user.has_permission('update') == True
        assert test_user.has_permission('delete') == False
        
        # Test admin permissions
        test_user.role = 'admin'
        assert test_user.has_permission('read') == True
        assert test_user.has_permission('create') == True
        assert test_user.has_permission('update') == True
        assert test_user.has_permission('delete') == True
        assert test_user.has_permission('manage_users') == True

class TestCHWModel:
    """Test cases for Community Health Worker model"""
    
    def test_chw_creation(self, test_chw):
        """Test CHW creation"""
        assert test_chw.id == "CHW001"
        assert test_chw.name == "John Doe"
        assert test_chw.village == "Test Village"
        assert test_chw.district == "Test District"
        assert test_chw.phone == "+254700000000"
        assert test_chw.is_active == True
    
    def test_years_active(self, test_chw):
        """Test years active calculation"""
        # Set registration date to exactly 2 years ago
        test_chw.date_registered = datetime.now() - timedelta(days=730)
        assert test_chw.years_active() == 2.0
        
        # Set to 1.5 years ago
        test_chw.date_registered = datetime.now() - timedelta(days=547)
        assert test_chw.years_active() == 1.5

class TestPatientModel:
    """Test cases for Patient model"""
    
    def test_patient_creation(self, test_patient):
        """Test patient creation"""
        assert test_patient.id == "PAT001"
        assert test_patient.name == "Jane Smith"
        assert test_patient.age == 30
        assert test_patient.village == "Test Village"
        assert test_patient.chw_id == "CHW001"
        assert test_patient.has_chronic_condition == True
    
    def test_needs_visit(self, test_patient):
        """Test needs_visit calculation"""
        # Patient with last visit 45 days ago should need visit (threshold 30)
        assert test_patient.needs_visit() == True
        
        # Update last visit to today
        test_patient.last_visit_date = datetime.now()
        assert test_patient.needs_visit() == False
        
        # Patient with no visits should need visit
        test_patient.last_visit_date = None
        assert test_patient.needs_visit() == True

class TestVisitModel:
    """Test cases for Health Visit model"""
    
    def test_visit_creation(self, test_visit):
        """Test visit creation"""
        assert test_visit.id == "VIS001"
        assert test_visit.patient_id == "PAT001"
        assert test_visit.chw_id == "CHW001"
        assert test_visit.visit_type == "routine"
        assert test_visit.notes == "Regular checkup"
        assert test_visit.is_offline_sync == False
    
    def test_visit_summary(self, test_visit):
        """Test visit summary generation"""
        summary = test_visit.visit_summary
        assert "routine visit" in summary
        assert test_visit.notes[:50] in summary