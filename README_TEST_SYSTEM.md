# Angles AI Universe™ Automated Test & Recovery System

## Overview

The Automated Test & Recovery System provides comprehensive monitoring, backup, and restoration capabilities for the Angles AI Universe backend infrastructure. The system continuously monitors Supabase, Notion API, and GitHub repository health, automatically restoring data when issues are detected.

### System Components

1. **Health Monitoring** (`health_check.py`) - Comprehensive system health verification
2. **GitHub Restore** (`restore_from_github.py`) - Automated data restoration from GitHub backups  
3. **Log Management** (`log_manager.py`) - Automated log archival and compression
4. **Automated Scheduler** (`automated_scheduler.py`) - Cron-like task scheduling

## Manual Script Execution

### Health Check
```bash
# Run comprehensive health check
python health_check.py

# Check results in logs
cat logs/active/system_health.log
```

**Exit Codes:**
- `0` - All systems healthy
- `1` - System degraded (partial failures)
- `2` - Critical failures detected

### GitHub Restore
```bash
# Run data restoration from GitHub backup
python restore_from_github.py

# Check restore logs
cat logs/active/restore.log
```

**Requirements:**
- GitHub repository `angles-backup` must exist
- Repository must contain valid backup JSON files
- Required environment variables: `GITHUB_TOKEN`, `GITHUB_USERNAME`

### Log Management
```bash
# Archive old logs and compress them
python log_manager.py

# Check archive status
ls -la logs/archive/
```

**Retention Policy:**
- Active logs: 30 days in `logs/active/`
- Archived logs: 365 days compressed in `logs/archive/`
- Archives older than 1 year are automatically deleted

### Manual Scheduler Control
```bash
# Start automated scheduler (runs continuously)
python automated_scheduler.py

# Stop with Ctrl+C
```

## Automated Scheduling

The system runs automatically via Replit workflows with the following schedule:

### Daily Tasks (03:00 UTC)
1. **Health Check** - Verify all system components
2. **Conditional Restore** - Only runs if health check fails
   - Pulls latest backup from GitHub
   - Restores missing data to Supabase
   - Logs all restoration activities

### Weekly Tasks (Sunday 02:00 UTC)
1. **Log Management** - Archive and compress old logs
2. **Storage Cleanup** - Remove archives older than 1 year

### Workflow Configuration
- **Name:** `Automated Test System`
- **Command:** `python automated_scheduler.py`
- **Type:** Continuous background process
- **Logging:** All activities logged to `logs/active/scheduler.log`

## Environment Variables

### Required Secrets
```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-or-service-key

# Notion API Configuration  
NOTION_TOKEN=secret_your-notion-integration-token
NOTION_DATABASE_ID=your-database-id

# GitHub Repository Access
GITHUB_TOKEN=ghp_your-personal-access-token
GITHUB_USERNAME=your-github-username  # defaults to 'angles-ai'
```

### Optional Configuration
```bash
# GitHub repository name (defaults to 'angles-backup')
GITHUB_REPO=angles-backup
```

## Log Files Structure

```
logs/
├── active/                     # Current logs (30 days retention)
│   ├── system_health.log       # Health check results
│   ├── restore.log             # Restoration activities
│   ├── log_manager.log         # Log management operations
│   ├── scheduler.log           # Automated scheduler activities
│   ├── health_report_YYYYMMDD_HHMMSS.json  # Detailed health reports
│   └── restore_summary_YYYYMMDD_HHMMSS.json # Restoration summaries
└── archive/                    # Compressed archived logs (365 days)
    ├── 2025-07-01_system_health.log.gz
    ├── 2025-07-01_restore.log.gz
    └── ...
```

## Health Check Details

### Supabase Health Verification
- API connectivity test
- `decision_vault` table access verification
- Response time measurement
- Sample record count validation

### Notion API Health Verification  
- User authentication verification
- Database access testing (if `NOTION_DATABASE_ID` configured)
- API response time measurement

### GitHub Repository Health Verification
- GitHub API authentication
- Repository existence and access verification
- Push/pull permission validation
- Repository content accessibility testing

### Health Status Levels
- **HEALTHY** - All systems operational
- **DEGRADED** - Non-critical failures (e.g., GitHub repo missing)
- **CRITICAL** - Supabase unavailable (triggers restore process)

## Restore Process Details

### Backup Source
- Pulls latest backup from GitHub repository `angles-backup`
- Searches for backup files in: `/backups/`, `/exports/`, and root directory
- Supports JSON backup format with metadata validation

