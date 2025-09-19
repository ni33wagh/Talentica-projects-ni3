#!/bin/bash
# Check Current Jenkins Status on EC2

EC2_HOST="65.1.251.65"
EC2_USER="ec2-user"
SSH_KEY="~/.ssh/id_rsa"

echo "🔍 Checking current Jenkins status on EC2..."

ssh -i $SSH_KEY $EC2_USER@$EC2_HOST << 'EOF'
cd /opt/cicd-health-dashboard

echo "📊 Container Status:"
docker-compose ps

echo ""
echo "📁 Jenkins Jobs Directory:"
ls -la /var/jenkins_home/jobs/ 2>/dev/null || echo "No jobs directory found"

echo ""
echo "📋 Jenkins Logs (last 10 lines):"
docker-compose logs jenkins | tail -10

echo ""
echo "🌐 Jenkins Access Test:"
curl -s http://localhost:8080/login | head -1 || echo "Jenkins not responding"

echo ""
echo "📊 Jenkins Volume Info:"
docker volume ls | grep jenkins || echo "No Jenkins volume found"

echo ""
echo "🔍 Jenkins Home Directory Contents:"
ls -la /var/jenkins_home/ | head -10
EOF

echo "✅ Status check completed!"
