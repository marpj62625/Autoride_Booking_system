
        // Password visibility toggle function
        function togglePasswordVisibility(inputId, button) {
            const input = document.getElementById(inputId);
            const icon = button.querySelector('i');
            
            if (input.type === 'password') {
                input.type = 'text';
                icon.className = 'fas fa-eye-slash';
            } else {
                input.type = 'password';
                icon.className = 'fas fa-eye';
            }
        }

        // Password validation function
        function validatePassword(password, errorElementId) {
            const requirements = {
                uppercase: /[A-Z]/.test(password),
                lowercase: /[a-z]/.test(password),
                number: /\d/.test(password),
                length: password.length >= 8
            };

            // Update requirement indicators
            const updateRequirement = (id, isValid) => {
                const element = document.getElementById(id);
                if (element) {
                    const icon = element.querySelector('i');
                    if (isValid) {
                        element.classList.add('valid');
                        element.classList.remove('invalid');
                        icon.className = 'fas fa-check';
                    } else {
                        element.classList.add('invalid');
                        element.classList.remove('valid');
                        icon.className = 'fas fa-times';
                    }
                }
            };

            updateRequirement('req-uppercase', requirements.uppercase);
            updateRequirement('req-lowercase', requirements.lowercase);
            updateRequirement('req-number', requirements.number);
            updateRequirement('req-length', requirements.length);

            // Check if all requirements are met
            const isValid = Object.values(requirements).every(req => req);
            
            // Update error message
            const errorElement = document.getElementById(errorElementId);
            if (errorElement) {
                if (password.length > 0 && !isValid) {
                    errorElement.textContent = 'Password does not meet all requirements';
                    errorElement.style.display = 'block';
                } else {
                    errorElement.textContent = '';
                    errorElement.style.display = 'none';
                }
            }

            return isValid;
        }
    