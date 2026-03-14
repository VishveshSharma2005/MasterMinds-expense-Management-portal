"""
============================================================================
validation.py — Splitsmart Backend Validation Module
============================================================================

Secure server-side validation for Sign-Up and Login.
Uses bcrypt for password hashing (install: pip install bcrypt).
This file is intentionally SEPARATE from app.py to avoid merge conflicts.

SIGN-UP:
    - sanitize_input()           → strips < > to prevent XSS
    - validate_name()            → letters, spaces, hyphens, apostrophes only
    - validate_username()        → alphanumeric + underscores, 3-30 chars
    - validate_email_format()   → regex email check
    - check_email_exists()      → queries SQLite for duplicate email
    - validate_password_strength() → min 8 chars, 1 number, 1 special char
    - hash_password_bcrypt()    → hashes with bcrypt
    - validate_signup()         → orchestrates all checks, returns errors list

LOGIN:
    - verify_credentials()      → safe credential check with bcrypt
                                  Returns generic "Invalid email or password"

HOW TO INTEGRATE WITH app.py:
    In your signup route, replace the validation section with:

        from validation import validate_signup, hash_password_bcrypt

        errors = validate_signup(email, password, confirm_password)
        if errors:
            for err in errors:
                flash(err, 'error')
            return redirect(url_for('signup'))

        hashed = hash_password_bcrypt(password)
        # Use 'hashed' when inserting into the DB instead of
        # generate_password_hash(password)

    In your login route:

        from validation import verify_credentials

        user, error = verify_credentials(login_input, password)
        if error:
            flash(error, 'error')
            return redirect(url_for('login'))
        # 'user' is the sqlite3.Row for the authenticated user

============================================================================
"""

import re
import sqlite3
import bcrypt

# ---------------------------------------------------------------------------
# Configuration — must match the DATABASE path used in app.py
# ---------------------------------------------------------------------------
DATABASE = 'expense_tracker.db'


# ---------------------------------------------------------------------------
# Input Sanitisation — strip HTML-dangerous characters from any string input
# ---------------------------------------------------------------------------
def sanitize_input(value):
    """
    Remove < and > characters from user input to prevent XSS/HTML injection.

    Args:
        value (str): Raw user input.

    Returns:
        str: Sanitised string with < > removed.
    """
    if not value:
        return value
    return re.sub(r'[<>]', '', value)


def _get_db():
    """
    Open a connection to the SQLite database.
    Returns a connection with Row factory for dict-like access.
    """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ===========================================================================
# SIGN-UP VALIDATION
# ===========================================================================

