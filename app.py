from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import datetime
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
DATABASE = 'expense_tracker.db'

# Create uploads folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY NOT NULL,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            phone_number TEXT UNIQUE NOT NULL,
            upi_id TEXT NOT NULL,
            password TEXT NOT NULL,
            profile_pic_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS friend_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_name TEXT NOT NULL,
            receiver_name TEXT NOT NULL,
            status TEXT CHECK(status IN ('pending', 'accepted', 'rejected')) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            responded_at TIMESTAMP,
            FOREIGN KEY (sender_name) REFERENCES users(username),
            FOREIGN KEY (receiver_name) REFERENCES users(username),
            UNIQUE(sender_name, receiver_name)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS friends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            friend_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_name) REFERENCES users(username),
            FOREIGN KEY (friend_name) REFERENCES users(username),
            UNIQUE(user_name, friend_name)
        )
    ''')
    conn.commit()
    conn.close()


# ============= HELPER FUNCTIONS =============

def get_user_friends(username):
    """Get list of friends for a user"""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT friend_name FROM friends WHERE user_name = ?', (username,))
    friends = [row['friend_name'] for row in c.fetchall()]
    conn.close()
    return friends


def search_non_friends(username, search_term):
    """Search for users who are not friends, prioritizing existing friends"""
    conn = get_db()
    c = conn.cursor()
    
    # Get current friends
    c.execute('SELECT friend_name FROM friends WHERE user_name = ?', (username,))
    friends = [row['friend_name'] for row in c.fetchall()]
    
    # Search for users matching search term (excluding self)
    search_pattern = f"%{search_term}%"
    c.execute('''
        SELECT username, full_name, profile_pic_url FROM users 
        WHERE (username LIKE ? OR full_name LIKE ?) AND username != ?
        ORDER BY username
    ''', (search_pattern, search_pattern, username))
    
    all_users = c.fetchall()
    conn.close()
    
    # Prioritize friends, then non-friends
    results = []
    for user in all_users:
        if user['username'] in friends:
            results.append({
                'username': user['username'],
                'full_name': user['full_name'],
                'profile_pic_url': user['profile_pic_url'],
                'is_friend': True
            })
    
    for user in all_users:
        if user['username'] not in friends:
            results.append({
                'username': user['username'],
                'full_name': user['full_name'],
                'profile_pic_url': user['profile_pic_url'],
                'is_friend': False
            })
    
    return results[:5]  # Return top 5 results


def get_friend_request_status(sender, receiver):
    """Get friend request status between two users"""
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT status FROM friend_requests 
        WHERE (sender_name = ? AND receiver_name = ?) 
           OR (sender_name = ? AND receiver_name = ?)
    ''', (sender, receiver, receiver, sender))
    result = c.fetchone()
    conn.close()
    return result['status'] if result else None


def send_friend_request(sender, receiver):
    """Send a friend request"""
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO friend_requests (sender_name, receiver_name, status, created_at)
            VALUES (?, ?, 'pending', ?)
        ''', (sender, receiver, datetime.now()))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def accept_friend_request(sender, receiver):
    """Accept a friend request and create bidirectional friendship"""
    conn = get_db()
    c = conn.cursor()
    try:
        # Update friend request status
        c.execute('''
            UPDATE friend_requests 
            SET status = 'accepted', responded_at = ?
            WHERE sender_name = ? AND receiver_name = ?
        ''', (datetime.now(), sender, receiver))
        
        # Create bidirectional friendship
        c.execute('''
            INSERT INTO friends (user_name, friend_name, created_at)
            VALUES (?, ?, ?)
        ''', (sender, receiver, datetime.now()))
        
        c.execute('''
            INSERT INTO friends (user_name, friend_name, created_at)
            VALUES (?, ?, ?)
        ''', (receiver, sender, datetime.now()))
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.rollback()
        conn.close()
        return False


def reject_friend_request(sender, receiver):
    """Reject a friend request"""
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('''
            UPDATE friend_requests 
            SET status = 'rejected', responded_at = ?
            WHERE sender_name = ? AND receiver_name = ?
        ''', (datetime.now(), sender, receiver))
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False


@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        username = request.form.get('username', '').strip()
        full_name = request.form.get('full_name', '').strip()
        phone_number = request.form.get('phone_number', '').strip()
        upi_id = request.form.get('upi_id', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not all([email, username, full_name, phone_number, upi_id, password, confirm_password]):
            flash('All fields are required (except profile picture)!', 'error')
            return redirect(url_for('signup'))
        
        if password != confirm_password:
            flash('Password and confirm password do not match!', 'error')
            return redirect(url_for('signup'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long!', 'error')
            return redirect(url_for('signup'))
        
        # Check if username, email, or phone already exists
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT username FROM users WHERE username = ?', (username,))
        if c.fetchone():
            flash('Username already exists! Please choose a different username.', 'error')
            conn.close()
            return redirect(url_for('signup'))
        
        c.execute('SELECT username FROM users WHERE email = ?', (email,))
        if c.fetchone():
            flash('Email already registered! Please use a different email.', 'error')
            conn.close()
            return redirect(url_for('signup'))
        
        c.execute('SELECT username FROM users WHERE phone_number = ?', (phone_number,))
        if c.fetchone():
            flash('Phone number already registered! Please use a different phone number.', 'error')
            conn.close()
            return redirect(url_for('signup'))
        
        conn.close()
        
        # Handle file upload
        profile_pic_url = None
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to filename to make it unique
                filename = f"{int(datetime.now().timestamp())}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                profile_pic_url = f"/uploads/{filename}"
            elif file and file.filename != '':
                flash('Invalid file type. Only png, jpg, jpeg, gif are allowed!', 'error')
                return redirect(url_for('signup'))
        
        try:
            conn = get_db()
            c = conn.cursor()
            hashed_password = generate_password_hash(password)
            c.execute('''
                INSERT INTO users (username, email, full_name, phone_number, upi_id, password, profile_pic_url, created_at, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (username, email, full_name, phone_number, upi_id, hashed_password, profile_pic_url, datetime.now(), None))
            conn.commit()
            conn.close()
            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError as e:
            flash('An error occurred during registration. Please try again.', 'error')
            return redirect(url_for('signup'))
    
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_input = request.form.get('login_input', '').strip()
        password = request.form.get('password', '')
        
        if not login_input or not password:
            flash('Username/Email and password are required!', 'error')
            return redirect(url_for('login'))
        
        conn = get_db()
        c = conn.cursor()
        
        # Check if input is email or username
        c.execute('SELECT * FROM users WHERE username = ? OR email = ?', (login_input, login_input))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['username']
            session['username'] = user['username']
            session['email'] = user['email']
            flash(f'Welcome {user["username"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username/email or password!', 'error')
            return redirect(url_for('login'))
    
    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (session['user_id'],))
    user = c.fetchone()
    conn.close()
    
    return render_template('dashboard.html', user=user)


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out!', 'success')
    return redirect(url_for('login'))


