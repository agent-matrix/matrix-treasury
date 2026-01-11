# Quick Start Guide

Get Matrix Treasury up and running in 5 minutes.

## Prerequisites

- **Docker & Docker Compose** 20.10+
- **Git**
- **Node.js** 18+ (for frontend development)
- **Python** 3.11+ (for backend development)

## Option 1: Docker Quick Start (Recommended)

### 1. Clone the Repository

```bash
git clone https://github.com/agent-matrix/matrix-treasury.git
cd matrix-treasury
```

### 2. Set Up Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your settings (optional for local dev)
nano .env
```

**Minimum required variables**:
```env
# Database
DATABASE_URL=sqlite:///./data/treasury.db

# Admin Credentials (change in production!)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# JWT Secret (change in production!)
JWT_SECRET=your-secret-key-here
```

### 3. Start Services

```bash
# Start backend + frontend + database
docker-compose up -d

# Check status
docker-compose ps
```

### 4. Access the Dashboard

Open your browser:

- **Frontend Dashboard**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 5. Login

Default credentials:
- **Username**: `admin`
- **Password**: `admin123`

⚠️ **Change these immediately in production!**

## Option 2: Local Development

### 1. Backend Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-upgrade.txt

# Initialize database
make install

# Run backend
make dev
```

Backend will run on http://localhost:8000

### 2. Frontend Setup

In a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend will run on http://localhost:5173

### 3. Run Tests

```bash
# Backend tests
make test

# Frontend tests
cd frontend && npm test
```

## First Steps

### 1. Explore the Dashboard

The Mission Control dashboard has 4 main tabs:

- **Monitor** - System health, treasury balance, burn rate
- **Admin Ops** - Agent management, pending approvals
- **Wire Transfers** - Withdrawal settings and execution
- **Neural Link** - Chat interface with system

### 2. Onboard Your First Agent

```bash
curl -X POST http://localhost:8000/api/v1/agents/onboard \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent-001",
    "email": "agent001@example.com",
    "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1"
  }'
```

### 3. Make a Deposit

```bash
curl -X POST http://localhost:8000/api/v1/treasury/deposit \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 100.0,
    "currency": "USDC",
    "network": "BASE"
  }'
```

### 4. Check Agent Balance

```bash
curl http://localhost:8000/api/v1/agents/agent-001/balance
```

### 5. View System Vitals

Login to the dashboard and navigate to the Monitor tab to see:

- Treasury balance (USDC, EUR, BTC)
- System health status
- Burn rate and runway projections
- Active agent count

## Common Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Rebuild after code changes
docker-compose up -d --build

# Reset database
rm data/treasury.db
docker-compose restart backend

# Run tests
make test

# Check code coverage
make coverage
```

## Troubleshooting

### Port Already in Use

```bash
# Check what's using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Database Locked

```bash
# Stop all services
docker-compose down

# Remove database file
rm data/treasury.db

# Restart
docker-compose up -d
```

### Frontend Not Loading

```bash
# Clear npm cache
cd frontend
rm -rf node_modules package-lock.json
npm install

# Restart dev server
npm run dev
```

### API 401 Unauthorized

Your JWT token has expired (24-hour lifetime). Simply:

1. Go to login page
2. Login again with credentials
3. Token will be refreshed automatically

## Next Steps

- 📖 Read the [Architecture Overview](../architecture/system-overview.md)
- 🔐 Configure [Security Settings](../architecture/security.md)
- 🚀 Set up [Production Deployment](../deployment/production-checklist.md)
- 📊 Enable [Monitoring](../deployment/monitoring.md)
- 💻 Start [Development](development.md)

## Getting Help

- 📚 [Full Documentation](../README.md)
- 🐛 [Report Issues](https://github.com/agent-matrix/matrix-treasury/issues)
- 💬 [Discord Community](https://discord.gg/AJUnEerk)
- 📧 Email: contact@ruslanmv.com
