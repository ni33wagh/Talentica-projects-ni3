/**
 * CI/CD Pipeline Health Dashboard JavaScript
 * Handles real-time updates, charts, and data management
 */

class DashboardManager {
    async fetchJenkinsNodeHealth() {
        try {
            const res = await fetch(`${this.backendUrl}/api/jenkins-node-health`);
            if (res.ok) {
                const raw = await res.json();
                // Normalize to expected keys regardless of backend shape
                const nodeHealth = {
                    connection_status: (raw.connection_status || (raw.status || '').toLowerCase()) === 'up' ? 'up' : 'down',
                    num_jobs: typeof raw.num_jobs === 'number' ? raw.num_jobs : (typeof raw.jobs === 'number' ? raw.jobs : (Array.isArray(raw.jobNames) ? raw.jobNames.length : 0)),
                    port: typeof raw.port === 'number' ? raw.port : 8080,
                    jenkins_url: raw.jenkins_url || raw.url || '',
                    jenkins_jobs: Array.isArray(raw.jenkins_jobs) ? raw.jenkins_jobs : (Array.isArray(raw.jobNames) ? raw.jobNames : [])
                };
                window.jenkinsNodeHealth = nodeHealth;
                // If using EJS templating, you may need to trigger a re-render or update DOM manually
                // Only update card after pipelines are refreshed
                this.latestNodeHealth = nodeHealth;
                if (this.pipelines) {
                    this.updateJenkinsNodeHealthCard(nodeHealth);
                }
            }
        } catch (e) {
            console.error('Failed to fetch Jenkins node health:', e);
        }
    }

    updateJenkinsNodeHealthCard(nodeHealth) {
        // Update status badge
        const statusContainer = document.querySelector('.card-body .row .col-md-4');
        if (statusContainer) {
            const badge = statusContainer.querySelector('.badge');
            if (badge) {
                badge.textContent = nodeHealth.connection_status === 'up' ? 'Up & Running' : 'Down';
                badge.className = nodeHealth.connection_status === 'up' ? 'badge bg-success' : 'badge bg-danger';
            }
        }
        // Update jobs count
        const jobsBadge = document.querySelector('.card-body .row .col-md-4:nth-child(2) .badge');
        if (jobsBadge) {
            jobsBadge.textContent = nodeHealth.num_jobs;
        }
        // Update port
        const portBadge = document.querySelector('.card-body .row .col-md-4:nth-child(3) .badge');
        if (portBadge) {
            portBadge.textContent = nodeHealth.port;
        }
        // Update Jenkins URL
        const urlLink = document.querySelector('.card-body a');
        if (urlLink) {
            urlLink.href = nodeHealth.jenkins_url;
            urlLink.textContent = nodeHealth.jenkins_url;
        }
        // Update job names list with correct build count
        const jobList = document.querySelector('.card-body ul.list-group');
        if (jobList) {
            jobList.innerHTML = '';
            if (nodeHealth.jenkins_jobs && nodeHealth.jenkins_jobs.length > 0) {
                nodeHealth.jenkins_jobs.forEach(job => {
                    let buildCount = 0;
                    if (this.pipelines && this.pipelines.length > 0) {
                        const pipeline = this.pipelines.find(p => p.name === job);
                        if (pipeline && pipeline.info && pipeline.info.builds) {
                            buildCount = pipeline.info.builds.length;
                        }
                    }
                    const li = document.createElement('li');
                    li.className = 'list-group-item d-flex justify-content-between align-items-center';
                    li.innerHTML = `<span>${job}</span><span class="badge bg-secondary ms-3">Builds: ${buildCount}</span>`;
                    jobList.appendChild(li);
                });
            } else {
                const span = document.createElement('span');
                span.className = 'text-muted';
                span.textContent = 'No jobs found.';
                jobList.appendChild(span);
            }
        }
    }
    applyFilters() {
        const name = document.getElementById('filter-name').value.trim().toLowerCase();
        const user = document.getElementById('filter-user').value.trim().toLowerCase();
        const status = document.getElementById('filter-status').value;
        const minBuildTime = parseFloat(document.getElementById('filter-build-time').value);

        const rows = document.querySelectorAll('#pipelines-tbody tr');
        rows.forEach(row => {
            let show = true;
            // Filter by name
            if (name) {
                const jobName = row.querySelector('td:first-child strong').textContent.toLowerCase();
                if (!jobName.includes(name)) show = false;
            }
            // Filter by user
            if (user) {
                const userCell = row.querySelector('td:nth-child(3) small.text-muted');
                if (!userCell || !userCell.textContent.toLowerCase().includes(user)) show = false;
            }
            // Filter by status
            if (status) {
                const statusCell = row.querySelector('td:nth-child(2) .badge');
                if (!statusCell || statusCell.textContent.toUpperCase() !== status) show = false;
            }
            // Filter by build time
            if (!isNaN(minBuildTime) && minBuildTime > 0) {
                const buildTimeCell = row.querySelector('td:nth-child(4)');
                const timeText = buildTimeCell ? buildTimeCell.textContent : '';
                const seconds = this.parseDurationToSeconds(timeText);
                if (seconds < minBuildTime) show = false;
            }
            row.style.display = show ? '' : 'none';
        });
    }

