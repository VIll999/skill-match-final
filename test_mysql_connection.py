#!/usr/bin/env python3
import os
import sys
import pymysql
from sqlalchemy import create_engine, text

print("🔍 Testing MySQL connection and API compatibility...")

# Database connection details
DB_CONFIG = {
    'host': 'database-3.cl7a5hmtnxws.us-east-1.rds.amazonaws.com',
    'user': 'congtian',
    'password': 'DbrWQkCVZu90n9H+112A2A==',
    'database': 'resume',
    'port': 3306
}

DATABASE_URL = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

def test_direct_connection():
    """Test direct PyMySQL connection"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = 'resume'")
        result = cursor.fetchone()
        print(f"✓ Direct MySQL connection successful! Found {result[0]} tables")
        
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        for table in tables:
            print(f"  - {table[0]}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Direct MySQL connection failed: {e}")
        return False

def test_sqlalchemy_connection():
    """Test SQLAlchemy connection"""
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✓ SQLAlchemy connection successful!")
            
            # Test table existence
            result = conn.execute(text("SHOW TABLES"))
            tables = result.fetchall()
            print(f"✓ Found {len(tables)} tables via SQLAlchemy")
            
        return True
    except Exception as e:
        print(f"✗ SQLAlchemy connection failed: {e}")
        return False

def test_skill_match_models():
    """Test if we can import skill-match models"""
    try:
        sys.path.append('./apps/api')
        from src.models.user import User
        from src.models.skill import EMSISkill
        print("✓ Skill-match models imported successfully")
        return True
    except Exception as e:
        print(f"✗ Model import failed: {e}")
        return False

def main():
    print("=" * 50)
    print("MySQL Connection Test for Skill-Match Backend")
    print("=" * 50)
    
    # Test connections
    direct_ok = test_direct_connection()
    sqlalchemy_ok = test_sqlalchemy_connection()
    models_ok = test_skill_match_models()
    
    print("\n" + "=" * 50)
    if direct_ok and sqlalchemy_ok and models_ok:
        print("🎉 All tests passed! Ready for deployment")
        print(f"📝 Database URL: {DATABASE_URL}")
        return 0
    else:
        print("❌ Some tests failed. Check configuration")
        return 1

if __name__ == "__main__":
    sys.exit(main())