#!/bin/bash
# Fix Jenkins Jobs Deployment - More Robust Approach

EC2_HOST="65.1.251.65"
EC2_USER="ec2-user"
SSH_KEY="~/.ssh/id_rsa"

echo "🚀 Fixing Jenkins jobs deployment with robust approach..."

# Create a temporary directory for the Jenkins jobs
TEMP_DIR="/tmp/jenkins-jobs-fix"
rm -rf $TEMP_DIR
mkdir -p $TEMP_DIR

echo "📦 Copying your local Jenkins jobs..."

# Copy all Jenkins jobs from your local machine
cp -r /Users/nitinw/Desktop/cicd-health-dashboard/jenkins/jobs/* $TEMP_DIR/

echo "📤 Copying Jenkins jobs to EC2..."

# Copy the Jenkins jobs to EC2
scp -i $SSH_KEY -r $TEMP_DIR/* $EC2_USER@$EC2_HOST:/tmp/jenkins-jobs-fix/

echo "🔧 Installing Jenkins jobs on EC2 with proper approach..."

# SSH into EC2 and install the Jenkins jobs properly
ssh -i $SSH_KEY $EC2_USER@$EC2_HOST << 'EOF'
cd /opt/cicd-health-dashboard

echo "🛑 Stopping all containers..."
docker-compose down

echo "📁 Checking current Jenkins volume..."
docker volume ls | grep jenkins || echo "No Jenkins volume found"

echo "📦 Creating Jenkins jobs backup..."
sudo mkdir -p /tmp/jenkins-backup
sudo cp -r /var/jenkins_home/jobs /tmp/jenkins-backup/ 2>/dev/null || echo "No existing jobs to backup"

echo "🗑️ Removing old Jenkins jobs..."
sudo rm -rf /var/jenkins_home/jobs/*

echo "📁 Creating Jenkins jobs directory..."
sudo mkdir -p /var/jenkins_home/jobs

echo "📦 Copying new Jenkins jobs to Jenkins home directory..."
sudo cp -r /tmp/jenkins-jobs-fix/* /var/jenkins_home/jobs/

echo "🔧 Setting proper permissions for Jenkins jobs..."
sudo chown -R 1000:1000 /var/jenkins_home/jobs
sudo chmod -R 755 /var/jenkins_home/jobs

echo "📋 Verifying jobs were copied..."
ls -la /var/jenkins_home/jobs/ | head -10

echo "🚀 Starting all containers..."
docker-compose up -d

echo "⏳ Waiting for services to start..."
sleep 30

echo "📊 Checking container status..."
docker-compose ps

echo "📋 Checking Jenkins logs..."
docker-compose logs jenkins | tail -20

echo "🌐 Testing Jenkins access..."
sleep 30
curl -s http://localhost:8080/login | head -1 || echo "Jenkins not responding yet"

echo "📋 Listing Jenkins jobs directory after restart..."
ls -la /var/jenkins_home/jobs/ | head -10

echo "✅ Jenkins jobs fix completed!"
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

echo "✅ Jenkins jobs fix completed!"
echo "🌐 Your Jenkins should now have all your local jobs at:"
echo "   http://$EC2_HOST:8080"
echo ""
echo "🔄 The frontend UI should automatically reflect these jobs once Jenkins is fully loaded."
echo "⏳ It may take 1-2 minutes for Jenkins to fully load all the jobs."
