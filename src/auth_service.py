"""
EverTrace Authentication Service
Extracted from app_clean_working.py for modular architecture
Created: September 3, 2025
"""

import os
import json
import hashlib
import random
import string
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Import email configuration
try:
    from email_config import EMAIL_CONFIG
    EMAIL_ENABLED = True
    print("Email configuration loaded")
except ImportError:
    try:
        import email_config
        EMAIL_ENABLED = True
        print("Email configuration loaded (direct import)")
    except ImportError:
        EMAIL_ENABLED = False
        print("Email configuration not found - using development mode")

# Global variables for authentication
active_sessions = {}
pending_registrations = {}

# File paths
USER_DATABASE_PATH = os.path.join('storage', 'Danhsach_user.json')

def ensure_directories():
    """Ensure required directories exist"""
    directories = ['storage', 'input', 'output']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"📁 Created directory: {directory}")

def load_user_database():
    """Load user database from JSON file"""
    ensure_directories()
    if os.path.exists(USER_DATABASE_PATH):
        try:
            with open(USER_DATABASE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Handle different database formats
                if isinstance(data, dict):
                    if 'users' in data:
                        # New format with users array - convert to dict
                        users_dict = {}
                        if isinstance(data['users'], list):
                            # Convert array to dict format
                            for user in data['users']:
                                if isinstance(user, dict) and 'username' in user:
                                    username = user['username']
                                    users_dict[username] = {
                                        'password_hash': user.get('password_hash', ''),
                                        'email': user.get('email', ''),
                                        'created_at': user.get('created_at', datetime.now().isoformat()),
                                        'verified': user.get('verified', False)
                                    }
                        return users_dict
                    else:
                        # Old format - direct dict
                        return data
                else:
                    # Fallback
                    return {}
        except Exception as e:
            print(f"❌ Error loading user database: {e}")
            return {}
    return {}

def save_user_database(users):
    """Save user database to JSON file"""
    ensure_directories()
    try:
        with open(USER_DATABASE_PATH, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
        print(f"💾 User database saved successfully")
        return True
    except Exception as e:
        print(f"❌ Error saving user database: {e}")
        return False

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def validate_email(email):
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    return len(password) >= 6

def validate_username(username):
    """Validate username"""
    if not username or len(username) < 3 or len(username) > 20:
        return False
    # Check for valid characters (alphanumeric and underscore)
    import re
    return re.match(r'^[a-zA-Z0-9_]+$', username) is not None

def generate_verification_code():
    """Generate a 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))

def send_verification_email(email, username, verification_code):
    """Send verification email"""
    try:
        import email_config
        
        # Check development mode first
        if hasattr(email_config, 'DEVELOPMENT_MODE') and email_config.DEVELOPMENT_MODE:
            print(f"📧 DEVELOPMENT MODE - Verification code for {username}: {verification_code}", flush=True)
            return True
            
        if not EMAIL_ENABLED:
            print(f"📧 EMAIL DISABLED - Verification code for {username}: {verification_code}")
            return True
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = email_config.EMAIL_ADDRESS
        msg['To'] = email
        msg['Subject'] = email_config.EMAIL_SUBJECT
        
        # Email body
        body = email_config.get_email_body(username, verification_code)
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Send email
        server = smtplib.SMTP(email_config.SMTP_SERVER, email_config.SMTP_PORT)
        server.starttls()
        server.login(email_config.EMAIL_ADDRESS, email_config.EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(email_config.EMAIL_ADDRESS, email, text)
        server.quit()
        
        print(f"📧 Verification email sent to {email}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False

def create_user_session(username):
    """Create a new user session"""
    import uuid
    session_id = str(uuid.uuid4())
    active_sessions[session_id] = {
        'user': username,
        'login_time': datetime.now().isoformat(),
        'last_activity': datetime.now().isoformat()
    }
    return session_id

def validate_session(session_id):
    """Validate user session"""
    if session_id not in active_sessions:
        return None
    
    session_data = active_sessions[session_id]
    # Update last activity
    session_data['last_activity'] = datetime.now().isoformat()
    
    return session_data['user']

def clear_session(session_id):
    """Clear user session"""
    if session_id in active_sessions:
        del active_sessions[session_id]
        return True
    return False

def register_user(username, email, password, confirm_password=None):
    """User registration logic"""
    # If confirm_password not provided, don't check it (for simplified API)
    if confirm_password is None:
        confirm_password = password
    
    # Validation
    if not username or not email or not password:
        return {'success': False, 'message': 'Vui lòng điền đầy đủ thông tin!'}
    
    if not validate_username(username):
        return {'success': False, 'message': 'Tên đăng nhập phải từ 3-20 ký tự và chỉ chứa chữ, số, dấu gạch dưới!'}
    
    if not validate_email(email):
        return {'success': False, 'message': 'Email không hợp lệ!'}
    
    if not validate_password(password):
        return {'success': False, 'message': 'Mật khẩu phải có ít nhất 6 ký tự!'}
    
    if password != confirm_password:
        return {'success': False, 'message': 'Mật khẩu nhập lại không khớp!'}
    
    # Check if user already exists
    users = load_user_database()
    if username in users:
        return {'success': False, 'message': 'Tên đăng nhập đã tồn tại!'}
    
    # Check if email already exists
    for user_data in users.values():
        if user_data.get('email') == email:
            return {'success': False, 'message': 'Email đã được sử dụng!'}
    
    # Generate verification code
    verification_code = generate_verification_code()
    
    # Store pending registration
    pending_registrations[username] = {  # Changed key to username instead of email
        'username': username,
        'password_hash': hash_password(password),
        'email': email,
        'verification_code': verification_code,
        'created_at': datetime.now().isoformat(),
        'expires_at': (datetime.now() + timedelta(minutes=15)).isoformat()
    }
    
    # Send verification email
    if send_verification_email(email, username, verification_code):
        # Check if in development mode for auto-verification
        try:
            import email_config
            if hasattr(email_config, 'DEVELOPMENT_MODE') and email_config.DEVELOPMENT_MODE:
                # In development mode, auto-verify the user
                print(f"🔧 Development mode: Auto-verifying user {username}", flush=True)
                return verify_registration_by_username(username, verification_code)
        except ImportError:
            pass
            
        return {
            'success': True, 
            'message': 'Mã xác thực đã được gửi đến email của bạn. Vui lòng kiểm tra và nhập mã để hoàn tất đăng ký.',
            'requires_verification': EMAIL_ENABLED,  # Only require verification if email is enabled
            'email': email
        }
    else:
        if not EMAIL_ENABLED:
            # Development mode - auto-verify
            return verify_registration_by_username(username, verification_code)
        else:
            return {'success': False, 'message': 'Không thể gửi email xác thực. Vui lòng thử lại!'}

def verify_registration(email, verification_code):
    """Verify user registration with code (legacy - by email)"""
    # Find by email in pending registrations
    for username, data in pending_registrations.items():
        if data.get('email') == email:
            return verify_registration_by_username(username, verification_code)
    
    return {'success': False, 'message': 'Không tìm thấy yêu cầu đăng ký cho email này!'}

def verify_registration_by_username(username, verification_code):
    """Verify user registration with code by username"""
    if username not in pending_registrations:
        return {'success': False, 'message': 'Không tìm thấy yêu cầu đăng ký!'}
    
    registration_data = pending_registrations[username]
    
    # Check if verification code expired
    expires_at = datetime.fromisoformat(registration_data['expires_at'])
    if datetime.now() > expires_at:
        del pending_registrations[username]
        return {'success': False, 'message': 'Mã xác thực đã hết hạn. Vui lòng đăng ký lại!'}
    
    # Check verification code
    if registration_data['verification_code'] != verification_code:
        return {'success': False, 'message': 'Mã xác thực không đúng!'}
    
    # Create user account
    users = load_user_database()
    
    users[username] = {
        'password_hash': registration_data['password_hash'],
        'email': registration_data['email'],
        'created_at': registration_data['created_at'],
        'verified': True,
        'verified_at': datetime.now().isoformat()
    }
    
    # Save to database
    if save_user_database(users):
        # Create user folders
        create_user_folders(username)
        
        # Remove from pending registrations
        del pending_registrations[username]
        
        return {
            'success': True, 
            'message': f'Đăng ký thành công! Chào mừng {username} đến với EverTrace!',
            'username': username
        }
    else:
        return {'success': False, 'message': 'Lỗi tạo tài khoản. Vui lòng thử lại!'}

def login_user(username, password):
    """User login logic"""
    if not username or not password:
        return {'success': False, 'message': 'Vui lòng nhập tên đăng nhập và mật khẩu!'}
    
    users = load_user_database()
    
    if username not in users:
        return {'success': False, 'message': 'Tên đăng nhập không tồn tại!'}
    
    user_data = users[username]
    
    # Check if account is verified
    if not user_data.get('verified', False):
        return {'success': False, 'message': 'Tài khoản chưa được xác thực. Vui lòng kiểm tra email!'}
    
    # Check password
    password_hash = hash_password(password)
    if user_data['password_hash'] != password_hash:
        return {'success': False, 'message': 'Mật khẩu không đúng!'}
    
    # Create session
    session_id = create_user_session(username)
    
    return {
        'success': True,
        'message': f'Đăng nhập thành công! Chào mừng {username}',
        'username': username,
        'session_id': session_id
    }

def authenticate_user(username, password):
    """Simplified authentication function for the new app structure"""
    return login_user(username, password)

def verify_email(username, verification_code):
    """Simplified email verification function for the new app structure"""
    return verify_registration_by_username(username, verification_code)

def logout_user(session_id):
    """User logout logic"""
    if clear_session(session_id):
        return {'success': True, 'message': 'Đăng xuất thành công!'}
    else:
        return {'success': False, 'message': 'Session không tồn tại!'}

def create_user_folders(username):
    """Create necessary folders for new user"""
    try:
        # Main user folder
        user_folder = os.path.join('E:', 'EverLiving_UserData', username)
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)
        
        # Input folder
        input_folder = os.path.join('input', username)
        if not os.path.exists(input_folder):
            os.makedirs(input_folder)
        
        # Subfolders
        subfolders = [
            'images', 'videos', 'videos/previews', 'music', 'memories', 
            'memories/previews', 'avatar', 'cover'
        ]
        
        for subfolder in subfolders:
            path = os.path.join(user_folder, subfolder)
            if not os.path.exists(path):
                os.makedirs(path)
        
        print(f"📁 Created user folders for: {username}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating user folders: {e}")
        return False

def get_user_info(username):
    """Get user information"""
    users = load_user_database()
    if username in users:
        user_data = users[username].copy()
        # Remove sensitive data
        user_data.pop('password_hash', None)
        return user_data
    return None

# Cleanup function for expired sessions and pending registrations
def cleanup_expired_data():
    """Clean up expired sessions and pending registrations"""
    current_time = datetime.now()
    
    # Clean expired pending registrations (older than 15 minutes)
    expired_registrations = []
    for email, data in pending_registrations.items():
        expires_at = datetime.fromisoformat(data['expires_at'])
        if current_time > expires_at:
            expired_registrations.append(email)
    
    for email in expired_registrations:
        del pending_registrations[email]
    
    if expired_registrations:
        print(f"🧹 Cleaned {len(expired_registrations)} expired pending registrations")
    
    # Clean expired sessions (older than 24 hours)
    expired_sessions = []
    for session_id, data in active_sessions.items():
        last_activity = datetime.fromisoformat(data['last_activity'])
        if (current_time - last_activity).total_seconds() > 24 * 3600:
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del active_sessions[session_id]
    
    if expired_sessions:
        print(f"🧹 Cleaned {len(expired_sessions)} expired sessions")

if __name__ == "__main__":
    print("🔐 EverTrace Authentication Service")
    print("This module provides authentication functions for the main application")
