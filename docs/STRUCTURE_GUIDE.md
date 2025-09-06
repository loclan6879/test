# EverTrace - Intelligent Memory Management System

## 🎯 Project Overview
EverTrace is a comprehensive Flask-based web application for personal memory management with video processing, user authentication, and intelligent file organization.

## 🚀 Quick Start
```powershell
# Navigate to project root
cd F:\EverTrace

# Activate virtual environment (if not already active)
.venv\Scripts\Activate.ps1

# Install dependencies (if needed)
pip install flask werkzeug

# Start the application
python app.py
```

**Access your application at: http://localhost:8080**

## 📁 Project Structure

```
F:\EverTrace/
├── app.py                    # 🚀 Main entry point (START HERE)
├── README.md                 # 📖 This documentation
├── requirements.txt          # 📦 Python dependencies
├── .venv/                    # 🐍 Python virtual environment
│
├── src/                      # 💾 Core source code
│   ├── app_restructured.py   # 🌐 Main Flask application
│   ├── auth_service.py       # 🔐 Authentication system
│   ├── video_processor.py    # 🎬 Video processing utilities
│   ├── list_music.py         # 🎵 Music management
│   └── music_selector.py     # 🎼 Music selection utilities
│
├── config/                   # ⚙️ Configuration files
│   └── email_config.py       # 📧 Email configuration
│
├── templates/                # 🎨 HTML templates
│   └── main_spa.html         # 🖥️ Main SPA interface
│
├── static/                   # 🎭 Static assets (CSS, JS)
│   └── style.css            # 🎨 Main stylesheet
│
├── LuuTru_User/             # 👤 User data (PROTECTED - DO NOT MODIFY)
│   ├── Danhsach_user.json   # 📝 User database
│   └── {username}/          # 📁 Individual user folders
│       ├── images/          # 🖼️ User images
│       ├── videos/          # 🎥 User videos
│       ├── music/           # 🎵 User music
│       ├── memories/        # 💭 User memories
│       └── moments.json     # ⏰ User moments data
│
├── assets/                   # 🎬 Media assets
│   ├── music/               # 🎵 Background music files
│   ├── nguyen-lieu/         # 🖼️ Source images/videos
│   └── outro/               # 🎬 Video outro files
│
├── scripts/                  # 🔧 Utility scripts
│   ├── check_update.bat     # 🔄 Update checker
│   └── quick_setup.ps1      # ⚡ Quick setup script
│
├── docs/                     # 📚 Documentation
│   ├── 2FA_APP_PASSWORD_SETUP.md
│   ├── EMAIL_SETUP_GUIDE.md
│   ├── REGISTRATION_SYSTEM_SUMMARY.md
│   └── bug_fixes_summary.md
│
├── tests/                    # 🧪 Test files
│   ├── clean_test_app.py    # 🧹 Cleanup tests
│   ├── simple_test_8080.py  # 🌐 Server tests
│   └── test_*.html          # 🌐 Frontend tests
│
├── temp/                     # 🗂️ Temporary files
│   ├── input/               # 📥 Input staging
│   └── output/              # 📤 Output staging
│
└── backup/                   # 💾 Backup files
    └── file_bot_backup/     # 🤖 Bot backup files
```

## 🔧 Key Features

### 🎨 User Interface
- **Grid Layouts**: 3x3 for memories, 5x5 for videos
- **Video Player**: Integrated modal video player with thumbnails
- **Image Lightbox**: Advanced lightbox with keyboard navigation
- **Responsive Design**: Mobile-friendly interface

### 🔐 Authentication System
- **User Registration**: Secure user account creation
- **Login/Logout**: Session-based authentication
- **Email Integration**: Password reset functionality

### 🎬 Media Management
- **Video Processing**: Automatic thumbnail generation
- **Image Organization**: Intelligent categorization
- **Music Integration**: Background music support
- **File Upload**: Drag-and-drop file uploads

### 💾 Data Storage
- **JSON Database**: Lightweight user data storage
- **File System**: Organized media file storage
- **Session Management**: Secure session handling

## 🔄 Development Workflow

### Making UI Changes
Edit these files for interface updates:
- `templates/main_spa.html` - Main SPA interface
- `static/style.css` - Styling and layouts

### Backend Changes
Edit these files for functionality updates:
- `src/app_restructured.py` - Main application logic
- `src/auth_service.py` - Authentication features
- `src/video_processor.py` - Media processing

### Configuration Changes
Edit these files for system configuration:
- `config/email_config.py` - Email settings
- `src/app_restructured.py` - Flask configuration

## 📊 Technical Stack
- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript (SPA)
- **Database**: JSON file storage
- **Media**: Video/Image processing
- **Environment**: Python Virtual Environment

## 🔒 Security Notes
- Keep `LuuTru_User/` directory protected
- Regular backup of user data recommended
- Email configuration for production deployment

## 📞 Support
For updates and modifications, use the AI assistant to automatically update the appropriate files based on this structure guide.

---
**Last Updated**: January 2025  
**Version**: 2.0 (Restructured)  
**Status**: ✅ Production Ready
