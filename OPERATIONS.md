# Angles AI Universe™ Operations Guide

## Daily Operations

### Morning Checklist (Recommended)

```bash
# 1. Check system health
python backend_monitor.py

# 2. Review overnight logs
tail -100 logs/active/scheduler.log
tail -100 logs/active/system_health.log

# 3. Verify automated backups
ls -la export/
cat logs/backup.log | tail -20

# 4. Check Notion sync status (with AI analysis)
python memory_sync.py --test

# 5. Verify GPT-5 AI functionality
python tests/test_gpt5_activation.py
```

### System Status Commands

```bash
# Quick health check
python backend_monitor.py

# Comprehensive verification
python verify_deployment.py

# View system metrics
cat logs/active/system_health.json | jq '.'

# Check active workflows
ps aux | grep python | grep -E "(scheduler|memory|backup)"
```

## Maintenance Procedures

### Weekly Maintenance

1. **Log Rotation**
   ```bash
   # Archive old logs
   mkdir -p logs/archive/$(date +%Y-%m-%d)
   mv logs/active/*.log logs/archive/$(date +%Y-%m-%d)/
   
   # Restart services to create new logs
   pkill -f scheduler.py
   nohup python scheduler.py > /dev/null 2>&1 &
   ```

2. **Database Maintenance**
   ```bash
   # Test migration
   python run_migration.py --dry-run
   
   # Verify data integrity
   python memory_sync.py --test
   ```

3. **Backup Verification**
   ```bash
   # Test restore process
   python restore_from_github.py --dry-run
   
   # Manual backup
   python run_backup_now.py
   ```

### Monthly Maintenance

1. **Performance Review**
   ```bash
   # Check system metrics trends
   grep "CPU:" logs/active/system_health.log | tail -30
   grep "Memory:" logs/active/system_health.log | tail -30
   ```

2. **Cleanup Operations**
   ```bash
   # Clean old exports (>30 days)
   find export/ -name "*.json" -mtime +30 -delete
   
   # Archive old logs (>14 days)
   find logs/ -name "*.log" -mtime +14 -exec gzip {} \;
   ```

## Monitoring and Alerts

### Key Metrics to Monitor

1. **System Health**
   - CPU usage < 80%
   - Memory usage < 80%
   - Disk usage < 85%
   - All required services running

2. **Application Health**
   - Database connectivity
   - Notion API availability
   - GitHub backup success
   - Scheduler uptime

3. **Data Flow**
   - Memory sync success rate
   - File change detection
   - Export generation
   - Backup completion

### Log Analysis

```bash
# Error detection
grep -i "error\|failed\|critical" logs/active/*.log

# Performance monitoring
grep "duration\|seconds" logs/active/*.log

# Success rate tracking
grep -c "success\|completed" logs/active/memory_sync.log
grep -c "failed\|error" logs/active/memory_sync.log
```

## Backup and Recovery

### Backup Strategy

1. **Automated Daily Backups** (02:00 UTC)
   - All export files
   - System configuration
   - Critical logs
   - Pushed to GitHub

2. **Manual Backup**
   ```bash
   python run_backup_now.py
   ```

3. **Emergency Backup**
   ```bash
   # Quick data export
   python memory_sync.py --export-only
   
   # Immediate GitHub push
   git add export/*.json
   git commit -m "Emergency backup $(date)"
   git push origin main
   ```

### Recovery Procedures

1. **Data Recovery from GitHub**
   ```bash
   # Test restore (dry run)
   python restore_from_github.py --dry-run
   
   # Full restore
   python restore_from_github.py --restore-decisions
   ```

2. **System Recovery**
   ```bash
   # Reset database schema
   python run_migration.py
   
   # Restore from backup
   python restore_from_github.py --restore-decisions
   
   # Verify system health
   python backend_monitor.py
   ```

3. **Service Recovery**
   ```bash
   # Restart scheduler
   pkill -f scheduler.py
   nohup python scheduler.py > /dev/null 2>&1 &
   
   # Restart health dashboard
   pkill -f health_server.py
   nohup python tools/health_server.py --port 5000 > /dev/null 2>&1 &
   ```

## Troubleshooting Guide

### Common Issues

#### 1. Scheduler Not Running
```bash
# Check if process exists
ps aux | grep scheduler.py

# Check logs for errors
tail -50 logs/active/scheduler.log

# Restart scheduler
pkill -f scheduler.py
nohup python scheduler.py > /dev/null 2>&1 &
```

#### 2. Memory Sync Failures
```bash
# Test connections
python memory_sync.py --test

# Check Notion API status
curl -H "Authorization: Bearer $NOTION_TOKEN" \
     -H "Notion-Version: 2022-06-28" \
     https://api.notion.com/v1/users/me

# Verify Supabase connectivity
python run_migration.py --dry-run
```

