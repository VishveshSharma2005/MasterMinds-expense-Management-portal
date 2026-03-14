/**
 * ============================================================================
 * validation.js — Splitsmart Frontend Validation
 * ============================================================================
 *
 * Real-time client-side validation for Sign-Up and Login pages.
 * This file is intentionally SEPARATE from auth.js to avoid merge conflicts.
 *
 * SIGN-UP validation covers:
 *   1. Email format (strict regex — requires valid TLD, no HTML chars)
 *   2. Full Name (letters, spaces, hyphens, apostrophes only)
 *   3. Username (alphanumeric + underscores only)
 *   4. Phone Number (exactly 10 digits)
 *   5. Password strength (min 8 chars, 1 number, 1 special character)
 *   6. Confirm-password match
 *   7. Input sanitisation — blocks < > to prevent XSS
 *
 * LOGIN validation covers:
 *   1. Non-empty email/username field
 *   2. Non-empty password field
 *
 * INTEGRATION:
 *   Add this script tag to your signup.html and login.html templates:
 *     <script src="{{ url_for('static', filename='js/validation.js') }}"></script>
 * ============================================================================
 */

(function () {
    'use strict';

    // =====================================================================
    // UTILITY HELPERS
    // =====================================================================

    /**
     * Set a validation message below an input field.
     * @param {HTMLElement} target  - The span/element to write the message into
     * @param {string}      message - Text to display
     * @param {'error'|'success'|''} type - CSS class to apply
     */
    function setMessage(target, message, type) {
        if (!target) return;
        target.textContent = message;
        target.classList.remove('error', 'success');
        if (type) {
            target.classList.add(type);
        }
    }

    /**
     * Toggle is-valid / is-invalid CSS classes on an input.
     * @param {HTMLElement} input - The input element
     * @param {boolean}     valid - Whether the current value is valid
     */
    function markInput(input, valid) {
        if (!input) return;
        input.classList.remove('is-valid', 'is-invalid');
        input.classList.add(valid ? 'is-valid' : 'is-invalid');
    }

    /**
     * Ensure a feedback <span> exists right after the given input.
     * If one already exists (from the template), reuse it.
     * @param {HTMLElement} input - The input element
     * @param {string}      id   - Desired id for the feedback span
     * @returns {HTMLElement} The feedback span element
     */
    function ensureFeedbackSpan(input, id) {
        var existing = document.getElementById(id);
        if (existing) return existing;

        var span = document.createElement('span');
        span.id = id;
        span.className = 'validation-msg';
        span.setAttribute('aria-live', 'polite');
        input.parentNode.insertBefore(span, input.nextSibling);
        return span;
    }

    /**
     * Strip dangerous HTML characters (< >) from an input field's value
     * in real-time so users can never type them.
     * @param {HTMLInputElement} input
     */
    function sanitizeInput(input) {
        if (!input) return;
        input.addEventListener('input', function () {
            var cleaned = input.value.replace(/[<>]/g, '');
            if (cleaned !== input.value) {
                input.value = cleaned;
            }
        });
    }

    // =====================================================================
    // SIGN-UP PAGE VALIDATION
    // =====================================================================

    function initSignupValidation() {
        var signupForm = document.querySelector('form[enctype="multipart/form-data"]');
        if (!signupForm) return; // Not on the sign-up page

        // --- Grab input elements ---
        var emailInput = document.getElementById('email');
        var fullNameInput = document.getElementById('full_name');
        var usernameInput = document.getElementById('username');
        var phoneInput = document.getElementById('phone_number');
        var upiInput = document.getElementById('upi_id');
        var passwordInput = document.getElementById('password');
        var confirmPasswordInput = document.getElementById('confirm_password');

        // --- Ensure feedback spans exist ---
        var emailFeedback = emailInput ? ensureFeedbackSpan(emailInput, 'emailFeedback') : null;
        var nameFeedback = fullNameInput ? ensureFeedbackSpan(fullNameInput, 'nameFeedback') : null;
        var usernameFeedback = usernameInput ? ensureFeedbackSpan(usernameInput, 'usernameFeedback') : null;
        var phoneFeedback = document.getElementById('phoneFeedback') || (phoneInput ? ensureFeedbackSpan(phoneInput, 'phoneFeedback') : null);
        var upiFeedback = document.getElementById('upiFeedback') || (upiInput ? ensureFeedbackSpan(upiInput, 'upiFeedback') : null);
        var passwordStrengthFeedback = passwordInput ? ensureFeedbackSpan(passwordInput, 'passwordStrengthFeedback') : null;
        var confirmFeedback = document.getElementById('passwordFeedback');

        // --- Apply input sanitisation (strip < >) to all text fields ---
        [emailInput, fullNameInput, usernameInput, phoneInput, upiInput].forEach(sanitizeInput);

        // --- Regex patterns ---

        // Email: local@domain.tld
        //   - local part: letters, digits, . _ % + -
        //   - domain:     letters, digits, . -  (at least 2 chars before the dot)
        //   - TLD:        2–10 letters only
        var emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,10}$/;

        // Full Name: letters (including accented), spaces, hyphens, apostrophes
        var nameRegex = /^[a-zA-ZÀ-ÿ\s'-]{2,}$/;

        // Username: alphanumeric + underscores, 3–30 chars
        var usernameRegex = /^[a-zA-Z0-9_]{3,30}$/;

        // Phone: exactly 10 digits
        var phoneRegex = /^[0-9]{10}$/;

        // UPI ID: prefix@suffix per NPCI guidelines
        //   prefix: 2-256 chars — alphanumeric, dot, hyphen, underscore
        //   suffix: 2-64 chars — alphabetic (bank/PSP handle)
        var upiRegex = /^[a-zA-Z0-9._-]{2,256}@[a-zA-Z]{2,64}$/;

        // Password helpers
        var hasNumber = /[0-9]/;
        var hasSpecial = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?`~]/;

        // =================================================================
        // 1. EMAIL FORMAT VALIDATION
        // =================================================================
        function validateEmail() {
            if (!emailInput) return true;
            var value = emailInput.value.trim();

            if (!value) {
                setMessage(emailFeedback, 'Email address is required.', 'error');
                markInput(emailInput, false);
                return false;
            }

            if (!emailRegex.test(value)) {
                setMessage(emailFeedback, 'Enter a valid email (e.g. user@example.com).', 'error');
                markInput(emailInput, false);
                return false;
            }

            setMessage(emailFeedback, 'Email format looks good.', 'success');
            markInput(emailInput, true);
            return true;
        }

        // =================================================================
        // 2. FULL NAME VALIDATION (letters, spaces, hyphens, apostrophes)
        // =================================================================
        function validateFullName() {
            if (!fullNameInput) return true;
            var value = fullNameInput.value.trim();

            if (!value) {
                setMessage(nameFeedback, 'Full name is required.', 'error');
                markInput(fullNameInput, false);
                return false;
            }

            if (!nameRegex.test(value)) {
                setMessage(nameFeedback, 'Name must contain only letters, spaces, hyphens, or apostrophes.', 'error');
                markInput(fullNameInput, false);
                return false;
            }

            setMessage(nameFeedback, '', '');
            markInput(fullNameInput, true);
            return true;
        }

        // =================================================================
        // 3. USERNAME VALIDATION (alphanumeric + underscores, 3-30 chars)
        // =================================================================
        function validateUsername() {
            if (!usernameInput) return true;
            var value = usernameInput.value.trim();

            if (!value) {
                setMessage(usernameFeedback, 'Username is required.', 'error');
                markInput(usernameInput, false);
                return false;
            }

            if (!usernameRegex.test(value)) {
                setMessage(usernameFeedback, 'Username: 3–30 characters, letters, numbers, and underscores only.', 'error');
                markInput(usernameInput, false);
                return false;
            }

            setMessage(usernameFeedback, '', '');
            markInput(usernameInput, true);
            return true;
        }

        // =================================================================
        // 4. PHONE NUMBER VALIDATION (exactly 10 digits)
        // =================================================================
        function validatePhone() {
            if (!phoneInput) return true;
            var value = phoneInput.value.trim();

            if (!value) {
                setMessage(phoneFeedback, 'Phone number is required.', 'error');
                markInput(phoneInput, false);
                return false;
            }

            if (!phoneRegex.test(value)) {
                setMessage(phoneFeedback, 'Enter a valid 10-digit phone number.', 'error');
                markInput(phoneInput, false);
                return false;
            }

            setMessage(phoneFeedback, '', '');
            markInput(phoneInput, true);
            return true;
        }

        // =================================================================
        // 5. UPI ID VALIDATION (NPCI format: prefix@bankhandle)
        // =================================================================
        function validateUpi() {
            if (!upiInput) return true;
            var value = upiInput.value.trim();

            if (!value) {
                setMessage(upiFeedback, 'UPI ID is required.', 'error');
                markInput(upiInput, false);
                return false;
            }

            // Must not contain whitespace
            if (/\s/.test(value)) {
                setMessage(upiFeedback, 'UPI ID must not contain spaces.', 'error');
                markInput(upiInput, false);
                return false;
            }

            if (!upiRegex.test(value)) {
                setMessage(upiFeedback, 'Enter a valid UPI ID (e.g. name@bank).', 'error');
                markInput(upiInput, false);
                return false;
            }

            setMessage(upiFeedback, 'Valid UPI ID ✓', 'success');
            markInput(upiInput, true);
            return true;
        }

        // =================================================================
        // 6. PASSWORD STRENGTH VALIDATION
        //    Rules: min 8 chars, at least 1 number, at least 1 special char
        // =================================================================
        function validatePasswordStrength() {
            if (!passwordInput) return true;

            var value = passwordInput.value;
            var errors = [];

            if (value.length < 8) {
                errors.push('at least 8 characters');
            }
            if (!hasNumber.test(value)) {
                errors.push('at least 1 number');
            }
            if (!hasSpecial.test(value)) {
                errors.push('at least 1 special character (!@#$%...)');
            }

            if (errors.length > 0) {
                setMessage(
                    passwordStrengthFeedback,
                    'Password needs: ' + errors.join(', ') + '.',
                    'error'
                );
                markInput(passwordInput, false);
                return false;
            }

            setMessage(passwordStrengthFeedback, 'Strong password ✓', 'success');
            markInput(passwordInput, true);
            return true;
        }

        // =================================================================
        // 7. CONFIRM PASSWORD MATCH
        // =================================================================
        function validateConfirmPassword() {
            if (!confirmPasswordInput || !passwordInput) return true;

            var password = passwordInput.value;
            var confirm = confirmPasswordInput.value;

            if (!confirm) {
                setMessage(confirmFeedback, 'Please re-enter your password.', 'error');
                markInput(confirmPasswordInput, false);
                return false;
            }

            if (password !== confirm) {
                setMessage(confirmFeedback, 'Passwords do not match.', 'error');
                markInput(confirmPasswordInput, false);
                return false;
            }

            setMessage(confirmFeedback, 'Passwords match ✓', 'success');
            markInput(confirmPasswordInput, true);
            return true;
        }

        // --- Attach real-time listeners ---
        if (emailInput) {
            emailInput.addEventListener('input', validateEmail);
            emailInput.addEventListener('blur', validateEmail);
        }
        if (fullNameInput) {
            fullNameInput.addEventListener('input', validateFullName);
            fullNameInput.addEventListener('blur', validateFullName);
        }
        if (usernameInput) {
            usernameInput.addEventListener('input', validateUsername);
            usernameInput.addEventListener('blur', validateUsername);
        }
        if (phoneInput) {
            phoneInput.addEventListener('input', validatePhone);
            phoneInput.addEventListener('blur', validatePhone);
        }
        if (upiInput) {
            upiInput.addEventListener('input', validateUpi);
            upiInput.addEventListener('blur', validateUpi);
        }
        if (passwordInput) {
            passwordInput.addEventListener('input', function () {
                validatePasswordStrength();
                if (confirmPasswordInput && confirmPasswordInput.value) {
                    validateConfirmPassword();
                }
            });
        }
        if (confirmPasswordInput) {
            confirmPasswordInput.addEventListener('input', validateConfirmPassword);
        }

        // --- Prevent form submission if validation fails ---
        signupForm.addEventListener('submit', function (event) {
            var isEmailValid = validateEmail();
            var isNameValid = validateFullName();
            var isUsernameValid = validateUsername();
            var isPhoneValid = validatePhone();
            var isUpiValid = validateUpi();
            var isPasswordStrong = validatePasswordStrength();
            var isConfirmValid = validateConfirmPassword();

            if (!isEmailValid || !isNameValid || !isUsernameValid || !isPhoneValid || !isUpiValid || !isPasswordStrong || !isConfirmValid) {
                event.preventDefault();
                var firstError = signupForm.querySelector('.is-invalid');
                if (firstError) {
                    firstError.focus();
                }
            }
        });
    }

    // =====================================================================
    // LOGIN PAGE VALIDATION
    // =====================================================================

    function initLoginValidation() {
        var loginInput = document.getElementById('login_input');
        if (!loginInput) return; // Not on the login page

        var loginForm = loginInput.closest('form');
        if (!loginForm) return;

        var passwordInput = document.getElementById('password');

        // Sanitise login inputs too
        sanitizeInput(loginInput);

        var loginFeedback = ensureFeedbackSpan(loginInput, 'loginInputFeedback');
        var passwordFeedback = passwordInput ? ensureFeedbackSpan(passwordInput, 'loginPasswordFeedback') : null;

        function validateLoginInput() {
            var value = loginInput.value.trim();
            if (!value) {
                setMessage(loginFeedback, 'This field is required.', 'error');
                markInput(loginInput, false);
                return false;
            }
            setMessage(loginFeedback, '', '');
            markInput(loginInput, true);
            return true;
        }

        function validateLoginPassword() {
            if (!passwordInput) return true;

            var value = passwordInput.value;
            if (!value) {
                setMessage(passwordFeedback, 'This field is required.', 'error');
                markInput(passwordInput, false);
                return false;
            }
            setMessage(passwordFeedback, '', '');
            markInput(passwordInput, true);
            return true;
        }

        loginInput.addEventListener('blur', validateLoginInput);
        if (passwordInput) {
            passwordInput.addEventListener('blur', validateLoginPassword);
        }

        loginForm.addEventListener('submit', function (event) {
            var isLoginValid = validateLoginInput();
            var isPasswordValid = validateLoginPassword();

            if (!isLoginValid || !isPasswordValid) {
                event.preventDefault();
                var firstError = loginForm.querySelector('.is-invalid');
                if (firstError) {
                    firstError.focus();
                }
            }
        });
    }

    // =====================================================================
    // INITIALIZE ON DOM READY
    // =====================================================================
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
            initSignupValidation();
            initLoginValidation();
        });
    } else {
        initSignupValidation();
        initLoginValidation();
    }
})();