    clearFilters() {
        document.getElementById('filter-name').value = '';
        document.getElementById('filter-user').value = '';
        document.getElementById('filter-status').value = '';
        document.getElementById('filter-build-time').value = '';
        this.applyFilters();
    }

    parseDurationToSeconds(durationStr) {
        // Converts "Xm Ys" or "Ys" to seconds
        if (!durationStr) return 0;
        const match = durationStr.match(/(?:(\d+)m)?\s*(\d+(?:\.\d+)?)s/);
        if (!match) return 0;
        const minutes = parseInt(match[1] || '0', 10);
        const seconds = parseFloat(match[2] || '0');
        return minutes * 60 + seconds;
    }
    failedBuilds = [];
    async fetchFailedBuilds() {
        try {
            const res = await fetch(`${this.backendUrl}/api/failed-builds`);
            if (res.ok) {
                let builds = await res.json();
                // Sort by timestamp descending and take top 10
                builds.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
                this.failedBuilds = builds.slice(0, 10);
            }
        } catch (e) {
            console.error('Failed to fetch failed builds:', e);
        }
    }

    updateFailedBuildsBadge() {
        // Show failed builds count badge with top 10 count
        const badge = document.getElementById('failed-builds-count');
        if (badge) {
            const count = this.failedBuilds.length;
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline-block' : 'none';
        }
    }

    showFailedBuilds() {
        if (!this.failedBuilds.length) return;
        let html = '<div class="card shadow" style="min-width:300px;max-width:400px;z-index:9999;position:absolute;top:60px;right:30px;">';
        html += '<div class="card-header bg-danger text-white"><i class="fas fa-bell"></i> Failed Builds</div>';
        html += '<ul class="list-group list-group-flush">';
        this.failedBuilds.forEach(b => {
            const url = b.pipeline_name && b.build_number ? `http://localhost:4000/job/${b.pipeline_name}/${b.build_number}/console` : 'http://localhost:4000/';
            const time = b.timestamp ? new Date(b.timestamp).toLocaleString() : '';
            html += `<li class="list-group-item d-flex justify-content-between align-items-center">
                <span><strong>${b.pipeline_name}</strong> #${b.build_number} <span class="badge bg-danger ms-2">${b.status}</span><br><small class="text-muted">${time}</small></span>
                <a href="${url}" target="_blank" class="btn btn-sm btn-outline-danger" data-pipeline="${b.pipeline_name}" data-build="${b.build_number}">View</a>
            </li>`;
        });
        html += '</ul></div>';
        let dropdown = document.getElementById('failed-builds-dropdown');
        if (!dropdown) {
            dropdown = document.createElement('div');
            dropdown.id = 'failed-builds-dropdown';
            document.body.appendChild(dropdown);
        }
        dropdown.innerHTML = html;
        dropdown.style.display = 'block';
        // Hide dropdown on click outside
        document.addEventListener('click', function handler(e) {
            if (!dropdown.contains(e.target) && e.target.id !== 'failed-builds-alert') {
                dropdown.style.display = 'none';
                document.removeEventListener('click', handler);
            }
        });
        // Remove build from dropdown after viewing and update badge
        dropdown.querySelectorAll('a[data-pipeline][data-build]').forEach(link => {
            link.addEventListener('click', async (e) => {
                const pipeline = link.getAttribute('data-pipeline');
                const build = link.getAttribute('data-build');
                await this.markFailedBuildViewed(pipeline, build);
                link.closest('li').remove();
                // Remove from failedBuilds array
                this.failedBuilds = this.failedBuilds.filter(b => !(b.pipeline_name === pipeline && b.build_number == build));
                this.updateFailedBuildsBadge();
                // Hide dropdown if no failed builds left
                if (this.failedBuilds.length === 0) {
                    dropdown.style.display = 'none';
                }
            });
        });
    }

