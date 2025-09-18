# CI/CD Health Dashboard - Terraform Outputs
# Generated with AI assistance

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = aws_subnet.private[*].id
}

output "security_group_id" {
  description = "ID of the security group"
  value       = aws_security_group.ec2.id
}

output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.main.id
}

output "instance_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_eip.main.public_ip
}

output "instance_public_dns" {
  description = "Public DNS name of the EC2 instance"
  value       = aws_instance.main.public_dns
}

output "elastic_ip" {
  description = "Elastic IP address"
  value       = aws_eip.main.public_ip
}

output "dashboard_url" {
  description = "URL to access the CI/CD Health Dashboard"
  value       = "http://${aws_eip.main.public_ip}:3000"
}

output "backend_api_url" {
  description = "URL to access the backend API"
  value       = "http://${aws_eip.main.public_ip}:8000"
}

output "jenkins_url" {
  description = "URL to access Jenkins"
  value       = "http://${aws_eip.main.public_ip}:8080"
}

output "api_docs_url" {
  description = "URL to access API documentation"
  value       = "http://${aws_eip.main.public_ip}:8000/docs"
}

output "ssh_connection_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i ~/.ssh/id_rsa ec2-user@${aws_eip.main.public_ip}"
}

output "route53_zone_id" {
  description = "Route 53 hosted zone ID (if created)"
  value       = var.create_dns_zone ? aws_route53_zone.main[0].zone_id : null
}

output "route53_name_servers" {
  description = "Route 53 name servers (if created)"
  value       = var.create_dns_zone ? aws_route53_zone.main[0].name_servers : null
}

output "s3_backup_bucket" {
  description = "S3 backup bucket name (if created)"
  value       = var.create_backup_bucket ? aws_s3_bucket.backup[0].bucket : null
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.app.name
}

# Application status outputs
output "deployment_status" {
  description = "Deployment status information"
  value = {
    instance_state = aws_instance.main.instance_state
    public_ip      = aws_eip.main.public_ip
    dashboard_url  = "http://${aws_eip.main.public_ip}:3000"
    jenkins_url    = "http://${aws_eip.main.public_ip}:8080"
    api_url        = "http://${aws_eip.main.public_ip}:8000"
  }
}

# Connection information
output "connection_info" {
  description = "Connection information for the deployed application"
  value = {
    ssh_command    = "ssh -i ~/.ssh/id_rsa ec2-user@${aws_eip.main.public_ip}"
    dashboard_url  = "http://${aws_eip.main.public_ip}:3000"
    jenkins_url    = "http://${aws_eip.main.public_ip}:8080"
    api_docs_url   = "http://${aws_eip.main.public_ip}:8000/docs"
    health_check   = "curl http://${aws_eip.main.public_ip}:8000/api/health"
  }
}
