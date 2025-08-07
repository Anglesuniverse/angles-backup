# Bidirectional Supabase-Notion Sync Service

A robust, production-ready bidirectional synchronization service between Supabase and Notion for Angles AI Universe™. This service keeps your `decision_vault` table and Notion database in perfect sync with intelligent conflict resolution and comprehensive monitoring.

## 🎯 Features

- **Bidirectional Sync**: Seamless two-way synchronization between Supabase and Notion
- **Intelligent Matching**: Primary matching by `notion_page_id`, fallback by content checksum
- **Conflict Resolution**: Timestamp-based conflict resolution with configurable strategies
- **Retry Logic**: Robust retry mechanisms with exponential backoff for transient failures
- **Rate Limiting**: Respects Notion API rate limits with intelligent backoff
- **Health Monitoring**: Real-time health dashboard and comprehensive logging
- **Dry Run Mode**: Safe preview of sync operations before execution
- **Manual Controls**: CLI tools for on-demand sync operations

## 📋 Prerequisites

### Required Environment Variables

Set these in your Replit Secrets:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
NOTION_API_KEY=secret_your_notion_integration_key
NOTION_DATABASE_ID=your_notion_database_id
```

### Optional Environment Variables

```bash
SYNC_BATCH_SIZE=100              # Records per batch (default: 100)
SYNC_MAX_RETRIES=3               # Max retry attempts (default: 3)
SYNC_INTERVAL_MINUTES=15         # Sync frequency (default: 15)
```

## 🗄️ Database Setup

### Supabase Schema

If your `decision_vault` table is missing required columns, run this SQL in your Supabase SQL Editor:

```sql
-- Add missing columns to decision_vault table
ALTER TABLE decision_vault 
ADD COLUMN IF NOT EXISTS notion_page_id TEXT,
ADD COLUMN IF NOT EXISTS notion_synced BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS checksum TEXT,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_decision_vault_notion_page_id 
ON decision_vault(notion_page_id);

CREATE INDEX IF NOT EXISTS idx_decision_vault_checksum 
ON decision_vault(checksum);

CREATE INDEX IF NOT EXISTS idx_decision_vault_notion_synced 
ON decision_vault(notion_synced);

-- Add trigger to update updated_at automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE OR REPLACE TRIGGER update_decision_vault_updated_at 
    BEFORE UPDATE ON decision_vault 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
```

### Complete Table Schema

Your `decision_vault` table should have this structure:

```sql
CREATE TABLE decision_vault (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision TEXT NOT NULL,
    type TEXT NOT NULL,
    date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    notion_page_id TEXT NULL,
    notion_synced BOOLEAN DEFAULT FALSE,
    checksum TEXT NULL
);
```

### Notion Database Setup

Your Notion database must have these properties with **exact** API names:

| Property Name | Type | API Name | Options |
|---------------|------|----------|---------|
| Decision | Title | `Decision` | - |
| Type | Multi-select | `Type` | Policy, Architecture, Ops, UX, Other |
| Date | Date | `Date` | - |
| Checksum | Rich text | `Checksum` | - |
| Synced | Checkbox | `Synced` | (optional) |

**Example Notion Property JSON:**
```json
{
  "Decision": {"title": [{"text": {"content": "Implement user authentication"}}]},
  "Type": {"multi_select": [{"name": "Architecture"}]},
  "Date": {"date": {"start": "2025-08-07"}},
  "Checksum": {"rich_text": [{"text": {"content": "abc123..."}}]},
  "Synced": {"checkbox": true}
}
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install supabase notion-client flask
```

### 2. Test Connection

```bash
python -m sync.run_sync --dry-run
```

### 3. Run Manual Sync

```bash
python -m sync.run_sync
```

### 4. Start Automated Sync

```bash
python -m sync.schedule_sync
```

### 5. Launch Health Dashboard

```bash
python tools/health_server.py
```

Then visit `http://localhost:8080` (or your Replit URL on port 8080).

## 🛠️ Usage

### Manual Operations

```bash
# Run sync immediately
python tools/controls.py sync-now

# Preview changes without applying
python tools/controls.py dry-run

# View last sync statistics
python tools/controls.py report
```

### Automated Scheduling

```bash
# Start continuous sync (every 15 minutes)
python -m sync.schedule_sync

# Run once and exit
python -m sync.schedule_sync --once
```

### Health Monitoring

```bash
# Start health dashboard on port 8080
python tools/health_server.py

# Custom host/port
python tools/health_server.py --host 0.0.0.0 --port 5000
```

## 📊 Monitoring & Health

### Health Dashboard

Access the web dashboard at `http://your-replit-url:8080`:

- **Real-time Status**: Current sync health and last run results
- **Statistics**: Record counts, sync metrics, and performance data  
- **Error Details**: Comprehensive error logging and troubleshooting
- **Auto-refresh**: Updates every 30 seconds automatically

