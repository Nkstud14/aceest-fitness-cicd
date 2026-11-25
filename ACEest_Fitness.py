"""
ACEest Fitness & Performance - Flask Web Application
Version: 3.2.4
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
import os
import logging

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///aceest_fitness.db')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== DATABASE MODELS ==========

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='User')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    age = db.Column(db.Integer)
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    program = db.Column(db.String(200))
    calories = db.Column(db.Integer)
    target_weight = db.Column(db.Float)
    target_adherence = db.Column(db.Integer)
    membership_status = db.Column(db.String(20), default='Active')
    membership_end = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    workout_type = db.Column(db.String(50))
    duration_min = db.Column(db.Integer)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Progress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    week = db.Column(db.String(20))
    adherence = db.Column(db.Integer)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Metric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    weight = db.Column(db.Float)
    waist = db.Column(db.Float)
    bodyfat = db.Column(db.Float)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

# ========== AUTHENTICATION ==========

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        user = User.query.filter_by(username=session['username']).first()
        if not user or user.role != 'Admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# ========== ROUTES ==========

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Kubernetes"""
    return jsonify({'status': 'healthy', 'version': '3.2.4'}), 200

@app.route('/ready', methods=['GET'])
def readiness_check():
    """Readiness check endpoint for Kubernetes"""
    try:
        db.session.execute('SELECT 1')
        return jsonify({'status': 'ready'}), 200
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return jsonify({'status': 'not ready', 'error': str(e)}), 503

@app.route('/', methods=['GET'])
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            if request.is_json:
                return jsonify({'error': 'Username and password required'}), 400
            return jsonify({'error': 'Invalid credentials'}), 401
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['username'] = username
            session['role'] = user.role
            logger.info(f"User {username} logged in")
            if request.is_json:
                return jsonify({'success': True, 'redirect': url_for('dashboard')}), 200
            return redirect(url_for('dashboard'))
        
        logger.warning(f"Failed login attempt for user {username}")
        if request.is_json:
            return jsonify({'error': 'Invalid credentials'}), 401
        return jsonify({'error': 'Invalid credentials'}), 401
    
    return jsonify({'message': 'POST to /login with credentials'}), 200

@app.route('/logout', methods=['POST'])
def logout():
    username = session.pop('username', None)
    session.pop('role', None)
    logger.info(f"User {username} logged out")
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    clients = Client.query.all()
    return jsonify({
        'username': session['username'],
        'role': session['role'],
        'clients': [{'id': c.id, 'name': c.name, 'program': c.program} for c in clients],
        'endpoints': {
            'clients': '/api/clients',
            'workouts': '/api/workouts',
            'progress': '/api/progress',
            'metrics': '/api/metrics'
        }
    }), 200

# ========== API ENDPOINTS ==========

@app.route('/api/clients', methods=['GET', 'POST'])
@login_required
def handle_clients():
    if request.method == 'GET':
        clients = Client.query.all()
        return jsonify([{
            'id': c.id,
            'name': c.name,
            'age': c.age,
            'weight': c.weight,
            'program': c.program,
            'membership_status': c.membership_status,
            'membership_end': c.membership_end.isoformat() if c.membership_end else None
        } for c in clients]), 200
    
    elif request.method == 'POST':
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'Client name required'}), 400
        
        try:
            client = Client(
                name=data['name'],
                age=data.get('age'),
                height=data.get('height'),
                weight=data.get('weight'),
                program=data.get('program'),
                calories=data.get('calories'),
                target_weight=data.get('target_weight'),
                target_adherence=data.get('target_adherence', 90),
                membership_status=data.get('membership_status', 'Active'),
                membership_end=data.get('membership_end')
            )
            db.session.add(client)
            db.session.commit()
            logger.info(f"Client {client.name} created")
            return jsonify({'id': client.id, 'name': client.name}), 201
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating client: {e}")
            return jsonify({'error': str(e)}), 400

@app.route('/api/clients/<int:client_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def handle_client(client_id):
    client = Client.query.get_or_404(client_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': client.id,
            'name': client.name,
            'age': client.age,
            'height': client.height,
            'weight': client.weight,
            'program': client.program,
            'calories': client.calories,
            'target_weight': client.target_weight,
            'target_adherence': client.target_adherence,
            'membership_status': client.membership_status,
            'membership_end': client.membership_end.isoformat() if client.membership_end else None,
            'created_at': client.created_at.isoformat()
        }), 200
    
    elif request.method == 'PUT':
        data = request.get_json()
        for field in ['name', 'age', 'height', 'weight', 'program', 'calories', 'target_weight', 'target_adherence', 'membership_status', 'membership_end']:
            if field in data:
                setattr(client, field, data[field])
        db.session.commit()
        logger.info(f"Client {client.name} updated")
        return jsonify({'message': 'Client updated'}), 200
    
    elif request.method == 'DELETE':
        db.session.delete(client)
        db.session.commit()
        logger.info(f"Client {client.id} deleted")
        return jsonify({'message': 'Client deleted'}), 200

