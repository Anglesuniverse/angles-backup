#!/usr/bin/env python3
"""
Manual Backup Runner for Angles AI Universe™
On-demand backup system with tag support for memory and GitHub operations

This script provides:
- Manual backup execution with custom tags
- Full integration with Supabase storage and database logging
- GitHub repository backup with tagged commits  
- Notion integration for backup notifications
- CLI interface with optional tag parameter
- Comprehensive error handling and recovery

Author: Angles AI Universe™ Backend Team
Version: 2.0.0
"""

import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent))

from backup_utils import UnifiedBackupManager, BackupConfig
from sanity_check import SanityChecker

def main():
    """Main entry point for manual backup system"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Manual backup system for Angles AI Universe™",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_backup_manual.py                    # Standard manual backup
  python run_backup_manual.py --tag hotfix      # Backup with 'hotfix' tag
  python run_backup_manual.py --tag "v2.1.0"    # Backup with version tag
  python run_backup_manual.py --no-github       # Memory backup only
  python run_backup_manual.py --no-encryption   # Unencrypted backup
        """
    )
    
    parser.add_argument(
        '--tag',
        type=str,
        help='Optional tag to add to backup filename (e.g., "hotfix", "v2.1.0")'
    )
    
    parser.add_argument(
        '--no-github',
        action='store_true',
        help='Skip GitHub repository backup'
    )
    
    parser.add_argument(
        '--no-encryption',
        action='store_true', 
        help='Skip encryption (backup will be unencrypted)'
    )
    
    parser.add_argument(
        '--no-sanity-check',
        action='store_true',
        help='Skip pre-backup sanity check'
    )
    
    args = parser.parse_args()
    
    try:
        print()
        print("🔧 ANGLES AI UNIVERSE™ MANUAL BACKUP SYSTEM")
        print("=" * 55)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        
        if args.tag:
            print(f"Tag: {args.tag}")
        
        if args.no_github:
            print("GitHub backup: DISABLED")
        
        if args.no_encryption:
            print("Encryption: DISABLED")
        
        print()
        
        # Run pre-backup sanity check unless disabled
        if not args.no_sanity_check:
            print("🔍 Running pre-backup sanity check...")
            
            sanity_checker = SanityChecker()
            sanity_results = sanity_checker.run_all_checks()
            
            if not sanity_results['overall_passed']:
                print("❌ BACKUP ABORTED")
                print(f"   • Reason: Sanity check failed")
                print(f"   • Errors: {sanity_results['total_errors_found']} found")
                print(f"   • Warnings: {sanity_results['total_warnings_found']} found")
                print(f"   • Check logs/sanity_check.log for details")
                print("=" * 55)
                sys.exit(1)
            
            print("✅ Sanity check passed - proceeding with backup")
            print()
        
        # Create backup configuration
        config = BackupConfig(
            backup_type='manual',
            tag=args.tag,
            include_memory=True,
            include_github=not args.no_github,
            encryption_enabled=not args.no_encryption,
            retention_days=15  # Keep 15 manual backups
        )
        
        # Initialize backup manager
        backup_manager = UnifiedBackupManager(config)
        
        # Execute backup
        result = backup_manager.run_unified_backup()
        
        # Display results
        print()
        print("🏁 MANUAL BACKUP RESULTS:")
        print("=" * 30)
        
        if result.success:
            print("✅ Status: Manual backup completed successfully")
            print(f"📁 Filename: {result.filename}")
            
            if result.tag:
                print(f"🏷️ Tag: {result.tag}")
            
            print(f"📊 Files: {result.file_count} backed up")
            print(f"📏 Size: {result.file_size} bytes")
            
            if result.storage_url:
                print(f"📤 Supabase: {result.storage_url}")
            
            if result.github_commit_hash:
                print(f"💾 GitHub: {result.github_commit_hash}")
                
                if result.github_commit_url:
                    print(f"🔗 Commit: {result.github_commit_url}")
        else:
            print("❌ Status: Manual backup failed")
            print(f"🚫 Error: {result.error_message}")
        
        print(f"⏱️ Duration: {result.duration_seconds:.1f}s")
        print(f"📝 Logs: logs/backup_manual.log")
        print()
        
        # Exit with appropriate code
        sys.exit(0 if result.success else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 Manual backup interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"💥 Manual backup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()