def validate_email_format(email):
    """
    Check if an email string matches a standard format.

    Args:
        email (str): The email address to validate.

    Returns:
        str or None: An error message if invalid, None if valid.

    Example:
        >>> validate_email_format('bad-email')
        'Please enter a valid email address.'
        >>> validate_email_format('user@example.com')
        None
    """
    # Strict pattern: local@domain.tld
    #   local:  letters, digits, . _ % + -
    #   domain: letters, digits, . - (at least 2-char segment before dot)
    #   TLD:    2-10 letters
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9]([a-zA-Z0-9.\-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,10}$'

    if not email or not email.strip():
        return 'Email address is required.'

    if not re.match(pattern, email.strip()):
        return 'Please enter a valid email address (e.g. user@example.com).'

    return None


def validate_name(name):
    """
    Validate that a name contains only letters, spaces, hyphens, and
    apostrophes (for names like O'Brien or Mary-Jane).

    Args:
        name (str): The name to validate.

    Returns:
        str or None: An error message if invalid, None if valid.

    Example:
        >>> validate_name('John123')
        'Name must contain only letters, spaces, hyphens, or apostrophes.'
        >>> validate_name("Mary-Jane O'Brien")
        None
    """
    if not name or not name.strip():
        return 'Full name is required.'

    # Allow letters (including accented), spaces, hyphens, apostrophes
    pattern = r"^[a-zA-Z\u00C0-\u00FF\s'-]{2,}$"
    if not re.match(pattern, name.strip()):
        return 'Name must contain only letters, spaces, hyphens, or apostrophes.'

    return None


def validate_username(username):
    """
    Validate that a username contains only alphanumeric characters and
    underscores, and is 3-30 characters long.

    Args:
        username (str): The username to validate.

    Returns:
        str or None: An error message if invalid, None if valid.
    """
    if not username or not username.strip():
        return 'Username is required.'

    pattern = r'^[a-zA-Z0-9_]{3,30}$'
    if not re.match(pattern, username.strip()):
        return 'Username must be 3-30 characters: letters, numbers, and underscores only.'

    return None


def validate_upi_id(upi_id):
    """
    Validate an Indian UPI ID (Virtual Payment Address) per NPCI guidelines.

    Rules:
        - Must contain exactly one @ symbol
        - No whitespace allowed
        - Prefix (before @): 2–256 chars, alphanumeric + dot/hyphen/underscore
        - Suffix (after @):  2–64 chars, alphabetic only (bank/PSP handle)

    Args:
        upi_id (str): The UPI ID to validate.

    Returns:
        str or None: An error message if invalid, None if valid.

    Example:
        >>> validate_upi_id('name@bank')
        None
        >>> validate_upi_id('bad upi')
        'Please enter a valid UPI ID (e.g. name@bank).'
    """
    if not upi_id or not upi_id.strip():
        return 'UPI ID is required.'

    value = upi_id.strip()

    # No whitespace allowed
    if re.search(r'\s', value):
        return 'UPI ID must not contain spaces.'

    # Strict NPCI format: prefix@suffix
    pattern = r'^[a-zA-Z0-9._-]{2,256}@[a-zA-Z]{2,64}$'
    if not re.match(pattern, value):
        return 'Please enter a valid UPI ID (e.g. name@bank).'

    return None


def check_email_exists(email):
    """
    Query the database to see if an email is already registered.

    Args:
        email (str): The email address to look up.

    Returns:
        str or None: An error message if the email exists, None otherwise.
    """
    conn = _get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users WHERE email = ?', (email.strip(),))
    row = cursor.fetchone()
    conn.close()

    if row:
        return 'This email is already registered. Please use a different email or log in.'

    return None


def validate_password_strength(password):
    """
    Enforce password strength rules (server-side — never trust the client).

    Rules:
        - Minimum 8 characters
        - At least 1 numeric digit
        - At least 1 special character

    Args:
        password (str): The plaintext password to validate.

    Returns:
        list[str]: A list of error messages. Empty list means the password is strong.

    Example:
        >>> validate_password_strength('short')
        ['Password must be at least 8 characters long.',
         'Password must contain at least 1 number.',
         'Password must contain at least 1 special character (!@#$%...).']
        >>> validate_password_strength('Str0ng@Pass')
        []
    """
    errors = []

    if len(password) < 8:
        errors.append('Password must be at least 8 characters long.')

    if not re.search(r'[0-9]', password):
        errors.append('Password must contain at least 1 number.')

    if not re.search(r'[!@#$%^&*()\-_=+\[\]{};:\'",.<>?/\\|`~]', password):
        errors.append('Password must contain at least 1 special character (!@#$%...).')

    return errors


def hash_password_bcrypt(password):
    """
    Hash a plaintext password using bcrypt.

    Bcrypt automatically generates a salt and embeds it in the output hash,
    so there is no need to store the salt separately.

    Args:
        password (str): The plaintext password.

    Returns:
        str: The bcrypt hash string (safe to store in the database).

    Example:
        >>> hashed = hash_password_bcrypt('MyP@ss1')
        >>> hashed.startswith('$2b$')
        True
    """
    # Encode the password to bytes, then hash with a generated salt
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)  # 12 rounds is a good default for 2024+
    hashed = bcrypt.hashpw(password_bytes, salt)
    # Return as string for easy storage in TEXT columns
    return hashed.decode('utf-8')


def validate_signup(email, password, confirm_password, full_name=None, username=None):
    """
    Full sign-up validation pipeline (call this from your /signup route).

    Checks:
        1. Input sanitisation (strip < >)
        2. Valid email format
        3. Email not already registered
        4. Full name (letters only)
        5. Username (alphanumeric + underscores)
        6. Password strength
        7. Password confirmation match

    Args:
        email (str):            The user's email.
        password (str):         The chosen password.
        confirm_password (str): The confirmation password.
        full_name (str):        The user's full name (optional for backward compat).
        username (str):         The user's username (optional for backward compat).

    Returns:
        list[str]: A list of error messages. Empty list means all checks passed.
    """
    errors = []

    # 0. Sanitise inputs
    email = sanitize_input(email) if email else email
    full_name = sanitize_input(full_name) if full_name else full_name
    username = sanitize_input(username) if username else username

    # 1. Email format
    email_error = validate_email_format(email)
    if email_error:
        errors.append(email_error)
    else:
        # 2. Email uniqueness (only check DB if format is valid)
        dup_error = check_email_exists(email)
        if dup_error:
            errors.append(dup_error)

    # 3. Full name validation (if provided)
    if full_name is not None:
        name_error = validate_name(full_name)
        if name_error:
            errors.append(name_error)

    # 4. Username validation (if provided)
    if username is not None:
        username_error = validate_username(username)
        if username_error:
            errors.append(username_error)

    # 5. Password strength (server-side re-validation)
    strength_errors = validate_password_strength(password)
    errors.extend(strength_errors)

    # 6. Password match
    if password != confirm_password:
        errors.append('Password and confirm password do not match.')

    return errors


