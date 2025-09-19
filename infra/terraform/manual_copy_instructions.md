# Manual Deployment Instructions

## Option 1: Automated Deployment (Recommended)
```bash
cd /Users/nitinw/Desktop/cicd-health-dashboard/infra/terraform
./deploy_full_app.sh
```

## Option 2: Manual Step-by-Step Deployment

### Step 1: Copy the entire project to EC2
```bash
# From your local machine
scp -i ~/.ssh/id_rsa -r /Users/nitinw/Desktop/cicd-health-dashboard/* ec2-user@65.1.251.65:/opt/cicd-health-dashboard/
```

### Step 2: SSH into EC2 and set up
```bash
ssh -i ~/.ssh/id_rsa ec2-user@65.1.251.65
cd /opt/cicd-health-dashboard
```

### Step 3: Install dependencies and start services
```bash
# Install Docker (if not already installed)
sudo yum update -y
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

# Set up backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

# Set up frontend
cd frontend
npm install
cd ..

# Start the application
docker-compose up --build -d
```

### Step 4: Verify deployment
```bash
# Check running containers
docker-compose ps

# Check logs if needed
docker-compose logs backend
docker-compose logs frontend
docker-compose logs jenkins
```

## What you'll get:
- ✅ Full CI/CD Health Dashboard with all features
- ✅ Professional UI with modern design
- ✅ Real-time updates and auto-refresh
- ✅ Email notifications
- ✅ All 15+ Jenkins jobs
- ✅ Complete backend API
- ✅ Responsive frontend

## Access URLs:
- Frontend: http://65.1.251.65:3000
- Backend: http://65.1.251.65:8000
- Jenkins: http://65.1.251.65:8080
- API Docs: http://65.1.251.65:8000/docs
