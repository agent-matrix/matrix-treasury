.PHONY: help install install-ui run serve test clean docker-build docker-run demo upgrade survival build-ui

help:
	@echo "Matrix Treasury - Available Commands"
	@echo "====================================="
	@echo "install          Install base dependencies (backend + frontend)"
	@echo "install-upgrade  Install autonomous survival upgrade"
	@echo "install-ui       Install frontend dependencies only"
	@echo "run              Run development server (backend)"
	@echo "serve            Run frontend development server"
	@echo "build-ui         Build production frontend"
	@echo "test             Run all tests"
	@echo "test-coverage    Run tests with coverage report"
	@echo "demo             Run 30-day survival simulation"
	@echo "survival-check   Run daily survival check (heartbeat)"
	@echo "docker-build     Build Docker image"
	@echo "docker-run       Run with Docker Compose"
	@echo "docker-stop      Stop Docker services"
	@echo "clean            Clean temporary files"
	@echo "lint             Run linters"
	@echo "format           Format code"
	@echo ""
	@echo "Autonomous Survival Commands"
	@echo "============================="
	@echo "install-upgrade  Install upgrade dependencies (CrewAI, Web3, etc.)"
	@echo "setup-vault      Initialize blockchain wallet and vault"
	@echo "survival-check   Run system health check and pay bills"
	@echo "test-cfo         Test CFO decision-making"
	@echo "test-vault       Test blockchain vault connection"
	@echo "demo-upgrade     Run autonomous survival demo"

install:
	@echo "📦 Installing base dependencies..."
	pip install -r requirements.txt
	@echo "📦 Installing dev dependencies (optional)..."
	-pip install -r requirements-dev.txt 2>/dev/null || echo "⚠️  Some dev dependencies failed (non-critical)"
	@echo "✅ Backend dependencies installed"
	@echo ""
	@echo "📦 Installing frontend dependencies..."
	cd ui && npm install
	@echo "✅ Frontend dependencies installed"
	@echo ""
	@echo "✅ Installation complete (backend + frontend)"

install-ui:
	@echo "📦 Installing frontend dependencies..."
	cd ui && npm install
	@echo "✅ Frontend installation complete"

install-upgrade:
	@echo "🚀 Installing Autonomous Survival Upgrade..."
	pip install -r requirements-upgrade.txt
	@echo "✅ Upgrade dependencies installed"
	@echo ""
	@echo "⚙️  Next steps:"
	@echo "1. Configure .env file with your keys"
	@echo "2. Run 'make setup-vault' to initialize wallet"
	@echo "3. Run 'make survival-check' to test the system"

run:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

serve:
	@echo "🚀 Starting frontend development server..."
	@echo "Frontend: http://localhost:3000"
	@echo "Backend API: http://localhost:8000"
	@echo ""
	cd ui && npm run dev

build-ui:
	@echo "🏗️  Building production frontend..."
	cd ui && npm run build
	@echo "✅ Frontend build complete (output in ui/dist)"

test:
	python3 -m pytest tests/ -v --ignore=tests/stress

test-coverage:
	python3 -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term --ignore=tests/stress

demo:
	python3 scripts/survival_simulation.py

docker-build:
	docker-compose build

docker-run:
	docker-compose up -d
	@echo "Services started!"
	@echo "API: http://localhost:8000"
	@echo "Docs: http://localhost:8000/docs"
	@echo "Grafana: http://localhost:3000"

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f

clean:
	@echo "🧹 Cleaning temporary files..."
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache htmlcov .coverage
	rm -rf ui/dist ui/node_modules ui/.vite
	@echo "✅ Clean complete"

lint:
	flake8 src tests
	mypy src --ignore-missing-imports

format:
	black src tests
	isort src tests

db-setup:
	python -c "from src.db.connection import init_db; init_db()"
	@echo "📁 Creating data directory for ledger..."
	mkdir -p data

# ============================================================================
# Autonomous Survival Upgrade Commands
# ============================================================================