### API Endpoints

- `GET /health` - JSON health status
- `GET /ping` - Simple health check
- `GET /` - HTML dashboard

### Log Files

- `logs/sync.log` - Detailed sync operations (rotating, 10MB max)
- `logs/last_success.json` - Latest sync run statistics

## 🔧 Configuration

### Sync Behavior

The sync service uses this logic:

1. **Fetch**: Paginate through both Supabase and Notion records
2. **Normalize**: Clean whitespace, compute SHA256 checksums
3. **Match**: Primary by `notion_page_id`, fallback by checksum
4. **Resolve**: Conflicts resolved by most recent `updated_at` timestamp
5. **Apply**: Create missing records, update changed records

### Conflict Resolution

When records differ:
- **Winner**: Most recently updated record (by timestamp)
- **Fallback**: Supabase as source of truth if no timestamps
- **Safety**: No hard deletes (soft-delete policy)

### Rate Limiting

- **Notion API**: Respects 429 rate limits with exponential backoff
- **Batch Processing**: 100 records per batch (configurable)
- **Retry Logic**: 3 attempts with jitter for transient failures

## 🧪 Testing

### Run Tests

```bash
python -m pytest tests/test_sync.py -v
```

### Integration Test

```bash
python tests/test_sync.py
```

### Dry Run Testing

```bash
# Test complete sync without changes
python -m sync.run_sync --dry-run

# Test specific operations
python tools/controls.py dry-run
```

## 🚨 Troubleshooting

### Common Issues

**"Missing required environment variables"**
- Verify all environment variables are set in Replit Secrets
- Check variable names match exactly (case-sensitive)

**"Supabase connection failed"**
- Verify `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`
- Ensure service role key has sufficient permissions
- Check if `decision_vault` table exists

**"Notion connection failed"**
- Verify `NOTION_API_KEY` and `NOTION_DATABASE_ID`
- Ensure Notion integration has database access
- Check database ID format (should be 32 characters)

**"Property not found" errors**
- Verify Notion database properties match required names exactly
- Check property types match the schema
- Ensure all required properties exist

**Sync conflicts or duplicates**
- Check if records have valid timestamps
- Verify checksum computation is working
- Review conflict resolution logs

### Debug Mode

Enable detailed logging:

```bash
export LOG_LEVEL=DEBUG
python -m sync.run_sync --dry-run
```

### Health Check

```bash
# Test all connections
python -c "
from sync.supabase_client import SupabaseClient
from sync.notion_client import NotionClient

sb = SupabaseClient()
notion = NotionClient()

print('Supabase:', sb.test_connection())
print('Notion:', notion.test_connection())
"
```

## 📁 Project Structure

```
sync/
├── __init__.py              # Package initialization
├── config.py                # Configuration and environment variables
├── supabase_client.py       # Supabase client wrapper
├── notion_client.py         # Notion API client wrapper
├── diff.py                  # Checksum computation and diff engine
├── run_sync.py              # Main sync orchestrator
├── schedule_sync.py         # Automated scheduling
└── logging_util.py          # Logging and health utilities

tools/
├── controls.py              # Manual sync controls
└── health_server.py         # Web health dashboard

tests/
└── test_sync.py             # Integration tests

logs/
├── sync.log                 # Rotating sync logs
└── last_success.json        # Latest run statistics
```

## 🔒 Security

- **Service Role Key**: Used for Supabase admin operations
- **No Secrets in Logs**: Sensitive data never logged
- **Environment Variables**: All credentials via environment only
- **Rate Limiting**: Prevents API abuse
- **Read-only Operations**: Dry-run mode for safe testing

## 🚀 Deployment in Replit

### 1. Add to Replit Workflows

Create a workflow for automated sync:

```python
# In your Replit configuration
workflows_set_run_config_tool(
    name="Bidirectional Sync",
    command="python -m sync.schedule_sync",
    output_type="console"
)
```

### 2. Health Dashboard Workflow

```python
workflows_set_run_config_tool(
    name="Sync Health Dashboard", 
    command="python tools/health_server.py --port 8080",
    output_type="webview",
    wait_for_port=8080
)
```

### 3. Port Configuration

For health dashboard access, expose port 8080 in your Replit configuration.

## 📈 Performance

- **Batch Processing**: 100 records per batch for optimal performance
- **Connection Pooling**: Reuses clients for multiple operations
- **Rate Limiting**: Prevents API throttling
- **Incremental Sync**: Only processes changed records
- **Checksum Optimization**: Fast content comparison

## 🆘 Support

For issues and questions:

1. Check the troubleshooting section above
2. Review logs in `logs/sync.log`
3. Test with dry-run mode first
4. Verify environment variables and database schema
5. Check the health dashboard for real-time status

---

**Angles AI Universe™ Backend Team**  
*Bidirectional Sync Service v1.0.0*