# Angles AI Universe™ Backend System

## Overview

This is a comprehensive backend system designed for automated GPT assistant output processing, decision management, and memory synchronization with **integrated GPT-5 AI analysis**. The system features unified sync operations between Supabase (PostgreSQL) and Notion databases, providing redundancy, cross-platform accessibility, and intelligent AI-powered automation.

### 🤖 GPT-5 Integration Features

- **AI-Powered Decision Analysis**: Every decision is automatically analyzed by GPT-5 for type, priority, and impact assessment
- **Intelligent Classification**: Automatic categorization into strategy, technical, architecture, process, security, ethical, product, or other types
- **Priority Ranking**: P0/P1/P2 priority assignment based on AI analysis
- **Impact Assessment**: Comprehensive evaluation of potential consequences and dependencies
- **Smart Recommendations**: AI-generated actionable insights and next steps
- **Enhanced Notion Sync**: Decisions are enriched with AI analysis before being synced to Notion

## System Architecture

### Core Components

1. **Database Migration** (`run_migration.py`)
   - Idempotent database schema setup
   - Creates `decision_vault` and `agent_activity` tables
   - Handles schema updates and column additions safely

2. **🤖 AI-Enhanced Memory Sync** (`memory_sync.py`)
   - Bidirectional Supabase ⇄ Notion synchronization with GPT-5 analysis
   - Decision processing with CLI flags and AI enhancement
   - Export generation for backup purposes
   - Real-time AI decision classification and enrichment

3. **🤖 GPT-5 AI Client** (`tools/ai_client.py`)
   - Centralized OpenAI GPT-5 integration
   - Decision analysis and classification engine
   - Performance monitoring and fallback handling
   - Comprehensive AI status reporting

4. **🤖 AI-Enhanced Memory Bridge** (`memory_bridge.py`)
   - GPT-5 powered decision intelligence
   - Advanced classification algorithms
   - Duplicate detection and similarity analysis
   - Natural language insights generation

5. **File Monitoring** (`autosync_files.py`)
   - Automated file change detection
   - SHA256 checksum validation
   - Decision vault integration for key files

6. **Health Monitoring** (`backend_monitor.py`)
   - Comprehensive system health checks
   - Performance metrics and alerts
   - Self-healing capabilities

7. **Backup & Restore** (`restore_from_github.py`, `run_backup_now.py`)
   - GitHub backup with sanitization
   - Collision-safe restore operations
   - Automated backup scheduling

8. **Unified Scheduler** (`scheduler.py`)
   - Automated task coordination
   - Built-in fallback scheduling
   - Comprehensive logging and monitoring

9. **🛡️ Schema Guard** (`tools/schema_guard.py`)
   - Database schema validation and auto-fixing
   - Performance index optimization
   - Production readiness verification

## System Health & Monitoring

### Viewing Latest Report
```bash
# View comprehensive system status
cat logs/post_run_review.txt

# Real-time health dashboard
curl http://localhost:5000/health | python -m json.tool
```

### Schema Guard Usage
```bash
# Check database schema compliance
python tools/schema_guard.py --check

# Auto-fix safe schema issues (adds columns, indexes)
python tools/schema_guard.py --autofix

# JSON output for automation
python tools/schema_guard.py --check --json
```

**Safety Notes:**
- Schema Guard only adds missing columns/indexes (never drops)
- Type mismatches require manual review to prevent data loss
- All changes are logged and can be rolled back via Supabase

## Quick Start

### 1. Environment Setup

Copy `.env.example` to `.env` and configure:

```bash
# Core Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Notion Integration
NOTION_TOKEN=secret_your-notion-integration-token
NOTION_DATABASE_ID=your-notion-database-id

# 🤖 GPT-5 AI Integration
OPENAI_API_KEY=sk-proj-your-openai-api-key

# GitHub Backup
GITHUB_TOKEN=ghp_your-github-personal-access-token
REPO_URL=https://github.com/username/repository.git
GIT_USERNAME=your-git-username
GIT_EMAIL=your-git-email

# Optional: AI Configuration
USE_GPT4O_FALLBACK=false  # Set to true to use GPT-4o instead of GPT-5
```

### 2. Initial Deployment

```bash
# Run database migration
python run_migration.py

# Verify system health
python backend_monitor.py

# Test memory sync
python memory_sync.py --test

# 🤖 Test GPT-5 integration
python tests/test_gpt5_activation.py

# 🤖 Test complete AI pipeline
python tests/run_gpt5_pipeline_check.py

# Run comprehensive verification
python verify_deployment.py
```

### 3. Start Automated Services

```bash
# Start unified scheduler
python scheduler.py

# Or run memory system manually
python run_all.py
```

## Component Details

### Database Schema

#### decision_vault Table
```sql
CREATE TABLE decision_vault (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision TEXT NOT NULL,
    date DATE DEFAULT CURRENT_DATE,
    type VARCHAR(50) DEFAULT 'other',
    active BOOLEAN DEFAULT true,
    comment TEXT,
    synced BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### agent_activity Table
```sql
CREATE TABLE agent_activity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name VARCHAR(100) NOT NULL,
    action VARCHAR(100) NOT NULL,
    details JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Configuration Files

