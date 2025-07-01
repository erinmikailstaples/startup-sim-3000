#!/usr/bin/env python3
"""
Test Flask app with Galileo integration to ensure no flush errors.
"""

import requests
import json
import time

def test_flask_galileo_integration():
    """Test Flask app with Galileo integration"""
    
    print("🔍 Testing Flask App with Galileo Integration")
    print("=" * 50)
    
    # Test data
    test_data = {
        "industry": "tech",
        "audience": "developers", 
        "randomWord": "innovation",
        "mode": "silly"
    }
    
    print(f"📋 Test Data: {json.dumps(test_data, indent=2)}")
    print()
    
    try:
        # Make request to Flask app
        print("🧪 Making request to Flask app...")
        response = requests.post(
            "http://localhost:2021/api/generate",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Flask app responded successfully!")
            print(f"   Status Code: {response.status_code}")
            print(f"   Result Length: {len(result.get('result', ''))}")
            print(f"   Result Preview: {result.get('result', '')[:100]}...")
            return True
        else:
            print(f"❌ Flask app returned error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Flask app. Is it running on port 2021?")
        print("   Start it with: python web_server.py")
        return False
    except Exception as e:
        print(f"❌ Error testing Flask app: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Make sure your Flask app is running first!")
    print("   Run: python web_server.py")
    print("   Then run this test in another terminal.")
    print()
    
    success = test_flask_galileo_integration()
    
    if success:
        print("\n🎉 Flask app with Galileo integration is working!")
        print("   No flush errors detected.")
    else:
        print("\n❌ Flask app needs attention.")
        print("   Check the Flask app logs for Galileo errors.") 