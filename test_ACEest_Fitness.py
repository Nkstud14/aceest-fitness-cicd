"""
Pytest test suite for ACEest Fitness Application
"""

import pytest
import json
from datetime import datetime, date
from ACEest_Fitness import app, db, User, Client, Workout, Progress, Metric
from werkzeug.security import generate_password_hash

@pytest.fixture
def client_fixture():
    """Create a test client and database"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        
        # Create test user
        admin = User(
            username='testadmin',
            password=generate_password_hash('testpass123'),
            role='Admin'
        )
        db.session.add(admin)
        db.session.commit()
        
        yield app.test_client()
        
        db.session.remove()
        db.drop_all()

class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_health_check(self, client_fixture):
        """Test /health endpoint"""
        response = client_fixture.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['version'] == '3.2.4'
    
    def test_readiness_check(self, client_fixture):
        """Test /ready endpoint"""
        response = client_fixture.get('/ready')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ready'

class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_login_missing_credentials(self, client_fixture):
        """Test login with missing credentials"""
        response = client_fixture.post('/login', 
            json={'username': 'testadmin'})
        assert response.status_code == 400
    
    def test_login_invalid_credentials(self, client_fixture):
        """Test login with invalid credentials"""
        response = client_fixture.post('/login',
            json={'username': 'testadmin', 'password': 'wrongpass'})
        assert response.status_code == 401
    
    def test_login_success(self, client_fixture):
        """Test successful login"""
        response = client_fixture.post('/login',
            json={'username': 'testadmin', 'password': 'testpass123'})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_login_then_access_dashboard(self, client_fixture):
        """Test accessing dashboard after login"""
        # Login first
        client_fixture.post('/login',
            json={'username': 'testadmin', 'password': 'testpass123'})
        
        # Access dashboard
        response = client_fixture.get('/dashboard')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['username'] == 'testadmin'
        assert data['role'] == 'Admin'
    
    def test_access_without_login(self, client_fixture):
        """Test accessing protected endpoint without login"""
        response = client_fixture.get('/dashboard')
        assert response.status_code == 302  # Redirect to login

class TestClientAPI:
    """Test client API endpoints"""
    
    def setup_method(self, method):
        """Login before each test"""
        self.app = app.test_client()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.app_context():
            db.create_all()
            admin = User(
                username='testadmin',
                password=generate_password_hash('testpass123'),
                role='Admin'
            )
            db.session.add(admin)
            db.session.commit()
        
        self.app.post('/login',
            json={'username': 'testadmin', 'password': 'testpass123'})
    
    def test_create_client(self, client_fixture):
        """Test creating a new client"""
        client_fixture.post('/login',
            json={'username': 'testadmin', 'password': 'testpass123'})
        
        response = client_fixture.post('/api/clients',
            json={
                'name': 'John Doe',
                'age': 30,
                'height': 180.0,
                'weight': 85.0,
                'program': 'Fat Loss',
                'calories': 2000
            })
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['name'] == 'John Doe'
    
    def test_create_client_missing_name(self, client_fixture):
        """Test creating client without name"""
        client_fixture.post('/login',
            json={'username': 'testadmin', 'password': 'testpass123'})
        
        response = client_fixture.post('/api/clients',
            json={'age': 30})
        assert response.status_code == 400
    
    def test_get_clients(self, client_fixture):
        """Test retrieving clients"""
        client_fixture.post('/login',
            json={'username': 'testadmin', 'password': 'testpass123'})
        
        # Create a client first
        client_fixture.post('/api/clients',
            json={'name': 'Jane Smith', 'age': 25})
        
        # Get clients
        response = client_fixture.get('/api/clients')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) > 0
        assert any(c['name'] == 'Jane Smith' for c in data)
    
    def test_update_client(self, client_fixture):
        """Test updating a client"""
        client_fixture.post('/login',
            json={'username': 'testadmin', 'password': 'testpass123'})
        
        # Create client
        create_response = client_fixture.post('/api/clients',
            json={'name': 'Bob Wilson', 'age': 40})
        client_id = json.loads(create_response.data)['id']
        
        # Update client
        update_response = client_fixture.put(f'/api/clients/{client_id}',
            json={'age': 41, 'weight': 90.0})
        assert update_response.status_code == 200
        
        # Verify update
        get_response = client_fixture.get(f'/api/clients/{client_id}')
        data = json.loads(get_response.data)
        assert data['age'] == 41
    
    def test_delete_client(self, client_fixture):
        """Test deleting a client"""
        client_fixture.post('/login',
            json={'username': 'testadmin', 'password': 'testpass123'})
        
        # Create client
        create_response = client_fixture.post('/api/clients',
            json={'name': 'Delete Test', 'age': 30})
        client_id = json.loads(create_response.data)['id']
        
        # Delete client
        delete_response = client_fixture.delete(f'/api/clients/{client_id}')
        assert delete_response.status_code == 200
        
        # Verify deletion
        get_response = client_fixture.get(f'/api/clients/{client_id}')
        assert get_response.status_code == 404

class TestWorkoutAPI:
    """Test workout API endpoints"""
    
    def test_create_workout(self, client_fixture):
        """Test creating a workout"""
        client_fixture.post('/login',
            json={'username': 'testadmin', 'password': 'testpass123'})
        
        # Create client first
        client_resp = client_fixture.post('/api/clients',
            json={'name': 'Workout Client', 'age': 30})
        client_id = json.loads(client_resp.data)['id']
        
        # Create workout
        response = client_fixture.post('/api/workouts',
            json={
                'client_id': client_id,
                'date': '2024-01-15',
                'workout_type': 'Strength',
                'duration_min': 60
            })
        assert response.status_code == 201
    
    def test_get_workouts(self, client_fixture):
        """Test retrieving workouts"""
        client_fixture.post('/login',
            json={'username': 'testadmin', 'password': 'testpass123'})
        
        response = client_fixture.get('/api/workouts')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)

class TestProgressAPI:
    """Test progress API endpoints"""
    
    def test_create_progress(self, client_fixture):
        """Test creating a progress record"""
        client_fixture.post('/login',
            json={'username': 'testadmin', 'password': 'testpass123'})
        
        # Create client first
        client_resp = client_fixture.post('/api/clients',
            json={'name': 'Progress Client', 'age': 30})
        client_id = json.loads(client_resp.data)['id']
        
        # Create progress
        response = client_fixture.post('/api/progress',
            json={
                'client_id': client_id,
                'week': 'Week 1',
                'adherence': 95
            })
        assert response.status_code == 201

class TestMetricsAPI:
    """Test metrics API endpoints"""
    
    def test_create_metric(self, client_fixture):
        """Test creating a metric"""
        client_fixture.post('/login',
            json={'username': 'testadmin', 'password': 'testpass123'})
        
        # Create client first
        client_resp = client_fixture.post('/api/clients',
            json={'name': 'Metric Client', 'age': 30})
        client_id = json.loads(client_resp.data)['id']
        
        # Create metric
        response = client_fixture.post('/api/metrics',
            json={
                'client_id': client_id,
                'date': '2024-01-15',
                'weight': 85.0,
                'waist': 32.0,
                'bodyfat': 15.0
            })
        assert response.status_code == 201

class TestErrorHandling:
    """Test error handling"""
    
    def test_404_error(self, client_fixture):
        """Test 404 error handling"""
        response = client_fixture.get('/nonexistent')
        assert response.status_code == 404
    
    def test_get_nonexistent_client(self, client_fixture):
        """Test getting nonexistent client"""
        client_fixture.post('/login',
            json={'username': 'testadmin', 'password': 'testpass123'})
        
        response = client_fixture.get('/api/clients/99999')
        assert response.status_code == 404
