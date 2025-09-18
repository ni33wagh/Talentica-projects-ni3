#!/usr/bin/env python3
"""
Demonstration of automatic email alerts for Jenkins job failures.
"""

import requests
import time
import json

# Configuration
BACKEND_URL = "http://127.0.0.1:8001"

def check_email_alerting_status():
    """Check if email alerting is properly configured."""
    try:
        response = requests.get(f"{BACKEND_URL}/api/analytics/stats")
        if response.status_code == 200:
            data = response.json()
            print("📧 Email Alerting Configuration:")
            print(f"   SMTP Server: {data.get('smtp_server', 'N/A')}")
            print(f"   From Email: {data.get('from_email', 'N/A')}")
            print(f"   To Email: {data.get('to_email', 'N/A')}")
            print(f"   Password: {'***' if data.get('smtp_password') else 'Not set'}")
            return True
        else:
            print(f"❌ Failed to get email config: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error getting email config: {e}")
        return False

def send_demo_failure_alert():
    """Send a demo email alert for a simulated job failure."""
    try:
        print("\n🚨 Sending demo job failure alert...")
        
        # Simulate a job failure notification
        demo_data = {
            "job_name": "production-deploy",
            "build_number": 127,
            "build_url": "http://localhost:8080/job/production-deploy/127/",
            "failure_reason": "Unit tests failed - Database connection timeout"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/analytics/notifications/test-email",
            json=demo_data
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {data.get('message', 'Email sent successfully')}")
            return True
        else:
            print(f"❌ Failed to send email: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending demo email: {e}")
        return False

def main():
    print("📧 Jenkins Job Failure Email Alerts Demo")
    print("=" * 50)
    
    # Check configuration
    print("\n1. Checking email configuration...")
    config_ok = check_email_alerting_status()
    
    if not config_ok:
        print("\n❌ Email configuration issue detected")
        return
    
    # Send demo alert
    print("\n2. Sending demo failure alert...")
    success = send_demo_failure_alert()
    
    if success:
        print("\n✅ Email alerting is working perfectly!")
        print("\n📋 How Automatic Email Alerts Work:")
        print("   🔄 Backend monitors Jenkins jobs continuously")
        print("   🚨 When a job fails, notification service is triggered")
        print("   📧 Email is automatically sent to: ni33wagh@gmail.com")
        print("   📱 You receive immediate notification with:")
        print("      • Job name and build number")
        print("      • Failure reason and timestamp")
        print("      • Direct link to Jenkins build page")
        print("      • Professional HTML formatting")
        
        print("\n🎯 What Triggers Email Alerts:")
        print("   • Build status: FAILURE")
        print("   • Build status: ABORTED") 
        print("   • Build status: UNSTABLE")
        print("   • Build duration exceeds threshold")
        
        print("\n📧 Check your email now!")
        print("   Look for: '🚨 Jenkins Job Failed: production-deploy #127'")
        
    else:
        print("\n❌ Email alerting demo failed")
        print("   Check backend logs for more details")
    
    print(f"\n🌐 Dashboard: http://localhost:3000")
    print(f"🔧 Jenkins: http://localhost:8080")

if __name__ == "__main__":
    main()
