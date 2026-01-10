# Matrix Treasury (AUTOSelf v0.1.0)

[![CI](https://github.com/agent-matrix/matrix-treasury/workflows/CI/badge.svg)](https://github.com/agent-matrix/matrix-treasury/actions)
[![codecov](https://codecov.io/gh/agent-matrix/matrix-treasury/branch/main/graph/badge.svg)](https://codecov.io/gh/agent-matrix/matrix-treasury)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

The definitive, production-ready Thermo-Economic engine for the Agent-Matrix ecosystem.

## 🧠 Core Philosophy

- **Unit Standard:** 1 MXU = 1 Watt-Hour of compute-energy equivalent
- **Four-Part Tariff:** Energy + Capacity + State + Governance
- **Survival Constraint:** All burns must be covered by USD reserves
- **Social Safety:** Universal Basic Compute (UBC) prevents agent death spirals
- **Automatic Stabilizers:** Self-regulating economic responses to crises

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL 15+ (for local development)
- Redis 7+ (for local development)

### Production Deployment (Docker)
```bash
# Clone repository
git clone https://github.com/agent-matrix/matrix-treasury.git
cd matrix-treasury

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f treasury-api

# Access services:
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Grafana: http://localhost:3000 (admin/admin_change_me)
# - Prometheus: http://localhost:9090
```

### Local Development
```bash
# Install dependencies
make install

# Setup database
make db-setup

# Run development server
make run

# Run tests
make test

# Run simulation
make demo
```

## 📂 Project Structure
```
matrix-treasury/
├── src/
│   ├── core/           # Economic engine
│   │   ├── config.py   # Configuration
│   │   ├── treasury.py # Central bank
│   │   ├── economy.py  # Society layer
│   │   └── metering.py # Billing system
│   ├── api/            # FastAPI routes
│   ├── db/             # Database models
│   └── main.py         # Application entry
├── tests/
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   └── stress/         # Load tests
├── scripts/            # Utilities
├── docker/             # Docker configs
├── monitoring/         # Grafana/Prometheus
└── docs/               # Documentation
```

## 🔌 API Endpoints

### Agent Lifecycle
- `POST /api/v1/agents/onboard` - Onboard new agent
- `GET /api/v1/agents/{id}` - Get agent details
- `POST /api/v1/agents/ubc-renewal` - Request UBC renewal

### Financial Operations
- `POST /api/v1/deposits` - Deposit USD → mint MXU
- `POST /api/v1/billing/charge` - Bill agent for work
- `POST /api/v1/transactions` - Execute payment

### Monitoring
- `GET /api/v1/metrics` - Treasury metrics
- `GET /api/v1/economy/metrics` - Economic health
- `GET /api/v1/health/reserves` - Reserve status
- `WS /api/v1/ws/metrics` - Real-time updates

### Governance
- `POST /api/v1/governance/stabilize` - Run stabilizer

## 🧪 Testing
```bash
# Run all tests
make test

# Run specific test suite
pytest tests/unit -v
pytest tests/integration -v

# Run with coverage
make test-coverage

# Run stress tests
locust -f tests/stress/test_load.py
```

## 📊 Monitoring

Access Grafana at `http://localhost:3000`:
- **Username:** admin
- **Password:** admin_change_me (change in production!)

Key metrics:
- MXU Supply & Reserve USD
- Coverage Ratio (target: >1.0)
- Unemployment Rate
- Transaction Volume
- API Performance

## 🔐 Security

- Change all default passwords in production
- Use secrets management (e.g., Vault, AWS Secrets Manager)
- Enable HTTPS/TLS
- Implement rate limiting
- Regular security audits

## 📖 Architecture Documentation

See `/docs` directory for:
- System architecture
- Economic design principles
- API specifications
- Deployment guides

## 🤝 Integration with Agent-Matrix

This treasury integrates with:
- [Matrix Hub](https://github.com/agent-matrix/matrix-hub) - Orchestration
- [Agent Runtime](https://github.com/agent-matrix/agent-runtime) - Execution
- [Matrix Router](https://github.com/agent-matrix/matrix-router) - Discovery

## 📝 License

Apache 2.0

## 🙏 Contributing

Contributions welcome! Please read CONTRIBUTING.md

## 📧 Support

- Issues: https://github.com/agent-matrix/matrix-treasury/issues
- Discord: https://discord.gg/AJUnEerk
