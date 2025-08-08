# Angles AI Universe™ Backend System

A comprehensive backend system for automated GPT assistant output processing, decision management, and memory synchronization with unified Supabase, Notion, and OpenAI integration.

## Overview

This system provides:
- **Memory Sync Agent**: Automated repository scanning and database synchronization
- **Historical Sweep**: AI-powered repository analysis and decision categorization  
- **Backend Monitor**: Health checks and system monitoring
- **Auto-sync**: File change detection and incremental updates
- **Backup & Restore**: Automated backups with GitHub integration
- **Cron Runner**: Scheduled task management and automation

## Environment Variables

Configure these environment variables in Replit Secrets:

### Required
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase anon/service role key

### Optional (graceful degradation if missing)
- `NOTION_API_KEY` - Notion integration token  
- `NOTION_DATABASE_ID` - Target Notion database ID
- `GITHUB_TOKEN` - GitHub personal access token
- `GITHUB_REPO` - GitHub repository URL for backups
- `OPENAI_API_KEY` - OpenAI API key for AI analysis
- `OPENAI_MODEL` - OpenAI model to use (default: gpt-4o)

## Quick Start

### 1. Database Setup

Run the database migration to create required tables:

```bash
python -m angles.run_migration
```

### 2. Initial Memory Sync

Scan and sync your repository files:

```bash
python -m angles.memory_sync_agent
```

### 3. Health Check

Verify system status:

```bash
python -m angles.backend_monitor
```

### 4. Historical Analysis

Generate AI-powered repository analysis:

```bash
python -m angles.historical_sweep
```

### 5. Start Scheduler

Begin automated operations:

```bash
python -m angles.cron_runner
```

## Components

### Memory Sync Agent
- Scans repository files (excludes .git, __pycache__, etc.)
- Computes SHA256 checksums for change detection
- Stores file snapshots in Supabase
- Logs all changes to system_logs table
- Writes summary to Notion (if configured)

### Auto-sync  
- File watcher with polling-based change detection
- Debounced updates to avoid spam
- Incremental sync of modified files
- Can run continuously or single-scan mode

### Historical Sweep
- Creates categorized decision placeholders
- Processes documentation files into decision entries
- AI-powered repository structure analysis
- Generates prioritized fix lists using OpenAI
- Stores artifacts and creates Notion summaries

### Backend Monitor
- Database connectivity checks
- Memory sync activity monitoring  
- System resource usage (CPU, memory, disk)
- OpenAI API connectivity testing
- Integration status reporting
- Health recommendations

### Backup & Restore
- Creates compressed database exports
- Includes configuration files and metadata
- Pushes backups to GitHub (if configured)
- Local backup retention management
- Restoration utilities

### Cron Runner
- **Memory Sync**: Every 6 hours
- **Historical Sweep**: Sundays at 02:00 UTC
- **Backup**: Daily at 03:00 UTC  
- **Health Monitor**: Every hour
- Graceful shutdown handling
- Job execution logging

## Database Schema

### Tables Created
- `decision_vault` - Categorized decisions and content
- `system_logs` - Application logs and events
- `file_snapshots` - Repository file versions
- `run_artifacts` - Generated reports and analysis

### Indexes
- Optimized for timestamp-based queries
- Category and status filtering
- Path-based file lookups

## Usage Examples

### Run Individual Components

```bash
# Memory sync with options
python -m angles.memory_sync_agent

# Auto-sync (continuous watching)
python -m angles.autosync --continuous --interval 30

# Create backup
python -m angles.restore --backup

# Run specific scheduled job
python -m angles.cron_runner --run-now memory_sync

# Health check with details
python -m angles.backend_monitor
```

### Configuration Check

```bash
python -c "from angles.config import print_config_status; print_config_status()"
```

## Troubleshooting

### Missing Environment Variables
Check configuration status:
```bash
python -m angles.backend_monitor
```

### Database Connection Issues
Test migration with dry-run:
```bash
python -m angles.run_migration --dry-run
```

### Memory Sync Problems
Check recent logs in the system_logs table and verify file permissions.

### Notion Integration Issues
- Verify NOTION_API_KEY and NOTION_DATABASE_ID
- Ensure Notion integration has database access
- Check database schema supports required fields

### GitHub Backup Failures
- Verify GITHUB_TOKEN and GITHUB_REPO
- Ensure token has repository write permissions
- Check local git configuration

## Security Notes

- All secrets are managed via environment variables
- Database operations use parameterized queries
- GitHub backups exclude sensitive information
- Logs sanitize secrets and API keys
- File scanning respects .gitignore patterns

## Development

### Adding New Components
1. Create module in `/angles/` directory
2. Add health check to `backend_monitor.py`
3. Include in `cron_runner.py` if scheduled
4. Add tests and update documentation

### Extending Database Schema
1. Update `run_migration.py` with new tables/indexes
2. Add corresponding methods to `supabase_client.py`
3. Test with dry-run before deployment

## Performance

- File scanning uses efficient path filtering
- Database operations include retry logic
- Batch processing for large datasets
- Connection pooling and timeouts
- Resource monitoring and alerts

## Support

For issues:
1. Check system logs in database
2. Run health monitor for diagnostics
3. Verify environment configuration
4. Review component-specific logs

---

**Angles AI Universe™** - Intelligent backend automation for modern development workflows.