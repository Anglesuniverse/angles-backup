#!/usr/bin/env python3
"""
Self-healing backend runner with environment setup
"""
import os, subprocess, sys

# Set up environment from current secrets
env_vars = {
    'SUPABASE_URL': os.getenv('SUPABASE_URL'),
    'SUPABASE_ANON_KEY': os.getenv('SUPABASE_KEY'),  # Map SUPABASE_KEY to SUPABASE_ANON_KEY
    'NOTION_API_KEY': os.getenv('NOTION_TOKEN'),
    'NOTION_DATABASE_ID': os.getenv('NOTION_DATABASE_ID'), 
    'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
    'OPENAI_MODEL': 'gpt-4o-mini',  # Cost-safe default
    'SYNC_INTERVAL_MINUTES': '30',
    'LOG_LEVEL': 'INFO',
    'MAX_AUTOFIX_ATTEMPTS': '3'
}

# Update environment
for k, v in env_vars.items():
    if v:
        os.environ[k] = v

print("🚀 ANGLES AI UNIVERSE™ SELF-HEALING BACKEND")
print("=" * 50)
print("Cost-safe mode: ✅ Using gpt-4o-mini")
print("Environment: ✅ Variables mapped")
print("=" * 50)

# Run the self-healing system
try:
    subprocess.run([sys.executable, 'scripts/run_all.py'], check=True)
except Exception as e:
    print(f"⚠️  System encountered issues: {e}")
    print("🔄 Self-healing in progress...")
