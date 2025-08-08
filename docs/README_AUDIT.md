# Angles AI Universe™ Audit System Documentation

## Overview

The Angles AI Universe™ Audit System provides comprehensive data integrity monitoring, performance benchmarking, and emergency validation capabilities for the entire platform. The system consists of three main components designed to ensure system reliability, data consistency, and operational excellence.

## System Components

### 1. Monthly Deep Audit (`audit/monthly_audit.py`)

**Purpose:** Comprehensive monthly data integrity sweep across all critical systems.

**Schedule:** 1st of each month at 03:30 UTC

**Key Features:**
- **Supabase Table Validation:** Validates data integrity for `decision_vault` and `ai_decision_log` tables
- **Schema Validation:** Checks column presence, data types, and constraint compliance
- **Null Analysis:** Monitors null percentages and flags excessive null values
- **Notion Sync Consistency:** Verifies synchronization between Supabase and Notion databases
- **GitHub Backup Verification:** Validates backup repository state and freshness
- **Comprehensive Reporting:** Generates JSON and Markdown reports with detailed findings

**Critical Thresholds:**
- Null percentage > 5% triggers critical alert
- Query performance > 200ms triggers warning
- Sync drift > 3 items triggers major drift alert
- Backup age > 168 hours (7 days) triggers outdated alert

**Output:**
- JSON Report: `export/audit/monthly_audit_{YYYYMMDD_HHMMSS}.json`
- Markdown Report: `export/audit/monthly_audit_{YYYYMMDD_HHMMSS}.md`
- Logs: `logs/audit/monthly_audit.log`

### 2. Auto-Benchmarking System (`perf/perf_benchmark.py`)

**Purpose:** Continuous performance monitoring across all external integrations.

**Schedule:** Daily at 04:10 UTC

**Performance Metrics:**
- **Supabase Read:** Latest 50 records from decision_vault (target: <2000ms)
- **Supabase Write:** Test record insertion to temp table (target: <2000ms)
- **Notion Write:** Performance test page creation (target: <2000ms)
- **Git Push:** Noop commit and push operation (target: <5000ms)

**Performance Thresholds:**
- **Warning:** >2000ms for database operations, >5000ms for Git operations
- **Critical:** >5000ms for any operation

**Output:**
- CSV Data: `logs/perf/perf_{YYYYMMDD}.csv`
- Rolling Summary: `docs/perf/summary.md` (last 30 days, min/avg/p95 statistics)
- Logs: `logs/perf/benchmark.log`

### 3. Panic Kit (`scripts/run_audit_now.py`)

**Purpose:** Emergency one-click audit system for immediate system validation.

**Usage:** Manual execution when system issues are suspected or for validation after maintenance.

**Audit Sequence:**
1. **Monthly Deep Audit** (critical) - Full data integrity sweep
2. **Restore Verification** (critical) - Dry-run backup validation
3. **Performance Benchmark** (non-critical) - System performance validation
4. **Operational Smoke Tests** (critical) - Basic system functionality validation

**Exit Codes:**
- `0`: All audits passed or only warnings detected
- `1`: Some audits failed but no critical findings
- `2`: Critical findings detected (≥1 critical issue)
- `130`: Interrupted by user (Ctrl+C)
- `255`: System error during execution

**Output:**
- JSON Report: `export/audit/panic_kit_{panic_id}.json`
- Markdown Report: `export/audit/panic_kit_{panic_id}.md`
- Logs: `logs/audit/panic_kit.log`

### 4. Restore Verification (`audit/verify_restore.py`)

**Purpose:** Dry-run validation of backup integrity and restore capability.

**Schedule:** Weekly on Sundays at 03:50 UTC

**Validation Steps:**
1. **Repository Clone:** Clones latest backup repository to temporary directory
2. **Export Discovery:** Catalogs all available export files
3. **Schema Validation:** Validates export file structure against expected schemas
4. **Data Comparison:** Compares export record counts with live Supabase data
5. **Integrity Verification:** Validates data types, constraints, and relationships

**Output:**
- JSON Report: `export/audit/restore_verify_{verify_id}.json`
- Logs: `logs/audit/restore_check.log`

## Scheduling Integration

All audit components are integrated into the main operations scheduler (`ops_scheduler.py`):

```
📅 AUTOMATED OPERATIONS SCHEDULE
   🌅 Daily 03:00 UTC: Health Check + Conditional Restore
   💾 Daily 02:10 UTC: Backup Operations
   📄 Weekly Sun 02:30 UTC: Weekly Summary Generation
   🔍 Every 60 min: Config Monitor + Schema Guard
   🏢 Monthly 1st 03:30 UTC: Deep Audit (Data Integrity)
   🔧 Weekly Sun 03:50 UTC: Restore Verification (Dry-run)
   ⚡ Daily 04:10 UTC: Performance Benchmark
```

## Manual Execution

### Running Individual Components

```bash
# Monthly Deep Audit
python audit/monthly_audit.py --run

# Performance Benchmark
python perf/perf_benchmark.py --run

# Restore Verification
python audit/verify_restore.py --run

# Panic Kit (Emergency Audit)
python scripts/run_audit_now.py --run
```

### Panic Kit Options

```bash
# List available audits
python scripts/run_audit_now.py --list

# Run with custom timeout
python scripts/run_audit_now.py --run --timeout 900

# Continue on failures (don't stop on critical audit failures)
python scripts/run_audit_now.py --run --continue-on-failure

# Disable alert notifications
python scripts/run_audit_now.py --run --no-alerts
```

### Performance Benchmark Options

