#!/bin/bash
# Deploy Actual Local Frontend Code to EC2

EC2_HOST="65.1.251.65"
EC2_USER="ec2-user"
SSH_KEY="~/.ssh/id_rsa"

echo "🚀 Deploying your actual local frontend code to EC2..."

# Create a temporary directory for the frontend files
TEMP_DIR="/tmp/frontend-deployment"
rm -rf $TEMP_DIR
mkdir -p $TEMP_DIR

echo "📦 Copying your local frontend files..."

# Copy the actual frontend files from your local machine
cp -r /Users/nitinw/Desktop/cicd-health-dashboard/frontend/* $TEMP_DIR/

# Remove node_modules to avoid conflicts
rm -rf $TEMP_DIR/node_modules

echo "📤 Copying frontend files to EC2..."

# Copy the frontend files to EC2
scp -i $SSH_KEY -r $TEMP_DIR/* $EC2_USER@$EC2_HOST:/opt/cicd-health-dashboard/frontend/

echo "🔧 Updating frontend on EC2..."

# SSH into EC2 and update the frontend
ssh -i $SSH_KEY $EC2_USER@$EC2_HOST << 'EOF'
cd /opt/cicd-health-dashboard

echo "🛑 Stopping frontend container..."
docker-compose stop frontend

echo "🔧 Updating frontend Dockerfile to use your actual code..."
cd frontend

# Create optimized Dockerfile for your actual frontend
cat > Dockerfile << 'DOCKERFILE_EOF'
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files FIRST for better caching
COPY package*.json ./

# Install dependencies (this layer will be cached if package.json doesn't change)
RUN npm install

# Copy application code AFTER dependencies are installed
COPY . .

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001 && \
    chown -R nodejs:nodejs /app
USER nodejs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

# Run the application
CMD ["npm", "start"]
DOCKERFILE_EOF

cd ..

echo "🚀 Rebuilding and starting frontend with your actual code..."
docker-compose up --build -d frontend

echo "⏳ Waiting for frontend to start..."
sleep 45

echo "📊 Checking container status..."
docker-compose ps

echo "📋 Checking frontend logs..."
docker-compose logs frontend

echo "🌐 Testing frontend..."
curl -s http://localhost:3000/health || echo "Frontend not responding"

echo "✅ Your actual frontend code has been deployed!"
echo "🌐 Access URLs:"
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
echo "   Frontend: http://$PUBLIC_IP:3000"
echo "   Backend: http://$PUBLIC_IP:8000"
echo "   Jenkins: http://$PUBLIC_IP:8080"
EOF

# Clean up
rm -rf $TEMP_DIR

echo "✅ Actual frontend deployment completed!"
echo "🌐 Your local CI/CD dashboard UI should now be available at:"
echo "   Frontend: http://$EC2_HOST:3000"
