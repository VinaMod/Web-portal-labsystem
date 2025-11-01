# Lab Management System Database Schema

## Overview
Hệ thống quản lý bài lab với authentication Google, enrollment môn học, và secure WebSocket terminal.

## Database Tables

### 1. users
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    google_id VARCHAR(100) UNIQUE NOT NULL,
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    role VARCHAR(20) DEFAULT 'student', -- 'student', 'instructor', 'admin'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
```

### 2. courses 
```sql
CREATE TABLE courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(20) UNIQUE NOT NULL, -- VD: "CS101", "SEC301"
    name VARCHAR(255) NOT NULL,
    description TEXT,
    instructor_id INTEGER,
    semester VARCHAR(20), -- VD: "Fall2025", "Spring2026"
    is_active BOOLEAN DEFAULT TRUE,
    max_students INTEGER DEFAULT 50,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (instructor_id) REFERENCES users(id)
);
```

### 3. labs
```sql
CREATE TABLE labs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_folder VARCHAR(255) NOT NULL, -- Path to template folder
    accessible_resources TEXT, -- JSON array of allowed paths/resources
    build_command TEXT, -- Command to setup lab environment
    order_index INTEGER DEFAULT 0,
    deadline TIMESTAMP,
    max_score INTEGER DEFAULT 100,
    estimated_duration INTEGER, -- in minutes
    difficulty VARCHAR(20) DEFAULT 'medium', -- 'easy', 'medium', 'hard'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(id)
);
```

### 4. enrollments
```sql
CREATE TABLE enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'dropped', 'completed'
    UNIQUE(user_id, course_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (course_id) REFERENCES courses(id)
);
```

### 5. lab_sessions
```sql
CREATE TABLE lab_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    lab_id INTEGER NOT NULL,
    student_folder VARCHAR(255), -- Path to student's cloned folder
    status VARCHAR(20) DEFAULT 'not_started', -- 'not_started', 'in_progress', 'completed', 'submitted'
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    last_accessed TIMESTAMP,
    score INTEGER,
    submission_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, lab_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (lab_id) REFERENCES labs(id)
);
```

### 6. terminal_sessions
```sql
CREATE TABLE terminal_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    lab_session_id INTEGER NOT NULL,
    current_directory VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    command_count INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (lab_session_id) REFERENCES lab_sessions(id)
);
```

### 7. command_logs
```sql
CREATE TABLE command_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    terminal_session_id INTEGER NOT NULL,
    command TEXT NOT NULL,
    output TEXT,
    exit_code INTEGER,
    is_allowed BOOLEAN,
    blocked_reason TEXT,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (terminal_session_id) REFERENCES terminal_sessions(id)
);
```

## Indexes for Performance
```sql
-- User lookups
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_google_id ON users(google_id);

-- Course and lab lookups
CREATE INDEX idx_labs_course_id ON labs(course_id);
CREATE INDEX idx_enrollments_user_course ON enrollments(user_id, course_id);
CREATE INDEX idx_lab_sessions_user_lab ON lab_sessions(user_id, lab_id);

-- Terminal session lookups
CREATE INDEX idx_terminal_sessions_session_id ON terminal_sessions(session_id);
CREATE INDEX idx_terminal_sessions_user ON terminal_sessions(user_id);
CREATE INDEX idx_command_logs_terminal_session ON command_logs(terminal_session_id);
```

## Sample Data

### Sample Courses
```sql
INSERT INTO courses (code, name, description, semester) VALUES 
('IAW301', 'Web Security', 'Learn about common web vulnerabilities and how to exploit/prevent them', 'Fall2025');
```

### Sample Labs
```sql
INSERT INTO labs (course_id, name, description, template_folder, accessible_resources, build_command, deadline) VALUES 
(1, 'SQL Injection Lab Combine RCE', 'Learn to identify and exploit SQL injection vulnerabilities', 'sql-injection-template';
```

## Security Considerations

1. **Email Validation**: Chỉ cho phép email có domain `.edu`
2. **Path Traversal Protection**: Validate accessible_resources để tránh path traversal
3. **Command Filtering**: Check commands against allowed resources
4. **Session Management**: Timeout inactive sessions
5. **Audit Logging**: Log tất cả commands và results
6. **Resource Isolation**: Mỗi sinh viên có folder riêng biệt

## Environment Variables Required

```env
# Database
DATABASE_URL=sqlite:///lab_management.db

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Security
SECRET_KEY=your_secret_key_here
JWT_SECRET=your_jwt_secret_here

# Lab Environment
LAB_TEMPLATES_PATH=/var/lab-templates
STUDENT_LABS_PATH=/var/student-labs
ALLOWED_COMMANDS=["ls", "cd", "cat", "grep", "find", "pwd", "whoami"]

# Server
HOST=0.0.0.0
PORT=5000
DEBUG=False
```