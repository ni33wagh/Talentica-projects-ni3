#!/bin/bash
# Fix Frontend Container Issue

EC2_HOST="65.1.251.65"
EC2_USER="ec2-user"
SSH_KEY="~/.ssh/id_rsa"

echo "🔧 Fixing frontend container issue..."

ssh -i $SSH_KEY $EC2_USER@$EC2_HOST << 'EOF'
cd /opt/cicd-health-dashboard

echo "📊 Checking current container status..."
docker-compose ps -a

echo "📋 Checking frontend logs..."
docker-compose logs frontend

echo "🔧 Stopping all containers..."
docker-compose down

echo "🔧 Rebuilding and starting all containers..."
docker-compose up --build -d

echo "⏳ Waiting for services to start..."
sleep 30

echo "📊 Checking final container status..."
docker-compose ps

echo "🌐 Testing endpoints..."
echo "Backend health check:"
curl -s http://localhost:8000/api/health || echo "Backend not responding"

echo "Frontend health check:"
curl -s http://localhost:3000/health || echo "Frontend not responding"

echo "✅ Fix completed!"
echo "🌐 Access URLs:"
echo "   Frontend: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):3000"
echo "   Backend: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000"
echo "   Jenkins: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8080"
EOF

echo "✅ Frontend fix script completed!"
