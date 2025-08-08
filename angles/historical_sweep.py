"""
Historical Sweep for Angles AI Universe™
Creates categorized entries and analyzes repository structure
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Any

from .config import print_config_status
from .supabase_client import SupabaseClient
from .notion_client_wrap import NotionClientWrap
from .openai_bridge import OpenAIBridge
from .utils import get_checksum, get_timestamp


logger = logging.getLogger(__name__)


class HistoricalSweep:
    """Full Historical Sweep™ - Repository analysis and categorization"""
    
    DECISION_CATEGORIES = [
        'core_prompts', 'exec_prompts', 'agent_specs', 
        'decisions', 'rules', 'todos'
    ]
    
    def __init__(self):
        self.db = SupabaseClient()
        self.notion = NotionClientWrap()
        self.openai = OpenAIBridge()
        self.stats = {
            'decisions_created': 0,
            'docs_processed': 0,
            'files_analyzed': 0
        }
    
    def create_placeholder_decisions(self):
        """Create placeholder decision entries for each category"""
        logger.info("📋 Creating placeholder decision entries")
        
        placeholder_decisions = [
            ('core_prompts', 'Core system prompts and instructions for AI agents'),
            ('exec_prompts', 'Execution prompts for specific operational tasks'),
            ('agent_specs', 'Agent specifications and behavioral definitions'),
            ('decisions', 'Architectural and operational decisions made'),
            ('rules', 'System rules and constraints'),
            ('todos', 'Pending tasks and action items')
        ]
        
        for category, content in placeholder_decisions:
            try:
                decision_id = self.db.insert_decision(
                    category=category,
                    content=f"Placeholder for {content}",
                    tags=[category, 'placeholder', 'system'],
                    source='historical_sweep'
                )
                
                if decision_id:
                    self.stats['decisions_created'] += 1
                    logger.info(f"✅ Created {category} placeholder")
                
            except Exception as e:
                logger.error(f"Failed to create {category} placeholder: {e}")
    
    def scan_documentation(self) -> List[Path]:
        """Scan for documentation files"""
        doc_patterns = ['*.md', '*.txt', '*.rst', '*.doc']
        doc_dirs = ['docs', 'documentation', 'README*', 'CHANGELOG*']
        
        docs = []
        
        # Scan root directory for common doc files
        for pattern in ['README*', 'CHANGELOG*', 'LICENSE*']:
            docs.extend(Path('.').glob(pattern))
        
        # Scan docs directories
        for doc_dir in ['docs', 'documentation']:
            doc_path = Path(doc_dir)
            if doc_path.exists() and doc_path.is_dir():
                for pattern in doc_patterns:
                    docs.extend(doc_path.rglob(pattern))
        
        logger.info(f"📄 Found {len(docs)} documentation files")
        return docs
    
    def process_documentation(self):
        """Process documentation files into decisions"""
        docs = self.scan_documentation()
        
        for doc_path in docs:
            try:
                with open(doc_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                if len(content.strip()) < 10:  # Skip empty/tiny files
                    continue
                
                # Determine category based on filename
                filename = doc_path.name.lower()
                if 'readme' in filename:
                    category = 'core_prompts'
                elif 'changelog' in filename or 'history' in filename:
                    category = 'decisions'
                elif 'todo' in filename or 'task' in filename:
                    category = 'todos'
                else:
                    category = 'rules'
                
                # Create decision entry
                decision_id = self.db.insert_decision(
                    category=category,
                    content=f"Documentation: {doc_path.name}\n\n{content[:1000]}...",
                    tags=[category, 'documentation', doc_path.suffix[1:] if doc_path.suffix else 'text'],
                    source='historical_sweep'
                )
                
                if decision_id:
                    self.stats['docs_processed'] += 1
                    logger.info(f"✅ Processed doc: {doc_path.name}")
                
            except Exception as e:
                logger.error(f"Failed to process {doc_path}: {e}")
    
    def analyze_repository_structure(self) -> str:
        """Analyze repository structure"""
        logger.info("🔍 Analyzing repository structure")
        
        structure_info = []
        
        # Get directory structure
        for root, dirs, files in os.walk('.'):
            # Skip common excluded directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
            
            level = root.replace('.', '').count(os.sep)
            indent = ' ' * 2 * level
            structure_info.append(f"{indent}{os.path.basename(root)}/")
            
            # Add files (limit to avoid huge output)
            subindent = ' ' * 2 * (level + 1)
            for file in files[:10]:  # Limit files per directory
                if not file.startswith('.'):
                    structure_info.append(f"{subindent}{file}")
            
            if len(files) > 10:
                structure_info.append(f"{subindent}... ({len(files) - 10} more files)")
        
        return '\n'.join(structure_info[:100])  # Limit total lines
    
    def generate_fix_list(self) -> str:
        """Generate prioritized fix list using AI analysis"""
        if not self.openai.is_available():
            return "OpenAI not available - manual review recommended"
        
        logger.info("🧠 Generating AI-powered fix list")
        
        # Get recent logs
        recent_logs = self.db.get_recent_logs(hours=24)
        
        # Get repository structure
        repo_structure = self.analyze_repository_structure()
        
        # Generate fix list
        fix_list = self.openai.generate_fix_list(recent_logs, repo_structure)
        
        return fix_list
    
    def run_historical_sweep(self) -> bool:
        """Run complete historical sweep"""
        logger.info("🚀 Starting Full Historical Sweep™")
        print_config_status()
        
        # Test database connection
        if not self.db.test_connection():
            logger.error("Database connection failed")
            return False
        
        try:
            # Create placeholder decisions
            self.create_placeholder_decisions()
            
            # Process documentation
            self.process_documentation()
            
            # Generate AI fix list
            fix_list = self.generate_fix_list()
            
            # Store fix list as run artifact
            self.db.store_run_artifact(
                kind='fix_list',
                ref='historical_sweep',
                notes='AI-generated prioritized fix list',
                blob=fix_list
            )
            
            # Write to Notion
            if self.notion.is_available():
                summary = f"""Historical Sweep completed:
- {self.stats['decisions_created']} decision placeholders created
- {self.stats['docs_processed']} documentation files processed
- AI fix list generated

Top priorities from AI analysis:
{fix_list[:500]}..."""
                
                self.notion.write_summary(
                    title=f"Historical Sweep - {get_timestamp()[:10]}",
                    text=summary,
                    tags=['historical_sweep', 'analysis', 'system']
                )
            
            # Log completion
            self.db.log_system_event(
                level='INFO',
                component='historical_sweep',
                message='Historical sweep completed',
                meta=self.stats
            )
            
            # Print results
            logger.info("📊 Historical Sweep Results:")
            logger.info(f"   📝 Decision entries: {self.stats['decisions_created']}")
            logger.info(f"   📄 Docs processed: {self.stats['docs_processed']}")
            logger.info("   🧠 AI fix list generated")
            
            return True
            
        except Exception as e:
            logger.error(f"Historical sweep failed: {e}")
            return False


def main():
    """Main entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    sweep = HistoricalSweep()
    success = sweep.run_historical_sweep()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())