#!/usr/bin/env python3
"""
Script to demonstrate email alerting functionality.
"""

import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "http://127.0.0.1:8001"

def send_demo_email_alert():
    """Send a demo email alert for a simulated build failure."""
    try:
        # Create a demo build failure notification
        demo_data = {
            "job_name": "demo-freestyle-job",
            "build_number": 42,
            "build_url": "http://localhost:8080/job/demo-freestyle-job/42/",
            "failure_reason": "Test failure - Unit tests failed on line 156"
        }
        
        print("📧 Sending demo email alert...")
        print(f"   Job: {demo_data['job_name']}")
        print(f"   Build: #{demo_data['build_number']}")
        print(f"   Reason: {demo_data['failure_reason']}")
        
        # Use the notification service directly
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
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending demo email: {e}")
        return False

def check_email_config():
    """Check the current email configuration."""
    try:
        response = requests.get(f"{BACKEND_URL}/api/analytics/stats")
        if response.status_code == 200:
            data = response.json()
            print("📋 Current Email Configuration:")
            print(f"   SMTP Server: {data.get('smtp_server', 'N/A')}")
            print(f"   SMTP Port: {data.get('smtp_port', 'N/A')}")
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

def main():
    print("📧 Gmail Email Alerting Demo")
    print("=" * 40)
    
    # Check email configuration
    print("\n1. Checking email configuration...")
    check_email_config()
    
    # Send demo email
    print("\n2. Sending demo email alert...")
    success = send_demo_email_alert()
    
    if success:
        print("\n✅ Email alerting is working!")
        print("📧 Check your email inbox at: ni33wagh@gmail.com")
        print("   Look for an email with subject: '🚨 Jenkins Job Failed: demo-freestyle-job #42'")
        print("\n📋 Email Alerting Features:")
        print("   • Automatic notifications on build failures")
        print("   • HTML formatted emails with build details")
        print("   • Direct links to Jenkins build pages")
        print("   • Failure reason and remediation advice")
        print("   • Professional styling and branding")
    else:
        print("\n❌ Email alerting demo failed")
        print("   Check the backend logs for more details")
    
    print(f"\n🌐 View the dashboard at: http://localhost:3000")
    print(f"📊 Backend API docs at: http://127.0.0.1:8001/docs")

if __name__ == "__main__":
    main()
