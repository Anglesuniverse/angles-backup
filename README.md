# Angles AI Universe™ Memory Bridge

A sophisticated memory bridge system that connects Replit with Supabase, enabling persistent AI memory management across sessions. This system allows decisions and system instructions to be saved, loaded, and synced automatically.

## 🚀 Features

- **Persistent Memory**: Store AI decisions and instructions in Supabase
- **Cross-Session Sync**: Maintain memory continuity between different sessions  
- **Notion Integration**: Optional sync with Notion databases for collaboration
- **Automated Processing**: Handles unsynced decisions automatically
- **Comprehensive Logging**: Detailed logs for monitoring and debugging
- **Modular Design**: Easy to extend and customize for different use cases

## 📋 Prerequisites

- Python 3.8+
- Supabase account and project
- Notion account (optional, for Notion integration)
- Required Python packages: `supabase`, `python-dotenv`, `requests`

## ⚙️ Setup

### 1. Environment Configuration

1. Copy the environment template:
   ```bash
   cp .env.template .env
   ```

2. Fill in your credentials in `.env`:
   ```env
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_KEY=your_supabase_anon_key_here
   NOTION_API_KEY=your_notion_integration_secret_here
   NOTION_DATABASE_ID=your_notion_database_id_here
   ```

### 2. Supabase Setup

Make sure your Supabase database has the `decision_vault` table with these columns:
- `id` (UUID, primary key)
- `decision` (TEXT)
- `date` (DATE)  
- `type` (TEXT)
- `active` (BOOLEAN)
- `comment` (TEXT)
- `created_at` (TIMESTAMPTZ)
- `updated_at` (TIMESTAMPTZ)
- `synced` (BOOLEAN, for sync tracking)
- `synced_at` (TIMESTAMPTZ, for sync tracking)

### 3. Install Dependencies

```bash
pip install supabase python-dotenv requests
```

## 🔧 Usage

### Manual Execution

Run the memory bridge manually:
```bash
python memory_bridge.py
```

### Programmatic Usage

```python
from memory_bridge import MemoryBridge

# Initialize the bridge
bridge = MemoryBridge()

# Fetch unsynced decisions
decisions = bridge.fetch_unsynced_decisions()
print(f"Found {len(decisions)} unsynced decisions")

# Run full sync process
result = bridge.sync()
if result["success"]:
    print(f"Sync successful: {result['message']}")
else:
    print(f"Sync failed: {result['error']}")
```

### Individual Functions

```python
# Fetch unsynced decisions only
decisions = bridge.fetch_unsynced_decisions()

# Send a specific decision to Notion
success = bridge.send_to_notion(decision_data)

# Mark a decision as synced
bridge.mark_as_synced(decision_id)
```

## 📊 System Architecture

### Core Components

1. **MemoryBridge Class**: Main orchestrator for all sync operations
2. **fetch_unsynced_decisions()**: Retrieves unprocessed data from Supabase
3. **send_to_notion()**: Handles Notion API integration (optional)
4. **mark_as_synced()**: Updates sync status in Supabase
5. **sync()**: Main workflow that coordinates all operations

### Data Flow

```
Supabase decision_vault → fetch_unsynced_decisions() → send_to_notion() → mark_as_synced()
```

## 📝 Logging

The system generates detailed logs in:
- Console output (INFO level)
- `memory_bridge.log` file (persistent logging)

Log format: `timestamp - logger_name - level - message`

## 🔒 Security Notes

- Store all credentials in `.env` file (never commit to version control)
- Use environment variables for all sensitive configuration
- The system validates all required environment variables on startup
- All API calls include proper timeout handling

## 🚨 Error Handling

The memory bridge includes comprehensive error handling:
- Connection validation before processing
- Individual decision error isolation  
- Detailed error logging and statistics
- Graceful degradation on partial failures

## 📈 Monitoring

The sync function returns detailed statistics:
```python
{
    "success": true,
    "message": "Synced 5/5 decisions", 
    "stats": {
        "total_found": 5,
        "successfully_synced": 5,
        "failed_sync": 0,
        "failed_mark": 0,
        "errors": []
    },
    "duration_seconds": 2.45
}
```

## 🔄 Automation

### Scheduled Execution

You can run the memory bridge on a schedule using:

**Cron (Linux/Mac):**
```bash
# Run every 5 minutes
*/5 * * * * cd /path/to/memory_bridge && python memory_bridge.py
```

**Windows Task Scheduler:**
Create a task that runs `python memory_bridge.py` at your desired interval.

### Integration with Other Systems

The modular design allows easy integration with:
- CI/CD pipelines
- Monitoring systems
- Other AI/ML workflows
- Custom scheduling solutions

## 🛠️ Development

### Adding New Sync Targets

To add support for additional services (besides Notion):

1. Create a new method like `send_to_service()`
2. Add the service configuration to environment variables
3. Update the `sync()` method to include the new target
4. Add appropriate error handling and logging

### Customizing Decision Processing

The system can be extended to handle different types of decisions or add custom processing logic by modifying the `send_to_notion()` method or creating new processing methods.

## 📄 License

This system is part of the Angles AI Universe™ backend engineering suite.

## 🤝 Support

For technical support or feature requests, contact the backend engineering team.

---

**Angles AI Universe™** - Enabling persistent AI memory for enhanced learning and decision continuity.