```bash
# Test individual components
python perf/perf_benchmark.py --test-supabase
python perf/perf_benchmark.py --test-notion
python perf/perf_benchmark.py --test-git

# Update performance summary only
python perf/perf_benchmark.py --summary
```

## Alert Integration

The audit system integrates with the existing alert manager (`alerts/notify.py`) to send notifications for:

- **Critical Data Integrity Issues:** Schema violations, excessive null values, constraint failures
- **Sync Drift Alerts:** Significant discrepancies between Supabase and Notion
- **Performance Degradation:** Operations exceeding critical thresholds
- **Backup Issues:** Missing or outdated backup repositories
- **System Failures:** Audit system failures or critical operational errors

## Configuration

### Environment Variables

All audit components use the same environment configuration:

```bash
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Optional (for full functionality)
NOTION_TOKEN=your-notion-integration-token
NOTION_DATABASE_ID=your-notion-database-id
GITHUB_TOKEN=your-github-personal-access-token
REPO_URL=https://github.com/your-org/your-backup-repo
```

### Performance Thresholds

Default performance thresholds can be adjusted in each component:

```python
# In perf/perf_benchmark.py
'warning_threshold_ms': 2000,
'critical_threshold_ms': 5000,

# In audit/monthly_audit.py
'slow_query_threshold_ms': 200,
'max_null_percentage': 5.0,
```

## Directory Structure

```
angles-ai-universe/
├── audit/
│   ├── monthly_audit.py          # Monthly deep audit system
│   └── verify_restore.py         # Restore verification system
├── perf/
│   └── perf_benchmark.py         # Performance benchmarking system
├── scripts/
│   └── run_audit_now.py          # Panic kit emergency audit runner
├── docs/
│   ├── README_AUDIT.md           # This documentation
│   └── perf/
│       └── summary.md            # Performance summary (auto-generated)
├── export/
│   ├── audit/                    # Audit reports (JSON/Markdown)
│   └── perf/                     # Performance reports
├── logs/
│   ├── audit/                    # Audit logs
│   └── perf/                     # Performance logs
└── tests/
    └── test_audit_components.py  # Unit tests for audit components
```

## Report Formats

### JSON Reports

All audit components generate structured JSON reports with the following common structure:

```json
{
  "timestamp": "2024-01-01T03:30:00Z",
  "audit_id": "unique_audit_identifier",
  "overall_status": "healthy|warning|critical|failed",
  "duration_seconds": 120.5,
  "critical_findings": [],
  "warning_findings": [],
  "component_results": {
    // Component-specific results
  }
}
```

### Markdown Reports

Human-readable Markdown reports include:
- Executive summary with key metrics
- Detailed findings by component
- Recommendations for issue resolution
- Historical trend information (where applicable)

### CSV Performance Data

Performance benchmarks generate CSV files with daily metrics:

```csv
timestamp,benchmark_id,supabase_read_ms,supabase_write_ms,notion_write_ms,git_push_ms,overall_status,duration_total_ms,warnings_count,errors_count
```

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**
   - Verify all required environment variables are set
   - Check Supabase URL and key validity
   - Ensure Notion token has proper permissions

2. **Performance Threshold Alerts**
   - Check network connectivity to external services
   - Review database query performance
   - Monitor system resource utilization

3. **Backup Verification Failures**
   - Verify GitHub repository access
   - Check backup repository structure
   - Ensure export files are present and valid

4. **Sync Drift Issues**
   - Manually trigger sync operations
   - Check Notion API rate limits
   - Verify database record integrity

### Log Locations

- **Audit Logs:** `logs/audit/`
- **Performance Logs:** `logs/perf/`
- **Main Scheduler:** `logs/active/ops_scheduler.log`
- **Health Dashboard:** `logs/health/`

### Emergency Procedures

1. **Run Panic Kit:** `python scripts/run_audit_now.py --run`
2. **Check System Health:** Access health dashboard at `http://localhost:5000`
3. **Review Recent Logs:** Check `logs/active/` for immediate issues
4. **Validate Backups:** Run restore verification manually

## Development

### Adding New Audit Checks

1. Create new validation function in appropriate audit component
2. Add configuration options for thresholds and parameters
3. Integrate with existing error handling and reporting
4. Update documentation and add unit tests

### Extending Performance Monitoring

1. Add new benchmark function to `perf/perf_benchmark.py`
2. Update CSV output format and rolling summary calculation
3. Set appropriate performance thresholds
4. Add component to panic kit sequence if critical

### Custom Alert Rules

1. Extend alert conditions in component logic
2. Use existing AlertManager integration
3. Define appropriate severity levels (warning/critical)
4. Include relevant context and suggested actions

## Security Considerations

- **Credential Management:** All sensitive credentials are loaded from environment variables
- **Data Sanitization:** Reports exclude sensitive data and credentials
- **Access Control:** Audit logs may contain sensitive operational information
- **Temporary Files:** Restore verification uses secure temporary directories with cleanup

## Maintenance

### Regular Tasks

- **Weekly:** Review performance trends and adjust thresholds
- **Monthly:** Analyze audit findings and address recurring issues
- **Quarterly:** Update documentation and validate emergency procedures

### Log Management

- Audit logs are automatically managed by the log management system
- CSV performance data accumulates over time - consider archival policies
- Export reports should be periodically cleaned up based on retention requirements

## Support

For issues with the audit system:
1. Check the troubleshooting section above
2. Review relevant log files for detailed error information
3. Use the panic kit to validate overall system health
4. Consult the main system health dashboard for additional context

---

*Generated by Angles AI Universe™ Development Team*  
*Last Updated: 2024-01-01*