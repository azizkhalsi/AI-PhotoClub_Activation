#!/usr/bin/env python3
"""
Test script to verify Photo Club Email Personalization Tool setup
"""

import os
import sys
import pandas as pd
import sqlite3
from datetime import datetime

def test_dependencies():
    """Test if all required packages are installed"""
    print("🔍 Testing dependencies...")
    
    try:
        import streamlit
        print("✅ Streamlit installed")
    except ImportError:
        print("❌ Streamlit not installed")
        return False
    
    try:
        import openai
        print("✅ OpenAI package installed")
    except ImportError:
        print("❌ OpenAI package not installed")
        return False
    
    try:
        import pandas
        print("✅ Pandas installed")
    except ImportError:
        print("❌ Pandas not installed")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✅ Python-dotenv installed")
    except ImportError:
        print("❌ Python-dotenv not installed")
        return False
    
    return True

def test_files():
    """Test if required files exist"""
    print("\n📁 Testing required files...")
    
    files_to_check = [
        'config.py',
        'email_personalizer.py',
        'streamlit_app.py',
        'test_results_20250701_092437.csv',
        'Introduction Email',
        'requirements.txt'
    ]
    
    all_exist = True
    for file in files_to_check:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
            all_exist = False
    
    return all_exist

def test_csv_format():
    """Test CSV file format"""
    print("\n📊 Testing CSV file format...")
    
    try:
        df = pd.read_csv('test_results_20250701_092437.csv')
        print(f"✅ CSV loaded successfully ({len(df)} rows)")
        
        required_columns = ['Club', 'Country', 'Website', 'Name', 'Role', 'Email']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"❌ Missing columns: {missing_columns}")
            return False
        else:
            print("✅ All required columns present")
            
        # Show sample data
        unique_clubs = df['Club'].unique()
        print(f"✅ Found {len(unique_clubs)} unique clubs")
        print("Sample clubs:", list(unique_clubs[:3]))
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return False

def test_email_template():
    """Test email template"""
    print("\n📧 Testing email template...")
    
    try:
        with open('Introduction Email', 'r', encoding='utf-8') as file:
            content = file.read()
            
        if '{{Company name}}' in content:
            print("✅ Email template contains required placeholder")
        else:
            print("❌ Email template missing {{Company name}} placeholder")
            return False
            
        if 'Killian' in content:
            print("✅ Email template contains Killian introduction")
        else:
            print("❌ Email template missing Killian introduction")
            return False
            
        print(f"✅ Email template loaded ({len(content)} characters)")
        return True
        
    except Exception as e:
        print(f"❌ Error reading email template: {e}")
        return False

def test_config():
    """Test configuration"""
    print("\n⚙️ Testing configuration...")
    
    try:
        import config
        print("✅ Config module imported")
        
        # Check if .env file exists
        if os.path.exists('.env'):
            print("✅ .env file exists")
        else:
            print("⚠️ .env file not found (you'll need to create it)")
        
        # Check API key (don't print the actual key)
        if config.OPENAI_API_KEY:
            print("✅ OpenAI API key configured")
        else:
            print("⚠️ OpenAI API key not configured")
        
        print(f"✅ OpenAI model: {config.OPENAI_MODEL}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing config: {e}")
        return False

def test_database():
    """Test database creation"""
    print("\n🗄️ Testing database setup...")
    
    try:
        from email_personalizer import EmailPersonalizer
        
        # This will create the database if it doesn't exist
        personalizer = EmailPersonalizer()
        print("✅ Database initialized successfully")
        
        # Test database connection
        conn = sqlite3.connect('email_tracking.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        conn.close()
        
        if tables:
            print(f"✅ Database tables created: {[table[0] for table in tables]}")
        else:
            print("❌ No database tables found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing database: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Photo Club Email Personalization Tool - Setup Test")
    print("=" * 60)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Files", test_files),
        ("CSV Format", test_csv_format),
        ("Email Template", test_email_template),
        ("Configuration", test_config),
        ("Database", test_database)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test error: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! You can run the application with:")
        print("   streamlit run streamlit_app.py")
    else:
        print("⚠️ Some tests failed. Please fix the issues above before running the application.")
        
        if not os.path.exists('.env'):
            print("\n💡 Quick fix: Create a .env file with your OpenAI API key:")
            print("   1. Copy env_example.txt to .env")
            print("   2. Add your OpenAI API key")
    
    print("\n🔧 Next steps:")
    print("1. Create .env file with your OpenAI API key")
    print("2. Run: streamlit run streamlit_app.py")
    print("3. Navigate to the generated URL")

if __name__ == "__main__":
    main() 