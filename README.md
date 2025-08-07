# Angles AI Universe™ Health Monitoring & Backup System

## Overview

Comprehensive automated health monitoring and backup system for Supabase-Notion sync infrastructure with GitHub backup integration, automated scheduling, and full restore capabilities.

## Features

- 🔍 **Health Monitoring**: Automated checks for Supabase, Notion API, and sync status
- 📦 **GitHub Backup**: Automated timestamped backups to GitHub repository
- 🔄 **Restore System**: Full restore capabilities with dry-run and schema validation
- 📧 **Notifications**: Slack webhook and email notifications for failures
- ⏰ **Automated Scheduling**: Daily runs at 03:00 UTC via Replit workflows
- 🧪 **Test Mode**: Comprehensive testing with simulated failures
- 📊 **Detailed Logging**: Complete audit trail with structured logging

## Quick Start

### 1. Setup Environment Secrets

Configure these secrets in your Replit environment:

**Required:**
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Supabase anon or service role key
- `GITHUB_TOKEN` - GitHub personal access token with repo access

**Optional (for notifications):**
- `SLACK_WEBHOOK_URL` - Slack webhook for error notifications
- `NOTION_API_KEY` - Notion integration token (for sync monitoring)
- `NOTION_DATABASE_ID` - Notion database ID

**Email notifications (alternative to Slack):**
- `SMTP_SERVER` - SMTP server hostname
- `SMTP_PORT` - SMTP server port (usually 587)
- `SMTP_USERNAME` - SMTP username
- `SMTP_PASSWORD` - SMTP password
- `EMAIL_RECIPIENT` - Email address for notifications

### 2. Initial Setup

```bash
# Run the automated setup
python scripts/scheduler.py

# Test the system
python run_manual.py --health --test

# Run a live health check
python run_manual.py --health

# Run health check and backup
python run_manual.py --all
```

### 3. Configure Automated Scheduling

Add a new workflow in Replit:
- **Name**: `Health Monitor & Backup`
- **Command**: `python run_all.py`
- **Schedule**: Daily at 03:00 UTC

## Usage

### Manual Operations

```bash
# Health check only
python run_manual.py --health

# Health check in test mode (simulates failures)
python run_manual.py --health --test

# Backup only
python run_manual.py --backup

# Complete process (health check + backup)
python run_manual.py --all

# Restore (dry-run)
python run_manual.py --restore

# Live restore
python run_manual.py --restore --live-restore

# Restore specific backup
python run_manual.py --restore --backup-file decision_vault_2025-08-07_15-30-00.json
```

### Direct Script Usage

```bash
# Health check with exit codes
python scripts/health_check.py          # 0=OK, 1=Warnings, 2=Errors
python scripts/health_check.py --test   # Test mode

# Backup to GitHub
python scripts/backup_to_github.py

# Restore from GitHub
python scripts/restore_from_github.py --dry-run
python scripts/restore_from_github.py --live
python scripts/restore_from_github.py --file backup.json --live
```

## Configuration

### config.json

```json
{
  "scheduler": {
    "run_time": "03:00",
    "timezone": "UTC"
  },
  "notifications": {
    "method": "slack",
    "email_enabled": false,
    "slack_enabled": true
  },
  "backup": {
    "repository": "angles-backup",
    "auto_commit": true,
    "retention_days": 30
  },
  "restore": {
    "auto_migrate": false,
    "dry_run_default": true
  },
  "health_check": {
    "timeout_seconds": 30,
    "max_unsynced_warning": 10,
    "max_unsynced_error": 50
  }
}
```

## System Components

### Health Monitoring (`scripts/health_check.py`)

- Tests Supabase connection and table access
- Validates Notion API connectivity
- Counts unsynced records in decision_vault
- Configurable warning/error thresholds
- Comprehensive logging and notifications

**Exit Codes:**
- `0` - All checks passed
- `1` - Warnings detected (e.g., some unsynced records)
- `2` - Errors detected (e.g., connection failures)

### Backup System (`scripts/backup_to_github.py`)

- Exports complete decision_vault table as JSON
- Uploads to GitHub with timestamped filenames
- Automatic cleanup of old backups (configurable retention)
- Metadata tracking and verification

### Restore System (`scripts/restore_from_github.py`)

- Downloads latest or specific backup from GitHub
- Schema compatibility checking
- Diff analysis between current and backup data
- Dry-run mode for safe preview
- Selective restore (insert missing, update modified)

### Automated Scheduling

- **`run_all.py`** - Main automated runner
- **`run_manual.py`** - Manual execution with options
- **`scripts/scheduler.py`** - Setup and configuration tool

## Backup File Structure

```json
{
  "metadata": {
    "timestamp": "2025-08-07T15:30:00.000Z",
    "record_count": 42,
    "backup_version": "1.0.0",
    "source": "decision_vault",
    "schema_version": "1.0"
  },
  "data": [
    {
      "id": "uuid-here",
      "decision": "Implement automated health monitoring",
      "type": "Architecture",
      "date": "2025-08-07",
      "created_at": "2025-08-07T12:00:00.000Z"
    }
  ]
}
```

## Logging

All operations are logged to:
- `logs/health_check.log` - Health monitoring results
- `logs/backup.log` - Backup operations
- `logs/restore.log` - Restore operations
- `logs/scheduler.log` - Scheduler setup and configuration
- `logs/automated_runs.log` - Daily automated executions

## Notifications

### Slack Integration

Configure `SLACK_WEBHOOK_URL` secret and set notification method to "slack" in config.json.

Sample notification:
```
🚨 Angles AI Universe™ Health Alert

Status: ERRORS
Timestamp: 2025-08-07 15:30:00 UTC
Duration: 12.34 seconds

Errors (2):
  • Supabase connection timeout
  • 25 unsynced records detected (error threshold: 20)

Please check the system and resolve issues.
```

### Email Integration

Configure SMTP settings and set notification method to "email" in config.json.

## Troubleshooting

### Common Issues

**Health check fails with connection timeout:**
- Verify SUPABASE_URL and SUPABASE_KEY are correct
- Check network connectivity
- Increase timeout_seconds in config.json

**Backup fails with GitHub API error:**
- Verify GITHUB_TOKEN has repo access
- Check repository name in config.json
- Ensure repository exists and is accessible

**Restore shows schema compatibility warnings:**
- Set auto_migrate to true in config.json for automatic handling
- Manually review schema differences
- Use dry-run mode to preview changes

**No notifications received:**
- Verify webhook URL or SMTP credentials
- Check notification method in config.json
- Review logs for notification errors

### Log Analysis

```bash
# Recent health check results
tail -f logs/health_check.log

# Backup status
tail -f logs/backup.log

# Automated run summary
tail -f logs/automated_runs.log

# All system logs
tail -f logs/*.log
```

## Security

- All sensitive credentials stored in Replit Secrets
- GitHub backups exclude sensitive environment variables
- Backup files include checksums for integrity verification
- Restore operations include validation and dry-run modes
- Comprehensive audit logging for all operations

## License

© 2025 Angles AI Universe™ Backend Team