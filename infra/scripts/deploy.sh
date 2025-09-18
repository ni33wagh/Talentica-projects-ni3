#!/bin/bash
# CI/CD Health Dashboard - Automated Deployment Script
# Generated with AI assistance

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Configuration
PROJECT_NAME="cicd-dashboard"
TERRAFORM_DIR="infra/terraform"
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"

# Function to check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if Terraform is installed
    if ! command -v terraform &> /dev/null; then
        error "Terraform is not installed. Please install Terraform first."
        exit 1
    fi
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        error "AWS CLI is not installed. Please install AWS CLI first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS credentials not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    # Check if SSH key exists
    if [ ! -f ~/.ssh/id_rsa.pub ]; then
        error "SSH public key not found at ~/.ssh/id_rsa.pub"
        error "Please generate an SSH key pair first:"
        error "ssh-keygen -t rsa -b 4096 -C 'your-email@example.com'"
        exit 1
    fi
    
    success "All prerequisites met!"
}

# Function to create backup
create_backup() {
    log "Creating backup of current configuration..."
    mkdir -p "$BACKUP_DIR"
    
    if [ -f "$TERRAFORM_DIR/terraform.tfstate" ]; then
        cp "$TERRAFORM_DIR/terraform.tfstate" "$BACKUP_DIR/"
        success "Backup created at $BACKUP_DIR"
    else
        warning "No existing terraform.tfstate found"
    fi
}

# Function to validate Terraform configuration
validate_terraform() {
    log "Validating Terraform configuration..."
    cd "$TERRAFORM_DIR"
    
    if terraform validate; then
        success "Terraform configuration is valid"
    else
        error "Terraform configuration validation failed"
        exit 1
    fi
    
    cd - > /dev/null
}

# Function to plan Terraform deployment
plan_terraform() {
    log "Planning Terraform deployment..."
    cd "$TERRAFORM_DIR"
    
    if terraform plan -out=tfplan; then
        success "Terraform plan created successfully"
    else
        error "Terraform planning failed"
        exit 1
    fi
    
    cd - > /dev/null
}

# Function to apply Terraform configuration
apply_terraform() {
    log "Applying Terraform configuration..."
    cd "$TERRAFORM_DIR"
    
    if terraform apply tfplan; then
        success "Terraform configuration applied successfully"
    else
        error "Terraform apply failed"
        exit 1
    fi
    
    cd - > /dev/null
}

# Function to get deployment outputs
get_outputs() {
    log "Retrieving deployment outputs..."
    cd "$TERRAFORM_DIR"
    
    echo ""
    echo "🎉 Deployment Complete!"
    echo "======================"
    echo ""
    
    # Get key outputs
    DASHBOARD_URL=$(terraform output -raw dashboard_url 2>/dev/null || echo "N/A")
    JENKINS_URL=$(terraform output -raw jenkins_url 2>/dev/null || echo "N/A")
    API_URL=$(terraform output -raw backend_api_url 2>/dev/null || echo "N/A")
    SSH_COMMAND=$(terraform output -raw ssh_connection_command 2>/dev/null || echo "N/A")
    
    echo "📊 Dashboard URLs:"
    echo "  Frontend: $DASHBOARD_URL"
    echo "  Backend API: $API_URL"
    echo "  API Docs: $API_URL/docs"
    echo "  Jenkins: $JENKINS_URL"
    echo ""
    echo "🔧 SSH Access:"
    echo "  $SSH_COMMAND"
    echo ""
    echo "⏳ Services are starting up. Please wait 2-3 minutes for full deployment."
    echo ""
    
    cd - > /dev/null
}

# Function to wait for services
wait_for_services() {
    log "Waiting for services to start..."
    
    # Get the public IP from Terraform output
    cd "$TERRAFORM_DIR"
    PUBLIC_IP=$(terraform output -raw instance_public_ip 2>/dev/null || echo "")
    cd - > /dev/null
    
    if [ -z "$PUBLIC_IP" ]; then
        warning "Could not retrieve public IP. Please check services manually."
        return
    fi
    
    log "Checking service health at $PUBLIC_IP..."
    
    # Wait for services to be ready
    for i in {1..30}; do
        if curl -s -f "http://$PUBLIC_IP:8000/api/health" > /dev/null 2>&1; then
            success "Backend API is ready!"
            break
        fi
        
        if [ $i -eq 30 ]; then
            warning "Backend API not ready after 5 minutes. Please check manually."
        else
            echo -n "."
            sleep 10
        fi
    done
    
    for i in {1..30}; do
        if curl -s -f "http://$PUBLIC_IP:3000" > /dev/null 2>&1; then
            success "Frontend is ready!"
            break
        fi
        
        if [ $i -eq 30 ]; then
            warning "Frontend not ready after 5 minutes. Please check manually."
        else
            echo -n "."
            sleep 10
        fi
    done
}

