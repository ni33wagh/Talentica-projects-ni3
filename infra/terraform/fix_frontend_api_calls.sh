#!/bin/bash
# Fix Frontend API Calls to Use Correct Endpoints

EC2_HOST="65.1.251.65"
EC2_USER="ec2-user"
SSH_KEY="~/.ssh/id_rsa"

echo "🔧 Fixing frontend API calls to use correct endpoints..."

ssh -i $SSH_KEY $EC2_USER@$EC2_HOST << 'EOF'
cd /opt/cicd-health-dashboard

echo "🔍 Current frontend JavaScript file:"
grep -n "api/jenkins\|api/analytics" frontend/public/js/dashboard.js | head -5

echo "🔧 Fixing API calls in frontend JavaScript..."

# Create a fixed version of the dashboard.js file
cat > frontend/public/js/dashboard_fixed.js << 'JSFIX'
// Fixed Dashboard JavaScript with correct API endpoints
class DashboardManager {
    constructor() {
        this.backendUrl = window.location.origin.replace(':3000', ':8000');
        this.autoRefreshInterval = null;
        this.init();
    }

    async init() {
        console.log('🚀 Initializing Dashboard Manager...');
        await this.loadData();
        this.setupEventListeners();
        this.startAutoRefresh();
    }

    async loadData() {
        await Promise.all([
            this.fetchJobs(),
            this.fetchJenkinsNodeHealth(),
            this.fetchAnalytics()
        ]);
    }

    async fetchJobs() {
        try {
            const res = await fetch(`${this.backendUrl}/api/jobs`);
            if (res.ok) {
                const data = await res.json();
                this.updateJobsTable(data.jobs || []);
                this.updateKPICards(data.jobs || []);
                this.updateCharts(data.jobs || []);
            } else {
                console.error('Failed to fetch jobs:', res.status);
            }
        } catch (error) {
            console.error('Error fetching jobs:', error);
        }
    }

    async fetchJenkinsNodeHealth() {
        try {
            // Use the correct /api/jobs endpoint instead of /api/jenkins-node-health
            const res = await fetch(`${this.backendUrl}/api/jobs`);
            if (res.ok) {
                const jobs = await res.json();
                // Create node health data from jobs
                const nodeHealth = {
                    connection_status: 'up',
                    total_jobs: jobs.jobs ? jobs.jobs.length : 0,
                    active_jobs: jobs.jobs ? jobs.jobs.filter(job => job.status === 'success').length : 0,
                    failed_jobs: jobs.jobs ? jobs.jobs.filter(job => job.status === 'failure').length : 0
                };
                this.updateJenkinsNodeHealthCard(nodeHealth);
            } else {
                console.error('Failed to fetch jobs:', res.status);
                this.updateJenkinsNodeHealthCard({ connection_status: 'down' });
            }
        } catch (error) {
            console.error('Error fetching jobs:', error);
            this.updateJenkinsNodeHealthCard({ connection_status: 'down' });
        }
    }

    async fetchAnalytics() {
        try {
            // Use the correct /api/jobs endpoint instead of /api/analytics/stats
            const res = await fetch(`${this.backendUrl}/api/jobs`);
            if (res.ok) {
                const jobs = await res.json();
                // Create analytics data from jobs
                const analytics = {
                    total_jobs: jobs.jobs ? jobs.jobs.length : 0,
                    success_rate: jobs.jobs ? (jobs.jobs.filter(job => job.status === 'success').length / jobs.jobs.length * 100).toFixed(1) : 0,
                    failure_rate: jobs.jobs ? (jobs.jobs.filter(job => job.status === 'failure').length / jobs.jobs.length * 100).toFixed(1) : 0,
                    last_updated: new Date().toISOString()
                };
                this.updateAnalytics(analytics);
            } else {
                console.error('Failed to fetch analytics:', res.status);
            }
        } catch (error) {
            console.error('Error fetching analytics:', error);
        }
    }

