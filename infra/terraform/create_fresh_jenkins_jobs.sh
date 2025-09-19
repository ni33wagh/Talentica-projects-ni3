#!/bin/bash
# Create Fresh Jenkins Jobs - 5 Successful + 3 Failed Pipelines

EC2_HOST="65.1.251.65"
EC2_USER="ec2-user"
SSH_KEY="~/.ssh/id_rsa"

echo "🗑️ Dropping corrupted Jenkins jobs and creating fresh sample jobs..."

ssh -i $SSH_KEY $EC2_USER@$EC2_HOST << 'EOF'
cd /opt/cicd-health-dashboard

echo "🛑 Stopping Jenkins..."
docker-compose stop jenkins

echo "🗑️ Removing corrupted jobs..."
sudo rm -rf /var/lib/docker/volumes/cicd-health-dashboard_jenkins_home/_data/jobs/*

echo "📁 Creating fresh jobs directory..."
sudo mkdir -p /var/lib/docker/volumes/cicd-health-dashboard_jenkins_home/_data/jobs

echo "🔧 Creating 5 successful pipeline jobs..."

# Job 1: Successful Pipeline - Build Project
sudo mkdir -p /var/lib/docker/volumes/cicd-health-dashboard_jenkins_home/_data/jobs/build-project
cat > /tmp/build-project-config.xml << 'XML'
<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job@2.45">
  <description>Successful build pipeline for main project</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@2.94">
    <script>pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                echo 'Building project...'
                sleep 2
            }
        }
        stage('Test') {
            steps {
                echo 'Running tests...'
                sleep 1
            }
        }
        stage('Deploy') {
            steps {
                echo 'Deploying to staging...'
                sleep 1
            }
        }
    }
}</script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>
XML

# Job 2: Successful Pipeline - Test Suite
sudo mkdir -p /var/lib/docker/volumes/cicd-health-dashboard_jenkins_home/_data/jobs/test-suite
cat > /tmp/test-suite-config.xml << 'XML'
<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job@2.45">
  <description>Comprehensive test suite pipeline</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@2.94">
    <script>pipeline {
    agent any
    stages {
        stage('Unit Tests') {
            steps {
                echo 'Running unit tests...'
                sleep 1
            }
        }
        stage('Integration Tests') {
            steps {
                echo 'Running integration tests...'
                sleep 2
            }
        }
        stage('E2E Tests') {
            steps {
                echo 'Running end-to-end tests...'
                sleep 1
            }
        }
    }
}</script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>
XML

# Job 3: Successful Pipeline - API Tests
sudo mkdir -p /var/lib/docker/volumes/cicd-health-dashboard_jenkins_home/_data/jobs/api-tests
cat > /tmp/api-tests-config.xml << 'XML'
<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job@2.45">
  <description>API testing pipeline</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@2.94">
    <script>pipeline {
    agent any
    stages {
        stage('API Health Check') {
            steps {
                echo 'Checking API health...'
                sleep 1
            }
        }
        stage('API Tests') {
            steps {
                echo 'Running API tests...'
                sleep 2
            }
        }
        stage('Performance Tests') {
            steps {
                echo 'Running performance tests...'
                sleep 1
            }
        }
    }
}</script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>
XML

# Job 4: Successful Pipeline - Security Scan
sudo mkdir -p /var/lib/docker/volumes/cicd-health-dashboard_jenkins_home/_data/jobs/security-scan
cat > /tmp/security-scan-config.xml << 'XML'
<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job@2.45">
  <description>Security scanning pipeline</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@2.94">
    <script>pipeline {
    agent any
    stages {
        stage('Dependency Scan') {
            steps {
                echo 'Scanning dependencies...'
                sleep 1
            }
        }
        stage('Code Analysis') {
            steps {
                echo 'Analyzing code for vulnerabilities...'
                sleep 2
            }
        }
        stage('Security Report') {
            steps {
                echo 'Generating security report...'
                sleep 1
            }
        }
    }
}</script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>
XML

# Job 5: Successful Pipeline - Deployment
sudo mkdir -p /var/lib/docker/volumes/cicd-health-dashboard_jenkins_home/_data/jobs/deployment
cat > /tmp/deployment-config.xml << 'XML'
<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job@2.45">
  <description>Production deployment pipeline</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@2.94">
    <script>pipeline {
    agent any
    stages {
        stage('Build Image') {
            steps {
                echo 'Building Docker image...'
                sleep 2
            }
        }
        stage('Deploy to Staging') {
            steps {
                echo 'Deploying to staging...'
                sleep 1
            }
        }
        stage('Deploy to Production') {
            steps {
                echo 'Deploying to production...'
                sleep 2
            }
        }
    }
}</script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>
XML

echo "🔧 Creating 3 failed pipeline jobs..."

# Job 6: Failed Pipeline - Database Migration
sudo mkdir -p /var/lib/docker/volumes/cicd-health-dashboard_jenkins_home/_data/jobs/database-migration
cat > /tmp/database-migration-config.xml << 'XML'
<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job@2.45">
  <description>Database migration pipeline (fails)</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@2.94">
    <script>pipeline {
    agent any
    stages {
        stage('Backup Database') {
            steps {
                echo 'Backing up database...'
                sleep 1
            }
        }
        stage('Run Migration') {
            steps {
                echo 'Running database migration...'
                sleep 2
                error 'Migration failed: Connection timeout'
            }
        }
        stage('Verify Migration') {
            steps {
                echo 'Verifying migration...'
                sleep 1
            }
        }
    }
}</script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>
XML

# Job 7: Failed Pipeline - Load Testing
sudo mkdir -p /var/lib/docker/volumes/cicd-health-dashboard_jenkins_home/_data/jobs/load-testing
cat > /tmp/load-testing-config.xml << 'XML'
<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job@2.45">
  <description>Load testing pipeline (fails)</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@2.94">
    <script>pipeline {
    agent any
    stages {
        stage('Setup Load Test') {
            steps {
                echo 'Setting up load test environment...'
                sleep 1
            }
        }
        stage('Run Load Test') {
            steps {
                echo 'Running load tests...'
                sleep 2
                error 'Load test failed: Performance threshold exceeded'
            }
        }
        stage('Generate Report') {
            steps {
                echo 'Generating load test report...'
                sleep 1
            }
        }
    }
}</script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>
XML

# Job 8: Failed Pipeline - Integration Tests
sudo mkdir -p /var/lib/docker/volumes/cicd-health-dashboard_jenkins_home/_data/jobs/integration-tests
cat > /tmp/integration-tests-config.xml << 'XML'
<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job@2.45">
  <description>Integration tests pipeline (fails)</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@2.94">
    <script>pipeline {
    agent any
    stages {
        stage('Setup Environment') {
            steps {
                echo 'Setting up test environment...'
                sleep 1
            }
        }
        stage('Run Integration Tests') {
            steps {
                echo 'Running integration tests...'
                sleep 2
                error 'Integration test failed: Service unavailable'
            }
        }
        stage('Cleanup') {
            steps {
                echo 'Cleaning up test environment...'
                sleep 1
            }
        }
    }
}</script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>
XML

echo "📦 Installing job configurations..."

# Copy all job configurations
sudo cp /tmp/build-project-config.xml /var/lib/docker/volumes/cicd-health-dashboard_jenkins_home/_data/jobs/build-project/config.xml
sudo cp /tmp/test-suite-config.xml /var/lib/docker/volumes/cicd-health-dashboard_jenkins_home/_data/jobs/test-suite/config.xml
sudo cp /tmp/api-tests-config.xml /var/lib/docker/volumes/cicd-health-dashboard_jenkins_home/_data/jobs/api-tests/config.xml
sudo cp /tmp/security-scan-config.xml /var/lib/docker/volumes/cicd-health-dashboard_jenkins_home/_data/jobs/security-scan/config.xml
sudo cp /tmp/deployment-config.xml /var/lib/docker/volumes/cicd-health-dashboard_jenkins_home/_data/jobs/deployment/config.xml
sudo cp /tmp/database-migration-config.xml /var/lib/docker/volumes/cicd-health-dashboard_jenkins_home/_data/jobs/database-migration/config.xml
sudo cp /tmp/load-testing-config.xml /var/lib/docker/volumes/cicd-health-dashboard_jenkins_home/_data/jobs/load-testing/config.xml
sudo cp /tmp/integration-tests-config.xml /var/lib/docker/volumes/cicd-health-dashboard_jenkins_home/_data/jobs/integration-tests/config.xml

echo "🔧 Setting proper permissions..."
sudo chown -R 1000:1000 /var/lib/docker/volumes/cicd-health-dashboard_jenkins_home/_data/jobs
sudo chmod -R 755 /var/lib/docker/volumes/cicd-health-dashboard_jenkins_home/_data/jobs

echo "📋 Verifying job creation..."
ls -la /var/lib/docker/volumes/cicd-health-dashboard_jenkins_home/_data/jobs/

echo "🚀 Starting Jenkins..."
docker-compose up -d jenkins

echo "⏳ Waiting for Jenkins to start and load jobs..."
sleep 45

echo "📊 Checking Jenkins status..."
docker-compose ps jenkins

echo "📋 Checking Jenkins logs..."
docker-compose logs jenkins | tail -10

echo "✅ Fresh Jenkins jobs created successfully!"
echo "📋 Created jobs:"
echo "✅ Successful Pipelines (5):"
echo "   • build-project"
echo "   • test-suite"
echo "   • api-tests"
echo "   • security-scan"
echo "   • deployment"
echo "❌ Failed Pipelines (3):"
echo "   • database-migration"
echo "   • load-testing"
echo "   • integration-tests"

echo ""
echo "🌐 Access URLs:"
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
echo "   Jenkins: http://$PUBLIC_IP:8080"
echo "   Frontend: http://$PUBLIC_IP:3000"
echo "   Backend: http://$PUBLIC_IP:8000"

# Clean up temp files
rm -f /tmp/*-config.xml

EOF

echo "✅ Fresh Jenkins jobs creation completed!"
echo "🎯 Your Jenkins now has 8 fresh jobs:"
echo "   • 5 successful pipelines"
echo "   • 3 failed pipelines"
echo "🌐 Check Jenkins at: http://$EC2_HOST:8080"
