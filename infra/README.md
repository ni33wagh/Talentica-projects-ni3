# Infrastructure-as-Code (IaC) - CI/CD Health Dashboard
## AWS Deployment with Terraform

### 🎯 Overview
This directory contains the complete Infrastructure-as-Code solution for deploying the CI/CD Health Dashboard to AWS using Terraform. The deployment is fully automated and includes all necessary infrastructure components.

---

## 📁 Directory Structure

```
infra/
├── terraform/                 # Terraform configuration files
│   ├── main.tf               # Main infrastructure configuration
│   ├── variables.tf          # Variable definitions
│   ├── outputs.tf            # Output definitions
│   ├── user_data.sh          # EC2 user data script
│   └── terraform.tfvars.example # Example variables file
├── scripts/                  # Deployment and utility scripts
│   └── deploy.sh             # Automated deployment script
└── docs/                     # Documentation
    ├── deployment.md         # Comprehensive deployment guide
    └── prompts.md            # AI prompts used in development
```

---

## 🚀 Quick Start

### Prerequisites
- **Terraform** (>= 1.0)
- **AWS CLI** (configured with credentials)
- **SSH Key Pair** (for EC2 access)

### 1. Setup
```bash
# Navigate to infrastructure directory
cd infra/terraform

# Copy and configure variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# Initialize Terraform
terraform init
```

### 2. Deploy
```bash
# Using the automated script (recommended)
../scripts/deploy.sh deploy

# Or manually
terraform plan
terraform apply
```

### 3. Access
After deployment, access your dashboard at:
- **Dashboard**: http://YOUR_PUBLIC_IP:3000
- **Jenkins**: http://YOUR_PUBLIC_IP:8080
- **API**: http://YOUR_PUBLIC_IP:8000

---

## 🏗️ Infrastructure Components

### Core Infrastructure
- **VPC**: Custom VPC with public/private subnets
- **EC2**: Ubuntu 22.04 instance with Docker
- **Security Groups**: Configured for web access
- **Elastic IP**: Static public IP address
- **CloudWatch**: Monitoring and logging

### Application Services
- **Frontend**: Express.js dashboard (port 3000)
- **Backend**: FastAPI application (port 8000)
- **Jenkins**: CI/CD server (port 8080)
- **Monitoring**: Health checks and logging

### Optional Components
- **Route53**: DNS management (optional)
- **S3**: Backup storage (optional)
- **CloudWatch**: Advanced monitoring (optional)

---

## 🔧 Configuration

### Required Variables
```hcl
# AWS Configuration
aws_region = "us-east-1"
environment = "dev"
project_name = "cicd-dashboard"

# Instance Configuration
instance_type = "t3.medium"
public_key_path = "~/.ssh/id_rsa.pub"

# Application Configuration
jenkins_admin_password = "secure-password"
smtp_password = "gmail-app-password"
notification_email = "your-email@gmail.com"
```

### Optional Variables
```hcl
# DNS Configuration
create_dns_zone = true
domain_name = "your-domain.com"

# Backup Configuration
create_backup_bucket = true

# Additional Tags
additional_tags = {
  Owner = "your-name"
  Project = "cicd-health-dashboard"
}
```

---

## 📊 Deployment Scripts

### Automated Deployment
```bash
# Deploy everything
./scripts/deploy.sh deploy

# Plan deployment
./scripts/deploy.sh plan

# Check status
./scripts/deploy.sh status

# Run health check
./scripts/deploy.sh health

# Destroy infrastructure
./scripts/deploy.sh destroy
```

### Manual Deployment
```bash
# Initialize
terraform init

# Plan
terraform plan

# Apply
terraform apply

# Outputs
terraform output
```

---

## 🔍 Monitoring and Maintenance

### Health Checks
```bash
# Check service health
curl http://YOUR_PUBLIC_IP:8000/api/health
curl http://YOUR_PUBLIC_IP:3000
curl http://YOUR_PUBLIC_IP:8080/login
```