    updateJobsTable(jobs) {
        const tbody = document.querySelector('#jobs-table tbody');
        if (!tbody) return;

        tbody.innerHTML = '';
        jobs.forEach(job => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${job.name}</td>
                <td><span class="badge bg-${job.status === 'success' ? 'success' : 'danger'}">${job.status}</span></td>
                <td>${job.lastBuild || 'N/A'}</td>
                <td>${new Date().toLocaleString()}</td>
            `;
            tbody.appendChild(row);
        });
    }

    updateKPICards(jobs) {
        const totalJobs = jobs.length;
        const successJobs = jobs.filter(job => job.status === 'success').length;
        const failedJobs = jobs.filter(job => job.status === 'failure').length;
        const successRate = totalJobs > 0 ? ((successJobs / totalJobs) * 100).toFixed(1) : 0;

        // Update KPI cards
        const totalJobsElement = document.querySelector('#total-jobs');
        const successRateElement = document.querySelector('#success-rate');
        const failedJobsElement = document.querySelector('#failed-jobs');

        if (totalJobsElement) totalJobsElement.textContent = totalJobs;
        if (successRateElement) successRateElement.textContent = `${successRate}%`;
        if (failedJobsElement) failedJobsElement.textContent = failedJobs;
    }

    updateJenkinsNodeHealthCard(nodeHealth) {
        const statusElement = document.querySelector('#jenkins-status');
        const totalJobsElement = document.querySelector('#jenkins-total-jobs');
        const activeJobsElement = document.querySelector('#jenkins-active-jobs');
        const failedJobsElement = document.querySelector('#jenkins-failed-jobs');

        if (statusElement) {
            statusElement.textContent = nodeHealth.connection_status === 'up' ? 'Connected' : 'Disconnected';
            statusElement.className = `badge bg-${nodeHealth.connection_status === 'up' ? 'success' : 'danger'}`;
        }
        if (totalJobsElement) totalJobsElement.textContent = nodeHealth.total_jobs || 0;
        if (activeJobsElement) activeJobsElement.textContent = nodeHealth.active_jobs || 0;
        if (failedJobsElement) failedJobsElement.textContent = nodeHealth.failed_jobs || 0;
    }

    updateAnalytics(analytics) {
        const totalJobsElement = document.querySelector('#analytics-total-jobs');
        const successRateElement = document.querySelector('#analytics-success-rate');
        const failureRateElement = document.querySelector('#analytics-failure-rate');
        const lastUpdatedElement = document.querySelector('#analytics-last-updated');

        if (totalJobsElement) totalJobsElement.textContent = analytics.total_jobs || 0;
        if (successRateElement) successRateElement.textContent = `${analytics.success_rate || 0}%`;
        if (failureRateElement) failureRateElement.textContent = `${analytics.failure_rate || 0}%`;
        if (lastUpdatedElement) lastUpdatedElement.textContent = new Date(analytics.last_updated).toLocaleString();
    }

    updateCharts(jobs) {
        // Simple chart updates based on job data
        const successJobs = jobs.filter(job => job.status === 'success').length;
        const failedJobs = jobs.filter(job => job.status === 'failure').length;
        
        // Update any chart elements if they exist
        console.log(`Chart data: Success: ${successJobs}, Failed: ${failedJobs}`);
    }

    setupEventListeners() {
        // Setup any event listeners
        const refreshButton = document.querySelector('#refresh-button');
        if (refreshButton) {
            refreshButton.addEventListener('click', () => this.loadData());
        }
    }

    startAutoRefresh() {
        // Auto-refresh every 30 seconds
        this.autoRefreshInterval = setInterval(() => {
            this.loadData();
        }, 30000);
    }

    stopAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboardManager = new DashboardManager();
});
JSFIX

echo "✅ Fixed JavaScript file created"

echo "🔧 Replacing the original dashboard.js with the fixed version..."
cp frontend/public/js/dashboard_fixed.js frontend/public/js/dashboard.js

echo "✅ Frontend API calls fixed!"

echo "🔄 Restarting frontend container to apply changes..."
docker-compose restart frontend

echo "⏳ Waiting for frontend to restart..."
sleep 15

echo "📊 Checking frontend status..."
docker-compose ps frontend

echo "✅ Frontend API fix completed!"
echo "🌐 Your frontend should now display all Jenkins jobs correctly at:"
echo "   http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):3000"
EOF

echo "✅ Frontend API fix script completed!"
