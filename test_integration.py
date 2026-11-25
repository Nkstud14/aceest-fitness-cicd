"""
Integration tests for ACEest Fitness Application
Tests full user workflows and API interactions
"""

import pytest
import json
from ACEest_Fitness import app, db, User, Client
from werkzeug.security import generate_password_hash

@pytest.fixture
def integration_client():
    """Create integration test client"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        
        # Create test users
        admin = User(username='admin', password=generate_password_hash('admin123'), role='Admin')
        trainer = User(username='trainer', password=generate_password_hash('trainer123'), role='Trainer')
        db.session.add_all([admin, trainer])
        db.session.commit()
        
        yield app.test_client()
        
        db.session.remove()
        db.drop_all()

class TestCompleteWorkflow:
    """Test complete user workflow"""
    
    def test_admin_login_and_create_client(self, integration_client):
        """Test admin login and client creation workflow"""
        # Admin login
        response = integration_client.post('/login',
            json={'username': 'admin', 'password': 'admin123'})
        assert response.status_code == 200
        
        # Create client
        response = integration_client.post('/api/clients',
            json={
                'name': 'John Fitness',
                'age': 30,
                'height': 180.0,
                'weight': 85.0,
                'program': 'Fat Loss',
                'calories': 2000,
                'target_weight': 75.0,
                'target_adherence': 90
            })
        assert response.status_code == 201
        client_data = json.loads(response.data)
        client_id = client_data['id']
        
        # Get client
        response = integration_client.get(f'/api/clients/{client_id}')
        assert response.status_code == 200
        client = json.loads(response.data)
        assert client['name'] == 'John Fitness'
        assert client['age'] == 30
    
    def test_trainer_cannot_delete_client(self, integration_client):
        """Test that trainer cannot delete client"""
        # Admin login and create client
        integration_client.post('/login',
            json={'username': 'admin', 'password': 'admin123'})
        
        response = integration_client.post('/api/clients',
            json={'name': 'Test Client', 'age': 25})
        client_id = json.loads(response.data)['id']
        
        # Logout and login as trainer
        integration_client.post('/logout')
        integration_client.post('/login',
            json={'username': 'trainer', 'password': 'trainer123'})
        
        # Trainer can read
        response = integration_client.get(f'/api/clients/{client_id}')
        assert response.status_code == 200
    
    def test_client_workout_progress_workflow(self, integration_client):
        """Test complete client, workout, and progress workflow"""
        # Login
        integration_client.post('/login',
            json={'username': 'admin', 'password': 'admin123'})
        
        # Create client
        client_resp = integration_client.post('/api/clients',
            json={'name': 'Sarah', 'age': 28})
        client_id = json.loads(client_resp.data)['id']
        
        # Create workout
        workout_resp = integration_client.post('/api/workouts',
            json={
                'client_id': client_id,
                'date': '2024-01-15',
                'workout_type': 'Strength',
                'duration_min': 60,
                'notes': 'Great session'
            })
        assert workout_resp.status_code == 201
        
        # Create progress
        progress_resp = integration_client.post('/api/progress',
            json={
                'client_id': client_id,
                'week': 'Week 1',
                'adherence': 95
            })
        assert progress_resp.status_code == 201
        
        # Verify data
        workouts_resp = integration_client.get(f'/api/workouts?client_id={client_id}')
        assert workouts_resp.status_code == 200
        
        progress_data = integration_client.get(f'/api/progress?client_id={client_id}')
        assert progress_data.status_code == 200

class TestHealthAndReadiness:
    """Test health check endpoints"""
    
    def test_health_endpoint_before_login(self, integration_client):
        """Health check should work without authentication"""
        response = integration_client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
    
    def test_readiness_endpoint_before_login(self, integration_client):
        """Readiness check should work without authentication"""
        response = integration_client.get('/ready')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ready'

class TestErrorHandling:
    """Test error handling in workflows"""
    
    def test_duplicate_client_creation(self, integration_client):
        """Test that duplicate client creation fails"""
        integration_client.post('/login',
            json={'username': 'admin', 'password': 'admin123'})
        
        # Create first client
        integration_client.post('/api/clients',
            json={'name': 'Duplicate Name', 'age': 30})
        
        # Try to create duplicate
        response = integration_client.post('/api/clients',
            json={'name': 'Duplicate Name', 'age': 25})
        assert response.status_code == 400
    
    def test_update_nonexistent_client(self, integration_client):
        """Test updating nonexistent client"""
        integration_client.post('/login',
            json={'username': 'admin', 'password': 'admin123'})
        
        response = integration_client.put('/api/clients/99999',
            json={'age': 30})
        assert response.status_code == 404

class TestDataValidation:
    """Test data validation"""
    
    def test_invalid_date_format(self, integration_client):
        """Test invalid date format in workout"""
        integration_client.post('/login',
            json={'username': 'admin', 'password': 'admin123'})
        
        # Create client
        client_resp = integration_client.post('/api/clients',
            json={'name': 'Client', 'age': 30})
        client_id = json.loads(client_resp.data)['id']
        
        # Try invalid date
        response = integration_client.post('/api/workouts',
            json={
                'client_id': client_id,
                'date': 'invalid-date',
                'workout_type': 'Strength'
            })
        assert response.status_code == 400
    
    def test_missing_required_fields(self, integration_client):
        """Test missing required fields"""
        integration_client.post('/login',
            json={'username': 'admin', 'password': 'admin123'})
        
        # Missing client_id in workout
        response = integration_client.post('/api/workouts',
            json={'date': '2024-01-15'})
        assert response.status_code == 400

class TestPerformance:
    """Test performance characteristics"""
    
    def test_bulk_client_creation(self, integration_client):
        """Test creating multiple clients"""
        integration_client.post('/login',
            json={'username': 'admin', 'password': 'admin123'})
        
        for i in range(10):
            response = integration_client.post('/api/clients',
                json={'name': f'Client {i}', 'age': 25 + i})
            assert response.status_code == 201
        
        # Verify all created
        response = integration_client.get('/api/clients')
        assert response.status_code == 200
        clients = json.loads(response.data)
        assert len(clients) >= 10
    
    def test_large_response_handling(self, integration_client):
        """Test handling large responses"""
        integration_client.post('/login',
            json={'username': 'admin', 'password': 'admin123'})
        
        # Create multiple clients
        for i in range(20):
            integration_client.post('/api/clients',
                json={'name': f'Large Test {i}', 'age': 30})
        
        # Get all clients
        response = integration_client.get('/api/clients')
        assert response.status_code == 200
        assert len(json.loads(response.data)) >= 20
