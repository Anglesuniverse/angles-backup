#!/usr/bin/env python3
"""
Orchestrator for Angles AI Universe™ Memory System
Runs memory sync agent followed by GitHub backup

This script coordinates:
1. Memory Sync Agent - Supabase ↔ Notion sync
2. Git Backup Agent - GitHub backup of exports and logs

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

# Configure logging for the orchestrator
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('run_all')

def run_memory_sync() -> bool:
    """Run the memory sync agent"""
    try:
        logger.info("Starting memory sync agent")
        
        # Import and run memory sync agent
        from memory_sync_agent import main as memory_sync_main
        
        success = memory_sync_main()
        
        if success:
            logger.info("Memory sync agent completed successfully")
            return True
        else:
            logger.error("Memory sync agent failed")
            return False
            
    except Exception as e:
        logger.error(f"Error running memory sync agent: {e}")
        return False

def run_git_backup() -> bool:
    """Run the git backup agent"""
    try:
        logger.info("Starting git backup agent")
        
        # Import and run git backup agent
        from backup.git_backup import main as git_backup_main
        
        git_backup_main()
        logger.info("Git backup agent completed successfully")
        return True
        
    except SystemExit as e:
        # Git backup agent uses sys.exit()
        if e.code == 0:
            logger.info("Git backup agent completed successfully")
            return True
        else:
            logger.error(f"Git backup agent failed with exit code: {e.code}")
            return False
            
    except Exception as e:
        logger.error(f"Error running git backup agent: {e}")
        return False

def print_status(memory_success: bool, backup_success: bool, sync_stats: Optional[dict] = None):
    """Print concise status summary"""
    
    # Print header
    print()
    print("=" * 60)
    print("ANGLES AI UNIVERSE™ MEMORY SYSTEM - RUN SUMMARY")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Memory sync status
    if memory_success:
        synced_count = sync_stats.get('successfully_synced', 0) if sync_stats else 0
        export_file = sync_stats.get('export_file', 'N/A') if sync_stats else 'N/A'
        print(f"✓ Memory Sync: OK - synced {synced_count} items")
        if export_file and export_file != 'N/A':
            print(f"  Export file: {export_file}")
    else:
        print("✗ Memory Sync: FAILED")
    
    # Backup status
    if backup_success:
        print("✓ GitHub Backup: OK - pushed to GitHub")
    else:
        print("✗ GitHub Backup: FAILED")
    
    # Overall status
    overall_success = memory_success and backup_success
    print()
    if overall_success:
        print("🎉 ALL SYSTEMS: SUCCESS")
    else:
        print("⚠️  PARTIAL SUCCESS" if memory_success or backup_success else "❌ ALL SYSTEMS: FAILED")
    
    print("=" * 60)
    print()

def main():
    """Main orchestrator function"""
    start_time = datetime.now()
    logger.info("Starting Angles AI Universe™ memory system run")
    
    # Initialize status tracking
    memory_success = False
    backup_success = False
    sync_stats = {}
    
    try:
        # Step 1: Run memory sync agent
        print("Running memory sync agent...")
        memory_success = run_memory_sync()
        
        if memory_success:
            # Try to get sync statistics for reporting
            try:
                from memory_sync_agent import MemorySyncAgent
                # We don't re-run the sync, just get basic info
                print("✓ Memory sync completed successfully")
            except Exception:
                pass
        
        # Step 2: Run git backup agent (regardless of memory sync result)
        print("Running git backup agent...")
        backup_success = run_git_backup()
        
        # Step 3: Print status summary
        print_status(memory_success, backup_success, sync_stats)
        
        # Determine overall success
        overall_success = memory_success and backup_success
        
        # Log final result
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"Run completed in {duration:.2f} seconds")
        if overall_success:
            logger.info("All systems completed successfully")
        else:
            logger.warning(f"Partial success: memory_sync={memory_success}, backup={backup_success}")
        
        # Exit with appropriate code
        sys.exit(0 if overall_success else 1)
        
    except KeyboardInterrupt:
        logger.info("Run interrupted by user")
        print("\nRun interrupted by user")
        sys.exit(130)  # Standard exit code for SIGINT
        
    except Exception as e:
        logger.error(f"Orchestrator failed: {e}")
        print(f"FATAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()