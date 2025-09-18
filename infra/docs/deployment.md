# CI/CD Health Dashboard - Cloud Deployment Guide
## Infrastructure-as-Code with Terraform

### 🎯 Overview
This guide provides step-by-step instructions for deploying the CI/CD Health Dashboard to AWS using Terraform. The deployment is fully automated and includes all necessary infrastructure components.

---

## 📋 Prerequisites

### Required Tools
- **Terraform** (>= 1.0)
- **AWS CLI** (configured with credentials)
- **SSH Key Pair** (for EC2 access)
- **Docker** (for local testing)

### AWS Requirements
- AWS Account with appropriate permissions
- IAM user with EC2, VPC, Route53, S3, and CloudWatch permissions
- AWS CLI configured with credentials

### Installation Commands
```bash
# Install Terraform (macOS)
brew install terraform

# Install AWS CLI (macOS)
brew install awscli

# Configure AWS CLI
aws configure
```

---

## 🚀 Quick Start Deployment

### 1. Clone and Setup
```bash
# Navigate to the project directory
cd /Users/nitinw/Desktop/cicd-health-dashboard

# Copy your application code to the infrastructure directory
cp -r backend frontend jenkins infra/terraform/

# Navigate to Terraform directory
cd infra/terraform
```

### 2. Configure Variables
```bash
# Create terraform.tfvars file
cat > terraform.tfvars << EOF
# AWS Configuration
aws_region = "us-east-1"
environment = "dev"
project_name = "cicd-dashboard"

# Instance Configuration
instance_type = "t3.medium"
root_volume_size = 20

# SSH Key (update path to your public key)
public_key_path = "~/.ssh/id_rsa.pub"

# Application Configuration
jenkins_admin_password = "your-secure-password"
smtp_password = "your-gmail-app-password"
notification_email = "your-email@gmail.com"

# Optional: DNS Configuration
create_dns_zone = false
domain_name = ""

# Optional: Backup Configuration
create_backup_bucket = false
EOF
```

### 3. Initialize and Deploy
```bash
# Initialize Terraform
terraform init

# Review the deployment plan
terraform plan

# Apply the infrastructure
terraform apply

# Confirm deployment (type 'yes' when prompted)
```

### 4. Access Your Dashboard
After deployment completes, you'll see output similar to:
```
dashboard_url = "http://54.123.45.67:3000"
jenkins_url = "http://54.123.45.67:8080"
backend_api_url = "http://54.123.45.67:8000"
api_docs_url = "http://54.123.45.67:8000/docs"
```

---

## 🔧 Detailed Configuration

### Infrastructure Components

#### VPC and Networking
- **VPC**: Custom VPC with CIDR 10.0.0.0/16
- **Public Subnets**: 2 availability zones for high availability
- **Private Subnets**: For future database deployment
- **Internet Gateway**: For public internet access
- **Route Tables**: Proper routing configuration

#### Security Groups
- **SSH Access**: Port 22 from anywhere (0.0.0.0/0)
- **Dashboard Frontend**: Port 3000 from anywhere
- **Backend API**: Port 8000 from anywhere
- **Jenkins**: Port 8080 from anywhere
- **All Outbound**: Full internet access

#### EC2 Instance
- **Instance Type**: t3.medium (2 vCPU, 4GB RAM)
- **AMI**: Ubuntu 22.04 LTS
- **Storage**: 20GB GP3 encrypted root volume
- **Elastic IP**: Static public IP address

### Application Deployment

#### Docker Installation
The user data script automatically installs:
- Docker Engine
- Docker Compose
- Required system packages

#### Application Services
- **Backend**: FastAPI application on port 8000
- **Frontend**: Express.js application on port 3000
- **Jenkins**: Jenkins LTS on port 8080
- **Health Checks**: Automated service monitoring

#### Monitoring and Logging
- **CloudWatch**: System and application metrics
- **Log Rotation**: Automated log management
- **Health Checks**: Service status monitoring

---

## 🛠️ Advanced Configuration

### Custom Domain Setup
```bash
# In terraform.tfvars
create_dns_zone = true
domain_name = "your-domain.com"
```

### Production Configuration
```bash
# In terraform.tfvars
environment = "prod"
instance_type = "t3.large"
root_volume_size = 50
create_backup_bucket = true
```

### Environment Variables
```bash
# Update user_data.sh or create .env file
export SMTP_PASSWORD="your-gmail-app-password"
export JENKINS_ADMIN_PASSWORD="secure-password"
export NOTIFICATION_EMAIL="your-email@gmail.com"
```

---

## 📊 Monitoring and Maintenance

### Health Checks
```bash
# SSH into your instance
ssh -i ~/.ssh/id_rsa ubuntu@YOUR_PUBLIC_IP

# Run health check script
cd /opt/cicd-dashboard
./health-check.sh
```

### Log Monitoring
```bash
# View application logs
docker-compose logs -f

# View system logs
tail -f /var/log/user-data.log

# View CloudWatch logs
aws logs describe-log-groups --log-group-name-prefix "/aws/ec2/cicd-dashboard"
```

