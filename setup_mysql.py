"""
Setup script for MySQL Database
Run this script to initialize the database with MySQL and Lab Parameters feature
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_mysql_connection():
    """Check if MySQL is running and accessible"""
    try:
        import pymysql
        db_url = os.getenv('DATABASE_URL', 'mysql+pymysql://labtainer:123456@localhost:3306/lab_management')
        
        # Parse connection details
        parts = db_url.replace('mysql+pymysql://', '').split('@')
        credentials = parts[0].split(':')
        host_db = parts[1].split('/')
        host_port = host_db[0].split(':')
        
        username = credentials[0]
        password = credentials[1] if len(credentials) > 1 else ''
        host = host_port[0]
        port = int(host_port[1]) if len(host_port) > 1 else 3306
        database = host_db[1].split('?')[0] if len(host_db) > 1 else 'lab_management'
        
        # Try to connect
        connection = pymysql.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database
        )
        connection.close()
        return True, "MySQL connection successful!"
    except Exception as e:
        return False, str(e)

def check_table_exists(engine, table_name):
    """Check if a table exists in the database"""
    from sqlalchemy import inspect
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def get_table_columns(engine, table_name):
    """Get list of columns for a table"""
    from sqlalchemy import inspect
    inspector = inspect(engine)
    if table_name in inspector.get_table_names():
        return [col['name'] for col in inspector.get_columns(table_name)]
    return []

def migrate_database():
    """Run database migrations"""
    print("\n" + "="*60)
    print("DATABASE MIGRATION - Lab Management System")
    print("="*60)
    
    # Check MySQL connection
    print("\n[1/5] Checking MySQL connection...")
    success, message = check_mysql_connection()
    if success:
        print(f"   ✅ {message}")
    else:
        print(f"   ❌ Connection failed: {message}")
        print("\n⚠️  Troubleshooting:")
        print("   1. Start XAMPP/MySQL server")
        print("   2. Create database 'lab_management'")
        print("   3. Check DATABASE_URL in .env file")
        return False
    
    try:
        # Import app and db
        print("\n[2/5] Loading application...")
        from lab_management_app import app, db
        print("   ✅ Application loaded")
        
        with app.app_context():
            # Check existing tables
            print("\n[3/5] Checking existing tables...")
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            print(f"   Existing tables: {', '.join(existing_tables) if existing_tables else 'None'}")
            
            # Create all tables
            print("\n[4/5] Creating/updating tables...")
            db.create_all()
            
            # Verify new tables
            inspector = inspect(db.engine)
            all_tables = inspector.get_table_names()
            
            # Check for new features
            print("\n[5/5] Verifying new features...")
            
            # Check lab_parameters table
            if 'lab_parameters' in all_tables:
                print("   ✅ lab_parameters table exists")
                cols = get_table_columns(db.engine, 'lab_parameters')
                print(f"      Columns: {', '.join(cols)}")
            else:
                print("   ❌ lab_parameters table missing")
            
            # Check run_command column in labs table
            if 'labs' in all_tables:
                labs_cols = get_table_columns(db.engine, 'labs')
                if 'run_command' in labs_cols:
                    print("   ✅ run_command column exists in labs table")
                else:
                    print("   ⚠️  run_command column missing in labs table")
                    print("      This might require manual ALTER TABLE")
            
            # Test connection with a query
            from sqlalchemy import text
            result = db.session.execute(text('SELECT VERSION()'))
            version = result.scalar()
            print(f"\n   MySQL Version: {version}")
            
            print("\n" + "="*60)
            print("✅ DATABASE SETUP COMPLETED!")
            print("="*60)
            print("\nNew Features Available:")
            print("   🎯 Lab Parameters - Configure dynamic parameters for labs")
            print("   🚀 Run Command - Auto-execute commands when lab starts")
            print("\nNext Steps:")
            print("   1. Run: python lab_management_app.py")
            print("   2. Go to: http://localhost:5000/admin")
            print("   3. Create a lab with parameters!")
            print("\n" + "="*60)
            
            return True
            
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        print("\nTroubleshooting:")
        print("   1. Make sure XAMPP MySQL is running")
        print("   2. Check if database 'lab_management' exists")
        print("   3. Verify DATABASE_URL in .env file")
        print("   4. Check MySQL credentials (username/password)")
        
        import traceback
        print("\nFull error:")
        traceback.print_exc()
        return False

def show_status():
    """Show current database status"""
    print("\n" + "="*60)
    print("DATABASE STATUS CHECK")
    print("="*60)
    
    # Check connection
    print("\n[1/3] Checking MySQL connection...")
    success, message = check_mysql_connection()
    if success:
        print(f"   ✅ {message}")
    else:
        print(f"   ❌ {message}")
        return
    
    try:
        from lab_management_app import app, db
        
        with app.app_context():
            print("\n[2/3] Checking tables...")
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            all_tables = inspector.get_table_names()
            
            expected_tables = [
                'users', 'courses', 'labs', 'lab_parameters',
                'enrollments', 'lab_sessions', 'terminal_sessions', 'command_logs'
            ]
            
            for table in expected_tables:
                if table in all_tables:
                    print(f"   ✅ {table}")
                else:
                    print(f"   ❌ {table} - MISSING")
            
            print("\n[3/3] Checking lab_parameters feature...")
            if 'lab_parameters' in all_tables:
                cols = get_table_columns(db.engine, 'lab_parameters')
                print(f"   Columns: {', '.join(cols)}")
                
                # Check for data
                from sqlalchemy import text
                result = db.session.execute(text('SELECT COUNT(*) FROM lab_parameters'))
                count = result.scalar()
                print(f"   Parameters count: {count}")
            
            if 'labs' in all_tables:
                labs_cols = get_table_columns(db.engine, 'labs')
                if 'run_command' in labs_cols:
                    print("   ✅ run_command column exists")
                else:
                    print("   ❌ run_command column missing")
            
            print("\n" + "="*60)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")

def create_sample_lab_with_parameters():
    """Create a sample lab with parameters for testing"""
    print("\n" + "="*60)
    print("CREATING SAMPLE LAB WITH PARAMETERS")
    print("="*60)
    
    try:
        from lab_management_app import app, db, Course, Lab, LabParameter
        import json
        from datetime import datetime, timedelta
        
        with app.app_context():
            # Check if sample course exists
            course = Course.query.filter_by(code='SAMPLE101').first()
            if not course:
                print("\n[1/3] Creating sample course...")
                course = Course(
                    code='SAMPLE101',
                    name='Sample Security Course',
                    description='Course for testing lab parameters',
                    semester='Fall2025',
                    instructor_id=1
                )
                db.session.add(course)
                db.session.commit()
                print(f"   ✅ Course created (ID: {course.id})")
            else:
                print(f"\n[1/3] Using existing course (ID: {course.id})")
            
            # Create sample lab
            print("\n[2/3] Creating sample lab...")
            lab = Lab(
                course_id=course.id,
                name='SQL Injection Lab with Parameters',
                description='Lab with dynamic parameters for field and table names',
                template_folder='sql-injection-template',
                accessible_resources=json.dumps(['./src', './database', './logs']),
                build_command='docker-compose up -d',
                run_command='python setup_db.py --field ${fieldName} --table ${tableName}',
                difficulty='medium',
                max_score=100,
                estimated_duration=60,
                deadline=datetime.utcnow() + timedelta(days=30)
            )
            db.session.add(lab)
            db.session.commit()
            print(f"   ✅ Lab created (ID: {lab.id})")
            print(f"   Run command: {lab.run_command}")
            
            # Create parameters
            print("\n[3/3] Creating parameters...")
            
            param1 = LabParameter(
                lab_id=lab.id,
                parameter_name='${fieldName}',
                parameter_values=json.dumps(['username', 'email', 'password', 'age']),
                description='Field name to inject SQL'
            )
            db.session.add(param1)
            print(f"   ✅ Parameter 1: {param1.parameter_name}")
            print(f"      Values: {param1.parameter_values}")
            
            param2 = LabParameter(
                lab_id=lab.id,
                parameter_name='${tableName}',
                parameter_values=json.dumps(['users', 'accounts', 'profiles', 'products']),
                description='Target table name'
            )
            db.session.add(param2)
            print(f"   ✅ Parameter 2: {param2.parameter_name}")
            print(f"      Values: {param2.parameter_values}")
            
            db.session.commit()
            
            print("\n" + "="*60)
            print("✅ SAMPLE LAB CREATED SUCCESSFULLY!")
            print("="*60)
            print(f"\nLab Details:")
            print(f"   ID: {lab.id}")
            print(f"   Name: {lab.name}")
            print(f"   Run Command: {lab.run_command}")
            print(f"   Parameters: 2")
            print(f"\nExample execution:")
            print(f"   python setup_db.py --field username --table users")
            print(f"   python setup_db.py --field email --table accounts")
            print(f"\n💡 Each student will get random parameter values!")
            print("="*60)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("\n" + "="*60)
        print("MySQL Database Setup - Lab Management System")
        print("="*60)
        print("\nUsage:")
        print("   python setup_mysql.py migrate        - Run migrations")
        print("   python setup_mysql.py status         - Check database status")
        print("   python setup_mysql.py sample         - Create sample lab")
        print("\nNew Features:")
        print("   🎯 Lab Parameters - Dynamic parameter configuration")
        print("   🚀 Run Command - Auto-execute on lab start")
        print("="*60 + "\n")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'migrate':
        migrate_database()
    elif command == 'status':
        show_status()
    elif command == 'sample':
        create_sample_lab_with_parameters()
    else:
        print(f"\n❌ Unknown command: {command}")
        print("Use: migrate, status, or sample")

if __name__ == '__main__':
    main()