- **`.env.example`** - Environment variable template
- **`logs/`** - System logs and health reports
- **`export/`** - Data exports and backups
- **`utils/git_helpers.py`** - Git operation utilities

### Automation Schedule

| Task | Frequency | Description |
|------|-----------|-------------|
| Backend Monitor | Hourly | System health checks |
| Memory Sync | 6 hours | Supabase ⇄ Notion sync |
| File AutoSync | Hourly | File change detection |
| Daily Backup | 02:00 UTC | GitHub backup |
| Weekly Restore Test | Sunday 03:00 UTC | Restore verification |

## API Endpoints

### Health Dashboard
- **http://localhost:5000** - Health dashboard
- **http://localhost:5000/health** - Health API
- **http://localhost:5000/ping** - Service ping

### Supabase REST API
- **GET** `/rest/v1/decision_vault` - List decisions
- **POST** `/rest/v1/decision_vault` - Create decision
- **PATCH** `/rest/v1/decision_vault?id=eq.{id}` - Update decision

## Operational Commands

### Manual Operations

```bash
# Run specific components
python run_migration.py                    # Database setup
python memory_sync.py --sync-decisions     # Sync to Notion
python autosync_files.py --once            # File scan
python backend_monitor.py                  # Health check
python run_backup_now.py                   # Manual backup
python restore_from_github.py --dry-run    # Test restore

# Testing and verification
python tests/test_all.py                   # Run test suite
python verify_deployment.py               # Full verification
```

### Maintenance Commands

```bash
# View logs
tail -f logs/active/system_health.log
tail -f logs/active/memory_sync.log
tail -f logs/active/scheduler.log

# Check system status
python backend_monitor.py
cat logs/active/system_health.json

# Manual backup and restore
python run_backup_now.py
python restore_from_github.py --restore-decisions
```

## Troubleshooting

### Common Issues

1. **Environment Variables Missing**
   ```bash
   python backend_monitor.py  # Check configuration
   ```

2. **Database Connection Issues**
   ```bash
   python run_migration.py --dry-run  # Test database
   ```

3. **Notion API Problems**
   ```bash
   python memory_sync.py --test  # Test Notion connection
   ```

4. **GitHub Backup Failures**
   ```bash
   python run_backup_now.py  # Manual backup test
   ```

### Log Locations

- **System Health**: `logs/active/system_health.log`
- **Memory Sync**: `logs/active/memory_sync.log`
- **Scheduler**: `logs/active/scheduler.log`
- **AutoSync**: `logs/active/autosync.log`
- **Backup**: `logs/backup.log`

### Health Monitoring

The system provides comprehensive health monitoring:

- **Environment variables validation**
- **Database connectivity tests**
- **API endpoint verification**
- **System resource monitoring**
- **Service functionality tests**

Health reports are saved as JSON in `logs/active/system_health.json`.

## Security Considerations

- All secrets are managed via environment variables
- GitHub backups include automatic sanitization
- Database operations use parameterized queries
- Token authentication for all API calls
- Logs exclude sensitive information

## Performance Optimization

- Batch processing for large sync operations
- Connection pooling and timeouts
- Retry logic with exponential backoff
- Resource monitoring and alerts
- Efficient file change detection

## Development

### Adding New Components

1. Create component file with proper logging
2. Add health check to `backend_monitor.py`
3. Include in `scheduler.py` automation
4. Add tests to `tests/test_all.py`
5. Update documentation

### Testing

```bash
# Run all tests
python tests/test_all.py

# Component-specific tests
python run_migration.py --dry-run
python memory_sync.py --test
python autosync_files.py --dry-run

# Integration testing
python verify_deployment.py
```

## Support

For issues and support:

1. Check system logs in `logs/active/`
2. Run health check: `python backend_monitor.py`
3. Verify configuration with test commands
4. Review this documentation

## Version History

- **v3.0.0** - GPT-5 Integration Release (2025-08-08)
  - 🤖 **GPT-5 AI integration** with comprehensive decision analysis
  - **AI-enhanced memory sync** with real-time decision classification
  - **Advanced decision intelligence** with priority ranking and impact assessment
  - **Comprehensive AI testing suite** with activation and pipeline verification
  - **Enhanced security** with AI data sanitization
  - **Performance optimized** AI analysis pipeline
  - **Fallback mechanisms** for high availability

- **v2.0.0** - Security & Automation Enhancement
  - Advanced security data sanitization
  - Automated backup and recovery systems
  - Comprehensive monitoring and alerting
  - Configuration management with versioning

- **v1.0.0** - Initial comprehensive backend deployment
  - Database migration system
  - Memory sync with Notion
  - File monitoring and automation
  - Health monitoring and self-healing
  - GitHub backup and restore
  - Unified scheduler
  - Comprehensive testing suite