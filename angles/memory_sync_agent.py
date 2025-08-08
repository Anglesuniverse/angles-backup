"""
Memory Sync Agent for Angles AI Universe™
Scans repository and syncs files to Supabase with Notion integration
"""

import os
import logging
from pathlib import Path
from typing import Set, List, Dict, Any

from .config import print_config_status
from .supabase_client import SupabaseClient
from .notion_client_wrap import NotionClientWrap
from .utils import get_checksum, get_timestamp, truncate_text


logger = logging.getLogger(__name__)


class MemorySyncAgent:
    """Agent for syncing repository files to database"""
    
    EXCLUDED_PATHS = {
        '.git', '__pycache__', 'venv', 'env', 'node_modules',
        'logs', 'backups', '.pytest_cache', '.vscode', '.idea',
        'test_results'
    }
    
    EXCLUDED_EXTENSIONS = {
        '.pyc', '.pyo', '.pyd', '.so', '.dll', '.dylib',
        '.log', '.tmp', '.cache', '.DS_Store'
    }
    
    def __init__(self):
        self.db = SupabaseClient()
        self.notion = NotionClientWrap()
        self.stats = {
            'scanned': 0,
            'new': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
    
    def should_exclude_path(self, path: Path) -> bool:
        """Check if path should be excluded from sync"""
        # Check if any parent directory is excluded
        for part in path.parts:
            if part in self.EXCLUDED_PATHS:
                return True
        
        # Check file extension
        if path.suffix in self.EXCLUDED_EXTENSIONS:
            return True
        
        # Exclude very large files (>1MB)
        try:
            if path.is_file() and path.stat().st_size > 1024 * 1024:
                return True
        except:
            pass
        
        return False
    
    def scan_repository(self, root_path: str = ".") -> List[Path]:
        """Scan repository for files to sync"""
        logger.info(f"Scanning repository from: {root_path}")
        files_to_sync = []
        
        root = Path(root_path).resolve()
        
        try:
            for item in root.rglob("*"):
                if item.is_file() and not self.should_exclude_path(item):
                    files_to_sync.append(item)
                    
        except Exception as e:
            logger.error(f"Error scanning repository: {e}")
        
        logger.info(f"Found {len(files_to_sync)} files to process")
        return files_to_sync
    
    def sync_file(self, file_path: Path) -> bool:
        """Sync individual file to database"""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Generate checksum
            checksum = get_checksum(content)
            relative_path = str(file_path.relative_to(Path.cwd()))
            
            # Upsert to database
            success = self.db.upsert_file_snapshot(
                path=relative_path,
                content=content,
                checksum=checksum
            )
            
            if success:
                # Log change event
                self.db.log_system_event(
                    level='INFO',
                    component='memory_sync',
                    message=f'File synced: {relative_path}',
                    meta={
                        'path': relative_path,
                        'checksum': checksum,
                        'size': len(content)
                    }
                )
                return True
            else:
                self.stats['errors'] += 1
                return False
                
        except Exception as e:
            logger.error(f"Error syncing file {file_path}: {e}")
            self.stats['errors'] += 1
            return False
    
    def run_sync(self) -> bool:
        """Run complete memory sync process"""
        logger.info("🚀 Starting Memory Sync Agent")
        print_config_status()
        
        # Test database connection
        if not self.db.test_connection():
            logger.error("Database connection failed")
            return False
        
        # Scan and sync files
        files = self.scan_repository()
        self.stats['scanned'] = len(files)
        
        for i, file_path in enumerate(files, 1):
            logger.info(f"Processing {i}/{len(files)}: {truncate_text(str(file_path), 60)}")
            
            if self.sync_file(file_path):
                self.stats['new'] += 1  # Simplified for now
            
            # Progress update every 10 files
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{len(files)} files processed")
        
        # Write summary to Notion
        if self.notion.is_available():
            summary = f"Memory sync completed: {self.stats['scanned']} files scanned, {self.stats['new']} synced"
            self.notion.write_summary(
                title=f"Memory Sync - {get_timestamp()[:10]}",
                text=summary,
                tags=['memory_sync', 'system']
            )
        
        # Log completion
        self.db.log_system_event(
            level='INFO',
            component='memory_sync',
            message='Memory sync completed',
            meta=self.stats
        )
        
        # Print results
        logger.info("📊 Memory Sync Results:")
        logger.info(f"   📝 Files scanned: {self.stats['scanned']}")
        logger.info(f"   ✅ Files synced: {self.stats['new']}")
        logger.info(f"   ❌ Errors: {self.stats['errors']}")
        
        return self.stats['errors'] == 0


def main():
    """Main entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    agent = MemorySyncAgent()
    success = agent.run_sync()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())