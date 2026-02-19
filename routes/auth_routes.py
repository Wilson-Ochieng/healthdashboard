from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, unset_jwt_cookies
from datetime import timedelta, datetime
import secrets
from models.user import User
import re

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# In-memory user store (replace with database in production)
users = {}  # email -> User
reset_tokens = {}  # token -> email

# Email validation regex
EMAIL_REGEX = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

def validate_email(email):
    """Validate email format"""
    return EMAIL_REGEX.match(email) is not None

def validate_password(password):
    """Validate password strength"""
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
    """Render login page"""
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET'])
def register_page():
    """Render registration page"""
    return render_template('auth/register.html')

@auth_bp.route('/forgot-password', methods=['GET'])
def forgot_password_page():
    """Render forgot password page"""
    return render_template('auth/forgot-password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET'])
def reset_password_page(token):
    """Render reset password page with token"""
    return render_template('auth/reset-password.html', token=token)

# ============== API ENDPOINTS ==============

@auth_bp.route('/api/register', methods=['POST'])
def api_register():
    """API endpoint for user registration"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['email', 'password', 'full_name']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    email = data['email'].lower().strip()
    password = data['password']
    full_name = data['full_name'].strip()
    
    # Validate email
    if not validate_email(email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Check if user exists
    if email in users:
        return jsonify({'error': 'Email already registered'}), 409
    
    # Validate password
    is_valid, message = validate_password(password)
    if not is_valid:
        return jsonify({'error': message}), 400
    
    # Create user
    user_id = f"USR{len(users)+1:04d}"
    user = User(
        id=user_id,
        email=email,
        password_hash=User.hash_password(password),
        full_name=full_name,
        role='viewer'  # Default role
    )
    users[email] = user
    
    # Create tokens
    access_token = create_access_token(
        identity=email,
        additional_claims={'role': user.role, 'name': user.full_name},
        expires_delta=timedelta(hours=1)
    )
    refresh_token = create_refresh_token(identity=email)
    
    return jsonify({
        'message': 'Registration successful',
        'user': user.to_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token
    }), 201

@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    """API endpoint for user login"""
    data = request.get_json()
    
    # Validate required fields
    if 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Email and password required'}), 400
    
    email = data['email'].lower().strip()
    password = data['password']
    remember = data.get('remember', False)
    
    # Check if user exists
    if email not in users:
        return jsonify({'error': 'Invalid email or password'}), 401
    
    user = users[email]
    
    # Verify password
    if not user.verify_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    # Check if user is active
    if not user.is_active:
        return jsonify({'error': 'Account is deactivated'}), 403
    
    # Update last login
    user.last_login = datetime.now()
    
    # Set token expiry based on remember me
    expiry = timedelta(days=7) if remember else timedelta(hours=1)
    
    # Create tokens
    access_token = create_access_token(
        identity=email,
        additional_claims={
            'role': user.role,
            'name': user.full_name,
            'id': user.id
        },
        expires_delta=expiry
    )
    refresh_token = create_refresh_token(identity=email)
    
    response = jsonify({
        'message': 'Login successful',
        'user': user.to_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token
    })
    
    # Set cookies for web interface
    response.set_cookie('access_token', access_token, httponly=True, secure=True, samesite='Lax', max_age=expiry.total_seconds())
    response.set_cookie('refresh_token', refresh_token, httponly=True, secure=True, samesite='Lax')
    
    return response

@auth_bp.route('/api/logout', methods=['POST'])
def api_logout():
    """API endpoint for logout"""
    response = jsonify({'message': 'Logout successful'})
    unset_jwt_cookies(response)
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    return response

@auth_bp.route('/api/refresh', methods=['POST'])
@jwt_required(refresh=True)
def api_refresh():
    """Refresh access token"""
    current_user = get_jwt_identity()
    user = users.get(current_user)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    new_access_token = create_access_token(
        identity=current_user,
        additional_claims={'role': user.role, 'name': user.full_name}
    )
    
    return jsonify({'access_token': new_access_token})

@auth_bp.route('/api/forgot-password', methods=['POST'])
def api_forgot_password():
    """Request password reset"""
    data = request.get_json()
    
    if 'email' not in data:
        return jsonify({'error': 'Email required'}), 400
    
    email = data['email'].lower().strip()
    
    # Always return success to prevent email enumeration
    if email in users:
        # Generate reset token
        token = secrets.token_urlsafe(32)
        expiry = datetime.now() + timedelta(hours=1)
        
        user = users[email]
        user.reset_token = token
        user.reset_token_expiry = expiry
        
        # In production, send email here
        # For demo, we'll log the token
        print(f"\n=== PASSWORD RESET ===")
        print(f"Email: {email}")
        print(f"Reset link: {url_for('auth.reset_password_page', token=token, _external=True)}")
        print(f"Token expires: {expiry}")
        print("======================\n")
        
        # Store token for demo (in production, this would be in database)
        reset_tokens[token] = email
    
    return jsonify({
        'message': 'If your email is registered, you will receive a password reset link'
    })

@auth_bp.route('/api/reset-password', methods=['POST'])
def api_reset_password():
    """Reset password with token"""
    data = request.get_json()
    
    if 'token' not in data or 'new_password' not in data:
        return jsonify({'error': 'Token and new password required'}), 400
    
    token = data['token']
    new_password = data['new_password']
    
    # Validate token
    if token not in reset_tokens:
        return jsonify({'error': 'Invalid or expired token'}), 400
    
    email = reset_tokens[token]
    
    if email not in users:
        return jsonify({'error': 'User not found'}), 404
    
    user = users[email]
    
    # Check token expiry
    if user.reset_token_expiry and user.reset_token_expiry < datetime.now():
        return jsonify({'error': 'Token has expired'}), 400
    
    # Validate new password
    is_valid, message = validate_password(new_password)
    if not is_valid:
        return jsonify({'error': message}), 400
    
    # Update password
    user.password_hash = User.hash_password(new_password)
    user.reset_token = None
    user.reset_token_expiry = None
    
    # Clean up token
    del reset_tokens[token]
    
    return jsonify({'message': 'Password reset successful'})

@auth_bp.route('/api/me', methods=['GET'])
@jwt_required()
def api_get_current_user():
    """Get current user info"""
    current_email = get_jwt_identity()
    user = users.get(current_email)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()})

@auth_bp.route('/api/update-profile', methods=['PUT'])
@jwt_required()
def api_update_profile():
    """Update user profile"""
    current_email = get_jwt_identity()
    user = users.get(current_email)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    if 'full_name' in data:
        user.full_name = data['full_name'].strip()
    
    if 'email' in data:
        new_email = data['email'].lower().strip()
        if new_email != current_email and new_email in users:
            return jsonify({'error': 'Email already in use'}), 409
        if not validate_email(new_email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Update email
        del users[current_email]
        user.email = new_email
        users[new_email] = user
    
    return jsonify({
        'message': 'Profile updated',
        'user': user.to_dict()
    })

# ============== PROTECTED ROUTE EXAMPLE ==============

@auth_bp.route('/dashboard')
@jwt_required()
def protected_dashboard():
    """Example protected route"""
    current_email = get_jwt_identity()
    user = users.get(current_email)
    
    return render_template('dashboard.html', user=user)