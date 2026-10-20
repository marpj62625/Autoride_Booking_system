
// Customer sidebar collapse/expand toggle & state persistence
function toggleCustomerSidebar() {
    var isCollapsed = document.body.classList.toggle('customer-sidebar-collapsed');
    try {
        localStorage.setItem('autoride_customer_sidebar_collapsed', isCollapsed ? 'true' : 'false');
    } catch(e) {}
}
(function() {
    try {
        if (localStorage.getItem('autoride_customer_sidebar_collapsed') === 'true' && window.innerWidth >= 768) {
            document.body.classList.add('customer-sidebar-collapsed');
        }
    } catch(e) {}
})();

// Password visibility toggle function
function togglePasswordVisibility(inputId, button) {
    var input = document.getElementById(inputId);
    var icon = button ? button.querySelector('i') : null;
    if (!input) return;
    if (input.type === 'password') {
        input.type = 'text';
        if (icon) icon.className = 'fas fa-eye-slash';
    } else {
        input.type = 'password';
        if (icon) icon.className = 'fas fa-eye';
    }
}

// Password validation function
function validatePassword(password, errorElementId, prefix) {
    if (!prefix) prefix = 'req-';
    var requirements = {
        uppercase: /[A-Z]/.test(password),
        lowercase: /[a-z]/.test(password),
        number: /\d/.test(password),
        special: /[^A-Za-z0-9]/.test(password),
        length: password.length >= 8
    };
    var updateRequirement = function(id, isValid) {
        var element = document.getElementById(id);
        if (element) {
            var icon = element.querySelector('i');
            if (isValid) {
                element.classList.add('valid');
                element.classList.remove('invalid');
                if (icon) icon.className = 'fas fa-check';
            } else {
                element.classList.add('invalid');
                element.classList.remove('valid');
                if (icon) icon.className = 'fas fa-times';
            }
        }
    };
    updateRequirement(prefix + 'uppercase', requirements.uppercase);
    updateRequirement(prefix + 'lowercase', requirements.lowercase);
    updateRequirement(prefix + 'number', requirements.number);
    updateRequirement(prefix + 'special', requirements.special);
    updateRequirement(prefix + 'length', requirements.length);
    var isValid = Object.values(requirements).every(function(req) { return req; });
    var errorElement = document.getElementById(errorElementId);
    if (errorElement) {
        if (password.length > 0 && !isValid) {
            errorElement.textContent = 'Password must meet all 5 requirements';
            errorElement.style.display = 'block';
        } else {
            errorElement.textContent = '';
            errorElement.style.display = 'none';
        }
    }
    return isValid;
}

function checkConfirmPasswordMatch() {
    var pwEl = document.getElementById('regPassword');
    var cpEl = document.getElementById('regConfirmPassword');
    var errEl = document.getElementById('regConfirmPasswordErr');
    if (!cpEl || !errEl) return true;
    var pw = pwEl ? pwEl.value : '';
    var cp = cpEl.value;
    if (!cp) {
        errEl.textContent = '';
        errEl.style.display = 'none';
        return true;
    }
    if (pw !== cp) {
        errEl.textContent = 'Passwords do not match';
        errEl.style.display = 'block';
        return false;
    } else {
        errEl.textContent = '';
        errEl.style.display = 'none';
        return true;
    }
}

function validateRegistrationEmailField(inputEl) {
    if (!inputEl) return true;
    var errEl = document.getElementById('regEmailErr');
    var val = (inputEl.value || '').trim();
    if (!val) {
        if (errEl) { errEl.textContent = ''; errEl.style.display = 'none'; }
        return true;
    }
    if (typeof validateEmailAddress === 'function') {
        var res = validateEmailAddress(val);
        if (!res.valid) {
            if (errEl) { errEl.textContent = res.error; errEl.style.display = 'block'; }
            return false;
        }
    }
    if (errEl) { errEl.textContent = ''; errEl.style.display = 'none'; }
    return true;
}

document.addEventListener('DOMContentLoaded', function() {
    var registerButton = document.querySelector('button[onclick="doRegister()"]');
    if (registerButton) {
        registerButton.addEventListener('click', function(e) {
            var passwordInput = document.getElementById('regPassword');
            if (passwordInput) {
                var password = passwordInput.value;
                if (!validatePassword(password, 'regPasswordErr')) {
                    e.preventDefault();
                    e.stopPropagation();
                    showToast('Please ensure your password meets all requirements before submitting.', 'error');
                    return false;
                }
            }
            var confirmInput = document.getElementById('regConfirmPassword');
            if (confirmInput) {
                var confirmPw = confirmInput.value;
                var passwordVal = passwordInput ? passwordInput.value : '';
                if (!confirmPw) {
                    e.preventDefault();
                    e.stopPropagation();
                    showToast('Please confirm your password.', 'error');
                    return false;
                }
                if (passwordVal !== confirmPw) {
                    e.preventDefault();
                    e.stopPropagation();
                    showToast('Passwords do not match.', 'error');
                    return false;
                }
            }
        });
    }
});
