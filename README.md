# Angles AI Universe™ Memory System - Backup & Restore

## Overview

The Angles AI Universe™ Memory System provides comprehensive backup and restore capabilities for the memory data and decision vault. The system supports both manual and automated backups with multiple restore sources.

## Backup System

### Manual Backups

Create on-demand backups with optional tagging:

```bash
# Standard manual backup
python run_backup_manual.py

# Tagged backup
python run_backup_manual.py --tag "hotfix-v2.1.0"

# Memory-only backup (skip GitHub)
python run_backup_manual.py --no-github

# Unencrypted backup
python run_backup_manual.py --no-encryption

# Skip sanity checks
python run_backup_manual.py --no-sanity-check
```

### Automated Backups

- **Daily Backups**: Automatically run at 02:00 UTC
- **Memory Backups**: Automatically run at 03:00 UTC
- **Configuration Backups**: Monitor and backup configuration changes every 60 seconds

### Backup Storage

Backups are stored in multiple locations:

- **Supabase Storage**: Private bucket with organized prefixes (`manual/`, `daily/`)
- **GitHub Repository**: Committed to the repository with tagged commits
- **Local Storage**: Temporary files during processing

## Restore System

### Usage

The restore system supports multiple sources and safety features:

```bash
# Restore from Supabase storage
python restore_memory.py --source supabase --file memory_backup_2025-08-07.zip

# Restore from GitHub repository
python restore_memory.py --source github --tag v2.1.0

# Restore from local file
python restore_memory.py --source local --file /backups/backup.zip --force

# Dry-run mode (simulate without changes)
python restore_memory.py --source supabase --file backup.zip --dry-run
```

### Restore Sources

1. **Supabase Storage**: Restore from the private memory_backups bucket
2. **GitHub Repository**: Clone and restore from repository backups
3. **Local Files**: Restore from local backup files

### Safety Features

- **Dry-run Mode**: Test restore operations without making changes
- **Pre-restore Snapshots**: Automatic backup before restore operations
- **Confirmation Prompts**: Double confirmation unless `--force` is used
- **Structure Validation**: Verify backup integrity before restoration

### Restore Process

1. **Source Validation**: Verify backup source availability
2. **File Download**: Retrieve backup from specified source
3. **Decryption**: Automatic AES-256 decryption if needed
4. **Validation**: Verify backup structure and metadata
5. **Extraction**: Unpack backup to temporary directory
6. **Memory Restore**: Restore memory files to `memory/` directory
7. **Database Restore**: Restore decision_vault records to Supabase
8. **Logging**: Log restore actions to Notion and local logs

## Security Features

### Encryption

- **AES-256 Encryption**: All backups encrypted using Fernet
- **Key Management**: Uses `BACKUP_ENCRYPTION_KEY` environment variable
- **Automatic Decryption**: Restore system handles decryption transparently

### Access Control

- **Environment Variables**: All credentials stored as environment secrets
- **Private Storage**: Supabase buckets configured as private
- **Git Authentication**: Uses token-based authentication for GitHub

## File Structure

### Backup Contents

Each backup contains:

```
backup.zip
├── backup_metadata.json     # Backup information and metadata
├── state.json              # Current memory state
├── session_cache.json      # Session cache data
├── long_term.db           # Long-term memory database
└── indexes/               # Search and category indexes
    ├── search_index.json
    └── category_index.json
```

### Directory Structure

```
project/
├── backup_utils.py         # Unified backup utilities
├── run_backup_manual.py    # Manual backup CLI
├── restore_memory.py       # Memory restore system
├── backups/                # Local backup directory
├── logs/                   # System logs
│   ├── backup_manual.log
│   ├── restore.log
│   └── memory_backup.log
└── memory/                 # Memory system files
    ├── state.json
    ├── session_cache.json
    ├── long_term.db
    └── indexes/
```

## Environment Variables

Required environment variables:

```bash
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Backup Encryption
BACKUP_ENCRYPTION_KEY=your_fernet_key

# GitHub Integration
GITHUB_TOKEN=your_github_token
REPO_URL=your_repository_url

# Notion Integration (optional)
NOTION_TOKEN=your_notion_token
NOTION_DATABASE_ID=your_database_id
```

## Retention Policies

- **Manual Backups**: 15 days retention
- **Daily Backups**: 30 days retention
- **Configuration Backups**: 10 most recent versions per file type

## Troubleshooting

### Common Issues

1. **Encryption Errors**: Verify `BACKUP_ENCRYPTION_KEY` is properly set
2. **Supabase Access**: Check RLS policies for bucket creation permissions
3. **GitHub Access**: Ensure `GITHUB_TOKEN` has repository write permissions
4. **File Not Found**: Use dry-run mode to verify backup file locations

### Logs

Check system logs for detailed error information:

- `logs/backup_manual.log` - Manual backup operations
- `logs/restore.log` - Restore operations
- `logs/memory_backup.log` - Daily backup operations

### Support

All operations are logged to Notion for tracking and support purposes. Check the backup/restore notifications in your Notion database for operation status and details.

## Advanced Usage

### Backup with Custom Configuration

```python
from backup_utils import UnifiedBackupManager, BackupConfig

config = BackupConfig(
    backup_type='manual',
    tag='custom-backup',
    include_memory=True,
    include_github=True,
    encryption_enabled=True,
    retention_days=15
)

backup_manager = UnifiedBackupManager(config)
result = backup_manager.run_unified_backup()
```

### Restore with Custom Options

The restore system provides programmatic access for advanced use cases:

```python
from restore_memory import MemoryRestoreManager

restore_manager = MemoryRestoreManager(dry_run=True)
success = restore_manager.run_restore(
    source='local',
    filename='backup.zip',
    force=True
)
```

---

**Angles AI Universe™ Backend Team**  
Version 2.0.0 - August 2025