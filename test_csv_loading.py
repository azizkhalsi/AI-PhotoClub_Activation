#!/usr/bin/env python3
"""
Test script to verify CSV loading functionality
"""

import sys
import os
sys.path.insert(0, 'src')

from email_personalizer import EmailPersonalizer

def test_csv_loading():
    print("🧪 Testing CSV loading functionality...")
    
    try:
        personalizer = EmailPersonalizer()
        print("✅ EmailPersonalizer initialized successfully")
        
        clubs_df = personalizer.load_clubs_data()
        
        if clubs_df.empty:
            print("❌ No clubs data loaded")
            return False
        
        print(f"✅ Successfully loaded {len(clubs_df)} unique clubs")
        print(f"📊 Sample clubs:")
        
        # Show first 5 clubs
        for i, row in clubs_df.head().iterrows():
            print(f"   {row['Club']} ({row['Country']})")
        
        print(f"\n🎯 CSV loading test: SUCCESS")
        return True
        
    except Exception as e:
        print(f"❌ CSV loading test failed: {e}")
        return False

if __name__ == "__main__":
    test_csv_loading() 