@app.route('/api/workouts', methods=['GET', 'POST'])
@login_required
def handle_workouts():
    if request.method == 'GET':
        client_id = request.args.get('client_id', type=int)
        query = Workout.query
        if client_id:
            query = query.filter_by(client_id=client_id)
        workouts = query.all()
        return jsonify([{
            'id': w.id,
            'client_id': w.client_id,
            'date': w.date.isoformat(),
            'workout_type': w.workout_type,
            'duration_min': w.duration_min,
            'notes': w.notes
        } for w in workouts]), 200
    
    elif request.method == 'POST':
        data = request.get_json()
        if not data or 'client_id' not in data or 'date' not in data:
            return jsonify({'error': 'client_id and date required'}), 400
        
        try:
            workout = Workout(
                client_id=data['client_id'],
                date=datetime.fromisoformat(data['date']).date(),
                workout_type=data.get('workout_type'),
                duration_min=data.get('duration_min'),
                notes=data.get('notes')
            )
            db.session.add(workout)
            db.session.commit()
            logger.info(f"Workout {workout.id} created for client {data['client_id']}")
            return jsonify({'id': workout.id}), 201
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating workout: {e}")
            return jsonify({'error': str(e)}), 400

@app.route('/api/progress', methods=['GET', 'POST'])
@login_required
def handle_progress():
    if request.method == 'GET':
        client_id = request.args.get('client_id', type=int)
        query = Progress.query
        if client_id:
            query = query.filter_by(client_id=client_id)
        progress = query.all()
        return jsonify([{
            'id': p.id,
            'client_id': p.client_id,
            'week': p.week,
            'adherence': p.adherence
        } for p in progress]), 200
    
    elif request.method == 'POST':
        data = request.get_json()
        if not data or 'client_id' not in data:
            return jsonify({'error': 'client_id required'}), 400
        
        try:
            progress = Progress(
                client_id=data['client_id'],
                week=data.get('week'),
                adherence=data.get('adherence')
            )
            db.session.add(progress)
            db.session.commit()
            logger.info(f"Progress record created for client {data['client_id']}")
            return jsonify({'id': progress.id}), 201
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating progress record: {e}")
            return jsonify({'error': str(e)}), 400

@app.route('/api/metrics', methods=['GET', 'POST'])
@login_required
def handle_metrics():
    if request.method == 'GET':
        client_id = request.args.get('client_id', type=int)
        query = Metric.query
        if client_id:
            query = query.filter_by(client_id=client_id)
        metrics = query.all()
        return jsonify([{
            'id': m.id,
            'client_id': m.client_id,
            'date': m.date.isoformat(),
            'weight': m.weight,
            'waist': m.waist,
            'bodyfat': m.bodyfat
        } for m in metrics]), 200
    
    elif request.method == 'POST':
        data = request.get_json()
        if not data or 'client_id' not in data or 'date' not in data:
            return jsonify({'error': 'client_id and date required'}), 400
        
        try:
            metric = Metric(
                client_id=data['client_id'],
                date=datetime.fromisoformat(data['date']).date(),
                weight=data.get('weight'),
                waist=data.get('waist'),
                bodyfat=data.get('bodyfat')
            )
            db.session.add(metric)
            db.session.commit()
            logger.info(f"Metric record created for client {data['client_id']}")
            return jsonify({'id': metric.id}), 201
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating metric: {e}")
            return jsonify({'error': str(e)}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}")
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

# ========== INITIALIZATION ==========

def initialize_db():
    """Initialize database with default data"""
    with app.app_context():
        db.create_all()
        
        # Create default admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                password=generate_password_hash('admin123'),
                role='Admin'
            )
            db.session.add(admin)
            db.session.commit()
            logger.info("Default admin user created")

# ========== MAIN ==========

if __name__ == '__main__':
    initialize_db()
    app.run(
        host=os.environ.get('FLASK_HOST', '0.0.0.0'),
        port=int(os.environ.get('FLASK_PORT', 5000)),
        debug=os.environ.get('FLASK_DEBUG', False)
    )
