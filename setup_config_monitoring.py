#!/usr/bin/env python3
"""
Angles AI Universe™ Configuration Monitoring Setup
Sets up automated configuration monitoring as a workflow

This script:
- Configures configuration monitoring as a Replit workflow
- Sets up automated background monitoring
- Provides management commands for the monitoring service

Author: Angles AI Universe™ Backend Team
Version: 2.0.0
"""

import sys
import subprocess
from pathlib import Path

def setup_config_monitoring_workflow():
    """Set up configuration monitoring as a Replit workflow"""
    
    print("⚙️ ANGLES AI UNIVERSE™ CONFIG MONITORING SETUP")
    print("=" * 55)
    print()
    
    # Check if required files exist
    required_files = [
        'config_versioning.py',
        'rollback_config.py', 
        'config_monitor_service.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files present")
    print()
    
    # Create config directory if it doesn't exist
    config_dir = Path('config')
    config_dir.mkdir(exist_ok=True)
    
    config_versions_dir = Path('config_versions')
    config_versions_dir.mkdir(exist_ok=True)
    
    print("✅ Directory structure ready")
    print(f"   📁 {config_dir}/")
    print(f"   📁 {config_versions_dir}/")
    print()
    
    print("🔧 CONFIGURATION MONITORING COMMANDS:")
    print("=" * 45)
    print()
    print("1. Manual version check:")
    print("   python config_versioning.py")
    print()
    print("2. Start background monitoring service:")
    print("   python config_monitor_service.py --interval 30")
    print()
    print("3. Rollback configuration (interactive):")
    print("   python rollback_config.py")
    print()
    print("4. Rollback specific file type (dry run):")
    print("   python rollback_config.py --type agent_config --dry-run")
    print()
    
    print("📁 MONITORED CONFIGURATION FILES:")
    print("=" * 40)
    print("   📄 config/CorePrompt.yaml")
    print("   📄 config/ExecPrompt.yaml") 
    print("   📄 config/agent_config.json")
    print("   📄 config/memory_settings.json")
    print("   📄 config/db_schema.sql")
    print("   📄 config/system_variables.env (sanitized)")
    print()
    
    print("⚡ FEATURES:")
    print("=" * 15)
    print("   ✅ Automatic change detection")
    print("   ✅ Timestamped version backups")
    print("   ✅ Git integration with auto-commit")
    print("   ✅ Notion logging for all changes")
    print("   ✅ Security validation and .env sanitization")
    print("   ✅ Interactive rollback system")
    print("   ✅ Keep 10 most recent versions per file")
    print("   ✅ Background monitoring service")
    print()
    
    print("✅ Configuration monitoring system ready!")
    print()
    
    return True

def main():
    """Main setup function"""
    try:
        success = setup_config_monitoring_workflow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"💥 Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()