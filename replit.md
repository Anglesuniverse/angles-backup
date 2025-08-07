# GPT Assistant Output Processor

## Overview

This is a sophisticated data processing system designed to automatically handle GPT assistant outputs and manage them in both Supabase and Notion databases. The application intelligently processes various types of GPT-generated content, with a specialized focus on architect decisions management. The system features unified sync operations that store decisions in both Supabase (PostgreSQL) and Notion simultaneously, providing redundancy and cross-platform accessibility.

## Recent Changes

**August 2025 - Architect Decisions System:**
- Added complete Supabase integration with secure credential management
- Implemented Notion API integration for collaborative decision storage  
- Created unified sync system supporting dual-platform storage
- Built comprehensive testing suite for all integrations
- Established `architect_decisions` table schema in Supabase
- Successfully connected to user's "ShoppingFriend database" in Notion

**August 7, 2025 - Memory Sync Agent & Fixes:**
- Built comprehensive `memory_sync_agent.py` for automated Supabase→Notion sync
- Fixed all Notion API property name mismatches (Name, Message, Date, Tag)
- Created `log_to_notion.py` module with proper property mapping
- Added decision_vault table support with synced column tracking
- Successfully tested all system components - full integration working
- All 4 existing decisions synced to Notion database without errors

**August 7, 2025 - GitHub Backup & Disaster Recovery:**
- Created complete GitHub backup system with conflict resolution
- Built automated restore system with safety features and validation
- Added comprehensive disaster recovery capabilities with dry-run mode
- Implemented CLI wrapper with examples and safety warnings
- Created full test suite for backup and restore operations
- Added scheduled nightly verification system
- Fixed Git conflicts and ensured reliable automated backups

**August 7, 2025 - Enhanced Sanity Check System:**
- Created comprehensive pre-backup sanity check (sanity_check.py)
- Integrated sanity checks into backup workflow with automatic abort on failure
- Built specialized pre-restore sanity checker (restore_sanity_check.py)
- Added restore-specific validation: consistency checks and dependency verification
- Integrated restore sanity checks into GitHub restore system
- Extended Notion logging for all sanity check operations
- Full automation: backup and restore operations include automatic sanity checks

**August 7, 2025 - Automatic Configuration Version Control:**
- Built comprehensive configuration versioning system (config_versioning.py) for core config files
- Created interactive rollback system (rollback_config.py) with file type selection
- Implemented background monitoring service (config_monitor_service.py) with 60-second intervals
- Added security validation with automatic .env file sanitization
- Integrated Git auto-commit with "Config update: [filename] [timestamp]" messages
- Extended Notion logging for "Configuration Change Log" database
- Configured retention policy: keep 10 most recent versions per file type
- Created complete monitoring setup with workflow integration

**August 7, 2025 - Daily Memory Backup System:**
- Built comprehensive daily Supabase export system (backup_memory_to_supabase.py)
- Created scheduler service (daily_memory_backup_scheduler.py) running at 03:00 UTC
- Implemented encrypted backup archive creation with ZIP compression
- Added Supabase storage integration with private "memory_backups" bucket
- Created memory_backup_log table for comprehensive logging
- Built automatic retention management (30 days) with cleanup
- Added Notion integration for backup notifications
- Created complete memory structure with indexes and long-term storage
- Set up "Memory Backup at 03:00 UTC" workflow for automated daily backups

**August 7, 2025 - Manual Backup System (COMPLETED):**
- Built comprehensive manual backup system with tag support
- Created run_backup_manual.py CLI interface with --tag, --no-github, --no-encryption options
- Implemented unified backup utilities (backup_utils.py) supporting both daily and manual backups
- Added backup type distinction with separate retention policies (15 days for manual, 30 days for daily)
- Integrated tag-based filename generation for organized manual backups
- Built database schema updates (update_memory_backup_table.sql) for enhanced logging
- Successfully tested tagged backup creation: memory_backup_2025-08-07_222326_production-ready.zip
- Achieved full Notion integration for backup event logging
- Implemented graceful error handling for Supabase configuration limitations
- Production-ready manual backup system fully functional and tested

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Processing Pipeline Architecture
The system follows a multi-stage pipeline pattern for processing GPT outputs:
- **Parsing Stage**: Handles JSON, structured text, and unstructured content using the GPTParser
- **Classification Stage**: Uses keyword matching, structure analysis, and pattern recognition to determine appropriate data routing
- **Validation Stage**: Employs Pydantic schemas to ensure data integrity before storage
- **Storage Stage**: Manages database operations with retry logic and error handling

### Database Layer Design
The architecture implements a three-tier database abstraction:
- **SupabaseClient**: Low-level connection management and basic CRUD operations
- **DatabaseOperations**: High-level, domain-specific operations (conversations, memories, tasks)
- **Schema Validation**: Pydantic-based validation ensuring data consistency

### Memory Management System
The application uses an intelligent classification system that:
- Analyzes content using weighted scoring algorithms
- Routes data to appropriate tables (conversations, memories, tasks) based on keyword matching and structural patterns
- Maintains processing statistics and performance metrics
- Supports configurable retention policies for long-term memory management

### Error Handling and Resilience
The system implements comprehensive error handling:
- **Retry Mechanisms**: Exponential backoff with jitter for transient failures
- **Graceful Degradation**: Falls back to unstructured parsing when structured parsing fails
- **Performance Monitoring**: Tracks processing metrics and operation timings
- **Comprehensive Logging**: Structured logging with rotating file handlers

