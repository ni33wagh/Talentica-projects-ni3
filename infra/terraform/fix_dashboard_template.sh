#!/bin/bash
# Fix Dashboard Template to Use Server-Side KPI Data

EC2_HOST="65.1.251.65"
EC2_USER="ec2-user"
SSH_KEY="~/.ssh/id_rsa"

echo "🔧 Fixing dashboard template to use server-side KPI data..."

ssh -i $SSH_KEY $EC2_USER@$EC2_HOST << 'EOF'
cd /opt/cicd-health-dashboard

echo "🔧 Updating dashboard template to use server-side KPI data..."

# Update the KPI cards in the dashboard template to use server-side data
sed -i 's/id="total-pipelines">-</id="total-pipelines"><%= kpiData ? kpiData.totalPipelines : 0 %></g' frontend/views/dashboard.ejs
sed -i 's/id="success-rate">-</id="success-rate"><%= kpiData ? kpiData.successRate : 0 %>%</g' frontend/views/dashboard.ejs
sed -i 's/id="failed-jobs">-</id="failed-jobs"><%= kpiData ? kpiData.failedJobs : 0 %></g' frontend/views/dashboard.ejs

# Also update any other KPI elements that might exist
sed -i 's/id="active-jobs">-</id="active-jobs"><%= kpiData ? kpiData.activeJobs : 0 %></g' frontend/views/dashboard.ejs

echo "✅ Dashboard template updated with server-side KPI data"

echo "🔄 Rebuilding frontend container to apply template changes..."
docker-compose stop frontend
docker-compose rm -f frontend
docker-compose build frontend
docker-compose up -d frontend

echo "⏳ Waiting for frontend to start..."
sleep 30

echo "📊 Checking frontend status..."
docker-compose ps frontend

echo "📋 Checking frontend logs..."
docker-compose logs frontend | tail -10

echo "✅ Dashboard template fix completed!"
echo "🌐 Your frontend should now display all KPI cards with real data at:"
echo "   http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):3000"

EOF

echo "✅ Dashboard template fix completed!"
echo "🎯 The frontend will now:"
echo "   • Display KPI cards with server-side data"
echo "   • Show total pipelines, success rate, failed jobs"
echo "   • Update all metrics from server data"
echo "   • No longer rely on JavaScript for KPI updates"
echo "🌐 Check your frontend at: http://$EC2_HOST:3000"
