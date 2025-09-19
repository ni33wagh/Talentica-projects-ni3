#!/bin/bash
# Fix Frontend Dependencies Issue

EC2_HOST="65.1.251.65"
EC2_USER="ec2-user"
SSH_KEY="~/.ssh/id_rsa"

echo "🔧 Fixing frontend dependencies issue..."

ssh -i $SSH_KEY $EC2_USER@$EC2_HOST << 'EOF'
cd /opt/cicd-health-dashboard

echo "📋 Current container status:"
docker-compose ps

echo "🛑 Stopping all containers..."
docker-compose down

echo "🔧 Fixing frontend package.json..."
cd frontend

# Ensure package.json has the right dependencies
cat > package.json << 'PACKAGE_EOF'
{
  "name": "cicd-health-dashboard-frontend",
  "version": "1.0.0",
  "description": "CI/CD Health Dashboard Frontend",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "ejs": "^3.1.9"
  },
  "devDependencies": {
    "nodemon": "^3.0.1"
  }
}
PACKAGE_EOF

echo "📦 Package.json updated with correct dependencies"

cd ..

echo "🔧 Updating Dockerfile to ensure npm install works..."
cd frontend

# Create a better Dockerfile
cat > Dockerfile << 'DOCKERFILE_EOF'
FROM node:18-alpine

WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application
COPY . .

# Expose port
EXPOSE 3000

# Start the application
CMD ["npm", "start"]
DOCKERFILE_EOF

echo "📦 Dockerfile updated"

cd ..

echo "🚀 Rebuilding and starting containers..."
docker-compose up --build -d

echo "⏳ Waiting for services to start..."
sleep 45

echo "📊 Checking container status..."
docker-compose ps

echo "📋 Checking frontend logs..."
docker-compose logs frontend

echo "🌐 Testing endpoints..."
echo "Backend health check:"
curl -s http://localhost:8000/api/health || echo "Backend not responding"

echo "Frontend health check:"
curl -s http://localhost:3000/health || echo "Frontend not responding"

echo "✅ Frontend dependencies fix completed!"
echo "🌐 Access URLs:"
echo "   Frontend: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):3000"
echo "   Backend: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000"
echo "   Jenkins: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8080"
EOF

echo "✅ Frontend dependencies fix script completed!"
