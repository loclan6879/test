# 🎬 EverTrace - Video Processing & Memory Management System

## 📁 Project Structure

```
F:\EverTrace\
├── 📂 src/                     # Source code
│   ├── app_restructured.py     # Main Flask application
│   ├── auth_service.py         # Authentication service
│   ├── video_processor.py      # Video processing module
│   ├── list_music.py          # Music listing utility
│   ├── music_selector.py      # Music selection module
│   ├── 📂 templates/          # HTML templates
│   └── 📂 static/             # CSS, JS, static assets
│
├── 📂 config/                  # Configuration files
│   ├── email_config.py        # Email configuration
│   └── requirements.txt       # Python dependencies
│
├── 📂 docs/                   # Documentation
│   ├── 2FA_APP_PASSWORD_SETUP.md
│   ├── EMAIL_SETUP_GUIDE.md
│   ├── NEW_ARCHITECTURE_README.md
│   ├── REGISTRATION_SYSTEM_SUMMARY.md
│   └── RESTRUCTURING_COMPLETE.md
│
├── 📂 assets/                 # Media assets
│   ├── 📂 music/             # Background music files
│   ├── 📂 nguyen lieu/       # Material files
│   └── 📂 outro/             # Outro video templates
│
├── 📂 scripts/               # Utility scripts
│   ├── check_update.bat     # Update checker
│   └── quick_setup.ps1      # Quick setup script
│
├── 📂 tests/                 # Test files
│   ├── test_*.html          # HTML test files
│   ├── debug_js.html        # JavaScript debugging
│   └── clean_auth_functions.js
│
├── 📂 temp/                  # Temporary files
│   ├── 📂 input/            # Input processing folder
│   ├── 📂 output/           # Output processing folder
│   └── 📂 __pycache__/      # Python cache
│
├── 📂 backup/               # Backup files
│   └── 📂 file bot backup/  # Bot backup files
│
├── 📂 LuuTru_User/         # User data (DO NOT TOUCH)
│   └── user1/
│       ├── 📂 images/      # User uploaded images
│       ├── 📂 videos/      # User uploaded videos
│       └── 📂 memories/    # Created memory videos
│
├── 📂 .venv/               # Python virtual environment
├── app.py                  # Main entry point
└── README.md              # This file
```

## 🚀 Quick Start

### 1. Activate Virtual Environment
```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r config/requirements.txt
```

### 3. Run Application
```bash
python app.py
```

### 4. Access Application
- 🌐 Web Interface: http://localhost:8080
- 📱 Mobile-friendly responsive design
- 🔐 Authentication required

## 🎯 Features

### 🎬 Video Management
- Upload and organize videos
- Automatic thumbnail generation
- Preview GIF creation
- Video player with controls

### 🖼️ Image Gallery
- Photo upload and management
- Lightbox viewer with navigation
- Keyboard shortcuts (← → ESC)
- Responsive grid layout

### 👤 User System
- User registration and login
- Email verification
- Session management
- Individual user storage

### 📱 Single Page Application
- Modern SPA design
- Tab-based navigation
- Real-time content loading
- Mobile responsive

## 🛠️ Technical Stack

- **Backend**: Python Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **Database**: JSON file storage
- **Authentication**: Custom session-based
- **Email**: SMTP with Gmail integration
- **Storage**: File system based

## 📝 Notes

- **LuuTru_User folder**: Contains all user data and should never be modified
- **Development Mode**: Email verification codes are displayed in console
- **Debug Mode**: Enabled for development (disable for production)
- **Port**: Default 8080 (configurable in app.py)

## 🔧 Configuration

Main configuration files:
- `config/email_config.py` - Email settings
- `config/requirements.txt` - Python dependencies
- `src/app_restructured.py` - Main app configuration

## 📚 Documentation

Detailed documentation is available in the `docs/` folder:
- Setup guides
- Architecture overview
- System summaries
- Bug fix history

---

**EverTrace Team** | Version 2.0 | Reorganized Structure
