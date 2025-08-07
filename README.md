# Angles AI Universe™ Memory System

A comprehensive memory management system that syncs AI decisions between Supabase and Notion, with automated GitHub backups and scheduled execution.

## 🚀 Overview

This system provides persistent memory for AI operations by:

1. **Memory Sync Agent** - Syncs unsynced decisions from Supabase to Notion
2. **Git Backup Agent** - Creates safe GitHub backups of sanitized exports and logs  
3. **Orchestrated Execution** - Coordinates both agents with concise status reporting
4. **Scheduled Automation** - Runs automatically every 6 hours via Replit schedules

## 📋 Required Secrets

Add these environment variables to your Replit secrets:

### Supabase Configuration
```
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
```
*Note: SUPABASE_KEY is accepted as fallback for SUPABASE_SERVICE_ROLE_KEY*

### Notion Configuration  
```
NOTION_API_KEY=your_notion_integration_secret
NOTION_DATABASE_ID=your_notion_database_id
```

### GitHub Configuration
```
GITHUB_TOKEN=your_github_personal_access_token
GIT_USERNAME=your_github_username
GIT_EMAIL=your_email@example.com
REPO_URL=https://github.com/username/repository-name.git
```

## 🛠️ How to Run Locally

### Manual Execution
```bash
# Run the complete system
python run_all.py

# Run components individually
python memory_sync_agent.py
python backup/git_backup.py
```

### Test Connections
```bash
# Test Supabase and Notion connections
python -c "from memory_sync_agent import MemorySyncAgent; agent = MemorySyncAgent(); agent.test_connections()"

# Test GitHub backup setup
python backup/git_backup.py
```

## ⚙️ How to Enable Replit Schedule

### Method 1: Replit UI (Recommended)
1. Go to your Replit project
2. Click on **"Tools"** → **"Deployments"**
3. Navigate to **"Schedules"** tab
4. Click **"Create Schedule"**
5. Configure:
   - **Name**: `Memory System Sync`
   - **Command**: `python run_all.py`
   - **Schedule**: `0 */6 * * *` (every 6 hours)
   - **Environment**: Select your environment with secrets

### Method 2: Manual Schedule Configuration
If Replit schedules are not available, the system will fall back to cron-like scheduling.

## 📊 Data Flow Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   SUPABASE      │    │   NOTION API    │    │   GITHUB REPO   │
│ decision_vault  │    │   Database      │    │   Backup        │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          │ 1. Fetch unsynced    │ 2. Create pages      │ 4. Push exports
          │    decisions         │    (title, date,     │    & logs
          ▼                      │     tags)            ▼
