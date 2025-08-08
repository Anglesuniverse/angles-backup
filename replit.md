# GPT Assistant Output Processor

## Overview

This is a sophisticated data processing system designed to automatically handle GPT assistant outputs and manage them in both Supabase and Notion databases. The application intelligently processes various types of GPT-generated content, with a specialized focus on architect decisions management. The system features unified sync operations that store decisions in both Supabase (PostgreSQL) and Notion simultaneously, providing redundancy and cross-platform accessibility. The project's vision is to streamline the management of AI-generated architectural decisions, ensuring their persistent storage, accessibility, and collaborative refinement.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Processing Pipeline
The system employs a multi-stage pipeline for GPT output processing:
- **Parsing**: Handles JSON, structured, and unstructured content.
- **Classification**: Determines data routing based on content analysis.
- **Validation**: Ensures data integrity using Pydantic schemas.
- **Storage**: Manages database operations with retry logic.

### Database Layer Design
A three-tier database abstraction is implemented:
- **SupabaseClient**: Low-level CRUD operations.
- **DatabaseOperations**: High-level, domain-specific operations (conversations, memories, tasks).
- **Schema Validation**: Pydantic-based validation for data consistency.

### Memory Management System
An intelligent classification system routes data to appropriate tables (conversations, memories, tasks) based on weighted scoring, keyword matching, and structural patterns. It supports configurable retention policies.

### Error Handling and Resilience
The system includes comprehensive error handling with retry mechanisms (exponential backoff), graceful degradation, performance monitoring, and structured logging.

### Configuration Management
A centralized configuration system supports environment variables, configurable processing intervals, batch sizes, retry policies, flexible table schema definitions via JSON, and performance tuning parameters. Core configuration files are version-controlled with rollback capabilities and automatic Git commits.

### Operational Hardening & Automation
The system includes:
- A cron-like scheduler for all automation tasks (`ops_scheduler.py`).
- Automated daily memory backups to Supabase (encrypted ZIP, 30-day retention).
- A manual backup system with tag support and separate retention (15 days).
- Comprehensive GitHub backup for disaster recovery, including automated backups, sanitization, and conflict resolution.
- A 4-level fallback restore system with dry-run mode, timestamp comparison, schema validation, and duplicate detection.
- Automated weekly recovery testing with logging to GitHub, Supabase, and Notion.
- Pre-backup and pre-restore sanity checks.
- Operational metrics and reporting, alerts, database schema verification, safe Git operations, log management, and a hardened health dashboard with JSON snapshots.

### UI/UX Decisions
The system primarily focuses on backend processing and API integrations. Any user interaction is typically through CLI tools or direct database/Notion interfaces.

## External Dependencies

### Database Services
- **Supabase**: Primary PostgreSQL database, including `architect_decisions` and `memory_backups` tables.
- **Supabase Python Client**: For interacting with Supabase.
- **Notion API**: Secondary storage and collaboration platform for architect decisions.
- **Notion Client**: For interacting with Notion API.

### Data Processing Libraries
- **Pydantic**: Data validation and settings management.
- **Python-dotenv**: Environment variable management.

### Utility Libraries
- **asyncio**: Asynchronous I/O operations.
- **pathlib**: Modern file system path handling.
- **json**: Native JSON parsing and serialization.
- **re**: Regular expression processing.
- **logging**: Python's native logging module.