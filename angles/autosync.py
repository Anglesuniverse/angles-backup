"""
Auto-sync file watcher for Angles AI Universe™
Monitors file changes and triggers incremental syncs
"""

import os
import time
import logging
from pathlib import Path
from typing import Dict, Set
from datetime import datetime, timedelta

from .memory_sync_agent import MemorySyncAgent


logger = logging.getLogger(__name__)


class AutoSync:
    """File watcher for automatic synchronization"""
    
    def __init__(self, watch_interval: int = 30, debounce_delay: int = 5):
        self.watch_interval = watch_interval
        self.debounce_delay = debounce_delay
        self.sync_agent = MemorySyncAgent()
        self.file_mtimes: Dict[str, float] = {}
        self.pending_changes: Set[str] = set()
        self.last_change_time = None
        
    def get_file_mtime(self, file_path: Path) -> float:
        """Get file modification time safely"""
        try:
            return file_path.stat().st_mtime
        except:
            return 0.0
    
    def scan_for_changes(self) -> Set[str]:
        """Scan for file changes since last check"""
        changes = set()
        
        # Get current file list
        files = self.sync_agent.scan_repository()
        
        for file_path in files:
            path_str = str(file_path)
            current_mtime = self.get_file_mtime(file_path)
            
            # Check if file is new or modified
            if path_str not in self.file_mtimes:
                # New file
                changes.add(path_str)
                logger.info(f"📄 New file detected: {file_path.name}")
            elif current_mtime > self.file_mtimes[path_str]:
                # Modified file
                changes.add(path_str)
                logger.info(f"✏️ Modified file detected: {file_path.name}")
            
            # Update mtime cache
            self.file_mtimes[path_str] = current_mtime
        
        # Check for deleted files
        existing_paths = {str(f) for f in files}
        deleted_paths = set(self.file_mtimes.keys()) - existing_paths
        
        for deleted_path in deleted_paths:
            logger.info(f"🗑️ Deleted file detected: {Path(deleted_path).name}")
            del self.file_mtimes[deleted_path]
        
        return changes
    
    def process_pending_changes(self):
        """Process accumulated changes after debounce period"""
        if not self.pending_changes:
            return
        
        logger.info(f"🔄 Processing {len(self.pending_changes)} pending changes")
        
        # Convert to Path objects and sync
        changed_files = [Path(p) for p in self.pending_changes]
        success_count = 0
        
        for file_path in changed_files:
            if file_path.exists() and self.sync_agent.sync_file(file_path):
                success_count += 1
        
        logger.info(f"✅ Synced {success_count}/{len(changed_files)} changed files")
        
        # Clear pending changes
        self.pending_changes.clear()
        self.last_change_time = None
    
    def run_continuous_watch(self):
        """Run continuous file watching"""
        logger.info("🔍 Starting continuous file watcher")
        logger.info(f"   📊 Watch interval: {self.watch_interval}s")
        logger.info(f"   ⏱️ Debounce delay: {self.debounce_delay}s")
        
        try:
            while True:
                # Scan for changes
                changes = self.scan_for_changes()
                
                if changes:
                    self.pending_changes.update(changes)
                    self.last_change_time = datetime.now()
                    logger.info(f"📝 {len(changes)} changes detected (total pending: {len(self.pending_changes)})")
                
                # Check if debounce period has passed
                if (self.last_change_time and 
                    datetime.now() - self.last_change_time >= timedelta(seconds=self.debounce_delay)):
                    self.process_pending_changes()
                
                # Wait before next scan
                time.sleep(self.watch_interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 File watcher stopped by user")
            
            # Process any remaining changes
            if self.pending_changes:
                self.process_pending_changes()
    
    def run_single_scan(self):
        """Run single file scan and sync"""
        logger.info("🔍 Running single file scan")
        changes = self.scan_for_changes()
        
        if changes:
            self.pending_changes.update(changes)
            self.process_pending_changes()
            logger.info(f"✅ Processed {len(changes)} changes")
        else:
            logger.info("ℹ️ No changes detected")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Auto-sync file watcher')
    parser.add_argument('--continuous', action='store_true', help='Run continuous watching')
    parser.add_argument('--interval', type=int, default=30, help='Watch interval in seconds')
    parser.add_argument('--debounce', type=int, default=5, help='Debounce delay in seconds')
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    autosync = AutoSync(
        watch_interval=args.interval,
        debounce_delay=args.debounce
    )
    
    if args.continuous:
        autosync.run_continuous_watch()
    else:
        autosync.run_single_scan()


if __name__ == "__main__":
    main()