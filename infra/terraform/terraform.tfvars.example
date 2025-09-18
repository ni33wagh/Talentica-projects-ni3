# CI/CD Health Dashboard - Terraform Variables Example
# Copy this file to terraform.tfvars and update with your values

# AWS Configuration
aws_region = "ap-south-1"
environment = "dev"
project_name = "cicd-dashboard"

# VPC Configuration
vpc_cidr = "10.0.0.0/16"
public_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24"]
private_subnet_cidrs = ["10.0.10.0/24", "10.0.20.0/24"]

# EC2 Instance Configuration
instance_type = "t3.small"
root_volume_size = 20

# SSH Key Configuration
# Update this path to your public key file
public_key_path = "~/.ssh/id_rsa.pub"

# Application Configuration
jenkins_admin_password = "your-secure-password-here"
smtp_password = "your-gmail-app-password-here"
notification_email = "your-email@gmail.com"

# DNS Configuration (Optional)
create_dns_zone = false
domain_name = ""

# Backup Configuration (Optional)
create_backup_bucket = false

# Additional Tags
additional_tags = {
  Owner = "your-name"
  Project = "cicd-health-dashboard"
  Environment = "dev"
}