┌─────────────────────────────────┴──────────────────────────────┐
│                MEMORY SYNC AGENT                               │
│  • Rotating logs (5x1MB) → logs/memory_sync.log              │
│  • Sanitized exports → export/decisions_YYYYMMDD.json        │
│  • Mark notion_synced=true after success                     │
└─────────────────┬───────────────────────────────────────────────┘
                  │ 3. Generate exports
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                   GIT BACKUP AGENT                              │
│  • git init (if needed) + configure user                      │  
│  • git add export/*.json logs/*.log                           │
│  • git commit "[auto] memory sync <timestamp>"                │
│  • git push origin main (with embedded GitHub token)          │
└─────────────────────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     RUN_ALL.PY                                 │
│  1. python memory_sync_agent.py                               │
│  2. python backup/git_backup.py                               │
│  3. Print: "OK: synced <n> items, exported <file>, backup     │
│            pushed to GitHub"                                   │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 File Structure

```
├── memory_sync_agent.py     # Main sync agent (Supabase ↔ Notion)
├── backup/
│   ├── __init__.py         # Backup module
│   └── git_backup.py       # GitHub backup agent
├── run_all.py              # Orchestrator script
├── logs/                   # Rotating logs (git-ignored)
│   └── memory_sync.log     # Main log file
├── export/                 # Sanitized JSON exports
│   └── decisions_*.json    # Daily exports
├── .gitignore              # Excludes logs/, secrets, temp files
└── README.md               # This file
```

## 🔧 Database Schema Requirements

### Supabase `decision_vault` Table

Required columns:
```sql
- id (UUID, primary key)
- decision (TEXT, not null)
- type (TEXT, not null) 
- date (DATE, not null)
- active (BOOLEAN, default true)
- comment (TEXT, optional)
- created_at (TIMESTAMPTZ)
- updated_at (TIMESTAMPTZ)

-- Sync tracking (one of these):
- notion_synced (BOOLEAN, default false)     -- Preferred
- synced (BOOLEAN, default false)            -- Fallback
```

### Notion Database Properties

Required properties:
```
- Name (Title) - Decision title/summary
- Message (Rich text) - Full decision content  
- Date (Date) - Decision date
- Tag (Multi-select) - Decision type + status tags
```

## 🚨 Troubleshooting

### Authentication Errors

**Supabase RLS (Row Level Security):**
```
Error: "permission denied" or "insufficient permissions"
Solution: Use SUPABASE_SERVICE_ROLE_KEY instead of SUPABASE_KEY, or disable RLS for decision_vault table
```

**Notion 400 Errors:**
```
Error: "Invalid property" or "body failed validation"
Solution: Verify Notion database has Name, Message, Date, Tag properties with correct types
```

**GitHub Authentication:**
```
Error: "authentication failed" or "remote: Repository not found"
Solutions:
1. Verify GITHUB_TOKEN has repo permissions
2. Check REPO_URL format: https://github.com/username/repo.git
3. Ensure repository exists and is accessible
```

### Common Issues

**No unsynced decisions found:**
```
1. Check if notion_synced or synced column exists in decision_vault
2. Verify there are rows with notion_synced=false or synced=false
3. Check Supabase RLS policies
```

**Export files not created:**
```
1. Verify export/ directory exists and is writable
2. Check if any decisions were successfully synced
3. Review logs/memory_sync.log for export errors
```

**GitHub backup fails:**
```
1. Verify git is installed and accessible
2. Check network connectivity to GitHub
3. Ensure repository permissions allow pushes
4. Review git backup logs for detailed errors
```

### Log Analysis

Check `logs/memory_sync.log` for detailed operation logs:
```bash
# View recent logs
tail -f logs/memory_sync.log

# Search for errors
grep -i error logs/memory_sync.log

# View sync statistics
grep -i "sync completed" logs/memory_sync.log
```

## 🔒 Security Features

- **No Secret Exposure**: All credentials read from environment variables only
- **Sanitized Exports**: Removes sensitive keywords (key, token, secret, password)
- **Git-ignored Logs**: Prevents accidental commit of logs with potential secrets
- **Embedded Token Authentication**: GitHub token embedded in URL at runtime, never stored
- **Rotating Logs**: Automatic log rotation prevents disk space issues

## 🎯 Success Indicators

When everything works correctly, you should see:
```
OK: synced 5 items, exported file export/decisions_20250807.json, backup pushed to GitHub
```

The system maintains:
- Rotating logs in `logs/` (max 5 files, 1MB each)
- Daily JSON exports in `export/` (sanitized, no secrets)
- Git history of all exports and logs in your GitHub repository
- Supabase records marked as `notion_synced=true`
- Corresponding Notion pages with decision content

## 📈 Monitoring

The system provides comprehensive monitoring through:
- Structured logging with timestamps and levels
- Export file generation for audit trails  
- Git commit history for backup verification
- Replit schedule execution logs
- Status summaries with success/failure counts

For production monitoring, review:
1. `logs/memory_sync.log` - Detailed operation logs
2. `export/decisions_*.json` - Daily export files  
3. GitHub repository - Backup commit history
4. Replit schedule logs - Execution history

---

**Angles AI Universe™** - Enabling persistent AI memory with automated backups and monitoring.