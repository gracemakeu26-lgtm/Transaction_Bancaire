import bcrypt
import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify

SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-very-long-change-in-production')

def hash_password(password):
    """Hash a password using bcrypt"""
    if isinstance(password, str):
        password = password.encode('utf-8')
    return bcrypt.hashpw(password, bcrypt.gensalt(rounds=12)).decode('utf-8')

def check_password(password, hashed_password):
    """Verify a password against its hash"""
    if isinstance(password, str):
        password = password.encode('utf-8')
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password, hashed_password)

def generate_token(user_id, email, expires_in=86400):
    """Generate a JWT token for a user"""
    payload = {
        'user_id': user_id,
        'email': email,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(seconds=expires_in)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def verify_token(token):
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    """Decorator to require a valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'erreur': 'Format de token invalide'}), 401
        
        if not token:
            return jsonify({'erreur': 'Token requis'}), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'erreur': 'Token invalide ou expiré'}), 401
        
        request.user_id = payload['user_id']
        request.user_email = payload['email']
        return f(*args, **kwargs)
    
    return decorated