# Function to run health check
run_health_check() {
    log "Running health check..."
    
    cd "$TERRAFORM_DIR"
    PUBLIC_IP=$(terraform output -raw instance_public_ip 2>/dev/null || echo "")
    cd - > /dev/null
    
    if [ -z "$PUBLIC_IP" ]; then
        warning "Could not retrieve public IP for health check"
        return
    fi
    
    echo ""
    echo "🔍 Health Check Results:"
    echo "========================"
    
    # Check backend API
    if curl -s -f "http://$PUBLIC_IP:8000/api/health" > /dev/null 2>&1; then
        success "✅ Backend API: Healthy"
    else
        error "❌ Backend API: Unhealthy"
    fi
    
    # Check frontend
    if curl -s -f "http://$PUBLIC_IP:3000" > /dev/null 2>&1; then
        success "✅ Frontend: Healthy"
    else
        error "❌ Frontend: Unhealthy"
    fi
    
    # Check Jenkins
    if curl -s -f "http://$PUBLIC_IP:8080/login" > /dev/null 2>&1; then
        success "✅ Jenkins: Healthy"
    else
        error "❌ Jenkins: Unhealthy"
    fi
    
    echo ""
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  deploy     Deploy the infrastructure and application"
    echo "  destroy    Destroy the infrastructure"
    echo "  plan       Plan the deployment without applying"
    echo "  status     Check the status of deployed services"
    echo "  health     Run health check on deployed services"
    echo "  help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 deploy     # Deploy everything"
    echo "  $0 plan       # Plan deployment"
    echo "  $0 status     # Check status"
    echo "  $0 destroy    # Destroy infrastructure"
}

# Function to destroy infrastructure
destroy_infrastructure() {
    warning "This will destroy all infrastructure and data!"
    read -p "Are you sure you want to continue? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log "Destruction cancelled"
        exit 0
    fi
    
    log "Destroying infrastructure..."
    cd "$TERRAFORM_DIR"
    
    if terraform destroy -auto-approve; then
        success "Infrastructure destroyed successfully"
    else
        error "Infrastructure destruction failed"
        exit 1
    fi
    
    cd - > /dev/null
}

# Function to check status
check_status() {
    log "Checking deployment status..."
    cd "$TERRAFORM_DIR"
    
    if [ ! -f "terraform.tfstate" ]; then
        error "No deployment found. Run 'deploy' first."
        exit 1
    fi
    
    echo ""
    echo "📊 Deployment Status:"
    echo "===================="
    
    # Show Terraform outputs
    terraform output
    
    echo ""
    echo "🔍 Instance Status:"
    echo "=================="
    
    # Get instance ID and check status
    INSTANCE_ID=$(terraform output -raw instance_id 2>/dev/null || echo "")
    if [ -n "$INSTANCE_ID" ]; then
        aws ec2 describe-instances --instance-ids "$INSTANCE_ID" --query 'Reservations[0].Instances[0].State.Name' --output text
    fi
    
    cd - > /dev/null
}

# Main deployment function
deploy() {
    log "Starting CI/CD Health Dashboard deployment..."
    
    check_prerequisites
    create_backup
    validate_terraform
    plan_terraform
    apply_terraform
    get_outputs
    wait_for_services
    run_health_check
    
    success "Deployment completed successfully!"
    echo ""
    echo "🎯 Next Steps:"
    echo "1. Access your dashboard at the URLs shown above"
    echo "2. Configure email notifications in the dashboard"
    echo "3. Set up monitoring and alerting"
    echo "4. Review security settings"
    echo ""
}

# Main script logic
case "${1:-deploy}" in
    deploy)
        deploy
        ;;
    destroy)
        destroy_infrastructure
        ;;
    plan)
        check_prerequisites
        validate_terraform
        plan_terraform
        ;;
    status)
        check_status
        ;;
    health)
        run_health_check
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        error "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac
