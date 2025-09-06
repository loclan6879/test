# Email Configuration for EverTrace
# IMPORTANT: Update these settings before using the registration system

# SMTP Server Settings
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Email Credentials
# ⚠️ QUAN TRỌNG: Để sử dụng Gmail, bạn PHẢI:
# 1. Bật 2-Factor Authentication (2FA) trước
# 2. Tạo App Password (không phải mật khẩu thường)
# 3. Sử dụng App Password 16 ký tự ở đây

# 📧 EMAIL SETUP:
EMAIL_ADDRESS = "everliving.service@gmail.com"        # Thay bằng Gmail của bạn
EMAIL_PASSWORD = "ecwdehdvucbdahip"          # App Password 16 ký tự (không có dấu cách)

# 🔑 APP PASSWORD LÀ GÌ?
# - Mật khẩu đặc biệt cho ứng dụng (16 ký tự)
# - CHỈ có khi đã bật 2FA
# - Tạo tại: https://myaccount.google.com/apppasswords
# - VD: "abcd efgh ijkl mnop" → nhập: "abcdefghijklmnop"

# Email Templates
EMAIL_SUBJECT = "EverTrace - Mã xác thực đăng ký tài khoản"

# Email Credentials
# For Gmail, you need to:
# 1. Enable 2-Factor Authentication
# 2. Generate an App Password
# 3. Use the App Password here (not your regular password)
EMAIL_ADDRESS = "everliving.service@gmail.com"        # Thay bằng Gmail của bạn
EMAIL_PASSWORD = "ecwdehdvucbdahip"   

# Email Templates
EMAIL_SUBJECT = "EverLiving - Mã xác thực đăng ký tài khoản"

def get_email_body(username, verification_code):
    return f"""
Xin chào {username},

Cảm ơn bạn đã đăng ký tài khoản EverTrace!

Mã xác thực của bạn là: {verification_code}

Vui lòng nhập mã này để hoàn tất quá trình đăng ký.
Mã xác thực có hiệu lực trong 15 phút.

Nếu bạn không đăng ký tài khoản này, vui lòng bỏ qua email này.

Trân trọng,
Đội ngũ EverTrace

---
© 2025 EverTrace. All rights reserved.
Website: http://localhost:8080
"""

# Development Mode
# Set to True to print verification codes to console instead of sending emails
DEVELOPMENT_MODE = True