# ===========================================================================
# LOGIN VALIDATION
# ===========================================================================

def verify_credentials(login_input, password):
    """
    Securely verify login credentials against the database.

    SECURITY NOTES:
        - Returns a GENERIC error message ("Invalid email or password")
          so an attacker cannot determine whether the email/username exists.
        - Compares using bcrypt.checkpw() for timing-safe comparison.

    Args:
        login_input (str): The username or email entered by the user.
        password (str):    The plaintext password entered by the user.

    Returns:
        tuple: (user_row, error_message)
            - On success: (sqlite3.Row, None)
            - On failure: (None, 'Invalid email or password.')

    Usage in Flask route:
        user, error = verify_credentials(login_input, password)
        if error:
            flash(error, 'error')
            return redirect(url_for('login'))
        # Login successful — set session
        session['user_id'] = user['username']
    """
    GENERIC_ERROR = 'Invalid email or password.'

    if not login_input or not login_input.strip():
        return None, GENERIC_ERROR

    if not password:
        return None, GENERIC_ERROR

    conn = _get_db()
    cursor = conn.cursor()

    # Look up user by username OR email (same logic as existing app.py)
    cursor.execute(
        'SELECT * FROM users WHERE username = ? OR email = ?',
        (login_input.strip(), login_input.strip())
    )
    user = cursor.fetchone()
    conn.close()

    if not user:
        # User not found — return generic error (don't reveal that the user
        # doesn't exist)
        return None, GENERIC_ERROR

    try:
        # Compare supplied password with the stored bcrypt hash
        stored_hash = user['password']

        # Handle both bcrypt hashes ($2b$...) and werkzeug hashes
        if stored_hash.startswith('$2b$') or stored_hash.startswith('$2a$'):
            # Bcrypt hash — use bcrypt.checkpw
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                return user, None
            else:
                return None, GENERIC_ERROR
        else:
            # Likely a werkzeug hash (existing passwords) — fall back to
            # werkzeug's check_password_hash for backward compatibility
            from werkzeug.security import check_password_hash
            if check_password_hash(stored_hash, password):
                return user, None
            else:
                return None, GENERIC_ERROR
    except Exception:
        # Any unexpected error during hash comparison — generic error
        return None, GENERIC_ERROR


# ===========================================================================
# STANDALONE QUICK TEST
# ===========================================================================
# Run this file directly to verify that bcrypt and validation logic work:
#   python validation.py
#
if __name__ == '__main__':
    print('=== Splitsmart Validation Module - Quick Self-Test ===\n')

    # Test 1: Email validation
    print('1. Email validation:')
    print(f'   "bad-email"   => {validate_email_format("bad-email")}')
    print(f'   "user@ex.com" => {validate_email_format("user@ex.com")}')

    # Test 2: Password strength
    print('\n2. Password strength:')
    print(f'   "weak"        => {validate_password_strength("weak")}')
    print(f'   "Str0ng@Pass" => {validate_password_strength("Str0ng@Pass")}')

    # Test 3: Bcrypt hashing
    print('\n3. Bcrypt hashing:')
    test_hash = hash_password_bcrypt('TestP@ss1')
    print(f'   hash("TestP@ss1") = {test_hash}')
    # Verify the hash
    matches = bcrypt.checkpw('TestP@ss1'.encode('utf-8'), test_hash.encode('utf-8'))
    print(f'   Verify correct pw  => {matches}')
    wrong = bcrypt.checkpw('WrongPassword'.encode('utf-8'), test_hash.encode('utf-8'))
    print(f'   Verify wrong pw    => {wrong}')

    # Test 4: Full signup validation
    print('\n4. Full signup validation:')
    errs = validate_signup('bad', 'short', 'different')
    print(f'   validate_signup("bad", "short", "different") => {errs}')
    errs2 = validate_signup('a@b.com', 'Str0ng@Pass', 'Str0ng@Pass')
    print(f'   validate_signup("a@b.com", "Str0ng@Pass", "Str0ng@Pass") => {errs2}')

    print('\nAll self-tests completed.')
