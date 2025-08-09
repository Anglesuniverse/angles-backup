# Angles OS™ Bootstrap

A production-ready FastAPI backend with PostgreSQL, Redis, TokenVault memory system, AI-powered decision management, and automated agents.

## 🚀 Quick Start

### Option 1: Replit (Recommended)
1. All dependencies are pre-installed
2. Secrets are managed automatically via Replit Secrets
3. Run: `bash run_local.sh`

### Option 2: Local Development
1. Install dependencies: `pip install -r requirements.txt`
2. Set up environment variables (see `.env.example`)
3. Run: `bash run_local.sh`

### Option 3: Docker Compose
```bash
docker-compose up -d
```

## 🏗️ Architecture

### Core Components
- **FastAPI Application**: Modern async REST API
- **TokenVault**: Persistent memory storage with semantic search
- **Decision System**: AI-powered decision tracking and recommendations  
- **Agent System**: Automated background agents (memory sync, strategy, verification)
- **External Connectors**: Supabase, Notion, OpenAI integration

### Database Schema
- `vault_chunks`: Knowledge storage with full-text search
- `decisions`: Decision tracking with status workflow
- `agent_logs`: Agent activity monitoring

## 📡 API Endpoints

### Health & Status
- `GET /health` - System health check
- `GET /health/ping` - Simple ping/pong
- `GET /health/ready` - Kubernetes readiness probe
- `GET /ui/summary` - Dashboard data

### TokenVault
- `POST /vault/ingest` - Add knowledge chunks
- `POST /vault/query` - Search knowledge base
- `GET /vault/source/{source}` - Get chunks by source
- `GET /vault/stats` - Vault statistics

### Decision Management
- `POST /decisions` - Create decision
- `GET /decisions` - List decisions (with optional status filter)
- `GET /decisions/{id}` - Get specific decision
- `POST /decisions/{id}/recommend` - Generate AI recommendation
- `POST /decisions/{id}/approve` - Approve decision
- `POST /decisions/{id}/decline` - Decline decision

### Agent Management
- `GET /agents/status` - Get all agent status
- `POST /agents/{name}/run` - Manually trigger agent

## 🤖 Automated Agents

### Memory Sync Agent
- **Schedule**: Every 6 hours
- **Function**: Monitors file changes, ingests to vault, syncs to external services
- **Triggers**: File modifications, new content detection

### Strategy Agent  
- **Schedule**: Every hour
- **Function**: Reviews open decisions, generates recommendations for stale items
- **Logic**: AI-powered recommendations with fallback heuristics

### Verifier Agent
- **Schedule**: Daily at 02:00 UTC  
- **Function**: System integrity checks, API health validation, data consistency
- **Alerts**: Logs warnings and errors for critical issues

## 🔧 Configuration

### Environment Variables (Replit Secrets)
```bash
# Database
POSTGRES_URL=postgresql://user:pass@host:5432/db

# Cache/Queue  
REDIS_URL=redis://host:6379

# External Services
SUPABASE_URL=https://project.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ... 
NOTION_API_KEY=secret_...
OPENAI_API_KEY=sk-...
GITHUB_TOKEN=ghp_...

# Application
LOG_LEVEL=INFO
ENV=production
```

## 🔌 External Integrations

### Supabase
- **Client Mode**: User operations with anon key
- **Server Mode**: Admin operations with service key
- **Auto-sync**: Vault chunks and decisions

### Notion  
- **Page Creation**: Structured data export
- **Database Mapping**: Configurable field mapping
- **Batch Operations**: Efficient bulk sync

### OpenAI (GPT-5 Ready)
- **Decision Recommendations**: AI-powered analysis
- **Content Summarization**: Intelligent chunk processing
- **Fallback System**: Rule-based alternatives

## 🏃‍♂️ Background Jobs

### RQ Worker System
- **Queue**: Redis-backed job processing
- **Jobs**: RSS ingestion, daily backups, artifact summarization
- **Monitoring**: Agent logs and status tracking

### Available Jobs
- `ingest_rss(url, source)` - RSS feed processing
- `daily_backup()` - System backup operations  
- `summarize_artifact(path, type)` - File summarization

## 🧪 Testing

### Automated Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Individual test suites  
python tests/test_health.py
python tests/test_vault.py
python tests/test_decisions.py
```

### Manual API Testing
```bash
# Health check
curl http://localhost:8000/health

# Ingest knowledge
curl -X POST http://localhost:8000/vault/ingest \
  -H "Content-Type: application/json" \
  -d '{"source": "test", "chunk": "Sample content"}'

# Create decision
curl -X POST http://localhost:8000/decisions \
  -H "Content-Type: application/json" \
  -d '{"topic": "Test decision", "options": [{"option": "A", "pros": ["Fast"], "cons": ["Limited"]}]}'
```

## 🔍 Monitoring & Debugging

### Health Dashboard
- System metrics and resource usage
- Service connectivity status
- Recent activity logs
- Agent execution history

### Log Files
- `app.log` - Application logs with rotation
- `logs/agent_*.log` - Agent-specific logs
- `run_review.json` - Post-deployment analysis

### Post-Run Review
```bash
python post_run_review.py
```
Automatically detects and fixes common deployment issues:
- Database connectivity
- Missing environment variables  
- Import errors
- API endpoint failures

## 🚢 Production Deployment

### Replit Deployment
1. Configure secrets in Replit Secrets manager
2. Run health checks: `python post_run_review.py`
3. Deploy using Replit's built-in deployment

### Manual Deployment
1. Set production environment variables
2. Run migrations: `python scripts/run_migration.py`
3. Start with gunicorn: `gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker`
4. Configure reverse proxy (nginx)
5. Set up monitoring and logging

### Docker Deployment
```bash
# Build and deploy
docker-compose up -d

# Scale workers
docker-compose scale worker=3

# View logs
docker-compose logs -f api
```

## 📊 System Requirements

### Minimum
- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- 512MB RAM
- 1GB disk space

### Recommended
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- 2GB RAM
- 5GB disk space
- Load balancer for production

## 🔒 Security

### Environment Isolation
- Secrets managed via Replit Secrets (not .env files)
- Database access controls with service/client key separation
- API rate limiting and input validation

### External Service Security
- OAuth flows for third-party integrations
- Encrypted data transmission (HTTPS only)
- Audit logging for sensitive operations

## 🆘 Troubleshooting

### Common Issues

**Database Connection Failed**
```bash
# Check PostgreSQL status
python scripts/run_migration.py

# Verify connection string
echo $POSTGRES_URL
```

**Agent Not Running**
```bash
# Check agent status
curl http://localhost:8000/agents/status

# Manually trigger agent
curl -X POST http://localhost:8000/agents/verifier/run
```

**Import Errors**
```bash
# Install missing dependencies
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

### Getting Help
1. Check `app.log` for detailed error messages
2. Run `python post_run_review.py` for automated diagnostics  
3. Review agent logs in `/logs/` directory
4. Verify environment variables are properly set

## 📚 API Documentation

Once running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🎯 Production Checklist

- [ ] All environment variables configured
- [ ] Database migrations completed
- [ ] External services connected and tested
- [ ] All tests passing
- [ ] Health checks returning green
- [ ] Monitoring and alerting configured
- [ ] Backup procedures established
- [ ] Load balancing configured (if needed)
- [ ] SSL certificates installed
- [ ] Security scanning completed

---

**Angles OS™** - Production-ready AI platform engineering solution
Built with FastAPI, PostgreSQL, Redis, and intelligent automation.