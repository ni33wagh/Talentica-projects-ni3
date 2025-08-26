#!/bin/bash

echo "Setting up Jenkins..."

# Wait for Jenkins to be ready
echo "Waiting for Jenkins to start..."
while ! curl -s http://localhost:8080/login > /dev/null; do
    sleep 5
done

echo "Jenkins is ready!"

# Get the initial admin password
ADMIN_PASSWORD=$(docker exec cicd-jenkins cat /var/jenkins_home/secrets/initialAdminPassword 2>/dev/null || echo "admin")

echo "Jenkins Admin Password: $ADMIN_PASSWORD"

# Get CSRF crumb
echo "Getting CSRF crumb..."
CRUMB_RESPONSE=$(curl -s -u admin:$ADMIN_PASSWORD http://localhost:8080/crumbIssuer/api/json)
CRUMB_FIELD=$(echo $CRUMB_RESPONSE | grep -o '"crumbRequestField":"[^"]*"' | cut -d'"' -f4)
CRUMB_VALUE=$(echo $CRUMB_RESPONSE | grep -o '"crumb":"[^"]*"' | cut -d'"' -f4)

echo "Crumb field: $CRUMB_FIELD"
echo "Crumb value: $CRUMB_VALUE"

# Create a simple pipeline job using Jenkins REST API with crumb
echo "Creating test pipeline job..."

# Create a simple pipeline job
curl -X POST http://localhost:8080/createItem \
  -u admin:$ADMIN_PASSWORD \
  -H "Content-Type: application/xml" \
  -H "$CRUMB_FIELD: $CRUMB_VALUE" \
  -d '<?xml version="1.0" encoding="UTF-8"?>
<flow-definition plugin="workflow-job@1300.vd2294d3341a_f">
  <description>Test pipeline for CI/CD Dashboard</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@3697.vb_490d4e019d_d">
    <script>pipeline {
    agent any
    stages {
        stage("Build") {
            steps {
                echo "Building application..."
                sh "sleep 5"
            }
        }
        stage("Test") {
            steps {
                echo "Running tests..."
                sh "sleep 3"
            }
        }
        stage("Deploy") {
            steps {
                echo "Deploying application..."
                sh "sleep 2"
            }
        }
    }
    post {
        always {
            echo "Pipeline completed!"
        }
    }
}</script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>' \
  --data-urlencode name=test-pipeline

echo "Test pipeline job created!"

# Create another test job
curl -X POST http://localhost:8080/createItem \
  -u admin:$ADMIN_PASSWORD \
  -H "Content-Type: application/xml" \
  -H "$CRUMB_FIELD: $CRUMB_VALUE" \
  -d '<?xml version="1.0" encoding="UTF-8"?>
<flow-definition plugin="workflow-job@1300.vd2294d3341a_f">
  <description>Another test pipeline</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@3697.vb_490d4e019d_d">
    <script>pipeline {
    agent any
    stages {
        stage("Setup") {
            steps {
                echo "Setting up environment..."
                sh "sleep 2"
            }
        }
        stage("Build") {
            steps {
                echo "Building project..."
                sh "sleep 4"
            }
        }
    }
    post {
        always {
            echo "Build completed!"
        }
    }
}</script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>' \
  --data-urlencode name=build-project

echo "Build project job created!"

echo "Jenkins setup complete!"
echo "Access Jenkins at: http://localhost:8080"
echo "Username: admin"
echo "Password: $ADMIN_PASSWORD"
