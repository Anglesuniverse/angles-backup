#!/bin/bash
# Angles OS™ Local Development Runner

set -e

echo "🚀 Starting Angles OS™ Local Development Setup"
echo "=============================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for service
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $service_name on $host:$port..."
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z $host $port 2>/dev/null; then
            echo "✅ $service_name is ready!"
            return 0
        fi
        echo "   Attempt $attempt/$max_attempts - waiting..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service_name failed to start after $max_attempts attempts"
    return 1
}

# Check required commands
echo "🔍 Checking dependencies..."
if ! command_exists python3; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

if ! command_exists pip; then
    echo "❌ pip is required but not installed"
    exit 1
fi

echo "✅ Dependencies check passed"

# Install Python dependencies (if not already installed)
echo "📦 Installing Python dependencies..."
pip install -q fastapi uvicorn psycopg2-binary redis rq schedule loguru

# Setup environment (use existing secrets in Replit)
echo "🔧 Environment setup..."
if [ ! -f ".env" ] && [ -z "$POSTGRES_URL" ]; then
    echo "⚠️ Creating local .env file (Replit uses Secrets instead)"
    cat > .env << EOF
POSTGRES_URL=postgresql://postgres:postgres@localhost:5432/angles_os
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO
ENV=development
EOF
fi

# Run database migration
echo "🗄️ Running database migration..."
if [ -f "scripts/run_migration.py" ]; then
    python scripts/run_migration.py
    if [ $? -eq 0 ]; then
        echo "✅ Database migration completed"
    else
        echo "⚠️ Database migration failed (this is normal in Replit - using existing database)"
    fi
else
    echo "⚠️ Migration script not found"
fi

# Seed sample data (optional)
echo "🌱 Seeding sample data..."
if [ -f "scripts/seed_sample_data.py" ]; then
    python scripts/seed_sample_data.py
    if [ $? -eq 0 ]; then
        echo "✅ Sample data seeded"
    else
        echo "⚠️ Sample data seeding failed (may already exist)"
    fi
fi

# Start the API server in background
echo "🌐 Starting Angles OS™ API server..."
cd "$(dirname "$0")"
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &
SERVER_PID=$!

# Wait for server to start
if wait_for_service localhost 8000 "FastAPI Server"; then
    echo "✅ Angles OS™ API server started successfully"
else
    echo "❌ Failed to start API server"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

# Run tests
echo "🧪 Running test suite..."
if command_exists pytest; then
    python -m pytest tests/ -v
    TEST_RESULT=$?
    
    if [ $TEST_RESULT -eq 0 ]; then
        echo "✅ All tests passed"
    else
        echo "⚠️ Some tests failed (exit code: $TEST_RESULT)"
    fi
else
    echo "⚠️ pytest not available, running manual tests..."
    
    # Run manual tests
    python tests/test_health.py && \
    python tests/test_vault.py && \
    python tests/test_decisions.py
    
    if [ $? -eq 0 ]; then
        echo "✅ Manual tests passed"
        TEST_RESULT=0
    else
        echo "❌ Manual tests failed"
        TEST_RESULT=1
    fi
fi

# Run post-run review
echo "🔍 Running post-deployment review..."
python post_run_review.py
REVIEW_RESULT=$?

# Final status
echo ""
echo "=============================================="
echo "📋 ANGLES OS™ DEPLOYMENT SUMMARY"
echo "=============================================="

if [ $TEST_RESULT -eq 0 ] && [ $REVIEW_RESULT -eq 0 ]; then
    echo "🎉 SUCCESS: Angles OS™ is fully operational!"
    echo ""
    echo "🌐 API Documentation: http://localhost:8000/docs"
    echo "🏥 Health Check: http://localhost:8000/health"
    echo "📊 UI Summary: http://localhost:8000/ui/summary"
    echo "🔍 Agent Status: http://localhost:8000/agents/status"
    echo ""
    echo "🚀 Ready for production deployment!"
    
    # Keep server running
    echo "⏳ Server running... Press Ctrl+C to stop"
    wait $SERVER_PID
    
elif [ $REVIEW_RESULT -eq 0 ]; then
    echo "⚠️ PARTIAL: API running but tests failed"
    echo "📊 Check test results and fix issues"
    
    # Keep server running
    wait $SERVER_PID
    
else
    echo "❌ FAILED: Critical issues detected"
    echo "🔧 Run 'python post_run_review.py' for detailed diagnostics"
    
    # Stop server
    kill $SERVER_PID 2>/dev/null
    exit 1
fi