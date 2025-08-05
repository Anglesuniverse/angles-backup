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