@app.route('/friends')
def friends():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor()
    
    username = session['user_id']
    
    # Get all friends with their details
    c.execute('''
        SELECT u.username, u.full_name, u.profile_pic_url, f.created_at
        FROM friends f
        JOIN users u ON f.friend_name = u.username
        WHERE f.user_name = ?
        ORDER BY f.created_at DESC
    ''', (username,))
    friends_list = c.fetchall()
    
    # Get pending friend requests (received)
    c.execute('''
        SELECT sender_name, created_at FROM friend_requests
        WHERE receiver_name = ? AND status = 'pending'
        ORDER BY created_at DESC
    ''', (username,))
    pending_requests = c.fetchall()
    
    # Get sent friend requests (pending)
    c.execute('''
        SELECT receiver_name, created_at FROM friend_requests
        WHERE sender_name = ? AND status = 'pending'
        ORDER BY created_at DESC
    ''', (username,))
    sent_requests = c.fetchall()
    
    conn.close()
    
    return render_template('friends.html', 
                         friends=friends_list, 
                         pending_requests=pending_requests,
                         sent_requests=sent_requests)


@app.route('/api/search-users', methods=['POST'])
def search_users():
    if 'user_id' not in session:
        return {'error': 'Not logged in'}, 401
    
    search_term = request.json.get('search_term', '').strip()
    username = session['user_id']
    
    if not search_term:
        return {'results': []}, 200
    
    results = search_non_friends(username, search_term)
    
    # Add request status for each user
    for user in results:
        status = get_friend_request_status(username, user['username'])
        user['request_status'] = status
    
    return {'results': results}, 200


@app.route('/api/send-friend-request', methods=['POST'])
def send_request():
    if 'user_id' not in session:
        return {'error': 'Not logged in'}, 401
    
    receiver = request.json.get('receiver_name', '').strip()
    sender = session['user_id']
    
    if not receiver or sender == receiver:
        return {'error': 'Invalid receiver'}, 400
    
    # Check if already friends
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM friends WHERE user_name = ? AND friend_name = ?', (sender, receiver))
    if c.fetchone():
        conn.close()
        return {'error': 'Already friends'}, 400
    conn.close()
    
    if send_friend_request(sender, receiver):
        return {'success': True, 'message': 'Friend request sent'}, 200
    else:
        return {'error': 'Request already sent or user does not exist'}, 400


@app.route('/api/accept-friend-request', methods=['POST'])
def accept_request():
    if 'user_id' not in session:
        return {'error': 'Not logged in'}, 401
    
    sender = request.json.get('sender_name', '').strip()
    receiver = session['user_id']
    
    if accept_friend_request(sender, receiver):
        return {'success': True, 'message': 'Friend request accepted'}, 200
    else:
        return {'error': 'Could not accept request'}, 400


@app.route('/api/reject-friend-request', methods=['POST'])
def reject_request():
    if 'user_id' not in session:
        return {'error': 'Not logged in'}, 401
    
    sender = request.json.get('sender_name', '').strip()
    receiver = session['user_id']
    
    if reject_friend_request(sender, receiver):
        return {'success': True, 'message': 'Friend request rejected'}, 200
    else:
        return {'error': 'Could not reject request'}, 400


@app.route('/api/get-friends', methods=['GET'])
def get_friends_api():
    if 'user_id' not in session:
        return {'error': 'Not logged in'}, 401
    
    username = session['user_id']
    conn = get_db()
    c = conn.cursor()
    
    c.execute('''
        SELECT u.username, u.full_name, u.profile_pic_url, f.created_at
        FROM friends f
        JOIN users u ON f.friend_name = u.username
        WHERE f.user_name = ?
        ORDER BY f.created_at DESC
    ''', (username,))
    
    friends_list = []
    for row in c.fetchall():
        friends_list.append({
            'username': row['username'],
            'full_name': row['full_name'],
            'profile_pic_url': row['profile_pic_url'],
            'created_at': row['created_at']
        })
    
    conn.close()
    return {'friends': friends_list}, 200


if __name__ == '__main__':
    init_db()
    app.run(debug=True)