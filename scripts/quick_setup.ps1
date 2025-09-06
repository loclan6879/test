# 🚀 Quick Start Script for EverTrace
# Run this after following SETUP_GUIDE.md

echo "🔧 EverTrace Quick Setup"
echo "========================"

# Check if Python is available
python --version
if ($LASTEXITCODE -ne 0) {
    echo "❌ Python not found! Please install Python 3.8+"
    exit 1
}

# Create virtual environment
if (!(Test-Path "venv")) {
    echo "📦 Creating virtual environment..."
    python -m venv venv
}

# Activate virtual environment
echo "🔄 Activating virtual environment..."
.\venv\Scripts\Activate.ps1

# Install dependencies
echo "📥 Installing Python packages..."
pip install -r requirements.txt

# Test system
echo "🧪 Testing system components..."
python test_system.py

echo ""
echo "🎉 Setup complete!"
echo "To run EverTrace:"
echo "  1. .\venv\Scripts\Activate.ps1"
echo "  2. python bot.py"