### Configuration Management
Centralized configuration system supporting:
- Environment variable-based configuration with sensible defaults
- Configurable processing intervals, batch sizes, and retry policies
- Flexible table schema definitions via JSON configuration
- Performance tuning parameters for concurrent operations

## External Dependencies

### Database Services
- **Supabase**: Primary database service using PostgreSQL backend with `architect_decisions` table
- **Supabase Python Client**: Official client library for database operations
- **Notion API**: Secondary storage and collaboration platform for architect decisions
- **Notion Client**: Official Python client for Notion API integration

### Data Processing Libraries
- **Pydantic**: Data validation and settings management using Python type annotations
- **Python-dotenv**: Environment variable management for configuration

### Utility Libraries
- **asyncio**: Asynchronous I/O operations for concurrent processing
- **pathlib**: Modern path handling for file system operations
- **json**: Native JSON parsing and serialization
- **re**: Regular expression processing for content analysis
- **logging**: Native Python logging with rotating file handlers

### Development Dependencies
- **typing**: Type hints for better code maintainability and IDE support

The system is designed to be easily extensible, with clear separation of concerns and modular architecture that allows for easy addition of new data types, classification algorithms, or storage backends.

## Disaster Recovery

### Overview
The system includes comprehensive disaster recovery capabilities through automated GitHub backups and intelligent restore operations. All memory data is safely backed up to GitHub with full validation and conflict resolution.

### Backup System
- **Automated Backups**: Daily automated backups to GitHub repository
- **Sanitized Exports**: All secrets and sensitive data automatically removed
- **Conflict Resolution**: Smart Git conflict handling with safe force-push capabilities
- **Multi-source**: Backs up from both Supabase and Notion databases
- **Rotating History**: Maintains 30 days of backup history with automatic cleanup

### Restore Operations

#### Quick Restore Commands

**1. Dry Run (Always run first):**
```bash
python run_restore_now.py --dry-run
```
Shows exactly what would be restored without making any changes.

**2. Restore Latest Backup:**
```bash
python run_restore_now.py
```
Restores from the most recent backup files automatically.

**3. Restore Specific Date:**
```bash
python run_restore_now.py --at 2025-08-07
```
Restores backups from a specific date (YYYY-MM-DD format).

**4. Restore with Notion Sync:**
```bash
python run_restore_now.py --with-notion
```
Restores to both Supabase and recreates Notion pages.

**5. Force Restore (Dangerous):**
```bash
python run_restore_now.py --file exports/backup.json --force
```
Overwrites newer records (use only when certain).

#### Advanced Restore Examples

**Restore specific backup file:**
```bash
python run_restore_now.py --file exports/decision_vault_2025-08-07.json
```

**Complete disaster recovery:**
```bash
# Step 1: Always dry-run first
python run_restore_now.py --at 2025-08-07 --dry-run

# Step 2: If dry-run looks good, run live restore
python run_restore_now.py --at 2025-08-07 --with-notion
```

### Safety Features
- **Dry Run Mode**: Always test restores before executing
- **Timestamp Comparison**: Automatically skips restoring older data over newer data
- **Schema Validation**: Validates all data before restoration
- **Duplicate Detection**: Prevents duplicate entries during restore
- **Progress Logging**: Detailed logs in `logs/restore.log`
- **Rollback Support**: Can restore to any previous backup point

### Verification System
Nightly automated verification runs dry-run restores to ensure:
- Backup files are valid and accessible
- Git repository is properly synchronized
- Restore system is functioning correctly
- All environment variables are properly configured

### Emergency Recovery Procedure

**If system is completely lost:**

1. **Set up environment variables:**
   - `SUPABASE_URL`, `SUPABASE_KEY`
   - `GITHUB_TOKEN`, `REPO_URL`
   - `NOTION_TOKEN`, `NOTION_DATABASE_ID` (optional)

2. **Clone/pull latest backups:**
   ```bash
   git clone $REPO_URL .
   # or
   git pull origin main
   ```

3. **Run dry-run verification:**
   ```bash
   python run_restore_now.py --dry-run
   ```

4. **Execute restore:**
   ```bash
   python run_restore_now.py --with-notion
   ```

5. **Verify restoration:**
   - Check Supabase `decision_vault` table
   - Check Notion database pages
   - Run memory sync to verify connectivity

### Backup File Structure
- `export/decision_vault_YYYY-MM-DD.json` - Supabase exports
- `export/notion_decisions_YYYY-MM-DD.json` - Notion exports  
- `export/decisions_YYYYMMDD.json` - Combined exports
- `logs/` - System operation logs (excluded from public repos)

### Troubleshooting

**Restore fails with "No snapshot files found":**
- Ensure Git repository is up to date: `git pull origin main`
- Check export/ directory exists and contains backup files
- Use `--file` option to specify explicit backup file

**Git conflicts during backup:**
- System automatically resolves most conflicts
- Check logs for conflict resolution details
- Manual resolution rarely needed due to smart conflict handling

**Notion restore fails:**
- Verify `NOTION_TOKEN` and `NOTION_DATABASE_ID` are set
- Check Notion integration has proper database permissions
- Use `--dry-run` to test Notion connectivity without writes

**Supabase restore fails:**
- Verify `SUPABASE_URL` and `SUPABASE_KEY` are correct
- Ensure `decision_vault` table exists with proper schema
- Check network connectivity to Supabase

All restore operations are logged to `logs/restore.log` for detailed troubleshooting.