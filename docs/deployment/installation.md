# Installation Guide

Complete installation instructions for all deployment scenarios.

## System Requirements

### Minimum Requirements

- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 20GB SSD
- **OS**: Linux (Ubuntu 20.04+), macOS, Windows (WSL2)

### Recommended for Production

- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Storage**: 100GB SSD
- **OS**: Ubuntu 22.04 LTS
- **Database**: PostgreSQL 14+

## Prerequisites

### Required Software

1. **Docker & Docker Compose**

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo usermod -aG docker $USER

# macOS
brew install docker docker-compose

# Verify installation
docker --version
docker-compose --version
```

2. **Git**

```bash
# Ubuntu/Debian
sudo apt-get install -y git

# macOS
brew install git

# Verify
git --version
```

3. **Python 3.11+** (for local development)

```bash
# Ubuntu/Debian
sudo apt-get install -y python3.11 python3.11-venv python3-pip

# macOS
brew install python@3.11

# Verify
python3 --version
```

4. **Node.js 18+** (for frontend development)

```bash
# Using nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18

# Verify
node --version
npm --version
```

### Optional Software

- **PostgreSQL 14+** (for production database)
- **Redis** (for caching and job queues)
- **Nginx** (for reverse proxy)

## Installation Methods

### Method 1: Docker Compose (Recommended)

**Best for**: Production deployments, testing, quick demos

#### Step 1: Clone Repository

```bash
git clone https://github.com/agent-matrix/matrix-treasury.git
cd matrix-treasury
```

#### Step 2: Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit configuration
nano .env
```

**Required variables**:

```env
# Database
DATABASE_URL=sqlite:///./data/treasury.db
# For PostgreSQL:
# DATABASE_URL=postgresql://user:pass@localhost:5432/treasury

# Admin Authentication
ADMIN_USERNAME=admin
ADMIN_PASSWORD=SecurePassword123!
ADMIN_WALLET=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1

# JWT Configuration
JWT_SECRET=generate-a-secure-random-string-here
JWT_EXPIRATION_HOURS=24

# Organization
ORGANIZATION_ID=ORG-8821

# LLM Provider (choose one)
LLM_PROVIDER=openai  # openai | claude | watsonx | ollama

# OpenAI Configuration
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o

# Claude Configuration
CLAUDE_API_KEY=sk-ant-your-key-here
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Network Configuration
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000
```

#### Step 3: Start Services

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

#### Step 4: Verify Installation

```bash
# Check backend health
curl http://localhost:8000/api/v1/

# Check frontend (in browser)
open http://localhost:5173

# Check API docs
open http://localhost:8000/docs
```

#### Step 5: Login

Navigate to http://localhost:5173 and login with:
- Username: `admin` (or your configured username)
- Password: Your configured password

### Method 2: Local Development

**Best for**: Active development, debugging

#### Backend Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-upgrade.txt

# Install development tools
pip install pytest pytest-cov black flake8 mypy

# Initialize database
make install

# Run database migrations (if any)
# alembic upgrade head

# Run backend server
make dev
```

Backend API: http://localhost:8000

#### Frontend Setup

In a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Install development tools
npm install --save-dev @types/react @types/node

# Start development server
npm run dev
```

Frontend: http://localhost:5173

### Method 3: Kubernetes

**Best for**: Enterprise production deployments, high availability

See [Kubernetes Deployment Guide](kubernetes.md) for detailed instructions.

### Method 4: Akash Network

**Best for**: Decentralized cloud deployment

```bash
# Install Akash CLI
curl -sSfL https://raw.githubusercontent.com/akash-network/node/master/install.sh | sh

# Configure deployment
cp deploy.yaml.example deploy.yaml
nano deploy.yaml

# Deploy to Akash
akash tx deployment create deploy.yaml --from $AKASH_KEY_NAME

# Get deployment status
akash query deployment list --owner $AKASH_ACCOUNT_ADDRESS
```

## Database Setup

### SQLite (Default for Development)

No additional setup required. Database file created automatically at `data/treasury.db`.

### PostgreSQL (Recommended for Production)

#### Install PostgreSQL

```bash
# Ubuntu/Debian
sudo apt-get install -y postgresql postgresql-contrib

# macOS
brew install postgresql
brew services start postgresql
```