#### 3. Backup Failures
```bash
# Check GitHub token
git remote -v
git push origin main

# Verify file permissions
ls -la export/
ls -la logs/

# Manual backup test
python run_backup_now.py
```

#### 4. High Resource Usage
```bash
# Check system metrics
python backend_monitor.py

# Identify resource-heavy processes
top -p $(pgrep -d',' python)

# Review scheduler frequency
grep "Every\|hours\|minutes" logs/active/scheduler.log
```

### Error Codes

| Exit Code | Component | Meaning |
|-----------|-----------|---------|
| 0 | All | Success |
| 1 | All | General failure |
| 2 | Migration | Database error |
| 3 | Memory Sync | API connection failure |
| 4 | Backup | GitHub authentication |
| 5 | Health Check | Critical system failure |

### Log Error Patterns

```bash
# Database connection issues
grep "connection\|timeout\|unreachable" logs/active/*.log

# API authentication problems
grep "401\|403\|unauthorized\|forbidden" logs/active/*.log

# Resource exhaustion
grep "memory\|disk\|space\|limit" logs/active/*.log

# Network connectivity
grep "network\|dns\|resolve" logs/active/*.log
```

## Performance Optimization

### Resource Management

1. **Memory Optimization**
   ```bash
   # Monitor memory usage
   ps aux --sort=-%mem | head -10
   
   # Reduce batch sizes if needed
   # Edit memory_sync.py BATCH_SIZE variable
   ```

2. **CPU Optimization**
   ```bash
   # Monitor CPU usage
   top -o %CPU
   
   # Adjust scheduler frequency if needed
   # Edit scheduler.py timing intervals
   ```

3. **Disk Optimization**
   ```bash
   # Clean up old files
   find logs/ -name "*.log" -mtime +7 -delete
   find export/ -name "*.json" -mtime +14 -delete
   
   # Compress large files
   gzip logs/active/*.log.old
   ```

### Network Optimization

1. **API Rate Limiting**
   - Notion API: 3 requests per second
   - Supabase: 100 requests per minute
   - GitHub API: 5000 requests per hour

2. **Connection Pooling**
   - Reuse HTTP connections
   - Implement connection timeouts
   - Use retry logic with backoff

## Security Operations

### Access Management

1. **Token Rotation**
   ```bash
   # Generate new GitHub token
   # Update .env file
   # Test backup functionality
   python run_backup_now.py
   ```

2. **Environment Security**
   ```bash
   # Verify .env permissions
   ls -la .env
   chmod 600 .env
   
   # Check for exposed secrets in logs
   grep -i "token\|key\|secret" logs/active/*.log
   ```

### Data Protection

1. **Backup Encryption**
   - GitHub repositories are private
   - Local files have restricted permissions
   - Sensitive data is sanitized in logs

2. **Access Auditing**
   ```bash
   # Review API access patterns
   grep "GET\|POST\|PATCH" logs/active/*.log
   
   # Monitor failed authentication
   grep "401\|403\|authentication" logs/active/*.log
   ```

## Scaling Considerations

### Horizontal Scaling

1. **Multiple Instances**
   - Use database locks for coordination
   - Implement leader election
   - Share state via database

2. **Load Distribution**
   - Separate read/write operations
   - Use connection pooling
   - Implement caching layers

### Vertical Scaling

1. **Resource Allocation**
   - Increase memory for large exports
   - Add CPU cores for parallel processing
   - Expand disk space for logs/exports

## Emergency Procedures

### System Down Recovery

1. **Assessment**
   ```bash
   python backend_monitor.py
   python verify_deployment.py
   ```

2. **Service Restart**
   ```bash
   pkill -f python
   nohup python scheduler.py > /dev/null 2>&1 &
   nohup python tools/health_server.py --port 5000 > /dev/null 2>&1 &
   ```

3. **Data Recovery**
   ```bash
   python restore_from_github.py --restore-decisions
   python memory_sync.py --sync-decisions
   ```

### Data Corruption Recovery

1. **Backup Verification**
   ```bash
   python restore_from_github.py --dry-run
   ```

2. **Schema Reset**
   ```bash
   python run_migration.py
   ```

3. **Data Restoration**
   ```bash
   python restore_from_github.py --restore-decisions
   python memory_sync.py --test
   ```

## Contact and Support

### Internal Escalation

1. **Level 1**: Check logs and restart services
2. **Level 2**: Run verification and recovery procedures
3. **Level 3**: Review system architecture and scaling

### External Dependencies

- **Supabase**: Database service status
- **Notion**: API service availability  
- **GitHub**: Repository access and API limits
- **System Resources**: CPU, memory, disk, network