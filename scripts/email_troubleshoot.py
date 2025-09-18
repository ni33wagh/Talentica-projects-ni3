#!/usr/bin/env python3
"""
Email troubleshooting script to help diagnose delivery issues.
"""

import requests
import time
import json
from datetime import datetime

# Configuration
BACKEND_URL = "http://127.0.0.1:8001"

def test_email_with_details():
    """Send a detailed test email with current timestamp."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"📧 Sending detailed test email at {timestamp}...")
        
        # Create a unique test email
        test_data = {
            "job_name": f"test-job-{int(time.time())}",
            "build_number": 999,
            "build_url": "http://localhost:8080/job/test-job/999/",
            "failure_reason": f"Test email sent at {timestamp} - This is a verification email"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/analytics/notifications/test-email",
            json=test_data
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {data.get('message', 'Email sent successfully')}")
            print(f"📧 Email sent to: ni33wagh@gmail.com")
            print(f"⏰ Sent at: {timestamp}")
            print(f"🔍 Subject should be: '🚨 Jenkins Job Failed: test-job-{int(time.time())} #999'")
            return True
        else:
            print(f"❌ Failed to send email: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending test email: {e}")
        return False

def check_gmail_tips():
    """Provide Gmail-specific troubleshooting tips."""
    print("\n📱 Gmail-Specific Troubleshooting:")
    print("=" * 40)
    print("1. Check these Gmail locations:")
    print("   • Inbox (primary tab)")
    print("   • Spam folder")
    print("   • Promotions tab")
    print("   • Updates tab")
    print("   • All Mail (Gmail > More > All Mail)")
    print()
    print("2. Search Gmail for:")
    print("   • 'Jenkins Job Failed'")
    print("   • 'ni33wagh@gmail.com'")
    print("   • 'test-job'")
    print()
    print("3. Check Gmail settings:")
    print("   • Settings > Filters and Blocked Addresses")
    print("   • Settings > Forwarding and POP/IMAP")
    print("   • Make sure 'Less secure app access' is enabled")
    print()
    print("4. Gmail App Password:")
    print("   • Verify the app password is correct")
    print("   • Check if 2FA is enabled on the account")
    print("   • Regenerate app password if needed")

def main():
    print("🔧 Email Delivery Troubleshooting Tool")
    print("=" * 45)
    
    # Test email configuration
    print("\n1. Testing email configuration...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/analytics/config/debug")
        if response.status_code == 200:
            data = response.json()
            config = data.get('data', {})
            print(f"✅ SMTP Server: {config.get('smtp_server')}")
            print(f"✅ From Email: {config.get('from_email')}")
            print(f"✅ To Email: {config.get('to_email')}")
            print(f"✅ Password: {'Set' if config.get('smtp_password') else 'Not Set'}")
        else:
            print("❌ Cannot access backend configuration")
            return
    except Exception as e:
        print(f"❌ Backend connection error: {e}")
        return
    
    # Send test email
    print("\n2. Sending detailed test email...")
    success = test_email_with_details()
    
    if success:
        print("\n✅ Email system is working correctly!")
        print("\n⏰ Expected delivery time: 1-5 minutes")
        print("📧 Check your email at: ni33wagh@gmail.com")
        
        check_gmail_tips()
        
        print(f"\n🌐 Dashboard: http://localhost:3000")
        print(f"🔧 Backend API: http://127.0.0.1:8001/docs")
        
    else:
        print("\n❌ Email system has issues")
        print("Check backend logs for more details")

if __name__ == "__main__":
    main()
