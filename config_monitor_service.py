#!/usr/bin/env python3
"""
Angles AI Universe™ Configuration Monitoring Service
Background service that monitors configuration files for changes

This service provides:
- Continuous monitoring of core configuration files
- Automatic version control and backup on changes
- Git integration for change tracking
- Notion logging for configuration changes
- Lightweight file watcher implementation

Author: Angles AI Universe™ Backend Team
Version: 2.0.0
"""

import os
import sys
import time
import signal
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Set
from dataclasses import dataclass

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent))

from config_versioning import AnglesConfigVersioner

@dataclass
class MonitorStats:
    """Statistics for the monitoring service"""
    service_started: str
    total_checks: int = 0
    changes_detected: int = 0
    files_versioned: int = 0
    errors_encountered: int = 0
    last_check: str = ""
    
class ConfigMonitorService:
    """Background service for monitoring configuration changes"""
    
    def __init__(self, check_interval_seconds: int = 30):
        """Initialize the monitoring service"""
        self.logger = self._setup_logging()
        self.versioner = AnglesConfigVersioner()
        self.check_interval = check_interval_seconds
        self.running = False
        
        # Statistics tracking
        self.stats = MonitorStats(
            service_started=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("🔍 ANGLES AI UNIVERSE™ CONFIG MONITOR SERVICE INITIALIZED")
        self.logger.info("=" * 60)
        self.logger.info(f"Check interval: {check_interval_seconds} seconds")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup service-specific logging"""
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        logger = logging.getLogger('config_monitor_service')
        logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # File handler
        file_handler = logging.FileHandler('logs/config_monitor_service.log')
        file_handler.setLevel(logging.INFO)
        
        # Console handler (for when running interactively)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
    
    def _check_for_changes(self) -> Dict[str, Any]:
        """Check for configuration changes and process them"""
        try:
            self.stats.total_checks += 1
            self.stats.last_check = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Run configuration monitoring
            result = self.versioner.run_config_monitoring()
            
            if result['success'] and result['changes_detected']:
                self.stats.changes_detected += 1
                self.stats.files_versioned += result['files_processed']
                
                self.logger.info(f"✅ Processed {result['files_processed']} configuration changes")
                self.logger.info(f"💾 Git commit: {result.get('git_commit', 'unknown')}")
            
            return result
            
        except Exception as e:
            self.stats.errors_encountered += 1
            self.logger.error(f"Error during change check: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _log_service_stats(self):
        """Log service statistics periodically"""
        self.logger.info("📊 SERVICE STATISTICS:")
        self.logger.info(f"   Started: {self.stats.service_started}")
        self.logger.info(f"   Total checks: {self.stats.total_checks}")
        self.logger.info(f"   Changes detected: {self.stats.changes_detected}")
        self.logger.info(f"   Files versioned: {self.stats.files_versioned}")
        self.logger.info(f"   Errors: {self.stats.errors_encountered}")
        self.logger.info(f"   Last check: {self.stats.last_check}")
    
    def start(self):
        """Start the monitoring service"""
        self.running = True
        self.logger.info("🚀 Starting configuration monitoring service...")
        
        checks_since_stats = 0
        stats_interval = 20  # Log stats every 20 checks
        
        try:
            while self.running:
                # Check for changes
                result = self._check_for_changes()
                
                # Log stats periodically
                checks_since_stats += 1
                if checks_since_stats >= stats_interval:
                    self._log_service_stats()
                    checks_since_stats = 0
                
                # Wait for next check
                if self.running:
                    time.sleep(self.check_interval)
                    
        except KeyboardInterrupt:
            self.logger.info("Service interrupted by user")
        except Exception as e:
            self.logger.error(f"Service error: {e}")
        finally:
            self._shutdown()
    
    def stop(self):
        """Stop the monitoring service"""
        self.running = False
    
    def _shutdown(self):
        """Perform cleanup on shutdown"""
        self.logger.info("🛑 Configuration monitoring service shutting down...")
        self._log_service_stats()
        self.logger.info("✅ Service shutdown complete")

def main():
    """Main entry point for the configuration monitoring service"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Angles AI Universe™ Configuration Monitoring Service")
    parser.add_argument('--interval', type=int, default=30, 
                       help='Check interval in seconds (default: 30)')
    parser.add_argument('--daemon', action='store_true',
                       help='Run as daemon (suppress console output)')
    
    args = parser.parse_args()
    
    try:
        print()
        print("🔍 ANGLES AI UNIVERSE™ CONFIGURATION MONITORING SERVICE")
        print("=" * 65)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"Check interval: {args.interval} seconds")
        print(f"Monitoring files: CorePrompt.yaml, ExecPrompt.yaml, agent_config.json,")
        print(f"                  memory_settings.json, db_schema.sql, system_variables.env")
        print()
        print("Press Ctrl+C to stop the service")
        print("=" * 65)
        print()
        
        # Create and start service
        service = ConfigMonitorService(args.interval)
        service.start()
        
    except KeyboardInterrupt:
        print("\n🛑 Service interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"💥 Service failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()