#!/usr/bin/env python3
"""
Script to trigger Jenkins builds and demonstrate email alerting.
"""

import requests
import time
import json

# Configuration
JENKINS_URL = "http://localhost:8080"
JENKINS_USER = "admin"
JENKINS_PASS = "EYdWn>DaN*G79gB*"
BACKEND_URL = "http://127.0.0.1:8001"

def get_jenkins_crumb():
    """Get Jenkins CSRF crumb."""
    try:
        response = requests.get(
            f"{JENKINS_URL}/crumbIssuer/api/json",
            auth=(JENKINS_USER, JENKINS_PASS)
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("crumbRequestField"), data.get("crumb")
    except Exception as e:
        print(f"Error getting crumb: {e}")
    return None, None

def trigger_jenkins_build(job_name):
    """Trigger a Jenkins build."""
    crumb_field, crumb_value = get_jenkins_crumb()
    if not crumb_field or not crumb_value:
        print(f"Failed to get crumb for {job_name}")
        return False
    
    try:
        response = requests.post(
            f"{JENKINS_URL}/job/{job_name}/build",
            auth=(JENKINS_USER, JENKINS_PASS),
            headers={
                crumb_field: crumb_value,
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data=""
        )
        
        if response.status_code in [200, 201]:
            print(f"✅ Successfully triggered build for {job_name}")
            return True
        else:
            print(f"❌ Failed to trigger build for {job_name}: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error triggering build for {job_name}: {e}")
        return False

def test_email_notification():
    """Test email notification functionality."""
    try:
        response = requests.post(f"{BACKEND_URL}/api/analytics/notifications/test-email")
        if response.status_code == 200:
            data = response.json()
            print(f"📧 Email test: {data.get('message', 'Unknown response')}")
            return True
        else:
            print(f"❌ Email test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing email: {e}")
        return False

def main():
    print("🚀 Jenkins Build Trigger & Email Alerting Demo")
    print("=" * 50)
    
    # Test email functionality first
    print("\n1. Testing email notification system...")
    test_email_notification()
    
    # Trigger some failing builds
    print("\n2. Triggering failing builds to test email alerts...")
    failing_jobs = ["fail-freestyle-1", "fail-freestyle-2", "fail-freestyle-3"]
    
    for job in failing_jobs:
        print(f"\nTriggering {job}...")
        success = trigger_jenkins_build(job)
        if success:
            time.sleep(2)  # Wait between builds
    
    print("\n3. Waiting for builds to complete and generate email alerts...")
    print("   (This may take 30-60 seconds)")
    
    # Wait and check for notifications
    for i in range(6):
        print(f"   Waiting... ({i+1}/6)")
        time.sleep(10)
    
    print("\n4. Checking backend for email notifications...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/analytics/stats")
        if response.status_code == 200:
            data = response.json()
            print("📊 Backend stats retrieved successfully")
            print(f"   Total jobs: {data.get('total_jobs', 'N/A')}")
            print(f"   Failed jobs: {data.get('failed_jobs', 'N/A')}")
        else:
            print(f"❌ Failed to get backend stats: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting backend stats: {e}")
    
    print("\n✅ Demo completed!")
    print("📧 Check your email (ni33wagh@gmail.com) for failure notifications")
    print("🌐 View the dashboard at: http://localhost:3000")

if __name__ == "__main__":
    main()
