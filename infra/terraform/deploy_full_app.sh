#!/bin/bash
# Deploy Full CI/CD Health Dashboard to EC2
# This script copies the actual application code and deploys it

set -e

EC2_HOST="65.1.251.65"
EC2_USER="ec2-user"
SSH_KEY="~/.ssh/id_rsa"

echo "🚀 Deploying Full CI/CD Health Dashboard to EC2..."

# Create a temporary directory for the deployment
TEMP_DIR="/tmp/cicd-deployment"
rm -rf $TEMP_DIR
mkdir -p $TEMP_DIR

echo "📦 Preparing application files..."

# Copy the entire project to temp directory
cp -r /Users/nitinw/Desktop/cicd-health-dashboard/* $TEMP_DIR/

# Remove unnecessary files
cd $TEMP_DIR
rm -rf .git
rm -rf node_modules
rm -rf backend/.venv
rm -rf frontend/node_modules
rm -rf infra/terraform/.terraform
rm -rf infra/terraform/terraform.tfstate*
rm -f terraform.zip
rm -f .DS_Store

echo "📤 Copying files to EC2 instance..."

# Copy the entire application to EC2
scp -i $SSH_KEY -r $TEMP_DIR/* $EC2_USER@$EC2_HOST:/opt/cicd-health-dashboard/

echo "🔧 Setting up the application on EC2..."

# SSH into EC2 and set up the application
ssh -i $SSH_KEY $EC2_USER@$EC2_HOST << 'EOF'
cd /opt/cicd-health-dashboard

echo "📦 Installing Docker and Docker Compose..."
sudo yum update -y
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

echo "🔧 Setting up backend..."
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

echo "🔧 Setting up frontend..."
cd frontend
npm install
cd ..

echo "🔧 Setting up Jenkins jobs..."
sudo mkdir -p jenkins/jobs
sudo cp -r jenkins/jobs/* /var/jenkins_home/jobs/ 2>/dev/null || true

echo "🚀 Starting the full application with Docker Compose..."
docker-compose down || true
docker-compose up --build -d

echo "⏳ Waiting for services to start..."
sleep 60

echo "📊 Checking service status..."
docker-compose ps

echo "✅ Full CI/CD Health Dashboard deployment completed!"
echo "🌐 Access URLs:"
echo "   Frontend: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):3000"
echo "   Backend: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000"
echo "   Jenkins: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8080"
echo "   API Docs: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000/docs"
EOF

# Clean up
rm -rf $TEMP_DIR

echo "✅ Deployment completed successfully!"
echo "🌐 Your full CI/CD Health Dashboard is now available at:"
echo "   Frontend: http://$EC2_HOST:3000"
echo "   Backend: http://$EC2_HOST:8000"
echo "   Jenkins: http://$EC2_HOST:8080"
echo "   API Docs: http://$EC2_HOST:8000/docs"
