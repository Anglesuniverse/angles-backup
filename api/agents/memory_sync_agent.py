"""
Angles OS™ Memory Sync Agent
Monitors filesystem changes and syncs to vault and external services
"""
import os
import time
from pathlib import Path
from typing import Dict, Any, List
from api.services.token_vault import TokenVault
from api.services.supabase_connector import SupabaseConnector
from api.services.notion_connector import NotionConnector
from api.services.openai_client import OpenAIClient
from api.utils.logging import logger
from api.deps import get_db_cursor

class MemorySyncAgent:
    """Agent for syncing filesystem changes to persistent memory"""
    
    def __init__(self):
        self.name = "memory_sync_agent"
        self.vault = TokenVault()
        self.supabase = SupabaseConnector()
        self.notion = NotionConnector()
        self.openai = OpenAIClient()
        self.last_run = 0
        self.tracked_files = {}
        
        # File patterns to track
        self.track_patterns = ['.py', '.md', '.txt', '.json', '.yaml', '.yml', '.sql']
        self.ignore_patterns = ['__pycache__', '.git', 'node_modules', '.venv', 'logs/']
        
    def should_track_file(self, filepath: Path) -> bool:
        """Determine if file should be tracked"""
        # Check if file extension is tracked
        if not any(str(filepath).endswith(pattern) for pattern in self.track_patterns):
            return False
            
        # Check if path contains ignored patterns
        if any(ignore in str(filepath) for ignore in self.ignore_patterns):
            return False
            
        return True
    
    def get_file_changes(self) -> List[Dict[str, Any]]:
        """Scan for file changes since last run"""
        changes = []
        current_dir = Path('.')
        
        try:
            for root, dirs, files in os.walk(current_dir):
                # Skip ignored directories
                dirs[:] = [d for d in dirs if not any(ignore in d for ignore in self.ignore_patterns)]
                
                for file in files:
                    filepath = Path(root) / file
                    
                    if not self.should_track_file(filepath):
                        continue
                    
                    try:
                        stat = filepath.stat()
                        mtime = stat.st_mtime
                        
                        # Check if file is new or modified
                        if str(filepath) not in self.tracked_files or self.tracked_files[str(filepath)] < mtime:
                            changes.append({
                                'path': str(filepath),
                                'mtime': mtime,
                                'size': stat.st_size,
                                'type': 'modified' if str(filepath) in self.tracked_files else 'new'
                            })
                            self.tracked_files[str(filepath)] = mtime
                            
                    except (OSError, IOError) as e:
                        logger.warning(f"Failed to stat file {filepath}: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"File system scan failed: {e}")
            self.log_activity('ERROR', f'File system scan failed: {e}')
        
        return changes
    
    def process_file_change(self, change: Dict[str, Any]) -> bool:
        """Process a single file change"""
        filepath = Path(change['path'])
        
        try:
            # Read file content
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Skip very large files
            if len(content) > 50000:  # 50KB limit
                logger.info(f"Skipping large file: {filepath}")
                return False
            
            # Generate summary if content is substantial
            summary = None
            if len(content) > 200:
                summary = self.openai.summarize(content[:1000])  # Summarize first 1KB
            
            # Ingest into vault
            chunk_id = self.vault.ingest(
                source=f"replit_file:{filepath}",
                chunk=content,
                summary=summary,
                links=[f"file://{filepath}"]
            )
            
            # Sync to external services (best effort)
            if self.supabase.is_available():
                chunk_data = {
                    'id': chunk_id,
                    'source': f"replit_file:{filepath}",
                    'chunk': content,
                    'summary': summary,
                    'links': [f"file://{filepath}"],
                    'created_at': 'now()'
                }
                self.supabase.sync_vault_chunk(chunk_data)
            
            if self.notion.is_available():
                # Note: Would need database ID configuration
                logger.debug(f"Notion sync would go here for {filepath}")
            
            logger.info(f"Processed file change: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process file change {filepath}: {e}")
            self.log_activity('ERROR', f'Failed to process file change {filepath}: {e}')
            return False
    
    def log_activity(self, level: str, message: str, meta: Dict[str, Any] = None):
        """Log agent activity to database"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO agent_logs (agent, level, message, meta, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                """, (self.name, level, message, meta or {}))
                
            # Also log to Supabase if available
            if self.supabase.is_available():
                self.supabase.log_agent_activity(self.name, level, message, meta)
                
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")
    
    def run(self):
        """Execute memory sync cycle"""
        start_time = time.time()
        
        try:
            logger.info("Starting memory sync agent cycle")
            self.log_activity('INFO', 'Starting memory sync cycle')
            
            # Get file changes
            changes = self.get_file_changes()
            
            if not changes:
                logger.info("No file changes detected")
                self.log_activity('INFO', 'No file changes detected')
                return
            
            # Process changes
            processed = 0
            failed = 0
            
            for change in changes:
                if self.process_file_change(change):
                    processed += 1
                else:
                    failed += 1
            
            # Update last run time
            self.last_run = start_time
            
            duration = time.time() - start_time
            message = f"Sync complete: {processed} processed, {failed} failed in {duration:.2f}s"
            
            logger.info(message)
            self.log_activity('INFO', message, {
                'processed': processed,
                'failed': failed,
                'duration': duration,
                'changes': len(changes)
            })
            
        except Exception as e:
            logger.error(f"Memory sync agent failed: {e}")
            self.log_activity('ERROR', f'Memory sync agent failed: {e}')
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            'name': self.name,
            'last_run': self.last_run,
            'tracked_files_count': len(self.tracked_files),
            'vault_available': True,
            'supabase_available': self.supabase.is_available(),
            'notion_available': self.notion.is_available(),
            'openai_available': self.openai.is_available()
        }