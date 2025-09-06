
        console.log('=== CLEAN TEST SCRIPT LOADING ===');
        
        // Show login form
        function showLoginForm() {
            console.log('✅ showLoginForm called');
            
            const loginForm = document.getElementById('loginForm');
            const registerForm = document.getElementById('registerForm');
            const loginTab = document.getElementById('loginTab');
            const registerTab = document.getElementById('registerTab');
            
            if (loginForm) loginForm.style.display = 'block';
            if (registerForm) registerForm.style.display = 'none';
            if (loginTab) loginTab.classList.add('active');
            if (registerTab) registerTab.classList.remove('active');
            
            // Clear status messages
            const loginStatus = document.getElementById('loginStatus');
            const registerStatus = document.getElementById('registerStatus');
            if (loginStatus) loginStatus.innerHTML = '';
            if (registerStatus) registerStatus.innerHTML = '';
        }
        
        // Show register form
        function showRegisterForm() {
            console.log('✅ showRegisterForm called');
            
            const loginForm = document.getElementById('loginForm');
            const registerForm = document.getElementById('registerForm');
            const loginTab = document.getElementById('loginTab');
            const registerTab = document.getElementById('registerTab');
            
            if (loginForm) loginForm.style.display = 'none';
            if (registerForm) registerForm.style.display = 'block';
            if (loginTab) loginTab.classList.remove('active');
            if (registerTab) registerTab.classList.add('active');
            
            // Show registration step
            const regStep = document.getElementById('registrationStep');
            const verStep = document.getElementById('verificationStep');
            if (regStep) regStep.style.display = 'block';
            if (verStep) verStep.style.display = 'none';
            
            // Clear status messages
            const loginStatus = document.getElementById('loginStatus');
            const registerStatus = document.getElementById('registerStatus');
            if (loginStatus) loginStatus.innerHTML = '';
            if (registerStatus) registerStatus.innerHTML = '';
        }
        
        // Login function
        function login() {
            console.log('✅ login called');
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value;
            const statusDiv = document.getElementById('loginStatus');
            
            // Basic validation
            if (!username || !password) {
                if (statusDiv) {
                    statusDiv.className = 'status error';
                    statusDiv.innerHTML = 'Vui lòng nhập đầy đủ thông tin!';
                }
                return;
            }
            
            // Show loading
            if (statusDiv) {
                statusDiv.className = 'status info';
                statusDiv.innerHTML = 'Đang đăng nhập...';
            }
            
            // Simulate API call
            setTimeout(() => {
                if (statusDiv) {
                    statusDiv.className = 'status success';
                    statusDiv.innerHTML = 'Đăng nhập thành công! (Đây là test)';
                }
            }, 1000);
        }
        
        // Register user
        function registerUser() {
            console.log('✅ registerUser called');
            const username = document.getElementById('regUsername').value.trim();
            const email = document.getElementById('regEmail').value.trim();
            const password = document.getElementById('regPassword').value;
            const confirmPassword = document.getElementById('regConfirmPassword').value;
            const statusDiv = document.getElementById('registerStatus');
            
            // Clear previous status
            if (statusDiv) {
                statusDiv.className = '';
                statusDiv.innerHTML = '';
            }
            
            // Validation
            if (!username || !email || !password || !confirmPassword) {
                if (statusDiv) {
                    statusDiv.className = 'status error';
                    statusDiv.innerHTML = 'Vui lòng điền đầy đủ thông tin!';
                }
                return;
            }
            
            if (password !== confirmPassword) {
                if (statusDiv) {
                    statusDiv.className = 'status error';
                    statusDiv.innerHTML = 'Mật khẩu nhập lại không khớp!';
                }
                return;
            }
            
            // Email validation
            const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$/;
            if (!emailRegex.test(email)) {
                if (statusDiv) {
                    statusDiv.className = 'status error';
                    statusDiv.innerHTML = 'Email không hợp lệ!';
                }
                return;
            }
            
            // Show loading
            if (statusDiv) {
                statusDiv.className = 'status info';
                statusDiv.innerHTML = 'Đang xử lý đăng ký...';
            }
            
            // Simulate registration
            setTimeout(() => {
                if (statusDiv) {
                    statusDiv.className = 'status success';
                    statusDiv.innerHTML = 'Đăng ký thành công! Chuyển sang bước xác minh...';
                }
                
                // Switch to verification step
                const regStep = document.getElementById('registrationStep');
                const verStep = document.getElementById('verificationStep');
                const verEmail = document.getElementById('verificationEmail');
                
                if (regStep) regStep.style.display = 'none';
                if (verStep) verStep.style.display = 'block';
                if (verEmail) verEmail.textContent = email;
                
                // Store email for verification
                window.pendingEmail = email;
            }, 1000);
        }
        
        // Verify registration
        function verifyRegistration() {
            console.log('✅ verifyRegistration called');
            const code = document.getElementById('verificationCode').value.trim();
            const statusDiv = document.getElementById('registerStatus');
            
            if (!code || code.length !== 6) {
                if (statusDiv) {
                    statusDiv.className = 'status error';
                    statusDiv.innerHTML = 'Vui lòng nhập mã 6 chữ số!';
                }
                return;
            }
            
            // Show loading
            if (statusDiv) {
                statusDiv.className = 'status info';
                statusDiv.innerHTML = 'Đang xác thực...';
            }
            
            // Simulate verification
            setTimeout(() => {
                if (statusDiv) {
                    statusDiv.className = 'status success';
                    statusDiv.innerHTML = 'Xác minh thành công! Chuyển về đăng nhập...';
                }
                
                setTimeout(() => {
                    showLoginForm();
                    delete window.pendingEmail;
                }, 2000);
            }, 1000);
        }
        
        // Back to registration
        function backToRegistration() {
            console.log('✅ backToRegistration called');
            const regStep = document.getElementById('registrationStep');
            const verStep = document.getElementById('verificationStep');
            const verCode = document.getElementById('verificationCode');
            const statusDiv = document.getElementById('registerStatus');
            
            if (regStep) regStep.style.display = 'block';
            if (verStep) verStep.style.display = 'none';
            if (verCode) verCode.value = '';
            if (statusDiv) statusDiv.innerHTML = '';
        }
        
        // Resend verification code
        function resendVerificationCode() {
            console.log('✅ resendVerificationCode called');
            const statusDiv = document.getElementById('registerStatus');
            
            if (statusDiv) {
                statusDiv.className = 'status info';
                statusDiv.innerHTML = 'Đang gửi lại mã...';
            }
            
            setTimeout(() => {
                if (statusDiv) {
                    statusDiv.className = 'status success';
                    statusDiv.innerHTML = 'Mã xác minh đã được gửi lại!';
                }
            }, 1000);
        }
        
        // Test all functions on load
        window.addEventListener('DOMContentLoaded', function() {
            console.log('=== TESTING ALL FUNCTIONS ===');
            
            const functions = ['showLoginForm', 'showRegisterForm', 'login', 'registerUser', 'verifyRegistration', 'backToRegistration', 'resendVerificationCode'];
            
            functions.forEach(funcName => {
                if (typeof window[funcName] === 'function') {
                    console.log(`✅ ${funcName}() - AVAILABLE`);
                } else {
                    console.log(`❌ ${funcName}() - MISSING`);
                }
            });
            
            console.log('=== TEST COMPLETE ===');
            console.log('🎯 Try clicking the buttons now!');
        });
    