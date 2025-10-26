import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager

DATABASE_PATH = 'labtainer_system.db'

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize the database with all required tables"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                provider TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Courses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Labs table (templates available in Labtainer)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS labs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                template_folder TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses (id)
            )
        ''')
        
        # Course enrollments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (course_id) REFERENCES courses (id),
                UNIQUE(user_id, course_id)
            )
        ''')
        
        # User lab instances table (individual labs for each user)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_labs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                lab_id INTEGER NOT NULL,
                folder_name TEXT NOT NULL,
                status TEXT DEFAULT 'ENROLLED',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (lab_id) REFERENCES labs (id),
                UNIQUE(user_id, lab_id)
            )
        ''')
        
        conn.commit()
        print("Database initialized successfully")

def seed_sample_data():
    """Add sample courses and labs for testing"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if sample data already exists
        cursor.execute('SELECT COUNT(*) FROM courses')
        if cursor.fetchone()[0] > 0:
            print("Sample data already exists")
            return
        
        # Add sample courses
        courses = [
            ('Introduction to Cybersecurity', 'Fundamentals of network security and ethical hacking'),
            ('Advanced Network Security', 'Deep dive into network protocols and security measures'),
            ('Web Application Security', 'Learn about OWASP vulnerabilities and secure coding')
        ]
        
        for name, desc in courses:
            cursor.execute('INSERT INTO courses (name, description) VALUES (?, ?)', (name, desc))
        
        # Add sample lab templates (these should match actual Labtainer folder names)
        labs = [
            (1, 'Network Reconnaissance', 'recon-lab', 'Learn network scanning and enumeration techniques'),
            (1, 'SQL Injection Basics', 'sql-injection-lab', 'Introduction to SQL injection vulnerabilities'),
            (1, 'Buffer Overflow Introduction', 'buffer-overflow-lab', 'Understanding memory corruption vulnerabilities'),
            (2, 'Firewall Configuration', 'firewall-lab', 'Configure and test firewall rules'),
            (2, 'VPN Setup', 'vpn-lab', 'Set up and secure VPN connections'),
            (3, 'XSS Vulnerabilities', 'xss-lab', 'Cross-site scripting attack and defense'),
        ]
        
        for course_id, name, template, desc in labs:
            cursor.execute(
                'INSERT INTO labs (course_id, name, template_folder, description) VALUES (?, ?, ?, ?)',
                (course_id, name, template, desc)
            )
        
        conn.commit()
        print("Sample data seeded successfully")

# Database query functions
def get_user_by_email(email):
    """Get user by email"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        return cursor.fetchone()

def create_user(email, name, provider='google'):
    """Create a new user"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (email, name, provider) VALUES (?, ?, ?)',
            (email, name, provider)
        )
        conn.commit()
        return cursor.lastrowid

def get_user_courses(user_id):
    """Get all courses a user is enrolled in"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.*, e.enrolled_at 
            FROM courses c
            JOIN enrollments e ON c.id = e.course_id
            WHERE e.user_id = ?
            ORDER BY e.enrolled_at DESC
        ''', (user_id,))
        return cursor.fetchall()

def get_course_labs(course_id):
    """Get all labs for a course"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM labs WHERE course_id = ? ORDER BY created_at',
            (course_id,)
        )
        return cursor.fetchall()

def get_user_labs(user_id):
    """Get all lab instances for a user with lab details"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ul.*, l.name as lab_name, l.template_folder, c.name as course_name
            FROM user_labs ul
            JOIN labs l ON ul.lab_id = l.id
            JOIN courses c ON l.course_id = c.id
            WHERE ul.user_id = ?
            ORDER BY ul.created_at DESC
        ''', (user_id,))
        return cursor.fetchall()

def enroll_in_course(user_id, course_id):
    """Enroll a user in a course"""
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
                (user_id, course_id)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Already enrolled

def create_user_lab(user_id, lab_id, folder_name):
    """Create a lab instance for a user"""
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO user_labs (user_id, lab_id, folder_name, status) VALUES (?, ?, ?, ?)',
                (user_id, lab_id, folder_name, 'ENROLLED')
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None  # Lab already exists for user

def update_lab_status(user_lab_id, status):
    """Update the status of a user's lab"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE user_labs SET status = ?, last_accessed = CURRENT_TIMESTAMP WHERE id = ?',
            (status, user_lab_id)
        )
        conn.commit()

def get_all_courses():
    """Get all available courses"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM courses ORDER BY created_at')
        return cursor.fetchall()

if __name__ == '__main__':
    # Initialize database when run directly
    init_db()
    seed_sample_data()
    print("Database setup complete!")