    async markFailedBuildViewed(pipeline_name, build_number) {
        try {
            await fetch(`${this.backendUrl}/api/failed-builds/viewed`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pipeline_name, build_number })
            });
            // Re-fetch failed builds from backend to ensure sync
            await this.fetchFailedBuilds();
            this.showFailedBuilds();
        } catch (e) {
            console.error('Failed to mark failed build as viewed:', e);
        }
    }
    constructor() {
        this.pipelines = [];
        this.overallMetrics = {};
        this.charts = {};
        this.socket = null;
        // backendUrl will be set by initializeDashboard
        this.backendUrl = '';
        this.currentFilter = 'all';
        this.refreshInterval = null;
        window.dashboardManager = this;
        this.init();
        // Auto-refresh Jenkins node health every 30 seconds
        setInterval(() => {
            this.fetchJenkinsNodeHealth();
        }, 30000);
    }
    
    init() {
        this.setupEventListeners();
        this.setupWebSocket();
        // Auto-refresh every 30 seconds, but do not block UI
        this.startAutoRefresh();
    // Setup filter buttons
    document.getElementById('apply-filters').addEventListener('click', () => this.applyFilters());
    document.getElementById('clear-filters').addEventListener('click', () => this.clearFilters());
    }
    
    setupEventListeners() {
        // Setup refresh button
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="refresh"]')) {
                this.refreshData();
            }
        });
        
        // Setup filter buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-filter]')) {
                const filter = e.target.dataset.filter;
                this.filterPipelines(filter);
            }
        });
    }
    
    setupWebSocket() {
        try {
            // Initialize Socket.IO connection to backend using correct URL
            // Note: If using Flask-SocketIO backend, use Socket.IO v3.x client for best compatibility
            this.socket = io(this.backendUrl, {
                transports: ['websocket', 'polling'],
                withCredentials: true
            });
            this.socket.on('connect', () => {
                this.updateConnectionStatus('Connected', 'success');
                console.log('Connected to backend via WebSocket');
            });
            this.socket.on('disconnect', () => {
                this.updateConnectionStatus('Disconnected', 'danger');
                console.log('Disconnected from backend');
            });
            this.socket.on('pipeline_update', (data) => {
                this.handlePipelineUpdate(data);
            });
            this.socket.on('build_update', (data) => {
                this.handleBuildUpdate(data);
            });
        } catch (error) {
            console.error('WebSocket setup failed:', error);
            this.updateConnectionStatus('WebSocket Error', 'warning');
        }
    }
    
    updateConnectionStatus(status, type) {
        const statusElement = document.getElementById('connection-status');
        const iconElement = statusElement.previousElementSibling;
        
        if (statusElement && iconElement) {
            statusElement.textContent = status;
            iconElement.className = `fas fa-circle text-${type} me-1`;
        }
    }
    
    startAutoRefresh() {
        if (this.refreshInterval) clearInterval(this.refreshInterval);
        this.refreshInterval = setInterval(() => {
            this.refreshData();
        }, 30000); // 30 seconds
    }
    
    async refreshData() {
    await this.fetchFailedBuilds();
    this.updateFailedBuildsBadge();
        try {
            const isManual = !!window._manualRefresh;
            if (isManual) this.showLoading(true);
            // First, trigger backend data collection, pass manual flag
            await fetch(`${this.backendUrl}/api/trigger-collection?manual=${isManual ? '1' : '0'}`);
            // Fetch fresh data from backend
            const [pipelinesResponse, metricsResponse] = await Promise.all([
                fetch(`${this.backendUrl}/api/pipelines`),
                fetch(`${this.backendUrl}/api/metrics/overall`)
            ]);
            if (pipelinesResponse.ok && metricsResponse.ok) {
                const pipelines = await pipelinesResponse.json();
                const metrics = await metricsResponse.json();
                let newBuildDetected = false;
                for (let i = 0; i < pipelines.length; i++) {
                    const pipeline = pipelines[i];
                    // Fetch the latest 50 builds for each pipeline
                    const buildsRes = await fetch(`${this.backendUrl}/api/pipelines/${encodeURIComponent(pipeline.name)}/builds?limit=50`);
                    if (buildsRes.ok) {
                        pipeline.info = pipeline.info || {};
                        const newBuildsRaw = await buildsRes.json();
                        // Normalize build objects from various backends
                        const newBuilds = (Array.isArray(newBuildsRaw) ? newBuildsRaw : []).map(b => ({
                            status: b.status || b.result || '',
                            duration: typeof b.duration === 'number' ? b.duration : (typeof b.durationMs === 'number' ? b.durationMs / 1000 : 0),
                            build_number: typeof b.build_number === 'number' ? b.build_number : b.number,
                            number: typeof b.number === 'number' ? b.number : b.build_number,
                            timestamp: b.timestamp,
                            url: b.url
                        }));
                        // Compare with previous builds
                        const prevBuilds = (this.pipelines[i] && this.pipelines[i].info && this.pipelines[i].info.builds) || [];
                        if (newBuilds.length > 0 && (!prevBuilds.length || (newBuilds[0].number !== prevBuilds[0].number && newBuilds[0].build_number !== prevBuilds[0].build_number))) {
                            newBuildDetected = true;
                            console.log(`[AutoRefresh] New build detected for pipeline: ${pipeline.name}, build number: ${newBuilds[0].number || newBuilds[0].build_number}`);
                        }
                        pipeline.info.builds = newBuilds;
                    }
                }
                // Always update dashboard every interval
                console.log(`[AutoRefresh] Dashboard updated. New build detected: ${newBuildDetected}, Manual: ${isManual}`);
                this.updateDashboard(pipelines, metrics);
            } else {
                throw new Error('Failed to fetch data');
            }
        } catch (error) {
            console.error('Error refreshing data:', error);
            this.showError('Failed to refresh data: ' + error.message);
        } finally {
            if (!!window._manualRefresh) this.showLoading(false);
            window._manualRefresh = false;
        }
    }
    
    updateDashboard(pipelines, metrics) {
        this.pipelines = pipelines;
        // Support nested analytics shape { success: true, data: { metrics: {...} } }
        if (metrics && metrics.success === true && metrics.data) {
            // If a rich summary object, prefer summary.metrics but also expose flattened keys for cards
            const m = metrics.data.metrics || {};
            this.overallMetrics = {
                ...m,
                // Also include top-level aliases commonly used elsewhere
                total_pipelines: typeof m.total_pipelines === 'number' ? m.total_pipelines : undefined,
                total_builds: typeof m.total_builds === 'number' ? m.total_builds : undefined,
                avg_duration: typeof m.avg_build_time === 'number' ? m.avg_build_time : undefined,
                success_rate: typeof m.success_rate === 'number' ? m.success_rate : undefined
            };
        } else {
            this.overallMetrics = metrics || {};
        }

        this.updateOverviewCards();
        this.updateCharts();
        this.updatePipelinesTable();
        // Update Jenkins Node Health card with latest build counts
        if (this.latestNodeHealth) {
            this.updateJenkinsNodeHealthCard(this.latestNodeHealth);
        }
    }
    
    updateOverviewCards() {
        // Derive metrics robustly across legacy/new API shapes
        const getFirstNumber = (keys, fallback = 0) => {
            for (let i = 0; i < keys.length; i++) {
                const val = this.overallMetrics ? this.overallMetrics[keys[i]] : undefined;
                if (typeof val === 'number' && !Number.isNaN(val)) return val;
            }
            return fallback;
        };
        const normalizeSuccessRate = (val) => {
            if (typeof val !== 'number' || Number.isNaN(val)) return 0;
            // If value looks like fraction 0..1, convert to %
            if (val > 0 && val <= 1) return val * 100;
            // If value already in percent (0..100), clamp
            if (val >= 0 && val <= 100) return val;
            // Fallback: keep as-is but clamp to [0,100]
            return Math.max(0, Math.min(100, val));
        };
        const computeTotalBuildsFromPipelines = () => {
            let total = 0;
            (this.pipelines || []).forEach(p => {
                if (p && p.info && Array.isArray(p.info.builds)) total += p.info.builds.length;
            });
            return total;
        };

        // total pipelines: prefer metrics keys then fallback to pipelines length
        const totalPipelines = getFirstNumber(['totalPipelines', 'pipelinesCount', 'total_pipelines'], (this.pipelines || []).length);
        this.updateCard('total-pipelines', totalPipelines);

        // success rate: support success_rate, successRatePercent, successRate (fraction)
        const rawSuccess = getFirstNumber(['success_rate', 'successRatePercent', 'successRate'], 0);
        const successRate = normalizeSuccessRate(rawSuccess);
        this.updateCard('success-rate', `${successRate.toFixed(1)}%`);

        // average build time: prefer seconds, else convert minutes to seconds
        let avgSeconds = getFirstNumber(['avg_duration', 'avgBuildTimeSeconds'], undefined);
        if (typeof avgSeconds !== 'number' || Number.isNaN(avgSeconds)) {
            const mins = getFirstNumber(['avgBuildTimeMinutes'], undefined);
            if (typeof mins === 'number' && !Number.isNaN(mins)) avgSeconds = mins * 60;
        }
        if (typeof avgSeconds !== 'number' || Number.isNaN(avgSeconds)) avgSeconds = 0;
        this.updateCard('avg-build-time', this.formatDuration(avgSeconds));

        // total builds: support multiple keys, else compute from pipelines
        let totalBuilds = getFirstNumber(['total', 'totalBuilds', 'totalBuildsCount', 'total_builds'], undefined);
        if (typeof totalBuilds !== 'number' || Number.isNaN(totalBuilds)) {
            totalBuilds = computeTotalBuildsFromPipelines();
        }
        this.updateCard('total-builds', totalBuilds);

        // success/failure counts from metrics if available, else compute from builds
        let successCount = getFirstNumber(['successCount', 'successful_jobs'], undefined);
        let failureCount = getFirstNumber(['failureCount', 'failed_jobs'], undefined);
        if (typeof successCount !== 'number' || typeof failureCount !== 'number') {
            let s = 0, f = 0;
            (this.pipelines || []).forEach(p => {
                const builds = (p && p.info && Array.isArray(p.info.builds)) ? p.info.builds : [];
                builds.forEach(b => {
                    const st = (b.status || '').toUpperCase();
                    if (st === 'SUCCESS') s++;
                    else if (st === 'FAILURE' || st === 'FAILED' || st === 'UNSTABLE' || st === 'ABORTED') f++;
                });
            });
            successCount = s;
            failureCount = f;
        }
        this.updateCard('success-count', successCount);
        this.updateCard('failure-count', failureCount);
    }
    
    updateCard(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
        }
    }
    
    updateCharts() {
        this.updateStatusChart();
        this.updateJobTrendChart();
        this.updateDurationChart();
    }
    updateJobTrendChart() {
        const ctx = document.getElementById('jobTrendChart');
        if (!ctx) return;

        // Count jobs by presence of statuses across their builds
        const counts = { Success: 0, Failure: 0, Building: 0, Unstable: 0, Aborted: 0, 'Not Built': 0, Other: 0 };
        (this.pipelines || []).forEach(pipeline => {
            let seen = new Set();
            const builds = (pipeline.info && Array.isArray(pipeline.info.builds)) ? pipeline.info.builds : [];
            builds.forEach(b => {
                const s = (b.status || '').toUpperCase();
                if (s === 'SUCCESS') seen.add('Success');
                else if (s === 'FAILURE' || s === 'FAILED') seen.add('Failure');
                else if (s === 'BUILDING' || s === 'IN_PROGRESS') seen.add('Building');
                else if (s === 'UNSTABLE') seen.add('Unstable');
                else if (s === 'ABORTED') seen.add('Aborted');
                else if (s === 'NOT_BUILT' || s === 'NOT_BUILT') seen.add('Not Built');
                else if (s) seen.add('Other');
            });
            if (seen.size === 0) seen.add('Other');
            seen.forEach(k => { counts[k] = (counts[k] || 0) + 1; });
        });

        const labels = Object.keys(counts);
        const data = labels.map(l => counts[l]);
        const colors = ['#10B981','#EF4444','#F59E0B','#F97316','#8B5CF6','#6B7280','#9CA3AF'];

        if (this.charts.jobTrendChart) {
            this.charts.jobTrendChart.destroy();
        }
        this.charts.jobTrendChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors.slice(0, labels.length),
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                return `${label}: ${value}`;
                            }
                        }
                    }
                }
            }
        });
    }

    updateStatusChart() {
        const ctx = document.getElementById('statusChart');
        if (!ctx) return;
        
        if (this.charts.statusChart) {
            this.charts.statusChart.destroy();
        }
        
        // Count builds by status across all pipelines
        const counts = { Success: 0, Failure: 0, Building: 0, Unstable: 0, Aborted: 0, 'Not Built': 0, Other: 0 };
        (this.pipelines || []).forEach(pipeline => {
            const builds = (pipeline.info && Array.isArray(pipeline.info.builds)) ? pipeline.info.builds : [];
            builds.forEach(b => {
                const s = (b.status || '').toUpperCase();
                if (s === 'SUCCESS') counts.Success++;
                else if (s === 'FAILURE' || s === 'FAILED') counts.Failure++;
                else if (s === 'BUILDING' || s === 'IN_PROGRESS') counts.Building++;
                else if (s === 'UNSTABLE') counts.Unstable++;
                else if (s === 'ABORTED') counts.Aborted++;
                else if (s === 'NOT_BUILT') counts['Not Built']++;
                else counts.Other++;
            });
        });

        const labels = Object.keys(counts);
        const data = labels.map(l => counts[l]);
        const colors = ['#10B981','#EF4444','#F59E0B','#F97316','#8B5CF6','#6B7280','#9CA3AF'];

        this.charts.statusChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors.slice(0, labels.length),
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                return `${label}: ${value}`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    updateDurationChart() {
        const ctx = document.getElementById('durationChart');
        if (!ctx) return;
        
        // Destroy existing chart if it exists
        if (this.charts.durationChart) {
            this.charts.durationChart.destroy();
        }
        
        const durationData = this.calculateDurationData();
        
        this.charts.durationChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: durationData.labels,
                datasets: [{
                    label: 'Build Duration (minutes)',
                    data: durationData.durations,
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Duration (minutes)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Build Number'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                }
            }
        });
    }
    
    calculateStatusCounts() {
        const counts = { success: 0, failure: 0, inProgress: 0, unknown: 0 };
        
        this.pipelines.forEach(pipeline => {
            // Prefer status field, fallback to color
            const status = pipeline.status ? pipeline.status.toUpperCase() : (pipeline.color || '').toLowerCase();
            if (status === 'SUCCESS' || status.includes('blue')) counts.success++;
            else if (status === 'FAILURE' || status.includes('red')) counts.failure++;
            else if (status === 'IN_PROGRESS' || status.includes('yellow')) counts.inProgress++;
            else counts.unknown++;
        });
        
        return counts;
    }
    
    calculateDurationData() {
        // Aggregate latest 50 builds from all pipelines
        let allBuilds = [];
        this.pipelines.forEach(pipeline => {
            if (pipeline.info && Array.isArray(pipeline.info.builds)) {
                allBuilds = allBuilds.concat(
                    pipeline.info.builds.filter(b => typeof b.duration === 'number' && b.duration > 0 && b.build_number)
                );
            }
        });
        // Sort by build number descending and take latest 50
        allBuilds.sort((a, b) => b.build_number - a.build_number);
        const builds = allBuilds.slice(0, 50).sort((a, b) => a.build_number - b.build_number);
        if (builds.length === 0) {
            return {
                labels: ['#101', '#102', '#103', '#104', '#105', '#106', '#107', '#108', '#109', '#110'],
                durations: ['2.5', '3.1', '2.8', '3.0', '2.7', '3.2', '2.9', '3.3', '2.6', '3.0']
            };
        }
        return {
            labels: builds.map(b => `#${b.build_number}`),
            durations: builds.map(b => (b.duration / 60).toFixed(1))
        };
    }
    
    updatePipelinesTable() {
        const tbody = document.getElementById('pipelines-tbody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        this.pipelines.forEach(pipeline => {
            const row = this.createPipelineRow(pipeline);
            tbody.appendChild(row);
        });
    }
    
    createPipelineRow(pipeline) {
        const row = document.createElement('tr');
        const status = this.getPipelineStatus(pipeline);
        const lastBuild = this.getLastBuildInfo(pipeline);
        const buildTime = this.getBuildTime(pipeline);
        let triggeredBy = 'admin';
        if (lastBuild && lastBuild.user) {
            triggeredBy = lastBuild.user;
        }
        // Calculate success and failure percentage
        let successCount = 0, failureCount = 0;
        if (pipeline.info && pipeline.info.builds) {
            pipeline.info.builds.forEach(b => {
                if (b.status === 'SUCCESS') successCount++;
                if (b.status === 'FAILURE') failureCount++;
            });
        }
        const totalBuilds = successCount + failureCount;
        const successRate = totalBuilds > 0 ? (successCount / totalBuilds) * 100 : 0;
        const failureRate = totalBuilds > 0 ? (failureCount / totalBuilds) * 100 : 0;
        // Health status
        const healthStatus = failureRate < 20 ? 'Healthy' : 'Unhealthy';
        const healthColor = healthStatus === 'Healthy' ? 'success' : 'danger';
        row.innerHTML = `
            <td>
                <strong>${pipeline.name}</strong>
                <br>
                <small class="text-muted">${pipeline.url || ''}</small>
            </td>
            <td>
                <span class="badge bg-${status.color}">${status.text}</span>
                <br>
                <span class="badge bg-${healthColor} mt-1">${healthStatus}</span>
            </td>
            <td>
                ${lastBuild ? `#${lastBuild.number}` : 'N/A'}
                <br>
                <small class="text-muted">${lastBuild ? this.formatTimestamp(lastBuild.timestamp) : ''}</small>
            </td>
            <td>${buildTime}</td>
            <td>${triggeredBy}</td>
            <td>
                <div style="display: flex; gap: 4px; align-items: center;">
                    <div class="progress" style="height: 10px; width: 60px; background-color: #e9ecef;">
                        <div class="progress-bar bg-success" style="width: ${successRate}%; height: 10px;"></div>
                    </div>
                    <span class="text-success" style="font-size: 0.85em;">${successRate.toFixed(1)}%</span>
                </div>
            </td>
            <td>
                <div style="display: flex; gap: 4px; align-items: center;">
                    <div class="progress" style="height: 10px; width: 60px; background-color: #e9ecef;">
                        <div class="progress-bar bg-danger" style="width: ${failureRate}%; height: 10px;"></div>
                    </div>
                    <span class="text-danger" style="font-size: 0.85em;">${failureRate.toFixed(1)}%</span>
                </div>
            </td>
            <td>
                <a href="/pipeline/${encodeURIComponent(pipeline.name)}" class="btn btn-sm btn-outline-primary">
                    <i class="fas fa-eye"></i> View
                </a>
                <button class="btn btn-sm btn-outline-secondary" onclick="refreshPipeline('${pipeline.name}')">
                    <i class="fas fa-sync-alt"></i>
                </button>
            </td>
        `;
        return row;
    }
    
    getPipelineStatus(pipeline) {
        const color = pipeline.color || '';
        
        if (color.includes('blue')) return { text: 'Success', color: 'success' };
        if (color.includes('red')) return { text: 'Failure', color: 'danger' };
        if (color.includes('yellow')) return { text: 'In Progress', color: 'warning' };
        if (color.includes('grey')) return { text: 'Disabled', color: 'secondary' };
        
        return { text: 'Unknown', color: 'secondary' };
    }
    
    getLastBuildInfo(pipeline) {
        if (pipeline.info && pipeline.info.builds && pipeline.info.builds.length > 0) {
            return pipeline.info.builds[0]; // First build is the latest
        }
        return null;
    }
    
    getBuildTime(pipeline) {
        const lastBuild = this.getLastBuildInfo(pipeline);
        if (lastBuild && lastBuild.duration) {
            return this.formatDuration(lastBuild.duration);
        }
        return 'N/A';
    }
    
    getSuccessRate(pipeline) {
        // This would need to be calculated from actual build data
        // For now, return a placeholder
        return Math.random() * 100;
    }
    
    formatDuration(seconds) {
        if (!seconds) return 'N/A';
        
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        
        if (minutes > 0) {
            return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
        }
        return `${remainingSeconds.toFixed(1)}s`;
    }
    
    formatTimestamp(timestamp) {
        if (!timestamp) return 'N/A';
        
        const date = new Date(timestamp);
        return moment(date).fromNow();
    }
    
    filterPipelines(filter) {
        this.currentFilter = filter;
        
        const rows = document.querySelectorAll('#pipelines-tbody tr');
        
        rows.forEach(row => {
            const statusCell = row.querySelector('td:nth-child(2) .badge');
            if (statusCell) {
                const status = statusCell.textContent.toLowerCase();
                
                let show = true;
                if (filter === 'success' && !status.includes('success')) show = false;
                if (filter === 'failure' && !status.includes('failure')) show = false;
                
                row.style.display = show ? '' : 'none';
            }
        });
        
        // Update active filter button
        document.querySelectorAll('[data-filter]').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-filter="${filter}"]`)?.classList.add('active');
    }
    
    handlePipelineUpdate(data) {
        console.log('Pipeline update received:', data);
        // Update specific pipeline data
        this.refreshData();
    }
    
    handleBuildUpdate(data) {
        console.log('Build update received:', data);
        // Update specific build data
        this.refreshData();
    }
    
    showLoading(show) {
        const modal = document.getElementById('loadingModal');
        if (modal) {
            if (show) {
                new bootstrap.Modal(modal).show();
            } else {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) {
                    modalInstance.hide();
                }
            }
        }
    }
    
    showError(message) {
        // Create and show error alert
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show';
        alertDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container-fluid');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);
        }
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    async loadAdvice(pipelineName) {
        try {
            const url = new URL(`${this.backendUrl}/api/advice`);
            if (pipelineName) url.searchParams.set('pipeline', pipelineName);
            const res = await fetch(url.toString());
            if (!res.ok) throw new Error('Failed to load advice');
            const data = await res.json();
            const adviceList = document.getElementById('advice-list');
            const failuresList = document.getElementById('failures-list');
            if (adviceList) adviceList.innerHTML = (data.advice || []).map(a => `<li>${a}</li>`).join('');
            if (failuresList) failuresList.innerHTML = (data.recent_failures || []).map(f => `<li>${f.pipeline_name} #${f.build_number} - ${f.status}</li>`).join('');

            // Render resource links
            let resourcesEl = document.getElementById('resources-list');
            if (!resourcesEl) {
                const adviceContainer = document.getElementById('advice-content');
                if (adviceContainer) {
                    const hdr = document.createElement('h6');
                    hdr.className = 'mt-3';
                    hdr.textContent = 'Helpful Resources';
                    adviceContainer.appendChild(hdr);
                    resourcesEl = document.createElement('ul');
                    resourcesEl.id = 'resources-list';
                    adviceContainer.appendChild(resourcesEl);
                }
            }
            if (resourcesEl) {
                resourcesEl.innerHTML = (data.resources || []).map(r => `<li><a href="${r.url}" target="_blank">${r.title}</a></li>`).join('');
            }
        } catch (e) {
            this.showError('Failed to load advice');
        }
    }

    async sendAdviceEmail(recipientsCsv, pipelineName) {
        try {
            const recipients = recipientsCsv.split(',').map(s => s.trim()).filter(Boolean);
            const res = await fetch(`${this.backendUrl}/api/email/advice`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ recipients, pipeline: pipelineName })
            });
            const status = document.getElementById('email-status');
            if (res.ok) {
                if (status) status.innerHTML = '<div class="alert alert-success">Email sent successfully.</div>';
            } else {
                const txt = await res.text();
                if (status) status.innerHTML = `<div class="alert alert-danger">Failed to send email: ${txt}</div>`;
            }
        } catch (e) {
            const status = document.getElementById('email-status');
            if (status) status.innerHTML = `<div class="alert alert-danger">Error: ${e.message}</div>`;
        }
    }
}

