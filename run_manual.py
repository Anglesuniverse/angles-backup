#!/usr/bin/env python3
"""
Angles AI Universe™ Manual Health Check & Backup Runner
For immediate execution of health checks and backups
"""

import sys
import argparse
import subprocess
from pathlib import Path

def run_health_check(test_mode=False):
    """Run health check"""
    print("🔍 Running health check...")
    
    cmd = [sys.executable, 'scripts/health_check.py']
    if test_mode:
        cmd.append('--test')
    
    result = subprocess.run(cmd)
    return result.returncode

def run_backup():
    """Run backup"""
    print("📦 Running backup...")
    result = subprocess.run([sys.executable, 'scripts/backup_to_github.py'])
    return result.returncode

def run_restore(dry_run=True, backup_file=None):
    """Run restore"""
    print("🔄 Running restore...")
    
    cmd = [sys.executable, 'scripts/restore_from_github.py']
    if dry_run:
        cmd.append('--dry-run')
    else:
        cmd.append('--live')
    
    if backup_file:
        cmd.extend(['--file', backup_file])
    
    result = subprocess.run(cmd)
    return result.returncode

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Manual Health Check & Backup Runner')
    parser.add_argument('--health', action='store_true', help='Run health check only')
    parser.add_argument('--backup', action='store_true', help='Run backup only')
    parser.add_argument('--restore', action='store_true', help='Run restore')
    parser.add_argument('--test', action='store_true', help='Run health check in test mode')
    parser.add_argument('--live-restore', action='store_true', help='Run live restore (not dry-run)')
    parser.add_argument('--backup-file', type=str, help='Specific backup file for restore')
    parser.add_argument('--all', action='store_true', help='Run health check and backup')
    
    args = parser.parse_args()
    
    if not any([args.health, args.backup, args.restore, args.all]):
        parser.print_help()
        return 1
    
    if args.all:
        print("🚀 Running complete health check and backup process...")
        health_code = run_health_check(test_mode=args.test)
        if health_code == 0:
            backup_code = run_backup()
            return backup_code
        else:
            print("❌ Health check failed - skipping backup")
            return health_code
    
    if args.health:
        return run_health_check(test_mode=args.test)
    
    if args.backup:
        return run_backup()
    
    if args.restore:
        return run_restore(dry_run=not args.live_restore, backup_file=args.backup_file)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
