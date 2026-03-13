(function () {
    const form = document.querySelector('form[enctype="multipart/form-data"]');
    if (!form) {
        return;
    }

    const phoneInput = document.getElementById('phone_number');
    const upiInput = document.getElementById('upi_id');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm_password');

    const phoneFeedback = document.getElementById('phoneFeedback');
    const upiFeedback = document.getElementById('upiFeedback');
    const passwordFeedback = document.getElementById('passwordFeedback');

    const phoneRegex = /^\d{10}$/;
    const upiRegex = /^[a-zA-Z0-9._-]{2,256}@[a-zA-Z]{2,64}$/;

    function setMessage(target, message, type) {
        target.textContent = message;
        target.classList.remove('error', 'success');
        if (type) {
            target.classList.add(type);
        }
    }

    function markInput(input, valid) {
        input.classList.remove('is-valid', 'is-invalid');
        input.classList.add(valid ? 'is-valid' : 'is-invalid');
    }

    function validatePhone() {
        const value = phoneInput.value.trim();
        const valid = phoneRegex.test(value);

        if (!value) {
            setMessage(phoneFeedback, 'Phone number is required.', 'error');
            markInput(phoneInput, false);
            return false;
        }

        if (!valid) {
            setMessage(phoneFeedback, 'Enter exactly 10 digits.', 'error');
            markInput(phoneInput, false);
            return false;
        }

        setMessage(phoneFeedback, 'Phone number looks good.', 'success');
        markInput(phoneInput, true);
        return true;
    }

    function validateUpi() {
        const value = upiInput.value.trim();
        const valid = upiRegex.test(value);

        if (!value) {
            setMessage(upiFeedback, 'UPI ID is required.', 'error');
            markInput(upiInput, false);
            return false;
        }

        if (!valid) {
            setMessage(upiFeedback, 'Use format like name@bank.', 'error');
            markInput(upiInput, false);
            return false;
        }

        setMessage(upiFeedback, 'UPI ID format is valid.', 'success');
        markInput(upiInput, true);
        return true;
    }

    function validatePasswords() {
        const password = passwordInput.value;
        const confirmPassword = confirmPasswordInput.value;

        if (!confirmPassword) {
            setMessage(passwordFeedback, 'Please re-enter password for confirmation.', 'error');
            markInput(confirmPasswordInput, false);
            return false;
        }

        if (password.length < 6) {
            setMessage(passwordFeedback, 'Password must be at least 6 characters.', 'error');
            markInput(passwordInput, false);
            markInput(confirmPasswordInput, false);
            return false;
        }

        if (password !== confirmPassword) {
            setMessage(passwordFeedback, 'Passwords do not match.', 'error');
            markInput(confirmPasswordInput, false);
            return false;
        }

        setMessage(passwordFeedback, 'Passwords match.', 'success');
        markInput(passwordInput, true);
        markInput(confirmPasswordInput, true);
        return true;
    }

    phoneInput.addEventListener('input', validatePhone);
    upiInput.addEventListener('input', validateUpi);
    passwordInput.addEventListener('input', validatePasswords);
    confirmPasswordInput.addEventListener('input', validatePasswords);

    form.addEventListener('submit', function (event) {
        const isPhoneValid = validatePhone();
        const isUpiValid = validateUpi();
        const arePasswordsValid = validatePasswords();

        if (!isPhoneValid || !isUpiValid || !arePasswordsValid) {
            event.preventDefault();
        }
    });
})();