setup-vault:
	@echo "💰 Initializing Blockchain Vault..."
	@python3 -c "from src.blockchain.vault import ExternalVault; v = ExternalVault(); print(f'✅ Vault initialized: {v.account.address if v.account else \"Read-only mode\"}'); print(f'💵 Balance: {v.get_real_balance()} USDC')"

setup-ledger:
	@echo "📒 Initializing Internal Ledger..."
	mkdir -p data
	@python3 -c "from src.blockchain.ledger import InternalLedger; l = InternalLedger(); print('✅ Ledger initialized')"

survival-check:
	@echo "💓 Running System Survival Check..."
	@mkdir -p logs
	python3 src/cron/survival.py

test-cfo:
	@echo "🧠 Testing CFO Intelligence..."
	@python3 -c "\
from src.blockchain.vault import ExternalVault; \
from src.blockchain.ledger import InternalLedger; \
from src.llm.cfo import MatrixCFO; \
import os; \
os.makedirs('data', exist_ok=True); \
v = ExternalVault(); \
l = InternalLedger(); \
l.create_wallet('test_agent', 1000); \
cfo = MatrixCFO(v, l); \
print('✅ CFO initialized'); \
health = cfo.get_treasury_health(); \
print(f'📊 Treasury Health: {health}')"

test-vault:
	@echo "🔗 Testing Blockchain Connection..."
	@python3 -c "\
from src.blockchain.vault import ExternalVault; \
v = ExternalVault(); \
print(f'✅ Connected to {v.network}'); \
print(f'🌐 RPC: {v.rpc_url}'); \
print(f'💰 USDC Contract: {v.usdc_address}'); \
balance = v.get_real_balance(); \
print(f'💵 Balance: {balance} USDC'); \
if v.account: \
    gas = v.get_native_balance(); \
    print(f'⛽ Gas Balance: {gas} ETH')"

test-llm:
	@echo "🤖 Testing LLM Provider..."
	@python3 -c "\
from src.llm.provider import build_llm, test_llm_connection; \
from src.llm.settings import get_llm_settings; \
settings = get_llm_settings(); \
print(f'🔧 Active Provider: {settings.provider}'); \
print('🔌 Testing connection...'); \
if test_llm_connection(): \
    print('✅ LLM connection successful'); \
else: \
    print('❌ LLM connection failed')"

demo-upgrade:
	@echo "🎬 Running Autonomous Survival Demo..."
	@echo ""
	@echo "This will demonstrate:"
	@echo "  1. CFO approving/rejecting expenses"
	@echo "  2. Agents earning and spending MXU"
	@echo "  3. Automatic infrastructure payments"
	@echo ""
	@python3 -c "\
from src.blockchain.vault import ExternalVault; \
from src.blockchain.ledger import InternalLedger; \
from src.llm.cfo import MatrixCFO; \
from src.services.income_gateway import AppStore; \
from src.services.akash.manager import AkashManager; \
from decimal import Decimal; \
import os; \
os.makedirs('data', exist_ok=True); \
print('🚀 Initializing system...'); \
v = ExternalVault(); \
l = InternalLedger(); \
cfo = MatrixCFO(v, l); \
store = AppStore(v, l); \
akash = AkashManager(v); \
print(''); \
print('📊 Initial State:'); \
health = cfo.get_treasury_health(); \
print(f'   Treasury: {health}'); \
print(''); \
print('💰 Simulating human payment...'); \
l.create_wallet('worker_agent', 0); \
receipt = store.receive_human_payment('user_123', 'worker_agent', Decimal('10.0')); \
print(f'   ✅ {receipt}'); \
print(''); \
print('💳 Agent requesting funding...'); \
decision = cfo.request_funding('worker_agent', { \
    'item': 'API Call', \
    'cost_usd': 0.05, \
    'reason': 'Need to call OpenAI API', \
    'address': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb' \
}); \
print(f'   CFO Decision: {decision}'); \
print(''); \
print('✅ Demo complete!')"
