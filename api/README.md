# Angles AI Universe™ FastAPI System

## Overview
A modern REST API built with FastAPI that runs alongside the existing Python backend, providing:
- **Knowledge Vault**: Document ingestion and semantic search
- **Decision Management**: AI-powered decision tracking and recommendations
- **Real-time API**: Fast, modern endpoints with automatic OpenAPI documentation

## Architecture
- **Database**: Uses existing Supabase PostgreSQL (shared with main backend)
- **Framework**: FastAPI with Uvicorn ASGI server
- **Integration**: Runs on port 8000 alongside existing systems
- **Tables**: `vault`, `fastapi_decisions`, `api_logs`

## API Endpoints

### Health Check
- `GET /health` - System status

### Knowledge Vault
- `POST /vault/ingest` - Add document chunks
- `POST /vault/query` - Search knowledge base

### Decision System  
- `POST /decisions` - Create decision with options
- `GET /decisions` - List decisions by status
- `GET /decisions/{id}` - Get decision details
- `POST /decisions/{id}/recommend` - Get AI recommendation
- `POST /decisions/{id}/approve` - Approve decision
- `POST /decisions/{id}/decline` - Decline decision

## Usage Examples

### Document Ingestion
```bash
curl -X POST http://localhost:8000/vault/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source": "API Documentation",
    "chunk": "FastAPI provides automatic API documentation",
    "summary": "FastAPI generates interactive docs",
    "links": ["https://fastapi.tiangolo.com"]
  }'
```

### Decision Creation
```bash
curl -X POST http://localhost:8000/decisions \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Choose authentication method",
    "options": [
      {
        "option": "JWT tokens",
        "pros": ["Stateless", "Scalable"],
        "cons": ["Token management"]
      },
      {
        "option": "Session-based",
        "pros": ["Simple", "Secure"],
        "cons": ["Server state"]
      }
    ]
  }'
```

## Integration with Existing System
- Shares database with main Angles AI Universe backend
- Preserves all existing automation and monitoring
- Adds modern API capabilities without disrupting workflows
- Health monitoring available on main dashboard (port 5000)

## Testing
Run comprehensive test suite:
```bash
python test_fastapi.py
```

## Status
✅ Production ready
✅ All tests passing
✅ Integrated with existing systems
✅ Auto-documentation at http://localhost:8000/docs