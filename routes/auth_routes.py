from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, unset_jwt_cookies, set_access_cookies, set_refresh_cookies
from datetime import timedelta, datetime
import secrets
from models.user import User
import re

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# In-memory user store
users = {}
reset_tokens = {}

EMAIL_REGEX = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

def validate_email(email):
    return EMAIL_REGEX.match(email) is not None

def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

# ============== RENDERED PAGES ==============

@auth_bp.route('/login', methods=['GET'])
def login_page():
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET'])
def register_page():
    return render_template('auth/register.html')

@auth_bp.route('/forgot-password', methods=['GET'])
def forgot_password_page():
    return render_template('auth/forgot-password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET'])
def reset_password_page(token):
    return render_template('auth/reset-password.html', token=token)

# ============== API ENDPOINTS ==============

@auth_bp.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    
    required_fields = ['email', 'password', 'full_name']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    email = data['email'].lower().strip()
    password = data['password']
    full_name = data['full_name'].strip()
    
    if not validate_email(email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    if email in users:
        return jsonify({'error': 'Email already registered'}), 409
    
    is_valid, message = validate_password(password)
    if not is_valid:
        return jsonify({'error': message}), 400
    
    user_id = f"USR{len(users)+1:04d}"
    user = User(
        id=user_id,
        email=email,
        password_hash=User.hash_password(password),
        full_name=full_name,
        role='viewer'
    )
    users[email] = user
    
    access_token = create_access_token(identity=email)
    refresh_token = create_refresh_token(identity=email)
    
    response = jsonify({
        'message': 'Registration successful',
        'user': user.to_dict()
    })
    
    # Set cookies in the response
    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)
    
    return response, 201

@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    
    if 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Email and password required'}), 400
    
    email = data['email'].lower().strip()
    password = data['password']
    remember = data.get('remember', False)
    
    if email not in users:
        return jsonify({'error': 'Invalid email or password'}), 401
    
    user = users[email]
    
    if not user.verify_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Account is deactivated'}), 403
    
    user.last_login = datetime.now()
    
    # Create tokens
    access_token = create_access_token(identity=email)
    refresh_token = create_refresh_token(identity=email)
    
    response = jsonify({
        'message': 'Login successful',
        'user': user.to_dict()
    })
    
    # Set cookies using JWT extended's built-in methods
    set_access_cookies(response, access_token, max_age=7*24*60*60 if remember else None)
    set_refresh_cookies(response, refresh_token)
    
    print(f"Login successful for {email}")  # Debug
    return response

@auth_bp.route('/api/logout', methods=['POST'])
def api_logout():
    response = jsonify({'message': 'Logout successful'})
    unset_jwt_cookies(response)
    return response

@auth_bp.route('/api/me', methods=['GET'])
@jwt_required()
def api_get_current_user():
    current_email = get_jwt_identity()
    print(f"API /me called for: {current_email}")  # Debug
    
    user = users.get(current_email)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()})

@auth_bp.route('/api/forgot-password', methods=['POST'])
def api_forgot_password():
    data = request.get_json()
    
    if 'email' not in data:
        return jsonify({'error': 'Email required'}), 400
    
    email = data['email'].lower().strip()
    
    if email in users:
        token = secrets.token_urlsafe(32)
        expiry = datetime.now() + timedelta(hours=1)
        
        user = users[email]
        user.reset_token = token
        user.reset_token_expiry = expiry
        
        print(f"\n=== PASSWORD RESET ===")
        print(f"Email: {email}")
        print(f"Reset link: {url_for('auth.reset_password_page', token=token, _external=True)}")
        print("======================\n")
        
        reset_tokens[token] = email
    
    return jsonify({
        'message': 'If your email is registered, you will receive a password reset link'
    })

@auth_bp.route('/api/reset-password', methods=['POST'])
def api_reset_password():
    data = request.get_json()
    
    if 'token' not in data or 'new_password' not in data:
        return jsonify({'error': 'Token and new password required'}), 400
    
    token = data['token']
    new_password = data['new_password']
    
    if token not in reset_tokens:
        return jsonify({'error': 'Invalid or expired token'}), 400
    
    email = reset_tokens[token]
    
    if email not in users:
        return jsonify({'error': 'User not found'}), 404
    
    user = users[email]
    
    if user.reset_token_expiry and user.reset_token_expiry < datetime.now():
        return jsonify({'error': 'Token has expired'}), 400
    
    is_valid, message = validate_password(new_password)
    if not is_valid:
        return jsonify({'error': message}), 400
    
    user.password_hash = User.hash_password(new_password)
    user.reset_token = None
    user.reset_token_expiry = None
    
    del reset_tokens[token]
    
    return jsonify({'message': 'Password reset successful'})

@auth_bp.route('/api/debug', methods=['GET'])
def debug_auth():
    """Debug endpoint to check authentication status"""
    token = request.cookies.get('access_token')
    return jsonify({
        'cookies': dict(request.cookies),
        'has_token': token is not None,
        'token_preview': token[:20] if token else None,
        'headers': dict(request.headers),
        'users_count': len(users),
        'user_emails': list(users.keys())
    })