### Backup and Recovery
```bash
# Create backup
cd /opt/cicd-dashboard
./backup.sh

# Restore from backup
# (Manual process - copy backup files and restart services)
```

---

## 🔍 Troubleshooting

### Common Issues

#### 1. SSH Connection Failed
```bash
# Check security group rules
aws ec2 describe-security-groups --group-ids sg-xxxxxxxxx

# Verify key pair
aws ec2 describe-key-pairs --key-names cicd-dashboard-key

# Check instance status
aws ec2 describe-instances --instance-ids i-xxxxxxxxx
```

#### 2. Services Not Starting
```bash
# SSH into instance and check logs
ssh -i ~/.ssh/id_rsa ubuntu@YOUR_PUBLIC_IP

# Check Docker status
sudo systemctl status docker
docker ps -a

# Check application logs
cd /opt/cicd-dashboard
docker-compose logs
```

#### 3. Dashboard Not Accessible
```bash
# Check if services are running
curl http://localhost:3000
curl http://localhost:8000/api/health
curl http://localhost:8080/login

# Check security group rules
aws ec2 describe-security-groups --group-ids sg-xxxxxxxxx
```

#### 4. Email Notifications Not Working
```bash
# Check SMTP configuration
curl -X POST "http://YOUR_PUBLIC_IP:8000/api/analytics/notifications/test-email"

# Verify Gmail App Password
# Check spam folder for test emails
```

### Debug Commands
```bash
# Check instance metadata
curl http://169.254.169.254/latest/meta-data/public-ipv4

# Check user data execution
sudo cat /var/log/cloud-init-output.log

# Check system resources
htop
df -h
free -h
```

---

## 🚀 Scaling and Optimization

### Horizontal Scaling
```bash
# Create multiple instances
terraform apply -var="instance_count=3"

# Use Application Load Balancer
# (Requires additional Terraform configuration)
```

### Performance Optimization
```bash
# Upgrade instance type
terraform apply -var="instance_type=t3.large"

# Add more storage
terraform apply -var="root_volume_size=50"

# Enable CloudWatch detailed monitoring
# (Add to EC2 instance configuration)
```

### Cost Optimization
```bash
# Use smaller instance for development
terraform apply -var="instance_type=t3.small"

# Enable instance scheduling
# (Stop/start instances during non-business hours)
```

---

## 🔒 Security Best Practices

### Network Security
- Use private subnets for databases
- Implement WAF for web application protection
- Enable VPC Flow Logs for network monitoring

### Access Control
- Use IAM roles instead of access keys
- Implement least privilege access
- Enable MFA for AWS console access

### Data Protection
- Enable encryption at rest and in transit
- Use AWS Secrets Manager for sensitive data
- Implement regular security updates

---

## 📈 Cost Estimation

### Monthly Costs (us-east-1)
- **t3.medium EC2**: ~$30/month
- **Elastic IP**: ~$3.65/month
- **EBS Storage (20GB)**: ~$2/month
- **Data Transfer**: ~$1-5/month
- **CloudWatch**: ~$1-3/month

**Total Estimated Cost**: ~$35-45/month

### Cost Optimization Tips
- Use Spot Instances for development
- Implement auto-scaling based on demand
- Use S3 Intelligent Tiering for backups
- Monitor costs with AWS Cost Explorer

---

## 🎯 AI-Assisted Development

### How AI Tools Were Used

#### 1. Terraform Code Generation
- **ChatGPT**: Generated initial Terraform configuration
- **Cursor**: Refined and optimized the code
- **Copilot**: Added best practices and security configurations

#### 2. User Data Script Creation
- **AI Assistance**: Generated comprehensive deployment script
- **Automation**: Docker installation and application deployment
- **Monitoring**: Health checks and logging configuration

#### 3. Documentation Generation
- **AI Tools**: Created comprehensive deployment guide
- **Best Practices**: Security and optimization recommendations
- **Troubleshooting**: Common issues and solutions

### AI Prompt Examples Used
```
"Create a Terraform configuration for deploying a containerized application to AWS EC2 with VPC, security groups, and automated deployment"
```

```
"Generate a user data script that installs Docker, deploys a multi-container application, and sets up monitoring"
```

```
"Write a comprehensive deployment guide for Infrastructure-as-Code with troubleshooting steps"
```

---

## 📞 Support and Maintenance

### Regular Maintenance Tasks
- **Weekly**: Check service health and logs
- **Monthly**: Update system packages and Docker images
- **Quarterly**: Review security groups and access permissions
- **Annually**: Review and update Terraform configurations

### Monitoring Alerts
- Set up CloudWatch alarms for:
  - High CPU utilization
  - Low disk space
  - Service health checks
  - Application errors

### Backup Strategy
- **Daily**: Application data backup
- **Weekly**: Full system backup
- **Monthly**: Test backup restoration
- **Quarterly**: Disaster recovery testing

---

*This deployment guide provides complete instructions for deploying the CI/CD Health Dashboard to AWS using Infrastructure-as-Code principles and AI-assisted development.*
