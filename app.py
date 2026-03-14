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
    c.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            group_id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT NOT NULL,
            description TEXT,
            currency TEXT CHECK(currency IN ('USD', 'INR', 'GBP', 'EUR', 'AUD')) DEFAULT 'INR',
            created_by TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            invite_token TEXT UNIQUE,
            FOREIGN KEY (created_by) REFERENCES users(username)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS groups_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            user_id TEXT NOT NULL,
            role TEXT CHECK(role IN ('creator', 'member')) DEFAULT 'member',
            joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (group_id) REFERENCES groups(group_id),
            FOREIGN KEY (user_id) REFERENCES users(username),
            UNIQUE(group_id, user_id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS groups_invitation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            invite_token TEXT UNIQUE NOT NULL,
            status TEXT CHECK(status IN ('pending', 'accepted', 'rejected')) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expire_at TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES groups(group_id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            paid_by TEXT NOT NULL,
            split_type TEXT CHECK(split_type IN ('EQUAL', 'EXACT', 'PERCENTAGE')) DEFAULT 'EQUAL',
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            category TEXT,
            receipt_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES groups(group_id),
            FOREIGN KEY (paid_by) REFERENCES users(username)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS expense_splits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expense_id INTEGER NOT NULL,
            user_id TEXT NOT NULL,
            amount_owed REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (expense_id) REFERENCES expenses(id),
            FOREIGN KEY (user_id) REFERENCES users(username),
            UNIQUE(expense_id, user_id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            expense_id INTEGER,
            payer_id TEXT NOT NULL,
            payee_id TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT CHECK(status IN ('PENDING', 'COMPLETED')) DEFAULT 'PENDING',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES groups(group_id),
            FOREIGN KEY (expense_id) REFERENCES expenses(id),
            FOREIGN KEY (payer_id) REFERENCES users(username),
            FOREIGN KEY (payee_id) REFERENCES users(username)
        )
    ''')
    
    # Migration: Add missing amount_owed column if it doesn't exist
    try:
        c.execute("PRAGMA table_info(expense_splits)")
        columns = [column[1] for column in c.fetchall()]
        if 'amount_owed' not in columns:
            c.execute("ALTER TABLE expense_splits ADD COLUMN amount_owed REAL NOT NULL DEFAULT 0")
    except Exception as e:
        print(f"Migration check failed: {e}")
    
    conn.commit()
    conn.close()


# ==================== ADVANCED GREEDY SETTLEMENT ALGORITHM ====================
def calculate_group_balances(group_id):
    """
    Calculate net balance for each group member.
    Returns: {username: balance} where positive = owed to them, negative = they owe
    """
    conn = get_db()
    c = conn.cursor()
    
    balances = {}
    
    # Initialize all members to 0
    c.execute("SELECT user_id FROM groups_members WHERE group_id = ? AND is_active = 1", (group_id,))
    for member in c.fetchall():
        balances[member['user_id']] = 0.0
    
    # Add what each person paid (positive for them)
    c.execute("""
        SELECT paid_by, SUM(amount) as total 
        FROM expenses 
        WHERE group_id = ? 
        GROUP BY paid_by
    """, (group_id,))
    
    for row in c.fetchall():
        balances[row['paid_by']] = balances.get(row['paid_by'], 0) + row['total']
    
    # Subtract what each person owes (negative for them)
    c.execute("""
        SELECT es.user_id, SUM(es.amount_owed) as total
        FROM expense_splits es
        JOIN expenses e ON e.id = es.expense_id
        WHERE e.group_id = ?
        GROUP BY es.user_id
    """, (group_id,))
    
    for row in c.fetchall():
        balances[row['user_id']] = balances.get(row['user_id'], 0) - row['total']
    
    conn.close()
    return {k: round(v, 2) for k, v in balances.items() if abs(v) > 0.01}


def advanced_greedy_settlement(group_id):
    """
    Calculate optimal payment settlements using Advanced Greedy Algorithm.
    Minimizes number of transactions needed to settle all debts.
    Creates COMPLETED transaction records in the ledger.
    """
    conn = get_db()
    c = conn.cursor()
    
    balances = calculate_group_balances(group_id)
    
    # Greedy settlement algorithm
    settlements = []
    balance_list = [(person, bal) for person, bal in balances.items() if abs(bal) > 0.01]
    
    while balance_list:
        # Sort by balance - creditors (positive) first, then debtors (negative)
        balance_list.sort(key=lambda x: x[1], reverse=True)
        
        # Get largest creditor and largest debtor
        largest_creditor = balance_list[0]
        largest_debtor = balance_list[-1]
        
        # Minimum amount to settle
        settlement_amount = min(largest_creditor[1], -largest_debtor[1])
        settlement_amount = round(settlement_amount, 2)
        
        if settlement_amount > 0.01:
            settlements.append({
                'from': largest_debtor[0],
                'to': largest_creditor[0],
                'amount': settlement_amount
            })
            
            # Create COMPLETED transaction record
            try:
                c.execute("""
                    INSERT INTO transactions (group_id, payer_id, payee_id, amount, status)
                    VALUES (?, ?, ?, ?, 'COMPLETED')
                """, (group_id, largest_debtor[0], largest_creditor[0], settlement_amount))
            except:
                pass  # Ignore if transaction already exists
        
        # Update balances
        new_balance_list = []
        for person, bal in balance_list:
            if person == largest_creditor[0]:
                new_bal = bal - settlement_amount
            elif person == largest_debtor[0]:
                new_bal = bal + settlement_amount
            else:
                new_bal = bal
            
            if abs(new_bal) > 0.01:  # Only keep non-zero balances
                new_balance_list.append((person, new_bal))
        
        balance_list = new_balance_list
    
    conn.commit()
    conn.close()
    
    return settlements, balances


# ==================== GROUP HELPER FUNCTIONS ====================
def generate_invite_token():
    """Generate unique invite token"""
    import secrets
    return secrets.token_urlsafe(16)


def get_user_groups(username):
    """Get all groups for a user"""
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT g.group_id, g.group_name, g.currency, g.created_by, g.created_at,
               g.invite_token, COUNT(gm.user_id) as member_count
        FROM groups g
        JOIN groups_members gm ON g.group_id = gm.group_id
        WHERE gm.user_id = ? AND gm.is_active = 1
        GROUP BY g.group_id
        ORDER BY g.created_at DESC
    """, (username,))
    
    groups = []
    for row in c.fetchall():
        groups.append({
            'group_id': row['group_id'],
            'group_name': row['group_name'],
            'currency': row['currency'],
            'created_by': row['created_by'],
            'created_at': row['created_at'],
            'invite_token': row['invite_token'],
            'member_count': row['member_count']
        })
    
    conn.close()
    return groups


def get_group_details(group_id, username):
    """Get detailed group info - verify user has access"""
    conn = get_db()
    c = conn.cursor()
    
    # Verify access
    c.execute("""
        SELECT gm.role FROM groups_members gm
        WHERE gm.group_id = ? AND gm.user_id = ?
    """, (group_id, username))
    
    access = c.fetchone()
    if not access:
        conn.close()
        return None
    
    # Get group info
    c.execute("""
        SELECT group_id, group_name, description, currency, created_by, created_at
        FROM groups
        WHERE group_id = ?
    """, (group_id,))
    
    group = c.fetchone()
    if not group:
        conn.close()
        return None
    
    # Get members
    c.execute("""
        SELECT user_id, role, joined_at
        FROM groups_members
        WHERE group_id = ? AND is_active = 1
        ORDER BY joined_at
    """, (group_id,))
    
    members = [{'user_id': m['user_id'], 'role': m['role'], 'joined_at': m['joined_at']} for m in c.fetchall()]
    
    conn.close()
    
    return {
        'group_id': group['group_id'],
        'group_name': group['group_name'],
        'description': group['description'],
        'currency': group['currency'],
        'created_by': group['created_by'],
        'created_at': group['created_at'],
        'members': members,
        'user_role': access['role']
    }


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


# ============= GROUP ROUTES =============

@app.route('/groups')
def groups_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_groups = get_user_groups(session['user_id'])
    return render_template('groups.html', groups=user_groups)


@app.route('/groups/<int:group_id>')
def group_detail(group_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    group = get_group_details(group_id, session['user_id'])
    if not group:
        flash('Group not found or you do not have access', 'error')
        return redirect(url_for('groups_dashboard'))
    
    conn = get_db()
    c = conn.cursor()
    
    # Get expenses
    c.execute("""
        SELECT id, paid_by, amount, name AS description, created_at, split_type AS split_method
        FROM expenses
        WHERE group_id = ?
        ORDER BY created_at DESC
    """, (group_id,))
    
    expenses = [
        {
            'id': row['id'],
            'paid_by': row['paid_by'],
            'amount': row['amount'],
            'description': row['description'],
            'created_at': row['created_at'],
            'split_method': row['split_method']
        }
        for row in c.fetchall()
    ]
    
    # Get settlement info
    settlements, balances = advanced_greedy_settlement(group_id)
    
    conn.close()
    
    return render_template('group_detail.html', 
                         group=group, 
                         expenses=expenses,
                         settlements=settlements,
                         balances=balances)


@app.route('/groups/create')
def create_group():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor()
    
    # Get friends
    c.execute('''
        SELECT friend_name, full_name FROM friends f
        JOIN users u ON f.friend_name = u.username
        WHERE f.user_name = ?
        ORDER BY u.full_name
    ''', (session['user_id'],))
    
    friends = [{'username': row['friend_name'], 'full_name': row['full_name']} for row in c.fetchall()]
    conn.close()
    
    return render_template('create_group.html', friends=friends)


# ============= GROUP API ROUTES =============

@app.route('/api/groups', methods=['GET'])
def api_get_groups():
    if 'user_id' not in session:
        return {'error': 'Not logged in'}, 401
    
    groups = get_user_groups(session['user_id'])
    return {'groups': groups}, 200


@app.route('/api/groups', methods=['POST'])
def api_create_group():
    if 'user_id' not in session:
        return {'error': 'Not logged in'}, 401
    
    data = request.json
    group_name = data.get('group_name', '').strip()
    description = data.get('description', '').strip()
    currency = data.get('currency', 'INR')
    initial_members = data.get('initial_members', [])  # List of usernames
    
    if not group_name:
        return {'error': 'Group name is required'}, 400
    
    if currency not in ['USD', 'INR', 'GBP', 'EUR', 'AUD']:
        return {'error': 'Invalid currency'}, 400
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        invite_token = generate_invite_token()
        
        # Create group
        c.execute("""
            INSERT INTO groups (group_name, description, currency, created_by, invite_token)
            VALUES (?, ?, ?, ?, ?)
        """, (group_name, description, currency, session['user_id'], invite_token))
        
        group_id = c.lastrowid
        
        # Add creator as member (role: creator)
        c.execute("""
            INSERT INTO groups_members (group_id, user_id, role, is_active)
            VALUES (?, ?, 'creator', 1)
        """, (group_id, session['user_id']))
        
        # Add initial members
        for member_username in initial_members:
            if member_username and member_username != session['user_id']:
                try:
                    c.execute("""
                        INSERT INTO groups_members (group_id, user_id, role, is_active)
                        VALUES (?, ?, 'member', 1)
                    """, (group_id, member_username))
                except sqlite3.IntegrityError:
                    pass  # Skip if user already in group
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'group_id': group_id,
            'invite_token': invite_token,
            'message': 'Group created successfully'
        }, 201
    
    except Exception as e:
        conn.rollback()
        conn.close()
        return {'error': str(e)}, 500


@app.route('/api/groups/<int:group_id>', methods=['GET'])
def api_get_group(group_id):
    if 'user_id' not in session:
        return {'error': 'Not logged in'}, 401
    
    group = get_group_details(group_id, session['user_id'])
    if not group:
        return {'error': 'Group not found'}, 404
    
    return {'group': group}, 200


@app.route('/api/groups/<int:group_id>/members', methods=['POST'])
def api_add_group_member(group_id):
    if 'user_id' not in session:
        return {'error': 'Not logged in'}, 401
    
    data = request.json
    username = data.get('username', '').strip()
    
    if not username:
        return {'error': 'Username is required'}, 400
    
    conn = get_db()
    c = conn.cursor()
    
    # Verify requester is creator
    c.execute("""
        SELECT role FROM groups_members
        WHERE group_id = ? AND user_id = ?
    """, (group_id, session['user_id']))
    
    access = c.fetchone()
    if not access or access['role'] != 'creator':
        conn.close()
        return {'error': 'Only group creator can add members'}, 403
    
    # Check user exists
    c.execute("SELECT username FROM users WHERE username = ?", (username,))
    if not c.fetchone():
        conn.close()
        return {'error': 'User not found'}, 404
    
    try:
        c.execute("""
            INSERT INTO groups_members (group_id, user_id, role, is_active)
            VALUES (?, ?, 'member', 1)
        """, (group_id, username))
        conn.commit()
        conn.close()
        
        return {'success': True, 'message': 'Member added successfully'}, 201
    
    except sqlite3.IntegrityError:
        conn.close()
        return {'error': 'User already in group'}, 400


@app.route('/api/groups/<int:group_id>/expenses', methods=['GET'])
def api_get_expenses(group_id):
    if 'user_id' not in session:
        return {'error': 'Not logged in'}, 401
    
    conn = get_db()
    c = conn.cursor()
    
    # Verify access
    c.execute("""
        SELECT role FROM groups_members
        WHERE group_id = ? AND user_id = ?
    """, (group_id, session['user_id']))
    
    if not c.fetchone():
        conn.close()
        return {'error': 'Access denied'}, 403
    
    # Get expenses
    c.execute("""
        SELECT id, paid_by, amount, name, category, created_at, split_type, receipt_url
        FROM expenses
        WHERE group_id = ?
        ORDER BY created_at DESC
    """, (group_id,))
    
    expenses = []
    for row in c.fetchall():
        # Get splits for this expense
        c.execute("""
            SELECT user_id, amount_owed
            FROM expense_splits
            WHERE expense_id = ?
        """, (row['id'],))
        
        splits = [
            {'user_id': s['user_id'], 'amount': s['amount_owed']}
            for s in c.fetchall()
        ]
        
        expenses.append({
            'id': row['id'],
            'paid_by': row['paid_by'],
            'amount': row['amount'],
            'name': row['name'],
            'category': row['category'],
            'created_at': row['created_at'],
            'split_type': row['split_type'],
            'receipt_url': row['receipt_url'],
            'splits': splits
        })
    
    conn.close()
    return {'expenses': expenses}, 200


@app.route('/api/groups/<int:group_id>/expenses', methods=['POST'])
def api_create_expense(group_id):
    if 'user_id' not in session:
        return {'error': 'Not logged in'}, 401
    
    data = request.json
    amount = data.get('amount')
    name = data.get('name', '').strip()
    category = data.get('category', '').strip()
    split_type = data.get('split_type', 'EQUAL').upper()
    splits = data.get('splits', {})  # Dict of {username: amount/percentage}
    
    # Validate
    if not amount or amount <= 0:
        return {'error': 'Invalid amount'}, 400
    
    if not name:
        return {'error': 'Expense name is required'}, 400
    
    if split_type not in ['EQUAL', 'EXACT', 'PERCENTAGE']:
        return {'error': 'Invalid split type'}, 400
    
    conn = get_db()
    c = conn.cursor()
    
    # Verify access
    c.execute("""
        SELECT role FROM groups_members
        WHERE group_id = ? AND user_id = ?
    """, (group_id, session['user_id']))
    
    if not c.fetchone():
        conn.close()
        return {'error': 'Access denied'}, 403
    
    try:
        # Get group members
        c.execute("""
            SELECT user_id FROM groups_members
            WHERE group_id = ? AND is_active = 1
        """, (group_id,))
        
        members = [m['user_id'] for m in c.fetchall()]
        
        if not members:
            conn.close()
            return {'error': 'Group has no members'}, 400
        
        # Create expense
        c.execute("""
            INSERT INTO expenses (group_id, paid_by, amount, name, category, split_type)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (group_id, session['user_id'], amount, name, category, split_type))
        
        expense_id = c.lastrowid
        
        # Create splits and transactions
        if split_type == 'EQUAL':
            split_amount = amount / len(members)
            for member in members:
                c.execute("""
                    INSERT INTO expense_splits (expense_id, user_id, amount_owed)
                    VALUES (?, ?, ?)
                """, (expense_id, member, split_amount))
                
                # Create PENDING transaction record
                if member != session['user_id']:
                    c.execute("""
                        INSERT INTO transactions (group_id, expense_id, payer_id, payee_id, amount, status)
                        VALUES (?, ?, ?, ?, ?, 'PENDING')
                    """, (group_id, expense_id, member, session['user_id'], split_amount))
        
        elif split_type == 'PERCENTAGE':
            total_percentage = sum(float(splits.get(m, 0)) for m in members)
            if abs(total_percentage - 100) > 0.01:
                raise ValueError('Percentages must sum to 100')
            
            for member in members:
                percentage = float(splits.get(member, 0))
                split_amount = (amount * percentage) / 100
                c.execute("""
                    INSERT INTO expense_splits (expense_id, user_id, amount_owed)
                    VALUES (?, ?, ?)
                """, (expense_id, member, split_amount))
                
                # Create PENDING transaction record
                if member != session['user_id']:
                    c.execute("""
                        INSERT INTO transactions (group_id, expense_id, payer_id, payee_id, amount, status)
                        VALUES (?, ?, ?, ?, ?, 'PENDING')
                    """, (group_id, expense_id, member, session['user_id'], split_amount))
        
        elif split_type == 'EXACT':
            total_amount = sum(float(splits.get(m, 0)) for m in members)
            if abs(total_amount - amount) > 0.01:
                raise ValueError('Split amounts must sum to total amount')
            
            for member in members:
                split_amount = float(splits.get(member, 0))
                if split_amount > 0.01:
                    c.execute("""
                        INSERT INTO expense_splits (expense_id, user_id, amount_owed)
                        VALUES (?, ?, ?)
                    """, (expense_id, member, split_amount))
                    
                    # Create PENDING transaction record
                    if member != session['user_id']:
                        c.execute("""
                            INSERT INTO transactions (group_id, expense_id, payer_id, payee_id, amount, status)
                            VALUES (?, ?, ?, ?, ?, 'PENDING')
                        """, (group_id, expense_id, member, session['user_id'], split_amount))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'expense_id': expense_id,
            'message': 'Expense created successfully'
        }, 201
    
    except Exception as e:
        conn.rollback()
        conn.close()
        return {'error': str(e)}, 400


@app.route('/api/groups/<int:group_id>/expenses/<int:expense_id>', methods=['DELETE'])
def api_delete_expense(group_id, expense_id):
    if 'user_id' not in session:
        return {'error': 'Not logged in'}, 401
    
    conn = get_db()
    c = conn.cursor()
    
    # Verify access to group
    c.execute("""
        SELECT role FROM groups_members
        WHERE group_id = ? AND user_id = ?
    """, (group_id, session['user_id']))
    
    if not c.fetchone():
        conn.close()
        return {'error': 'Access denied'}, 403
    
    # Verify expense belongs to group
    c.execute("""
        SELECT paid_by FROM expenses
        WHERE id = ? AND group_id = ?
    """, (expense_id, group_id))
    
    expense = c.fetchone()
    if not expense:
        conn.close()
        return {'error': 'Expense not found'}, 404
    
    try:
        # Delete splits
        c.execute("DELETE FROM expense_splits WHERE expense_id = ?", (expense_id,))
        
        # Delete expense
        c.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'message': 'Expense deleted successfully'}, 200
    
    except Exception as e:
        conn.rollback()
        conn.close()
        return {'error': str(e)}, 500


@app.route('/api/groups/<int:group_id>/balances', methods=['GET'])
def api_get_balances(group_id):
    if 'user_id' not in session:
        return {'error': 'Not logged in'}, 401
    
    conn = get_db()
    c = conn.cursor()
    
    # Verify access
    c.execute("""
        SELECT role FROM groups_members
        WHERE group_id = ? AND user_id = ?
    """, (group_id, session['user_id']))
    
    if not c.fetchone():
        conn.close()
        return {'error': 'Access denied'}, 403
    
    conn.close()
    
    balances = calculate_group_balances(group_id)
    
    return {'balances': balances}, 200


@app.route('/api/groups/<int:group_id>/settle', methods=['GET'])
def api_get_settlement(group_id):
    if 'user_id' not in session:
        return {'error': 'Not logged in'}, 401
    
    conn = get_db()
    c = conn.cursor()
    
    # Verify access
    c.execute("""
        SELECT role FROM groups_members
        WHERE group_id = ? AND user_id = ?
    """, (group_id, session['user_id']))
    
    if not c.fetchone():
        conn.close()
        return {'error': 'Access denied'}, 403
    
    conn.close()
    
    settlements, balances = advanced_greedy_settlement(group_id)
    
    return {
        'settlements': settlements,
        'balances': balances
    }, 200


@app.route('/api/groups/<int:group_id>/transactions', methods=['GET'])
def api_get_transactions(group_id):
    """Get all transactions (ledger) for a group with user details"""
    if 'user_id' not in session:
        return {'error': 'Not logged in'}, 401
    
    conn = get_db()
    c = conn.cursor()
    
    # Verify access
    c.execute("""
        SELECT role FROM groups_members
        WHERE group_id = ? AND user_id = ?
    """, (group_id, session['user_id']))
    
    if not c.fetchone():
        conn.close()
        return {'error': 'Access denied'}, 403
    
    # Get all transactions with user details
    c.execute("""
        SELECT t.id, t.expense_id, t.payer_id, t.payee_id, t.amount, t.status, t.timestamp,
               payer.full_name as payer_name, payee.full_name as payee_name,
               e.name as expense_name
        FROM transactions t
        JOIN users payer ON t.payer_id = payer.username
        JOIN users payee ON t.payee_id = payee.username
        LEFT JOIN expenses e ON t.expense_id = e.id
        WHERE t.group_id = ?
        ORDER BY t.timestamp DESC
    """, (group_id,))
    
    transactions = []
    for row in c.fetchall():
        transactions.append({
            'id': row['id'],
            'expense_id': row['expense_id'],
            'payer_id': row['payer_id'],
            'payer_name': row['payer_name'],
            'payee_id': row['payee_id'],
            'payee_name': row['payee_name'],
            'amount': row['amount'],
            'status': row['status'],
            'timestamp': row['timestamp'],
            'expense_name': row['expense_name']
        })
    
    conn.close()
    return {'transactions': transactions}, 200


@app.route('/api/groups/<token>/join', methods=['POST'])
def api_join_group_via_invite(token):
    if 'user_id' not in session:
        return {'error': 'Not logged in'}, 401
    
    conn = get_db()
    c = conn.cursor()
    
    # Find group by invite token
    c.execute("""
        SELECT group_id FROM groups
        WHERE invite_token = ?
    """, (token,))
    
    group = c.fetchone()
    if not group:
        conn.close()
        return {'error': 'Invalid invite token'}, 404
    
    group_id = group['group_id']
    
    try:
        # Add user to group
        c.execute("""
            INSERT INTO groups_members (group_id, user_id, role, is_active)
            VALUES (?, ?, 'member', 1)
        """, (group_id, session['user_id']))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'group_id': group_id,
            'message': 'Successfully joined group'
        }, 201
    
    except sqlite3.IntegrityError:
        conn.close()
        return {'error': 'Already a member of this group'}, 400
    
    except Exception as e:
        conn.rollback()
        conn.close()
        return {'error': str(e)}, 500


if __name__ == '__main__':
    init_db()
    app.run(debug=True)