# Flask Login & Signup System

A simple Flask application with SQLite database for user authentication and profile management.

## Features

- **User Registration (Signup)**
  - Email and username validation (unique)
  - Password confirmation
  - Full name, phone number, and UPI ID fields
  - Optional profile picture upload
  - Automatic timestamp for account creation
  
- **User Login**
  - Login with username or email
  - Password hashing using Werkzeug security
  
- **User Dashboard**
  - View all profile information
  - Display profile picture with upload timestamp
  - Show last updated timestamp (initially None)
  - View account creation date

- **Database**
  - SQLite database with users table
  - Stores all user information securely
  - Timestamps for created_at and last_updated

## Installation

1. **Install Python** (if not already installed)

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. **Navigate to the project directory:**
   ```bash
   cd MasterMinds-expense-Management-portal
   ```

2. **Run the Flask application:**
   ```bash
   python app.py
   ```

3. **Access the application:**
   - Open your browser and go to `http://localhost:5000`
   - You will be redirected to the login page

## Database Schema

### Users Table
```
- id (INTEGER, PRIMARY KEY)
- email (TEXT, UNIQUE, NOT NULL)
- username (TEXT, UNIQUE, NOT NULL)
- full_name (TEXT, NOT NULL)
- phone_number (TEXT, NOT NULL)
- upi_id (TEXT, NOT NULL)
- password (TEXT, NOT NULL) - hashed
- profile_pic_url (TEXT, OPTIONAL)
- created_at (TIMESTAMP) - automatically set
- last_updated (TIMESTAMP) - initially NULL
```

## File Structure

```
MasterMinds-expense-Management-portal/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── expense_tracker.db     # SQLite database (auto-created)
├── uploads/              # Folder for uploaded profile pictures
└── templates/
    ├── login.html        # Login page
    ├── signup.html       # Signup page
    └── dashboard.html    # User dashboard
```

## How to Use

### Sign Up
1. Click "Sign up here" on the login page
2. Fill in all required fields:
   - Email (must be unique)
   - Username (must be unique)
   - Full Name
   - Phone Number
   - UPI ID
   - Password (minimum 6 characters)
   - Confirm Password (must match password)
3. Optionally upload a profile picture (PNG, JPG, JPEG, GIF)
4. Click "Sign Up"
5. You'll be redirected to the login page

### Login
1. Enter your email or username
2. Enter your password
3. Click "Login"
4. View your dashboard with all profile information

### Dashboard
- View all your profile information
- See your profile picture (if uploaded)
- See when your account was created and last updated
- Click "Logout" to exit

## Validation Rules

- **All fields required** except profile picture
- **Email** must be unique and valid
- **Username** must be unique
- **Password** minimum 6 characters
- **Confirm Password** must match the password field
- **Profile Picture** must be PNG, JPG, JPEG, or GIF (16MB max)

## Notes

- Profile pictures are stored in the `uploads/` folder
- Passwords are hashed using Werkzeug's security functions
- The database is created automatically on first run
- Session-based authentication is used
- All timestamps are in SQLite format

## Future Enhancements

You can add styling and customization later using CSS frameworks like:
- Bootstrap
- Tailwind CSS
- Or custom CSS styling

---

Happy coding!
