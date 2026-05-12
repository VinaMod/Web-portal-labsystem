import random
import sys
import hashlib

def generate_flag(email, date, suffix, random_key):
    """Generate FLAG using SHA1 hash of date_email_suffix"""
    hash_input = f"{date}_{email}_{suffix}"
    sha1_hash = hashlib.sha1(hash_input.encode()).hexdigest()
    return f"FLAG{{{sha1_hash}}}:{random_key}"

def generate_sql(email="default@example.com", date="24112025", idor_mode="student_id", random_key=""):
    # Classes and Students
    num_classes = 50
    students_per_class = 40
    class_id_min = 100
    class_id_max = 500

    # Randomly pick 50 unique class IDs between 100 and 500 for every run
    classes = sorted(random.sample(range(class_id_min, class_id_max + 1), num_classes))
    
    total_students = num_classes * students_per_class
    
    sql = """DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS grades;
DROP TABLE IF EXISTS enrollments;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'student'
);

CREATE TABLE grades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    class_id INT NOT NULL,
    semester_id VARCHAR(20) NOT NULL,
    subject_name VARCHAR(100),
    score INT,
    comments TEXT
);

CREATE TABLE enrollments (
    student_id INT,
    class_id INT,
    PRIMARY KEY (student_id, class_id)
);

INSERT INTO users (username, password, role) VALUES
('admin', 'admin123', 'admin'),
('alice', 'alice123', 'student'),
('bob', 'bob123', 'student');
"""

    # Generate the rest of the students so each class has exactly 40 members
    generated_students = total_students - 3  # subtract admin, alice, bob
    student_inserts = []
    for i in range(1, generated_students + 1):
        student_inserts.append(f"('student_{i}', 'password', 'student')")
    
    sql += "INSERT INTO users (username, password, role) VALUES\n" + ",\n".join(student_inserts) + ";\n\n"

    # RANDOM FLAG LOCATIONS
    # Pick random student ID for FLAG (depends on ENV mode)
    if idor_mode == "student_id":
        flag_student_id = random.randint(1, students_per_class)  # First class (IDs 1-40)
    else:
        flag_student_id = random.randint(1, total_students)
    
    # Pick random class ID for secret FLAG (depends on ENV mode)
    flag_class_choices = classes.copy()
    
    # Enrollments
    enrollments = []
    student_class_map = [] # List of (student_id, class_id) tuples
    
    # STRATEGY: Each class has EXACTLY 40 students (total 2000)
    current_student_id = 1
    for cid in classes:
        for _ in range(students_per_class):
            if current_student_id > total_students:
                break
            enrollments.append(f"({current_student_id}, {cid})")
            student_class_map.append((current_student_id, cid))
            current_student_id += 1
    
    student_class_lookup = {sid: cid for sid, cid in student_class_map}
                
    sql += "INSERT INTO enrollments (student_id, class_id) VALUES\n" + ",\n".join(enrollments) + ";\n\n"

    # Grades
    subjects = [
        'Mathematics', 'Physics', 'Chemistry', 'Biology', 'History', 
        'Literature', 'English', 'Computer Science', 'Geography', 
        'Economics', 'Physical Education', 'Art'
    ]
    comments_list = [
        "Excellent work! Keep up the great effort.", 
        "Needs improvement in understanding core concepts.", 
        "Good participation in class discussions.", 
        "Late submission affected the grade.",
        "Outstanding performance! Top of the class.", 
        "Average results, but showing steady progress.",
        "Keep it up! You're on the right track.", 
        "Please see me after class for additional help.", 
        "Very creative approach to problem-solving.", 
        "Solid understanding of the material.",
        "Highly engaged and motivated student.",
        "Missing assignments need to be completed.",
        "Exceptional analytical skills demonstrated.",
        "Good effort, continue practicing.",
        "Impressive improvement from last semester!",
        "Focus on time management for better results.",
        "Strong grasp of fundamental principles.",
        "Participation could be more active.",
        "Well-prepared for exams.",
        "Shows great potential in this subject."
    ]
    
    grade_inserts = []
    
    # Generate FLAGs using SHA1
    flag_student = generate_flag(email, date, "IDOR", random_key)
    flag_class = generate_flag(email, date, "IDOR", random_key)
    
    # 1. Admin's grade in Class 101 (always there for reference)
    # Already covered by the loop below since Admin is ID 1 and is in all classes
    
    # 2. FLAG for ENV=student_id: Random student has the flag (always uses their real class)
    flag_student_class = student_class_lookup.get(flag_student_id, classes[0])
    grade_inserts.append(f"({flag_student_id}, {flag_student_class}, 'SEM1', 'Secret Subject', 100, '{flag_student}')")
    
    # 3. FLAG for ENV=class_id: Alice has secret grade in random class different from her official one
    alice_class = student_class_lookup.get(2, classes[0])
    forbidden_classes = {alice_class}
    available_secret_classes = [c for c in flag_class_choices if c not in forbidden_classes]
    flag_class_id = random.choice(available_secret_classes) if available_secret_classes else alice_class
    grade_inserts.append(f"(2, {flag_class_id}, 'SEM1', 'Classified Training', 100, '{flag_class}')")
    
    # 4. Regular grades for all enrolled students
    for sid, cid in student_class_map:
        # Give each student grades for 5-7 random subjects
        num_subjects = random.randint(5, 7)
        student_subjects = random.sample(subjects, num_subjects)
        for subj in student_subjects:
            score = random.randint(40, 100)
            comment = random.choice(comments_list)
            # Escape single quotes in comments to prevent SQL syntax errors
            comment_escaped = comment.replace("'", "''")
            grade_inserts.append(f"({sid}, {cid}, 'SEM1', '{subj}', {score}, '{comment_escaped}')")
            
    sql += "INSERT INTO grades (student_id, class_id, semester_id, subject_name, score, comments) VALUES\n" + ",\n".join(grade_inserts) + ";\n"

    with open('sql/init.sql', 'w') as f:
        f.write(sql)
    
    print("=" * 60)
    print("SQL Database Generated Successfully!")
    print("=" * 60)
    print(f"Total Classes: {num_classes}")
    print(f"Class IDs: {classes}")
    print(f"Total Students: {total_students}")
    print()
    print(f"📧 Email: {email}")
    print(f"📅 Date: {date}")
    print(f"🛠️ Mode: {idor_mode}")
    print()
    print("🚩 FLAG LOCATIONS (RANDOM):")
    print("-" * 60)
    print(f"ENV=student_id → Student ID {flag_student_id} in Class {flag_student_class}")
    print(f"                 FLAG: {flag_student}")
    print()
    print(f"ENV=class_id   → Alice (ID 2) in Class {flag_class_id}")
    print(f"                 FLAG: {flag_class}")
    print("=" * 60)
    print()

if __name__ == "__main__":
    # Get email, date, and vulnerability mode from command line arguments
    email = sys.argv[1] if len(sys.argv) > 1 else "default@example.com"
    date = sys.argv[2] if len(sys.argv) > 2 else "24112025"
    idor_mode = sys.argv[3] if len(sys.argv) > 3 else "student_id"
    random_key = sys.argv[4] if len(sys.argv) > 4 else ""
    generate_sql(email, date, idor_mode, random_key)

