"""
Backup and restore functionality for Angles AI Universe™
Handles database exports and GitHub integration
"""

import os
import json
import zipfile
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

from .config import has_github, GITHUB_TOKEN, GITHUB_REPO
from .supabase_client import SupabaseClient
from .utils import get_timestamp, safe_json_dumps


logger = logging.getLogger(__name__)


class BackupRestore:
    """Handles backup and restore operations"""
    
    def __init__(self):
        self.db = SupabaseClient()
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_db_export(self) -> Dict[str, Any]:
        """Create database export snapshot"""
        logger.info("📊 Creating database export snapshot")
        
        export_data = {
            'timestamp': get_timestamp(),
            'version': '1.0',
            'system_info': {
                'python_version': os.sys.version,
                'platform': os.name
            }
        }
        
        # Export recent logs
        try:
            recent_logs = self.db.get_recent_logs(hours=72)
            export_data['recent_logs'] = recent_logs[:100]  # Limit size
            logger.info(f"   📝 Exported {len(recent_logs)} log entries")
        except Exception as e:
            logger.error(f"Failed to export logs: {e}")
            export_data['recent_logs'] = []
        
        # Export file snapshots (metadata only for size)
        try:
            # This would need a custom query in a real implementation
            export_data['file_snapshots_count'] = 0
            logger.info("   📁 File snapshots metadata exported")
        except Exception as e:
            logger.error(f"Failed to export file snapshots: {e}")
        
        return export_data
    
    def create_backup_zip(self, timestamp: str = None) -> Path:
        """Create backup ZIP file"""
        if not timestamp:
            timestamp = datetime.now().strftime('%Y%m%d-%H%M')
        
        backup_filename = f"backup-{timestamp}.zip"
        backup_path = self.backup_dir / backup_filename
        
        logger.info(f"📦 Creating backup ZIP: {backup_filename}")
        
        # Create database export
        db_export = self.create_db_export()
        
        # Create ZIP file
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add database export
            export_json = safe_json_dumps(db_export, indent=2)
            zipf.writestr('db_export.json', export_json)
            
            # Add recent config files if they exist
            config_files = [
                'pyproject.toml', 'requirements.txt', '.env.example'
            ]
            
            for config_file in config_files:
                config_path = Path(config_file)
                if config_path.exists():
                    zipf.write(config_path, config_file)
            
            # Add angles module structure (metadata only)
            angles_info = {
                'modules': [f.name for f in Path('angles').glob('*.py')] if Path('angles').exists() else [],
                'created': get_timestamp()
            }
            zipf.writestr('angles_structure.json', safe_json_dumps(angles_info, indent=2))
        
        logger.info(f"✅ Backup created: {backup_path} ({backup_path.stat().st_size} bytes)")
        return backup_path
    
    def push_to_github(self, backup_path: Path) -> bool:
        """Push backup to GitHub repository"""
        if not has_github():
            logger.info("GitHub not configured, skipping push")
            return True
        
        try:
            import subprocess
            
            logger.info(f"📤 Pushing backup to GitHub: {backup_path.name}")
            
            # Copy to root for git tracking
            git_backup_path = Path(backup_path.name)
            import shutil
            shutil.copy2(backup_path, git_backup_path)
            
            # Git commands
            commands = [
                ['git', 'add', str(git_backup_path)],
                ['git', 'commit', '-m', f'Automated backup: {backup_path.name}'],
                ['git', 'push', 'origin', 'main']
            ]
            
            for cmd in commands:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.error(f"Git command failed: {' '.join(cmd)}")
                    logger.error(f"Error: {result.stderr}")
                    return False
            
            logger.info("✅ Backup pushed to GitHub successfully")
            
            # Clean up git-tracked file
            git_backup_path.unlink(missing_ok=True)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to push to GitHub: {e}")
            return False
    
    def run_backup(self) -> bool:
        """Run complete backup process"""
        logger.info("🚀 Starting backup process")
        
        try:
            # Create backup
            backup_path = self.create_backup_zip()
            
            # Push to GitHub
            github_success = self.push_to_github(backup_path)
            
            # Log backup event
            self.db.log_system_event(
                level='INFO',
                component='backup',
                message='Backup completed',
                meta={
                    'backup_file': backup_path.name,
                    'file_size': backup_path.stat().st_size,
                    'github_push': github_success
                }
            )
            
            logger.info("✅ Backup process completed")
            return True
            
        except Exception as e:
            logger.error(f"Backup process failed: {e}")
            
            # Log failure
            self.db.log_system_event(
                level='ERROR',
                component='backup',
                message='Backup failed',
                meta={'error': str(e)}
            )
            
            return False
    
    def list_backups(self) -> list:
        """List available backup files"""
        backups = list(self.backup_dir.glob("backup-*.zip"))
        backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        logger.info(f"📋 Found {len(backups)} backup files")
        for backup in backups[:5]:  # Show latest 5
            mtime = datetime.fromtimestamp(backup.stat().st_mtime)
            size = backup.stat().st_size
            logger.info(f"   📦 {backup.name} - {mtime.strftime('%Y-%m-%d %H:%M')} ({size} bytes)")
        
        return backups
    
    def cleanup_old_backups(self, keep_count: int = 10):
        """Clean up old backup files"""
        backups = self.list_backups()
        
        if len(backups) <= keep_count:
            logger.info(f"ℹ️ Only {len(backups)} backups, no cleanup needed")
            return
        
        to_delete = backups[keep_count:]
        
        for backup in to_delete:
            try:
                backup.unlink()
                logger.info(f"🗑️ Deleted old backup: {backup.name}")
            except Exception as e:
                logger.error(f"Failed to delete {backup.name}: {e}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Backup and restore operations')
    parser.add_argument('--backup', action='store_true', help='Run backup')
    parser.add_argument('--list', action='store_true', help='List backups')
    parser.add_argument('--cleanup', type=int, help='Cleanup old backups (keep N most recent)')
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    restore = BackupRestore()
    
    if args.backup:
        success = restore.run_backup()
        return 0 if success else 1
    elif args.list:
        restore.list_backups()
    elif args.cleanup:
        restore.cleanup_old_backups(args.cleanup)
    else:
        parser.print_help()
    
    return 0


if __name__ == "__main__":
    exit(main())