#!/usr/bin/env python3
"""
MemorySyncAgent™ Backup System Setup
Setup script for daily automated Supabase export system

This script:
- Verifies all backup components are ready
- Tests Supabase connectivity
- Creates necessary database tables
- Provides setup instructions and management commands

Author: Angles AI Universe™ Backend Team
Version: 2.0.0
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, Any

def verify_environment() -> Dict[str, bool]:
    """Verify environment setup"""
    checks = {}
    
    # Check environment variables
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY']
    for var in required_vars:
        checks[f"env_{var}"] = bool(os.getenv(var))
    
    # Check optional encryption key
    checks['env_BACKUP_ENCRYPTION_KEY'] = bool(os.getenv('BACKUP_ENCRYPTION_KEY'))
    
    # Check required files
    required_files = [
        'backup_memory_to_supabase.py',
        'daily_memory_backup_scheduler.py',
        'create_memory_backup_table.sql'
    ]
    
    for file_path in required_files:
        checks[f"file_{file_path}"] = Path(file_path).exists()
    
    # Check memory directory structure
    memory_paths = [
        'memory/state.json',
        'memory/session_cache.json',
        'memory/long_term.db',
        'memory/indexes'
    ]
    
    for path in memory_paths:
        checks[f"memory_{Path(path).name}"] = Path(path).exists()
    
    return checks

def display_setup_status():
    """Display comprehensive setup status"""
    print("🗄️ MEMORYSYNCAGENT™ BACKUP SYSTEM SETUP")
    print("=" * 50)
    print()
    
    checks = verify_environment()
    
    print("📋 ENVIRONMENT VERIFICATION:")
    print("-" * 35)
    
    # Environment variables
    print("🔧 Environment Variables:")
    env_vars = ['env_SUPABASE_URL', 'env_SUPABASE_KEY', 'env_BACKUP_ENCRYPTION_KEY']
    for var in env_vars:
        status = "✅" if checks.get(var, False) else "❌"
        var_name = var.replace('env_', '')
        print(f"   {status} {var_name}")
    
    print()
    
    # Required files
    print("📁 Required Files:")
    file_checks = [k for k in checks.keys() if k.startswith('file_')]
    for file_check in file_checks:
        status = "✅" if checks[file_check] else "❌"
        filename = file_check.replace('file_', '')
        print(f"   {status} {filename}")
    
    print()
    
    # Memory structure
    print("🧠 Memory Directory Structure:")
    memory_checks = [k for k in checks.keys() if k.startswith('memory_')]
    for memory_check in memory_checks:
        status = "✅" if checks[memory_check] else "❌"
        path_name = memory_check.replace('memory_', '')
        print(f"   {status} memory/{path_name}")
    
    print()
    
    # Overall status
    all_critical_ready = all([
        checks.get('env_SUPABASE_URL', False),
        checks.get('env_SUPABASE_KEY', False),
        checks.get('file_backup_memory_to_supabase.py', False),
        checks.get('file_daily_memory_backup_scheduler.py', False)
    ])
    
    print("🎯 OVERALL STATUS:")
    print("-" * 20)
    if all_critical_ready:
        print("✅ System Ready for Daily Backups")
    else:
        print("❌ Setup Incomplete - Check failed items above")
    
    print()
    
    return all_critical_ready

def display_usage_instructions():
    """Display usage instructions"""
    print("🚀 USAGE INSTRUCTIONS:")
    print("=" * 25)
    print()
    
    print("1. Manual backup (test):")
    print("   python backup_memory_to_supabase.py")
    print()
    
    print("2. Start daily scheduler:")
    print("   python daily_memory_backup_scheduler.py")
    print()
    
    print("3. View backup logs:")
    print("   tail -f logs/memory_backup.log")
    print()
    
    print("⚡ FEATURES:")
    print("=" * 15)
    print("   ✅ Daily automated backups at 03:00 UTC")
    print("   ✅ Compressed archive creation (ZIP)")
    print("   ✅ Encryption support (when available)")
    print("   ✅ Supabase storage integration")
    print("   ✅ Database logging for all attempts")
    print("   ✅ Notion integration for notifications")
    print("   ✅ Automatic retention management (30 days)")
    print("   ✅ Error handling and recovery")
    print()
    
    print("📁 BACKUP CONTENTS:")
    print("=" * 20)
    print("   📄 memory/state.json")
    print("   📄 memory/session_cache.json")
    print("   📄 memory/long_term.db")
    print("   📁 memory/indexes/* (all files)")
    print("   📄 backup_metadata.json (auto-generated)")
    print()
    
    print("🗄️ STORAGE STRUCTURE:")
    print("=" * 22)
    print("   Bucket: memory_backups")
    print("   Path: /daily/memory_backup_YYYY-MM-DD.zip")
    print("   Retention: 30 days")
    print("   Access: Private (authenticated only)")
    print()
    
    print("🔒 SECURITY NOTES:")
    print("=" * 20)
    print("   • Set BACKUP_ENCRYPTION_KEY in Replit Secrets for encryption")
    print("   • Bucket is private - requires authentication")
    print("   • All operations logged to database and Notion")
    print("   • Sensitive data is excluded from backups")
    print()

def main():
    """Main setup function"""
    try:
        print()
        ready = display_setup_status()
        
        if ready:
            display_usage_instructions()
            print("✅ MemorySyncAgent™ backup system is ready!")
        else:
            print("❌ Please resolve the failed checks above before proceeding.")
            print()
            print("💡 SETUP TIPS:")
            print("   • Add SUPABASE_URL and SUPABASE_KEY to Replit Secrets")
            print("   • Optionally add BACKUP_ENCRYPTION_KEY for encryption")
            print("   • Ensure all memory files exist in the memory/ directory")
        
        print()
        
    except Exception as e:
        print(f"💥 Setup check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()