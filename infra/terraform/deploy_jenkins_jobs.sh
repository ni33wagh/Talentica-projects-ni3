#!/bin/bash
# Deploy Local Jenkins Jobs to EC2 Jenkins Instance

EC2_HOST="65.1.251.65"
EC2_USER="ec2-user"
SSH_KEY="~/.ssh/id_rsa"

echo "🚀 Deploying your local Jenkins jobs to EC2..."

# Create a temporary directory for the Jenkins jobs
TEMP_DIR="/tmp/jenkins-jobs-deployment"
rm -rf $TEMP_DIR
mkdir -p $TEMP_DIR

echo "📦 Copying your local Jenkins jobs..."

# Copy all Jenkins jobs from your local machine
cp -r /Users/nitinw/Desktop/cicd-health-dashboard/jenkins/jobs/* $TEMP_DIR/

echo "📤 Copying Jenkins jobs to EC2..."

# Copy the Jenkins jobs to EC2
scp -i $SSH_KEY -r $TEMP_DIR/* $EC2_USER@$EC2_HOST:/tmp/jenkins-jobs/

echo "🔧 Installing Jenkins jobs on EC2..."

# SSH into EC2 and install the Jenkins jobs
ssh -i $SSH_KEY $EC2_USER@$EC2_HOST << 'EOF'
cd /opt/cicd-health-dashboard

echo "🛑 Stopping Jenkins container..."
docker-compose stop jenkins

echo "📁 Creating Jenkins jobs directory..."
sudo mkdir -p /var/jenkins_home/jobs

echo "📦 Copying Jenkins jobs to Jenkins home directory..."
sudo cp -r /tmp/jenkins-jobs/* /var/jenkins_home/jobs/

echo "🔧 Setting proper permissions for Jenkins jobs..."
sudo chown -R 1000:1000 /var/jenkins_home/jobs
sudo chmod -R 755 /var/jenkins_home/jobs

echo "🚀 Starting Jenkins container..."
docker-compose up -d jenkins

echo "⏳ Waiting for Jenkins to start and load jobs..."
sleep 60

echo "📊 Checking Jenkins container status..."
docker-compose ps jenkins

echo "📋 Checking Jenkins logs..."
docker-compose logs jenkins | tail -20

echo "🌐 Testing Jenkins access..."
curl -s http://localhost:8080/login | head -1 || echo "Jenkins not responding"

echo "✅ Jenkins jobs deployment completed!"
echo "🌐 Access URLs:"
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
echo "   Jenkins: http://$PUBLIC_IP:8080"
echo "   Frontend: http://$PUBLIC_IP:3000"
echo "   Backend: http://$PUBLIC_IP:8000"

echo ""
echo "📋 Your Jenkins jobs should now be available:"
echo "• build-project"
echo "• test-pipeline" 
echo "• TMO API Check"
echo "• TMO Device Change Check"
echo "• fail-freestyle-1 through fail-freestyle-5"
echo "• success-freestyle-1 through success-freestyle-5"
echo "• pipeline-success-1 through pipeline-success-3"
echo "• pipeline-fail-1 and pipeline-fail-2"
EOF

# Clean up
rm -rf $TEMP_DIR

echo "✅ Jenkins jobs deployment completed!"
echo "🌐 Your Jenkins should now have all your local jobs at:"
echo "   http://$EC2_HOST:8080"
echo ""
echo "🔄 The frontend UI should automatically reflect these jobs once Jenkins is fully loaded."