### Log Monitoring
```bash
# SSH into instance
ssh -i ~/.ssh/id_rsa ubuntu@YOUR_PUBLIC_IP

# Check application logs
cd /opt/cicd-dashboard
docker-compose logs -f

# Run health check
./health-check.sh
```

### CloudWatch Monitoring
- **Instance Metrics**: CPU, memory, disk usage
- **Application Logs**: Container and application logs
- **Custom Metrics**: Application-specific metrics
- **Alerts**: Automated alerting for issues

---

## 🛠️ Troubleshooting

### Common Issues

#### 1. SSH Connection Failed
```bash
# Check security group
aws ec2 describe-security-groups --group-ids sg-xxxxxxxxx

# Verify key pair
aws ec2 describe-key-pairs --key-names cicd-dashboard-key
```

#### 2. Services Not Starting
```bash
# SSH and check logs
ssh -i ~/.ssh/id_rsa ubuntu@YOUR_PUBLIC_IP
sudo journalctl -u cicd-dashboard.service -f
```

#### 3. Dashboard Not Accessible
```bash
# Check security group rules
aws ec2 describe-security-groups --group-ids sg-xxxxxxxxx

# Test connectivity
curl -v http://YOUR_PUBLIC_IP:3000
```

### Debug Commands
```bash
# Check instance status
aws ec2 describe-instances --instance-ids i-xxxxxxxxx

# Check user data execution
ssh -i ~/.ssh/id_rsa ubuntu@YOUR_PUBLIC_IP
sudo cat /var/log/cloud-init-output.log
```

---

## 💰 Cost Optimization

### Estimated Monthly Costs (us-east-1)
- **t3.medium EC2**: ~$30/month
- **Elastic IP**: ~$3.65/month
- **EBS Storage (20GB)**: ~$2/month
- **Data Transfer**: ~$1-5/month
- **CloudWatch**: ~$1-3/month

**Total**: ~$35-45/month

### Cost Optimization Tips
- Use Spot Instances for development
- Implement auto-scaling based on demand
- Use S3 Intelligent Tiering for backups
- Monitor costs with AWS Cost Explorer

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

## 🤖 AI-Assisted Development

### AI Tools Used
- **ChatGPT**: Initial Terraform configuration generation
- **Cursor**: Code refinement and optimization
- **Copilot**: Best practices and security configurations

### Development Process
1. **Initial Setup**: AI-generated basic infrastructure
2. **Enhancement**: AI-assisted feature additions
3. **Security**: AI-suggested security improvements
4. **Documentation**: AI-generated comprehensive guides

### AI Prompts Used
See `docs/prompts.md` for detailed AI prompt examples and usage patterns.

---

## 📈 Scaling and Optimization

### Horizontal Scaling
- Use Application Load Balancer
- Deploy multiple instances
- Implement auto-scaling groups

### Performance Optimization
- Upgrade instance types
- Add more storage
- Enable CloudWatch detailed monitoring

### High Availability
- Deploy across multiple AZs
- Use RDS for database
- Implement backup and recovery

---

## 📞 Support and Maintenance

### Regular Maintenance
- **Weekly**: Check service health and logs
- **Monthly**: Update system packages and Docker images
- **Quarterly**: Review security groups and access permissions

### Monitoring Alerts
- High CPU utilization
- Low disk space
- Service health checks
- Application errors

### Backup Strategy
- **Daily**: Application data backup
- **Weekly**: Full system backup
- **Monthly**: Test backup restoration

---

## 📚 Additional Resources

### Documentation
- [Deployment Guide](docs/deployment.md)
- [AI Prompts Log](docs/prompts.md)
- [Terraform Documentation](https://terraform.io/docs)

### External Links
- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)
- [Docker Documentation](https://docs.docker.com/)
- [Jenkins Documentation](https://www.jenkins.io/doc/)

---

*This infrastructure solution provides a complete, production-ready deployment of the CI/CD Health Dashboard using Infrastructure-as-Code principles and AI-assisted development.*
