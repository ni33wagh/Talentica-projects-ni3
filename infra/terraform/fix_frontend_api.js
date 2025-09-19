// Fixed frontend JavaScript with correct API endpoints
// This will replace the problematic API calls in the frontend

const fixedJavaScript = `
// Fix the fetchJenkinsNodeHealth method to use correct endpoint
async fetchJenkinsNodeHealth() {
    try {
        // Use the correct /api/jobs endpoint instead of /api/jenkins-node-health
        const res = await fetch(\`\${this.backendUrl}/api/jobs\`);
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

// Fix the fetchAnalytics method to use correct endpoint
async fetchAnalytics() {
    try {
        // Use the correct /api/jobs endpoint instead of /api/analytics/stats
        const res = await fetch(\`\${this.backendUrl}/api/jobs\`);
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
`;

console.log("Fixed JavaScript code created. This needs to be applied to the frontend.");