### Restoration Logic
1. **Data Analysis** - Compare current Supabase data with backup
2. **Missing Records** - Identify records present in backup but missing from Supabase
3. **Selective Restore** - Insert only missing records (no overwrites)
4. **Validation** - Verify successful restoration with record counts

### Safety Features
- Only inserts missing data (never overwrites existing records)
- Comprehensive logging of all operations
- Detailed summaries with restoration counts
- Error handling with graceful degradation

## Error Handling & Recovery

### Health Check Failures
- **Supabase Unavailable:** Triggers immediate restore process
- **Notion API Issues:** Logged as degraded but doesn't trigger restore
- **GitHub Problems:** Noted in health report, restore may fail

### Restore Failures
- **Repository Not Found:** Logged error, manual intervention required
- **Invalid Backup Format:** Skipped with error logging
- **Network Issues:** Retry logic with timeout handling
- **Supabase Insert Errors:** Individual record errors logged, process continues

### Log Management Issues
- **Archive Failures:** Individual file errors logged, process continues
- **Storage Issues:** Space monitoring and cleanup prioritization
- **Permission Problems:** Error logging with fallback to console output

## Manual Recovery Procedures

### Create Missing GitHub Repository
```bash
# Via GitHub CLI (if available)
gh repo create angles-backup --private

# Or create manually via GitHub web interface
# Repository: https://github.com/your-username/angles-backup
```

### Manual Backup Creation
```bash
# Create backup directory structure
mkdir -p /tmp/manual-backup/backups

# Export Supabase data (requires manual SQL export)
# Save as: /tmp/manual-backup/backups/decision_vault_YYYY-MM-DD.json

# Commit to GitHub
cd /tmp/manual-backup
git init
git add .
git commit -m "Manual backup creation"
git remote add origin https://github.com/your-username/angles-backup.git
git push -u origin main
```

### Force Health Check
```bash
# Run immediate health check regardless of schedule
python health_check.py

# Review detailed results
cat logs/active/health_report_*.json | jq .
```

### Emergency Restore
```bash
# Force restore even if health check passes
python restore_from_github.py

# Monitor restoration progress
tail -f logs/active/restore.log
```

## Troubleshooting

### Common Issues

**"Repository not found" Error:**
- Verify `GITHUB_USERNAME` and repository name
- Check GitHub token permissions (repo scope required)
- Ensure repository `angles-backup` exists

**Supabase Connection Timeout:**
- Verify `SUPABASE_URL` and `SUPABASE_KEY`
- Check network connectivity
- Validate Supabase project status

**Notion API Authentication Failed:**
- Verify `NOTION_TOKEN` is valid integration token
- Check `NOTION_DATABASE_ID` format and permissions
- Ensure Notion integration has database access

**Log Archival Failures:**
- Check disk space availability
- Verify write permissions to `logs/archive/`
- Review `logs/active/log_manager.log` for details

### Performance Optimization

**Large Backup Files:**
- Backup files are processed incrementally
- Only missing records are restored (not full replace)
- Network timeouts increased for large transfers

**High Log Volume:**
- Archive retention can be adjusted in `log_manager.py`
- Compression typically achieves 70-90% size reduction
- Active log retention period is configurable

## System Monitoring

### Key Metrics to Monitor
- Health check success rate (should be >95%)
- Restore frequency (should be rare)
- Log archive success rate
- Disk space usage in `/logs/`

### Alert Conditions
- Health check fails for >24 hours
- Restore operations fail repeatedly  
- Log archival failures
- Disk space >80% full

### Regular Maintenance
- Monthly review of archived logs
- Quarterly backup repository cleanup
- Annual review of retention policies
- Periodic GitHub token renewal

## Security Considerations

### Secret Management
- All credentials stored in Replit Secrets (never in code)
- GitHub tokens use minimal required permissions
- Supabase keys should use row-level security when possible

### Backup Security
- GitHub repository should be private
- Backup files contain production data
- Access logs maintained for audit purposes

### Network Security
- All API calls use HTTPS encryption
- Timeout values prevent hung connections
- Error messages avoid exposing sensitive information

---

## Quick Reference

### Start Automated System
```bash
# System starts automatically via Replit workflow
# Manual start: python automated_scheduler.py
```

### Check System Status
```bash
python health_check.py && echo "System Healthy" || echo "Issues Detected"
```

### View Recent Activity
```bash
tail -20 logs/active/system_health.log
tail -20 logs/active/scheduler.log
```

### Emergency Recovery
```bash
python restore_from_github.py
```

For support, check logs in `logs/active/` directory for detailed error information.