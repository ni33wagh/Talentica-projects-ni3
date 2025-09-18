# Gmail Email Alerting Configuration Guide

## ✅ Current Status
Gmail email alerting is **already configured and working** in your CI/CD Health Dashboard!

## 📧 Current Configuration
- **SMTP Server**: smtp.gmail.com
- **SMTP Port**: 587 (TLS)
- **From Email**: ni33wagh@gmail.com
- **To Email**: ni33wagh@gmail.com
- **Password**: ztlegvdbfotzxetu (App Password)

## 🚀 How It Works

### Automatic Email Alerts
The system automatically sends email notifications when:
- ✅ Jenkins builds fail
- ✅ Builds are aborted
- ✅ Builds are unstable
- ✅ Build duration exceeds threshold

### Email Features
- 📧 **HTML formatted emails** with professional styling
- 🔗 **Direct links** to Jenkins build pages
- 📊 **Build details** including job name, build number, duration
- 🚨 **Failure reasons** and remediation advice
- 🎨 **Professional branding** with CI/CD Health Dashboard styling

## 🧪 Testing Email Alerts

### Method 1: Test Endpoint
```bash
curl -X POST "http://127.0.0.1:8001/api/analytics/notifications/test-email"
```

### Method 2: Demo Script
```bash
cd /Users/nitinw/Desktop/cicd-health-dashboard
python3 scripts/demo_email_alert.py
```

### Method 3: Trigger Failing Builds
```bash
# Trigger builds that are designed to fail
python3 scripts/trigger_builds.py
```

## 📋 Email Template Example

When a build fails, you'll receive an email like this:

**Subject**: 🚨 Jenkins Job Failed: [Job Name] #[Build Number]

**Content**:
- Job name and build number
- Failure timestamp
- Failure reason
- Direct link to build details
- Professional HTML formatting
- CI/CD Health Dashboard branding

## 🔧 Configuration Files

### Environment Variables (docker-compose.yml)
```yaml
SMTP_SERVER: "smtp.gmail.com"
SMTP_PORT: "587"
SMTP_USERNAME: "ni33wagh@gmail.com"
SMTP_PASSWORD: "ztlegvdbfotzxetu"
FROM_EMAIL: "ni33wagh@gmail.com"
TO_EMAIL: "ni33wagh@gmail.com"
```

### Backend Configuration (backend/app/config.py)
```python
smtp_server: str = Field(default="smtp.gmail.com", env="SMTP_SERVER")
smtp_port: int = Field(default=587, env="SMTP_PORT")
smtp_username: str = Field(default="ni33wagh@gmail.com", env="SMTP_USERNAME")
smtp_password: str = Field(default="", env="SMTP_PASSWORD")
from_email: str = Field(default="ni33wagh@gmail.com", env="FROM_EMAIL")
to_email: str = Field(default="ni33wagh@gmail.com", env="TO_EMAIL")
```

## 🎯 Next Steps

1. **Check your email** at ni33wagh@gmail.com for test notifications
2. **Trigger some builds** to see real-time email alerts
3. **Customize recipients** by updating the TO_EMAIL environment variable
4. **Add more notification channels** (Slack, Teams, etc.)

## 🔍 Monitoring

- View email notification logs in backend console
- Check dashboard at http://localhost:3000
- Monitor Jenkins builds at http://localhost:8080

## 📞 Support

If you need to modify email settings:
1. Update environment variables in docker-compose.yml
2. Restart the backend service
3. Test with the demo script

The email alerting system is fully functional and ready for production use! 🎉
