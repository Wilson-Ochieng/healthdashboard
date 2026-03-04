import pytest
import json
from datetime import datetime, timedelta

class TestDashboardRoutes:
    """Test cases for dashboard routes"""
    
    def test_health_check(self, app):
        """Test health check endpoint"""
        response = app.get('/api/stats')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'total_chws' in data
        assert 'total_patients' in data
        assert 'total_visits' in data

class TestCHWRoutes:
    """Test cases for CHW routes"""
    
    def test_list_chws(self, app):
        """Test listing CHWs"""
        response = app.get('/chws')
        assert response.status_code == 200  # Should redirect to login
        # Since not authenticated, should redirect
    
    def test_chw_model_creation(self, test_chw):
        """Test CHW model creation (doesn't need auth)"""
        assert test_chw.name == "John Doe"
        assert test_chw.district == "Test District"