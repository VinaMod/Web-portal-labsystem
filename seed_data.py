import os
from app import app, db
from models import Course, LabTemplate

def seed_database():
    with app.app_context():
        print("Starting database seeding...")
        
        db.drop_all()
        db.create_all()
        print("Database tables created/reset")
        
        courses = [
            Course(
                name="Introduction to Cybersecurity",
                description="Learn the fundamentals of cybersecurity, including network security, encryption, and threat analysis."
            ),
            Course(
                name="Advanced Network Security",
                description="Deep dive into network protocols, firewall configuration, and intrusion detection systems."
            ),
            Course(
                name="Web Application Security",
                description="Study common web vulnerabilities like SQL injection, XSS, and CSRF attacks."
            )
        ]
        
        for course in courses:
            db.session.add(course)
        
        print(f"Added {len(courses)} courses")
        
        lab_templates = [
            LabTemplate(
                name="Network Analysis Lab",
                folder_name="network-analysis",
                description="Practice analyzing network traffic using Wireshark and tcpdump"
            ),
            LabTemplate(
                name="Buffer Overflow Lab",
                folder_name="buffer-overflow",
                description="Learn about memory vulnerabilities and exploitation techniques"
            ),
            LabTemplate(
                name="SQL Injection Lab",
                folder_name="sql-injection",
                description="Understand and practice SQL injection attacks and defenses"
            )
        ]
        
        for template in lab_templates:
            db.session.add(template)
        
        print(f"Added {len(lab_templates)} lab templates")
        
        db.session.commit()
        
        print("\nDatabase seeding completed successfully!")
        print("\nCourses:")
        for course in courses:
            print(f"  - {course.name}")
        
        print("\nLab Templates:")
        for template in lab_templates:
            print(f"  - {template.name} ({template.folder_name})")
        
        print("\nNote: Make sure to create the lab template folders in /labs:")
        for template in lab_templates:
            print(f"  mkdir -p /labs/{template.folder_name}")


if __name__ == "__main__":
    seed_database()