#### Create Database

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE treasury;
CREATE USER treasury_user WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE treasury TO treasury_user;
\q
```

#### Configure Connection

Update `.env`:

```env
DATABASE_URL=postgresql://treasury_user:secure_password@localhost:5432/treasury
```

### Database Migrations

```bash
# Initialize Alembic (if not done)
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

## Frontend Build

### Development Build

```bash
cd frontend
npm run dev
```

### Production Build

```bash
cd frontend

# Build optimized production bundle
npm run build

# Preview production build
npm run preview

# Build artifacts in frontend/dist/
ls -la dist/
```

### Serve with Nginx

```bash
# Install Nginx
sudo apt-get install -y nginx

# Copy build to web root
sudo cp -r frontend/dist/* /var/www/html/

# Configure Nginx (see deployment/production-checklist.md)
sudo nano /etc/nginx/sites-available/treasury

# Restart Nginx
sudo systemctl restart nginx
```

## Verification

### Backend Health Check

```bash
# API health
curl http://localhost:8000/api/v1/

# Expected response
{
  "status": "healthy",
  "service": "Matrix Treasury",
  "version": "1.0.0"
}
```

### Database Verification

```bash
# Check database connection
python3 << EOF
from src.db.connection import get_db
db = next(get_db())
print(f"Database connected: {db}")
EOF
```

### Authentication Test

```bash
# Login
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.access_token')

# Test authenticated endpoint
curl http://localhost:8000/api/v1/analytics/vitals \
  -H "Authorization: Bearer $TOKEN"
```

### Run Test Suite

```bash
# Backend tests
make test

# Expected output
======================== 16 passed, 2 warnings in 4.33s ========================

# Frontend tests
cd frontend
npm test
```

## Post-Installation

### 1. Change Default Credentials

```bash
# Update .env file
ADMIN_PASSWORD=YourSecurePassword123!
JWT_SECRET=generate-new-secret-with-openssl-rand-hex-32

# Restart services
docker-compose restart backend
```

### 2. Configure LLM Provider

Choose and configure your AI provider:

```bash
# For OpenAI
OPENAI_API_KEY=sk-your-actual-key

# For Claude
CLAUDE_API_KEY=sk-ant-your-actual-key

# For local Ollama
OLLAMA_BASE_URL=http://localhost:11434
```

### 3. Set Up Monitoring

```bash
# Enable monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Access Grafana
open http://localhost:3000
```

### 4. Configure Backups

```bash
# Create backup script
cat > scripts/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p backups
sqlite3 data/treasury.db ".backup backups/treasury_$DATE.db"
echo "Backup created: backups/treasury_$DATE.db"
EOF

chmod +x scripts/backup.sh

# Add to crontab (daily at 2 AM)
crontab -e
0 2 * * * /path/to/matrix-treasury/scripts/backup.sh
```

## Upgrading

### From Previous Version

```bash
# Pull latest changes
git pull origin main

# Backup database
./scripts/backup.sh

# Rebuild containers
docker-compose down
docker-compose up -d --build

# Run migrations
docker-compose exec backend alembic upgrade head
```

## Troubleshooting

### Installation Issues

**Problem**: Docker permission denied

```bash
# Solution
sudo usermod -aG docker $USER
newgrp docker
```

**Problem**: Port 8000 already in use

```bash
# Find process
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
```

**Problem**: Python version mismatch

```bash
# Install specific version
pyenv install 3.11.0
pyenv local 3.11.0
```

### Database Issues

**Problem**: Database locked

```bash
# Stop all processes
docker-compose down

# Remove lock
rm data/treasury.db-wal data/treasury.db-shm

# Restart
docker-compose up -d
```

**Problem**: Migration failed

```bash
# Rollback migration
alembic downgrade -1

# Fix migration file
nano alembic/versions/xxx_migration.py

# Reapply
alembic upgrade head
```

## Next Steps

- ✅ Configure [Production Settings](production-checklist.md)
- ✅ Set up [Monitoring](monitoring.md)
- ✅ Review [Security Guide](../architecture/security.md)
- ✅ Read [Development Guide](../guides/development.md)

## Support

- 📖 [Documentation](../README.md)
- 🐛 [Report Issues](https://github.com/agent-matrix/matrix-treasury/issues)
- 💬 [Discord](https://discord.gg/AJUnEerk)
- 📧 Email: contact@ruslanmv.com
