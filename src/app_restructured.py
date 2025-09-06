"""
EverLiving Main Application
Restructured according to clean architecture
Port: 8080

Flow:
1. Khởi động: app.py (port 8080)
2. Landing page: login/register form
3. Authentication: auth_service.py
4. Success: Main application interface
"""

import os
import shutil
import json
import sys
import traceback
import secrets
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for, abort
from werkzeug.utils import secure_filename

# Add parent directory to path for config imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))

# Import services
import auth_service
import video_processor

# Import email configuration from config folder
try:
    import email_config
    EMAIL_AVAILABLE = True
    print("✅ Email configuration loaded")
except ImportError:
    EMAIL_AVAILABLE = False
    print("⚠️ Email configuration not available")

# Define project root and storage paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
STORAGE_DIR = os.path.join(PROJECT_ROOT, 'storage')
os.makedirs(STORAGE_DIR, exist_ok=True)

# Change working directory to project root
os.chdir(PROJECT_ROOT)

print("🚀 EVERLIVING MAIN APPLICATION STARTING...", flush=True)
print(f"📁 Project root: {PROJECT_ROOT}", flush=True)
print(f"📂 Storage directory: {STORAGE_DIR}", flush=True)

# ================================
# APP CONFIGURATION
# ================================

# Configure template and static directories
template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
static_dir = os.path.join(os.path.dirname(__file__), '..', 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.secret_key = b'everliving_super_secret_key_2025_very_long_and_secure_key_for_session_management'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# Disable template caching for development
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Session configuration
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = False
app.config['SESSION_COOKIE_SAMESITE'] = None
app.config['SESSION_COOKIE_NAME'] = 'everliving_session'
app.config['SESSION_COOKIE_DOMAIN'] = None
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

print("🔧 Application configuration completed", flush=True)

# ================================
# HELPER FUNCTIONS
# ================================

def get_current_user():
    """Get current authenticated user from session"""
    try:
        if 'username' in session:
            username = session['username']
            # Verify user still exists in auth_service
            users = auth_service.load_user_database()
            if username in users:
                return username
            else:
                # User no longer exists, clear session
                session.clear()
                return None
        return None
    except Exception as e:
        print(f"❌ Error getting current user: {e}")
        return None

def require_auth(f):
    """Decorator to require authentication for routes"""
    def decorated_function(*args, **kwargs):
        current_user = get_current_user()
        if not current_user:
            return redirect(url_for('landing_page'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def ensure_user_directories(username):
    """Ensure all user directories exist"""
    try:
        # Storage directories
        user_folder = os.path.join(STORAGE_DIR, username)
        subdirs = [
            'images', 
            'videos', 
            'videos/previews', 
            'music', 
            'memories', 
            'memories/previews', 
            'avatar', 
            'cover',
            'moments'
        ]
        
        # Create all required directories
        for subdir in subdirs:
            path = os.path.join(user_folder, subdir)
            os.makedirs(path, exist_ok=True)
            print(f"📁 Created directory: {os.path.abspath(path)}")
        
        # Create user data files if they don't exist
        user_data_files = [
            os.path.join(user_folder, 'moments.json'),
            os.path.join(STORAGE_DIR, 'Danhsach_user.json')
        ]
        
        for data_file in user_data_files:
            if not os.path.exists(data_file):
                with open(data_file, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
                print(f"📄 Created data file: {data_file}")
        
        return True
    except Exception as e:
        print(f"❌ Error creating user directories: {e}")
        import traceback
        traceback.print_exc()
        return False

# ================================
# ROUTES - LANDING & AUTHENTICATION
# ================================

@app.route('/')
def landing_page():
    """
    Landing page - Entry point of application
    Show login/register forms if not authenticated
    Redirect to main app if already authenticated
    """
    try:
        current_user = get_current_user()
        
        if current_user:
            print(f"✅ User {current_user} already authenticated, redirecting to main app")
            return redirect(url_for('main_app'))
        
        # Clear any corrupted session data
        session.clear()
        
        # Show landing page with login/register options
        return render_template('login_register.html')
        
    except Exception as e:
        print(f"❌ Error in landing page: {e}")
        session.clear()  # Clear session on error
        return render_template('login_register.html')

@app.route('/clear_session')
def clear_session_route():
    """Clear session for debugging"""
    session.clear()
    return redirect(url_for('landing_page'))

@app.route('/login')
def login_page():
    """Login page"""
    try:
        current_user = get_current_user()
        if current_user:
            return redirect(url_for('main_app'))
        
        return render_template('login_register.html')
        
    except Exception as e:
        print(f"❌ Error in login page: {e}")
        return f"Lỗi tải trang đăng nhập: {str(e)}", 500

@app.route('/register')
def register_page():
    """Register page"""
    try:
        current_user = get_current_user()
        if current_user:
            return redirect(url_for('main_app'))
        
        return render_template('login_register.html')
        
    except Exception as e:
        print(f"❌ Error in register page: {e}")
        return f"Lỗi tải trang đăng ký: {str(e)}", 500

# ================================
# API ROUTES - AUTHENTICATION
# ================================

@app.route('/api/login', methods=['POST'])
def api_login():
    """API endpoint for user login"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'message': 'Vui lòng nhập đầy đủ thông tin'
            }), 400
        
        # Authenticate with auth_service
        result = auth_service.authenticate_user(username, password)
        
        if result['success']:
            # Set session
            session['username'] = username
            session.permanent = True
            
            # Ensure user directories exist
            ensure_user_directories(username)
            
            print(f"✅ User {username} logged in successfully")
            
            return jsonify({
                'success': True,
                'message': 'Đăng nhập thành công',
                'redirect': url_for('main_app')
            })
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 401
            
    except Exception as e:
        print(f"❌ Error in login API: {e}")
        return jsonify({
            'success': False,
            'message': 'Lỗi hệ thống khi đăng nhập'
        }), 500

@app.route('/api/register', methods=['POST'])
def api_register():
    """API endpoint for user registration"""
    try:
        data = request.get_json()
        print(f"📝 Registration request data: {data}", flush=True)  # Debug logging
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        print(f"📝 Extracted data: username='{username}', email='{email}', password='{len(password)} chars'", flush=True)  # Debug logging
        
        if not username or not email or not password:
            print(f"❌ Missing data: username={bool(username)}, email={bool(email)}, password={bool(password)}")
            return jsonify({
                'success': False,
                'message': 'Vui lòng nhập đầy đủ thông tin'
            }), 400
        
        # Register with auth_service
        result = auth_service.register_user(username, email, password)
        print(f"📝 Auth service result: {result}", flush=True)  # Debug logging
        
        if result['success']:
            print(f"✅ User {username} registered successfully")
            return jsonify({
                'success': True,
                'message': result['message'],
                'requires_verification': result.get('requires_verification', False)
            })
        else:
            print(f"❌ Registration failed: {result['message']}")
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400
            
    except Exception as e:
        print(f"❌ Error in register API: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'Lỗi hệ thống khi đăng ký'
        }), 500

@app.route('/api/verify_email', methods=['POST'])
def api_verify_email():
    """API endpoint for email verification"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        verification_code = data.get('verification_code', '').strip()
        
        if not username or not verification_code:
            return jsonify({
                'success': False,
                'message': 'Vui lòng nhập đầy đủ thông tin'
            }), 400
        
        # Verify with auth_service
        result = auth_service.verify_email(username, verification_code)
        
        if result['success']:
            # Auto login after verification
            session['username'] = username
            session.permanent = True
            
            # Ensure user directories exist
            ensure_user_directories(username)
            
            print(f"✅ User {username} verified and logged in")
            
            return jsonify({
                'success': True,
                'message': result['message'],
                'redirect': url_for('main_app')
            })
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400
            
    except Exception as e:
        print(f"❌ Error in email verification API: {e}")
        return jsonify({
            'success': False,
            'message': 'Lỗi hệ thống khi xác thực email'
        }), 500

@app.route('/api/resend_verification', methods=['POST'])
def api_resend_verification():
    """API endpoint to resend verification code"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        
        if not username:
            return jsonify({
                'success': False,
                'message': 'Username không được cung cấp'
            }), 400
        
        # Check if user has pending registration
        if username not in auth_service.pending_registrations:
            return jsonify({
                'success': False,
                'message': 'Không tìm thấy yêu cầu đăng ký'
            }), 400
        
        # Get registration data
        registration_data = auth_service.pending_registrations[username]
        
        # Generate new verification code
        new_code = auth_service.generate_verification_code()
        registration_data['verification_code'] = new_code
        registration_data['expires_at'] = (datetime.now() + auth_service.timedelta(minutes=15)).isoformat()
        
        # Resend email
        if auth_service.send_verification_email(registration_data['email'], username, new_code):
            return jsonify({
                'success': True,
                'message': 'Mã xác thực mới đã được gửi đến email của bạn'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Không thể gửi email. Vui lòng thử lại'
            }), 500
            
    except Exception as e:
        print(f"❌ Error in resend verification API: {e}")
        return jsonify({
            'success': False,
            'message': 'Lỗi hệ thống'
        }), 500

@app.route('/api/logout', methods=['POST'])
def api_logout():
    """API endpoint for user logout"""
    try:
        current_user = get_current_user()
        if current_user:
            print(f"✅ User {current_user} logged out")
        
        session.clear()
        
        return jsonify({
            'success': True,
            'message': 'Đăng xuất thành công',
            'redirect': url_for('landing_page')
        })
        
    except Exception as e:
        print(f"❌ Error in logout API: {e}")
        return jsonify({
            'success': False,
            'message': 'Lỗi khi đăng xuất'
        }), 500

# ================================
# MAIN APPLICATION ROUTES
# ================================

@app.route('/test_avatar_cover')
@require_auth
def test_avatar_cover():
    """Test page for avatar and cover functionality"""
    return render_template('test_avatar_cover.html')

@app.route('/test_main')
@require_auth  
def test_main():
    """Test main page with cleared video section"""
    try:
        current_user = get_current_user()
        print(f"✅ TEST: User {current_user} accessing test main page")
        return render_template('test_main.html', username=current_user)
    except Exception as e:
        print(f"❌ Error in test main: {e}")
        return f"Error: {str(e)}", 500

@app.route('/main')
@require_auth
def main_app():
    """
    Main application interface - SPA version
    This is where users manage their memories
    """
    try:
        current_user = get_current_user()
        print(f"✅ User {current_user} accessing main SPA application")
        
        # Debug: Print template path
        template_path = os.path.join(app.template_folder, 'main_spa.html')
        print(f"🔍 Loading template from: {template_path}")
        print(f"🔍 Template exists: {os.path.exists(template_path)}")
        
        # Ensure user directories exist
        ensure_user_directories(current_user)
        
        return render_template('main_spa.html', username=current_user)
        
    except Exception as e:
        print(f"❌ Error in main app: {e}")
        return f"Lỗi tải ứng dụng chính: {str(e)}", 500

@app.route('/api/user_info', methods=['GET'])
@require_auth
def api_user_info():
    """API endpoint to get current user information"""
    try:
        current_user = get_current_user()
        return jsonify({
            'success': True,
            'username': current_user
        })
        
    except Exception as e:
        print(f"❌ Error getting user info: {e}")
        return jsonify({
            'success': False,
            'message': 'Lỗi lấy thông tin người dùng'
        }), 500

# ================================
# AVATAR & COVER UPLOAD ROUTES
# ================================

@app.route('/upload/avatar', methods=['POST'])
@require_auth
def upload_avatar():
    """Upload avatar for current user"""
    try:
        current_user = get_current_user()
        
        # Check if file is present
        if 'avatar' not in request.files:
            return jsonify({
                'success': False,
                'message': 'Không có file được chọn'
            }), 400
        
        file = request.files['avatar']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'Không có file được chọn'
            }), 400
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        if not file.filename.lower().endswith(tuple(allowed_extensions)):
            return jsonify({
                'success': False,
                'message': 'Chỉ hỗ trợ file ảnh: PNG, JPG, JPEG, GIF, WEBP'
            }), 400
        
        # Validate file size (5MB max)
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > 5 * 1024 * 1024:  # 5MB
            return jsonify({
                'success': False,
                'message': 'File quá lớn. Tối đa 5MB.'
            }), 400
        
        # Ensure user directories exist
        ensure_user_directories(current_user)
        
        # Save to storage user directory
        local_avatar_dir = os.path.join(STORAGE_DIR, current_user, 'avatar')
        os.makedirs(local_avatar_dir, exist_ok=True)
        
        # Use secure filename and add timestamp to avoid caching issues
        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1].lower()
        avatar_filename = f'avatar_{datetime.now().strftime("%Y%m%d_%H%M%S")}.{file_extension}'
        
        local_path = os.path.join(local_avatar_dir, avatar_filename)
        file.save(local_path)

        print(f"✅ Avatar saved: {avatar_filename}")
        
        # Clean up old avatar files AFTER saving new one
        try:
            for old_file in os.listdir(local_avatar_dir):
                if old_file != avatar_filename and old_file.startswith('avatar_') and old_file.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    old_path = os.path.join(local_avatar_dir, old_file)
                    os.remove(old_path)
                    print(f"🗑️ Removed old avatar: {old_file}")
        except Exception as e:
            print(f"⚠️ Could not clean old avatars: {e}")
        
        avatar_url = f'/api/serve_file/{current_user}/avatar/{avatar_filename}'
        
        return jsonify({
            'success': True,
            'message': 'Upload avatar thành công!',
            'avatar_url': avatar_url
        })
        
    except Exception as e:
        print(f"❌ Error uploading avatar: {e}")
        return jsonify({
            'success': False,
            'message': f'Lỗi upload avatar: {str(e)}'
        }), 500

@app.route('/upload/cover', methods=['POST'])
@require_auth
def upload_cover():
    """Upload cover photo for current user"""
    try:
        current_user = get_current_user()
        
        # Check if file is present
        if 'cover' not in request.files:
            return jsonify({
                'success': False,
                'message': 'Không có file được chọn'
            }), 400
        
        file = request.files['cover']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'Không có file được chọn'
            }), 400
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        if not file.filename.lower().endswith(tuple(allowed_extensions)):
            return jsonify({
                'success': False,
                'message': 'Chỉ hỗ trợ file ảnh: PNG, JPG, JPEG, GIF, WEBP'
            }), 400
        
        # Validate file size (10MB max for cover)
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > 10 * 1024 * 1024:  # 10MB
            return jsonify({
                'success': False,
                'message': 'File quá lớn. Tối đa 10MB.'
            }), 400
        
        # Ensure user directories exist
        ensure_user_directories(current_user)
        
        # Save to storage user directory
        local_cover_dir = os.path.join(STORAGE_DIR, current_user, 'cover')
        os.makedirs(local_cover_dir, exist_ok=True)
        
        # Use secure filename and add timestamp
        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1].lower()
        cover_filename = f'cover_{datetime.now().strftime("%Y%m%d_%H%M%S")}.{file_extension}'
        
        local_path = os.path.join(local_cover_dir, cover_filename)
        file.save(local_path)
        
        print(f"✅ Cover photo saved: {cover_filename}")
        
        # Clean up old cover files AFTER saving new one
        try:
            for old_file in os.listdir(local_cover_dir):
                if old_file != cover_filename and old_file.startswith('cover_') and old_file.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    old_path = os.path.join(local_cover_dir, old_file)
                    os.remove(old_path)
                    print(f"🗑️ Removed old cover: {old_file}")
        except Exception as e:
            print(f"⚠️ Could not clean old covers: {e}")
        
        cover_url = f'/api/serve_file/{current_user}/cover/{cover_filename}'
        
        return jsonify({
            'success': True,
            'message': 'Upload ảnh bìa thành công!',
            'cover_url': cover_url
        })
        
    except Exception as e:
        print(f"❌ Error uploading cover: {e}")
        return jsonify({
            'success': False,
            'message': f'Lỗi upload ảnh bìa: {str(e)}'
        }), 500

@app.route('/api/user/<username>/avatar', methods=['GET'])
def get_user_avatar(username):
    """Get user avatar URL"""
    try:
        # Check storage first
        external_avatar_dir = os.path.join(STORAGE_DIR, username, 'avatar')
        
        if os.path.exists(external_avatar_dir):
            # Find the latest avatar file
            avatar_files = [f for f in os.listdir(external_avatar_dir) if f.startswith('avatar_')]
            if avatar_files:
                # Sort by filename to get the latest (timestamp in filename)
                latest_avatar = sorted(avatar_files)[-1]
                avatar_url = f'/api/serve_file/{username}/avatar/{latest_avatar}'
                
                return jsonify({
                    'success': True,
                    'avatar_url': avatar_url
                })
        
        return jsonify({
            'success': False,
            'message': 'Avatar not found'
        }), 404
        
    except Exception as e:
        print(f"❌ Error getting avatar: {e}")
        return jsonify({
            'success': False,
            'message': 'Lỗi lấy avatar'
        }), 500

@app.route('/api/user/<username>/cover', methods=['GET'])
def get_user_cover(username):
    """Get user cover photo URL"""
    try:
        # Check storage first
        external_cover_dir = os.path.join(STORAGE_DIR, username, 'cover')
        
        if os.path.exists(external_cover_dir):
            # Find the latest cover file
            cover_files = [f for f in os.listdir(external_cover_dir) if f.startswith('cover_')]
            if cover_files:
                # Sort by filename to get the latest (timestamp in filename)
                latest_cover = sorted(cover_files)[-1]
                cover_url = f'/api/serve_file/{username}/cover/{latest_cover}'
                
                return jsonify({
                    'success': True,
                    'cover_url': cover_url
                })
        
        return jsonify({
            'success': False,
            'message': 'Cover photo not found'
        }), 404
        
    except Exception as e:
        print(f"❌ Error getting cover: {e}")
        return jsonify({
            'success': False,
            'message': 'Lỗi lấy ảnh bìa'
        }), 500

# ================================
# VIDEO PROCESSING ROUTES
# ================================

@app.route('/api/create_video', methods=['POST'])
@require_auth
def api_create_video():
    """API endpoint for video creation"""
    try:
        current_user = get_current_user()
        
        # Get form data
        form_data = {
            'username': current_user,
            'title': request.form.get('title', ''),
            'description': request.form.get('description', ''),
            'music_file': request.files.get('music_file'),
            'images': request.files.getlist('images')
        }
        
        # Validate input
        if not form_data['title'] or not form_data['images']:
            return jsonify({
                'success': False,
                'message': 'Vui lòng nhập tiêu đề và chọn ít nhất một hình ảnh'
            }), 400
        
        # Process video using video_processor
        result = video_processor.create_video(form_data)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error in video creation: {e}")
        return jsonify({
            'success': False,
            'message': f'Lỗi tạo video: {str(e)}'
        }), 500

# ================================
# STATIC FILE SERVING
# ================================

@app.route('/static/assets/<path:filename>')
def serve_assets(filename):
    """Serve static assets like flags, icons, etc."""
    try:
        assets_path = os.path.join(PROJECT_ROOT, 'assets')
        file_path = os.path.join(assets_path, filename)
        if os.path.exists(file_path):
            return send_file(file_path)
        else:
            return "File không tồn tại", 404
    except Exception as e:
        print(f"❌ Error serving asset: {e}")
        return "Lỗi server", 500

@app.route('/api/serve_file/<username>/<filename>')
@require_auth
def serve_user_avatar_file(username, filename):
    """Serve user avatar files from storage directory"""
    try:
        # Security check - prevent directory traversal
        if '..' in filename or filename.startswith('/'):
            abort(403)
        
        # Serve from storage user folder
        file_path = os.path.join(STORAGE_DIR, username, 'avatar', filename)
        
        if os.path.exists(file_path):
            return send_file(file_path)
        else:
            print(f"❌ Avatar file not found: {file_path}")
            abort(404)
    except Exception as e:
        print(f"❌ Error serving avatar file: {e}")
        abort(500)

@app.route('/api/serve_file/<username>/<file_type>/<filename>')
@require_auth
def serve_user_media_file(username, file_type, filename):
    """Serve user uploaded media files from storage directory"""
    try:
        # Security check - prevent directory traversal
        if '..' in filename or filename.startswith('/') or '..' in file_type or file_type.startswith('/'):
            abort(403)
        
        # Validate file type
        if file_type not in ['images', 'videos']:
            abort(400, description="Invalid file type")
        
        # Serve from storage
        file_path = os.path.join(STORAGE_DIR, username, file_type, filename)
        
        if os.path.exists(file_path):
            return send_file(file_path)
        else:
            print(f"❌ Media file not found: {file_path}")
            abort(404)
    except Exception as e:
        print(f"❌ Error serving media file: {e}")
        abort(500)

@app.route('/api/serve_file/<username>/<file_type>/<subfolder>/<filename>')
@require_auth
def serve_user_preview_file(username, file_type, subfolder, filename):
    """Serve user preview files from storage directory"""
    try:
        # Security check - prevent directory traversal
        if any(c in filename + file_type + subfolder for c in ['..', '/']):
            abort(403)
        
        # Validate file type and subfolder
        if file_type not in ['videos', 'memories'] or subfolder != 'previews':
            abort(400, description="Invalid file type or subfolder")
        
        # Build the full file path
        previews_dir = os.path.join(STORAGE_DIR, username, file_type, 'previews')
        file_path = os.path.join(previews_dir, filename)
        
        print(f"🔍 Looking for preview file at: {file_path}")
        print(f"🔍 STORAGE_DIR: {STORAGE_DIR}")
        print(f"🔍 Previews dir exists: {os.path.exists(previews_dir)}")
        if os.path.exists(previews_dir):
            print(f"🔍 Files in previews dir: {os.listdir(previews_dir)}")
        
        # Check if path exists and is a file (not a directory)
        if not os.path.exists(file_path):
            print(f"❌ Preview file not found: {file_path}")
            print(f"❌ Current working directory: {os.getcwd()}")
            print(f"❌ Absolute path exists: {os.path.exists(os.path.abspath(file_path))}")
            abort(404)
            
        if not os.path.isfile(file_path):
            print(f"❌ Preview path is not a file: {file_path}")
            print(f"❌ Is directory: {os.path.isdir(file_path)}")
            abort(404)
            
        # Check if the preview file is empty (0 bytes)
        file_size = os.path.getsize(file_path)
        print(f"📏 Preview file size: {file_size} bytes")
        if file_size == 0:
            print(f"⚠️ Preview file is empty: {file_path}")
            abort(404)
            
        return send_file(file_path)
        
    except Exception as e:
        print(f"❌ Error serving preview file: {e}")
        abort(500)

# ================================
# ERROR HANDLERS
# ================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('landing.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    print(f"❌ Internal server error: {error}")
    return "Lỗi máy chủ nội bộ", 500

# ================================
# APPLICATION STARTUP
# ================================

# ================================
# SPA API ENDPOINTS
# ================================

@app.route('/api/user_info')
@require_auth
def get_user_info():
    """Get current user information for SPA"""
    try:
        current_user = get_current_user()
        return jsonify({
            'success': True,
            'username': current_user,
            'email': session.get('email', ''),
            'login_time': session.get('login_time', '')
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/upload_memory', methods=['POST'])
@require_auth
def upload_memory():
    """Upload images and videos to memory library"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'Không có file được chọn'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Không có file được chọn'}), 400
            
        # Get current user
        current_user = get_current_user()
        if not current_user:
            return jsonify({'success': False, 'message': 'Chưa đăng nhập'}), 401
            
        # Ensure user directories exist
        ensure_user_directories(current_user)
        
        # Check file type
        filename = file.filename.lower()
        is_image = filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'))
        is_video = filename.endswith(('.mp4', '.webm', '.ogg', '.mov', '.avi', '.mkv'))
        
        if not (is_image or is_video):
            return jsonify({
                'success': False, 
                'message': 'Định dạng file không được hỗ trợ. Chỉ chấp nhận ảnh (PNG, JPG, GIF, WEBP) và video (MP4, WebM, OGG, MOV, AVI, MKV)'
            }), 400
            
        # Check file size
        file_size = request.content_length
        if is_image and file_size > 10 * 1024 * 1024:  # 10MB
            return jsonify({
                'success': False,
                'message': 'File ảnh quá lớn. Tối đa 10MB.'
            }), 400
            
        if is_video and file_size > 50 * 1024 * 1024:  # 50MB
            return jsonify({
                'success': False,
                'message': 'File video quá lớn. Tối đa 50MB.'
            }), 400
            
        # Determine target directory - storage
        if is_image:
            target_dir = os.path.join(STORAGE_DIR, current_user, 'images')
        else:
            target_dir = os.path.join(STORAGE_DIR, current_user, 'videos')
        
        os.makedirs(target_dir, exist_ok=True)
        
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_extension = filename.rsplit('.', 1)[1].lower()
        unique_filename = f'{timestamp}_{secrets.token_hex(8)}.{file_extension}'
        
        # Save file
        file_path = os.path.join(target_dir, unique_filename)
        file.save(file_path)
        
        # For videos, generate preview
        preview_url = None
        if is_video:
            try:
                # Generate preview in background
                preview_filename = f'preview_{os.path.splitext(unique_filename)[0]}.gif'
                preview_dir = os.path.join(STORAGE_DIR, current_user, 'videos', 'previews')
                os.makedirs(preview_dir, exist_ok=True)
                preview_path = os.path.join(preview_dir, preview_filename)
                
                # Generate preview using video_processor
                from video_processor import generate_preview_thumbnail
                
                # Generate the preview - pass directory and filename separately
                result = generate_preview_thumbnail(file_path, preview_dir)
                
                if result['success']:
                    # Update preview_path with the actual filename from the result
                    preview_filename = result['preview_filename']
                    preview_path = os.path.join(preview_dir, preview_filename)
                    
                    # Verify the preview was created as a file
                    if not os.path.isfile(preview_path):
                        print(f"❌ Failed to create preview file at {preview_path}")
                        if os.path.exists(preview_path):
                            print(f"⚠️ Path exists but is a directory. Removing and retrying...")
                            os.rmdir(preview_path)  # Remove if it's a directory
                            result = generate_preview_thumbnail(file_path, preview_dir)
                            if result['success']:
                                preview_filename = result['preview_filename']
                                preview_path = os.path.join(preview_dir, preview_filename)
                    
                    preview_url = f'/api/serve_file/{current_user}/videos/previews/{preview_filename}'
                    print(f'✅ Generated video preview: {preview_path}')
                    print(f'✅ Preview file exists: {os.path.isfile(preview_path)}')
                    print(f'✅ Preview file size: {os.path.getsize(preview_path) if os.path.exists(preview_path) else 0} bytes')
                else:
                    print(f"❌ Failed to generate preview: {result.get('message', 'Unknown error')}")
                    preview_url = None
            except Exception as e:
                print(f'❌ Error generating video preview: {e}')
        
        # Get file URL
        file_url = f'/api/serve_file/{current_user}/videos/{unique_filename}' if is_video else f'/api/serve_file/{current_user}/images/{unique_filename}'
        
        return jsonify({
            'success': True,
            'message': 'Tải lên thành công',
            'fileUrl': file_url,
            'previewUrl': preview_url,
            'isVideo': is_video,
            'filename': unique_filename
        })
        
    except Exception as e:
        print(f'❌ Error uploading memory: {e}')
        return jsonify({
            'success': False,
            'message': f'Lỗi khi tải lên: {str(e)}'
        }), 500

@app.route('/api/create_moment', methods=['POST'])
@require_auth
def create_moment():
    """Create a new memory moment"""
    try:
        current_user = get_current_user()
        
        # Get form data
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        date = request.form.get('date')
        
        # Validate required fields
        if not all([title, description, category, date]):
            return jsonify({'success': False, 'message': 'Vui lòng điền đầy đủ thông tin'}), 400
        
        # Handle file uploads
        files = request.files.getlist('files')
        uploaded_files = []
        
        # Create user moment directory
        user_moment_dir = os.path.join(STORAGE_DIR, current_user, 'moments')
        os.makedirs(user_moment_dir, exist_ok=True)
        
        # Save uploaded files
        for file in files:
            if file and file.filename:
                # Generate safe filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{secure_filename(file.filename)}"
                filepath = os.path.join(user_moment_dir, filename)
                file.save(filepath)
                uploaded_files.append(filename)
        
        # Create moment data
        moment_data = {
            'id': str(datetime.now().timestamp()),
            'title': title,
            'description': description,
            'category': category,
            'date': date,
            'files': uploaded_files,
            'created_at': datetime.now().isoformat(),
            'username': current_user
        }
        
        # Save to moments database (JSON file)
        moments_file = os.path.join(STORAGE_DIR, current_user, 'moments.json')
        moments = []
        if os.path.exists(moments_file):
            with open(moments_file, 'r', encoding='utf-8') as f:
                moments = json.load(f)
        
        moments.append(moment_data)
        
        with open(moments_file, 'w', encoding='utf-8') as f:
            json.dump(moments, f, ensure_ascii=False, indent=2)
        
        print(f"✨ User {current_user} created new moment: {title}")
        
        return jsonify({
            'success': True,
            'message': 'Khoảnh khắc đã được tạo thành công!',
            'moment_id': moment_data['id']
        })
        
    except Exception as e:
        print(f"❌ Error creating moment: {str(e)}")
        return jsonify({'success': False, 'message': 'Có lỗi xảy ra khi tạo khoảnh khắc'}), 500

@app.route('/api/get_moments')
@require_auth
def get_moments():
    """Get all moments (videos) for current user from memories folder"""
    try:
        current_user = get_current_user()
        memories_dir = os.path.join(STORAGE_DIR, current_user, 'memories')
        previews_dir = os.path.join(memories_dir, 'previews')
        
        moments = []
        if os.path.exists(memories_dir):
            for filename in os.listdir(memories_dir):
                if filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                    file_path = os.path.join(memories_dir, filename)
                    stat = os.stat(file_path)
                    
                    # Check for preview GIF
                    preview_name = f"preview_{os.path.splitext(filename)[0]}.gif"
                    preview_path = os.path.join(previews_dir, preview_name)
                    has_preview = os.path.exists(preview_path)
                    
                    moments.append({
                        'filename': filename,
                        'path': f'/api/serve_file/{current_user}/memories/{filename}',
                        'preview': f'/api/serve_file/{current_user}/memories/previews/{preview_name}' if has_preview else None,
                        'size': stat.st_size,
                        'modified': stat.st_mtime,
                        'type': 'video'
                    })
        
        # Sort by modification time (newest first)
        moments.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            'success': True,
            'moments': moments
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/get_images')
@require_auth
def get_images():
    """Get all images for current user"""
    try:
        current_user = get_current_user()
        images_dir = os.path.join(STORAGE_DIR, current_user, 'images')
        
        images = []
        if os.path.exists(images_dir):
            for filename in os.listdir(images_dir):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                    file_path = os.path.join(images_dir, filename)
                    file_stat = os.stat(file_path)
                    images.append({
                        'filename': filename,
                        'path': f'/api/serve_file/{current_user}/images/{filename}',
                        'size': file_stat.st_size,
                        'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                        'type': 'image'
                    })
        
        # Sort by modification time (newest first)
        images.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            'success': True,
            'images': images
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/get_videos')
@require_auth
def get_videos():
    """Get all videos for current user with improved preview handling"""
    try:
        current_user = get_current_user()
        videos_dir = os.path.join(STORAGE_DIR, current_user, 'videos')
        previews_dir = os.path.join(videos_dir, 'previews')
        
        videos = []
        if os.path.exists(videos_dir):
            for filename in os.listdir(videos_dir):
                if filename.lower().endswith(('.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv')):
                    file_path = os.path.join(videos_dir, filename)
                    file_stat = os.stat(file_path)
                    
                    # Check for preview GIF
                    preview_name = None
                    has_preview = False
                    base_filename = filename.rsplit('.', 1)[0]
                    
                    # Pattern 1: preview_filename.gif (matching the upload_memory function)
                    preview_name1 = f"preview_{base_filename}.gif"
                    preview_path1 = os.path.join(previews_dir, preview_name1)
                    
                    # Pattern 2: Look for any preview file containing the video name
                    if os.path.exists(previews_dir) and os.path.isdir(previews_dir):
                        for preview_file in os.listdir(previews_dir):
                            preview_path = os.path.join(previews_dir, preview_file)
                            # Only consider files (not directories) with .gif extension
                            if (os.path.isfile(preview_path) and 
                                preview_file.endswith('.gif') and 
                                base_filename in preview_file and
                                os.path.getsize(preview_path) > 0):  # Ensure file is not empty
                                preview_name = preview_file
                                has_preview = True
                                break
                    
                    # Fallback to pattern 1 if no preview found and it's a valid file
                    if (not has_preview and 
                        os.path.exists(preview_path1) and 
                        os.path.isfile(preview_path1) and 
                        os.path.getsize(preview_path1) > 0):
                        preview_name = preview_name1
                        has_preview = True
                    
                    videos.append({
                        'filename': filename,
                        'path': f'/api/serve_file/{current_user}/videos/{filename}',
                        'preview': f'/api/serve_file/{current_user}/videos/previews/{preview_name}' if has_preview and preview_name else None,
                        'size': file_stat.st_size,
                        'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                        'type': 'video'
                    })
        
        # Sort by modification time (newest first)
        videos.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            'success': True,
            'videos': videos
        })
        
    except Exception as e:
        import traceback
        print(f"Error in get_videos: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/get_memories')
@require_auth
def get_memories():
    """Get all memories from user's memories directory"""
    try:
        current_user = get_current_user()
        memories_dir = os.path.join(STORAGE_DIR, current_user, 'memories')
        previews_dir = os.path.join(memories_dir, 'previews')
        
        print(f"🔍 DEBUG get_memories: current_user = {current_user}")
        print(f"🔍 DEBUG get_memories: memories_dir = {memories_dir}")
        print(f"🔍 DEBUG get_memories: directory exists = {os.path.exists(memories_dir)}")
        
        memories = []
        if os.path.exists(memories_dir):
            files = os.listdir(memories_dir)
            print(f"🔍 DEBUG get_memories: found {len(files)} files in directory")
            
            for filename in files:
                print(f"🔍 DEBUG get_memories: processing file = {filename}")
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv')):
                    file_path = os.path.join(memories_dir, filename)
                    file_stat = os.stat(file_path)
                    
                    file_type = 'image' if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')) else 'video'
                    
                    memory_item = {
                        'filename': filename,
                        'path': f'/api/serve_file/{current_user}/memories/{filename}',
                        'size': file_stat.st_size,
                        'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                        'type': file_type
                    }
                    
                    # Add preview for videos
                    if file_type == 'video':
                        preview_filename = f"preview_{os.path.splitext(filename)[0]}.gif"
                        preview_path = os.path.join(previews_dir, preview_filename)
                        print(f"🔍 DEBUG get_memories: checking preview path = {preview_path}")
                        if os.path.exists(preview_path):
                            memory_item['preview'] = f'/api/serve_file/{current_user}/memories/previews/{preview_filename}'
                            print(f"🔍 DEBUG get_memories: preview found, added to memory_item")
                    memories.append(memory_item)
                    print(f"🔍 DEBUG get_memories: added memory = {memory_item}")
        else:
            print(f"❌ DEBUG get_memories: Directory does not exist: {memories_dir}")
        
        # Sort by modification time (newest first)
        memories.sort(key=lambda x: x['modified'], reverse=True)
        
        print(f"🔍 DEBUG get_memories: returning {len(memories)} memories")
        
        return jsonify({
            'success': True,
            'memories': memories
        })
        
    except Exception as e:
        print(f"❌ ERROR get_memories: {str(e)}")
        print(f"❌ ERROR get_memories traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/get_all_memories')
@require_auth
def get_all_memories():
    """Get all memories (images, videos, moments) for current user sorted by time"""
    try:
        current_user = get_current_user()
        all_memories = []
        
        # Get images
        images_dir = os.path.join(STORAGE_DIR, current_user, 'images')
        if os.path.exists(images_dir):
            for filename in os.listdir(images_dir):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                    file_path = os.path.join(images_dir, filename)
                    file_stat = os.stat(file_path)
                    all_memories.append({
                        'filename': filename,
                        'path': f'/api/serve_file/{current_user}/images/{filename}',
                        'size': file_stat.st_size,
                        'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                        'type': 'image',
                        'title': filename.split('.')[0],
                        'description': f'Hình ảnh được tải lên'
                    })
        
        # Get videos
        videos_dir = os.path.join(STORAGE_DIR, current_user, 'videos')
        if os.path.exists(videos_dir):
            previews_dir = os.path.join(videos_dir, 'previews')
            
            for filename in os.listdir(videos_dir):
                if filename.lower().endswith(('.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv')):
                    file_path = os.path.join(videos_dir, filename)
                    file_stat = os.stat(file_path)
                    
                    # Check for preview GIF
                    preview_name = None
                    has_preview = False
                    
                    # Pattern 1: upload_preview_filename.gif
                    preview_name1 = f"upload_preview_{filename.rsplit('.', 1)[0]}.gif"
                    preview_path1 = os.path.join(previews_dir, preview_name1)
                    
                    # Pattern 2: Look for any preview file containing the video name
                    if os.path.exists(previews_dir):
                        for preview_file in os.listdir(previews_dir):
                            if preview_file.endswith('.gif') and filename.rsplit('.', 1)[0] in preview_file:
                                preview_name = preview_file
                                has_preview = True
                                break
                    
                    # Fallback to pattern 1 if no preview found
                    if not has_preview and os.path.exists(preview_path1):
                        preview_name = preview_name1
                        has_preview = True
                    
                    all_memories.append({
                        'filename': filename,
                        'path': f'/api/serve_file/{current_user}/videos/{filename}',
                        'preview': f'/api/serve_file/{current_user}/videos/previews/{preview_name}' if has_preview and preview_name else None,
                        'size': file_stat.st_size,
                        'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                        'type': 'video',
                        'title': filename.split('.')[0],
                        'description': f'Video được tải lên'
                    })
        
        # Get created moments
        moments_file = os.path.join(STORAGE_DIR, current_user, 'moments.json')
        if os.path.exists(moments_file):
            with open(moments_file, 'r', encoding='utf-8') as f:
                moments = json.load(f)
                for moment in moments:
                    all_memories.append({
                        'id': moment.get('id', ''),
                        'title': moment.get('title', ''),
                        'description': moment.get('description', ''),
                        'category': moment.get('category', ''),
                        'modified': moment.get('created_at', ''),
                        'type': 'moment',
                        'files': moment.get('files', [])
                    })
        
        # Sort by modification time (newest first)
        all_memories.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            'success': True,
            'memories': all_memories
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/get_user_profile', methods=['GET'])
@require_auth
def get_user_profile():
    """Get user profile data (avatar, cover)"""
    try:
        current_user = get_current_user()
        user_dir = os.path.join(STORAGE_DIR, current_user)
        
        profile_data = {
            'username': current_user,
            'avatar_url': None,
            'cover_url': None
        }
        
        # Check for avatar (look for avatar_*.ext files)
        avatar_dir = os.path.join(user_dir, 'avatar')
        if os.path.exists(avatar_dir):
            avatar_files = [f for f in os.listdir(avatar_dir) if f.startswith('avatar_') and 
                          f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'))]
            if avatar_files:
                # Get the most recent avatar file
                avatar_files.sort(reverse=True)  # Sort by filename (timestamp)
                latest_avatar = avatar_files[0]
                profile_data['avatar_url'] = f'/api/serve_file/{current_user}/avatar/{latest_avatar}'
        
        # Check for cover (look for cover_*.ext files)
        cover_dir = os.path.join(user_dir, 'cover')
        if os.path.exists(cover_dir):
            cover_files = [f for f in os.listdir(cover_dir) if f.startswith('cover_') and 
                          f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'))]
            if cover_files:
                # Get the most recent cover file
                cover_files.sort(reverse=True)  # Sort by filename (timestamp)
                latest_cover = cover_files[0]
                profile_data['cover_url'] = f'/api/serve_file/{current_user}/cover/{latest_cover}'
        
        return jsonify({
            'success': True,
            'profile': profile_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==========================================
# USER FILES SERVING ROUTES
# ==========================================

@app.route('/api/serve_file/<username>/avatar/<filename>')
def serve_avatar(username, filename):
    """Serve avatar files from storage directory"""
    try:
        # Security check to prevent directory traversal
        if '..' in filename or filename.startswith('/'):
            abort(403)
            
        # Serve from storage directory
        avatar_path = os.path.join(STORAGE_DIR, username, 'avatar', filename)
        if os.path.exists(avatar_path):
            return send_file(avatar_path)
        
        # If not found, return 404
        abort(404)
        
    except Exception as e:
        print(f"❌ Error serving avatar {filename}: {e}")
        abort(404)

@app.route('/api/serve_file/<username>/cover/<filename>')  
def serve_cover(username, filename):
    """Serve cover files from storage directory"""
    try:
        # Security check to prevent directory traversal
        if '..' in filename or filename.startswith('/'):
            abort(403)
            
        # Serve from storage directory
        cover_path = os.path.join(STORAGE_DIR, username, 'cover', filename)
        if os.path.exists(cover_path):
            return send_file(cover_path)
        
        # If not found, return 404
        abort(404)
        
    except Exception as e:
        print(f"❌ Error serving cover {filename}: {e}")
        abort(404)

if __name__ == "__main__":
    try:
        # Ensure required directories exist
        required_dirs = ['static/user_files', 'input', 'output', 'templates', 'static']
        for directory in required_dirs:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                print(f"📁 Created directory: {directory}")
        
        print("=" * 50)
        print("🎬 EVERLIVING VIDEO PROCESSING APPLICATION")
        print("=" * 50)
        print(f"🌐 Server running on: http://localhost:8080")
        print(f"🔐 Authentication: Enabled")
        print(f"📧 Email verification: {'Enabled' if auth_service.EMAIL_ENABLED else 'Disabled'}")
        print("=" * 50)
        print("📋 Available endpoints:")
        print("   GET  /           - Landing page")
        print("   GET  /login      - Login page")
        print("   GET  /register   - Register page")
        print("   GET  /main       - Main SPA application")
        print("   POST /api/login  - Login API")
        print("   POST /api/register - Register API")
        print("   POST /api/logout - Logout API")
        print("   GET  /api/user_info - Get user information")
        print("   POST /api/create_moment - Create memory moment")
        print("   GET  /api/get_moments - Get user moments")
        print("   GET  /api/get_images - Get user images")
        print("   GET  /api/get_videos - Get user videos")
        print("   GET  /api/get_all_memories - Get all memories sorted by time")
        print("   POST /api/upload_avatar - Upload user avatar")
        print("   POST /api/upload_cover - Upload user cover image")
        print("   GET  /api/get_user_profile - Get user profile (avatar, cover)")
        print("   GET  /static/user_files/<username>/<filename> - Serve user avatar")
        print("   GET  /static/user_files/<username>/<type>/<filename> - Serve user files")
        print("=" * 50)
        
        app.run(host='0.0.0.0', port=8080, debug=True)
        
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        sys.exit(1)