// Global functions for HTML onclick handlers
function refreshData() {
    window._manualRefresh = true;
    if (window.dashboardManager) {
        window.dashboardManager.refreshData();
    }
}

// Add a button to trigger backend data collection manually
document.addEventListener('DOMContentLoaded', () => {
    const nav = document.querySelector('.navbar-nav');
    if (nav) {
        const triggerBtn = document.createElement('button');
        triggerBtn.className = 'btn btn-outline-warning btn-sm ms-2';
        triggerBtn.innerHTML = '<i class="fas fa-bolt"></i> Reload from Jenkins';
        triggerBtn.onclick = async () => {
            if (window.dashboardManager) {
                window.dashboardManager.showLoading(true);
                try {
                    const res = await fetch(`${window.dashboardManager.backendUrl}/api/trigger-collection`);
                    if (res.ok) {
                        window.dashboardManager.showError('Backend data collection triggered. Please refresh after a few seconds.');
                    } else {
                        window.dashboardManager.showError('Failed to trigger backend data collection.');
                    }
                } catch (e) {
                    window.dashboardManager.showError('Error triggering backend data collection.');
                } finally {
                    window.dashboardManager.showLoading(false);
                }
            }
        };
        nav.appendChild(triggerBtn);
    }
});

function filterPipelines(filter) {
    if (window.dashboardManager) {
        window.dashboardManager.filterPipelines(filter);
    }
}

function refreshPipeline(pipelineName) {
    if (window.dashboardManager) {
        window.dashboardManager.refreshData();
    }
}

// Initialize dashboard when DOM is loaded
function initializeDashboard(data) {
    window.dashboardManager = new DashboardManager();
    window.dashboardManager.backendUrl = data.backendUrl;
    window.dashboardManager.updateDashboard(data.pipelines, data.overallMetrics);
}

// Tab helpers bound from HTML buttons
async function loadAdvice() {
    const val = document.getElementById('advice-pipeline')?.value || '';
    if (window.dashboardManager) {
        await window.dashboardManager.loadAdvice(val);
    }
}

async function sendAdviceEmail() {
    const recipients = document.getElementById('email-recipients')?.value || '';
    const pipeline = document.getElementById('email-pipeline')?.value || '';
    if (window.dashboardManager) {
        await window.dashboardManager.sendAdviceEmail(recipients, pipeline);
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DashboardManager;
}
