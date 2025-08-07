#!/usr/bin/env python3
"""
Angles AI Universe™ Backend Logging System
Integrates decision_vault, memory_log, and agent_activity tables with local queuing

Features:
- Automatic timestamps on all inserts
- Local queuing when Supabase is unreachable
- Automatic retry and reconnection logic
- Thread-safe operations for concurrent use

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import json
import os
import queue
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
import uuid

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Warning: supabase package not available - running in offline mode")


class AnglesLogger:
    """Main logging system for Angles AI Universe™ backend"""
    
    def __init__(self):
        """Initialize the logging system"""
        self.supabase: Optional[Client] = None
        self.queue_path = Path("logs/pending_logs.json")
        self.log_queue = queue.Queue()
        self.is_connected = False
        self.last_connection_attempt = 0
        self.connection_retry_interval = 30  # seconds
        
        # Ensure logs directory exists
        self.queue_path.parent.mkdir(exist_ok=True)
        
        # Initialize Supabase connection
        self._initialize_supabase()
        
        # Load any pending logs from previous session
        self._load_pending_logs()
        
        # Start background worker thread
        self.worker_thread = threading.Thread(target=self._background_worker, daemon=True)
        self.worker_thread.start()
        
        print("✅ Angles AI Universe™ logging system initialized")
    
    def _initialize_supabase(self):
        """Initialize Supabase connection with environment variables"""
        
        if not SUPABASE_AVAILABLE:
            print("⚠️ Supabase not available - operating in offline mode")
            return
        
        try:
            # Get credentials from environment
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                print("⚠️ Supabase credentials not found - operating in offline mode")
                print("   Required: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
                return
            
            # Create Supabase client
            self.supabase = create_client(supabase_url, supabase_key)
            
            # Test connection
            if self._test_connection():
                self.is_connected = True
                print("✅ Supabase connection established")
            else:
                print("⚠️ Supabase connection failed - will retry in background")
                
        except Exception as e:
            print(f"⚠️ Failed to initialize Supabase: {e}")
            self.supabase = None
    
    def _test_connection(self) -> bool:
        """Test Supabase connection"""
        
        if not self.supabase:
            return False
        
        try:
            # Simple test query
            result = self.supabase.table('decision_vault').select("id").limit(1).execute()
            return True
        except Exception:
            return False
    
    def _load_pending_logs(self):
        """Load pending logs from previous session"""
        
        if not self.queue_path.exists():
            return
        
        try:
            with open(self.queue_path, 'r') as f:
                pending_logs = json.load(f)
            
            for log_entry in pending_logs:
                self.log_queue.put(log_entry)
            
            # Clear the file after loading
            self.queue_path.unlink()
            
            if pending_logs:
                print(f"📥 Loaded {len(pending_logs)} pending logs from previous session")
                
        except Exception as e:
            print(f"⚠️ Failed to load pending logs: {e}")
    
    def _save_pending_logs(self):
        """Save current queue to disk"""
        
        if self.log_queue.empty():
            return
        
        try:
            pending_logs = []
            temp_queue = queue.Queue()
            
            # Extract all items from queue
            while not self.log_queue.empty():
                try:
                    item = self.log_queue.get_nowait()
                    pending_logs.append(item)
                    temp_queue.put(item)
                except queue.Empty:
                    break
            
            # Put items back in queue
            while not temp_queue.empty():
                self.log_queue.put(temp_queue.get_nowait())
            
            # Save to file
            if pending_logs:
                with open(self.queue_path, 'w') as f:
                    json.dump(pending_logs, f, indent=2, default=str)
                
                print(f"💾 Saved {len(pending_logs)} pending logs to disk")
                
        except Exception as e:
            print(f"⚠️ Failed to save pending logs: {e}")
    
    def _background_worker(self):
        """Background worker to process queued logs"""
        
        while True:
            try:
                # Check connection periodically
                current_time = time.time()
                if (not self.is_connected and 
                    current_time - self.last_connection_attempt > self.connection_retry_interval):
                    
                    self.last_connection_attempt = current_time
                    if self._test_connection():
                        self.is_connected = True
                        print("✅ Supabase connection restored")
                
                # Process queue if connected
                if self.is_connected:
                    self._process_queue()
                
                # Sleep before next iteration
                time.sleep(5)
                
            except Exception as e:
                print(f"⚠️ Background worker error: {e}")
                time.sleep(10)
    
    def _process_queue(self):
        """Process queued log entries"""
        
        if not self.is_connected or self.log_queue.empty():
            return
        
        processed_count = 0
        max_batch_size = 10
        
        while not self.log_queue.empty() and processed_count < max_batch_size:
            try:
                log_entry = self.log_queue.get_nowait()
                
                if self._insert_to_supabase(log_entry):
                    processed_count += 1
                    self.log_queue.task_done()
                else:
                    # Put back in queue if insert failed
                    self.log_queue.put(log_entry)
                    self.is_connected = False  # Mark as disconnected
                    break
                    
            except queue.Empty:
                break
            except Exception as e:
                print(f"⚠️ Error processing queue item: {e}")
                self.is_connected = False
                break
        
        if processed_count > 0:
            print(f"📤 Processed {processed_count} queued logs")
    
    def _insert_to_supabase(self, log_entry: Dict[str, Any]) -> bool:
        """Insert log entry to appropriate Supabase table"""
        
        if not self.supabase:
            return False
        
        try:
            table_name = log_entry.get('table')
            data = log_entry.get('data', {})
            
            if not table_name or not data:
                print(f"⚠️ Invalid log entry: {log_entry}")
                return True  # Consider it processed to avoid infinite retry
            
            # Insert to Supabase
            result = self.supabase.table(table_name).insert(data).execute()
            
            if result.data:
                return True
            else:
                print(f"⚠️ Failed to insert to {table_name}: No data returned")
                return False
                
        except Exception as e:
            print(f"⚠️ Supabase insert error: {e}")
            return False
    
    def _queue_log(self, table: str, data: Dict[str, Any]):
        """Queue a log entry for later processing"""
        
        log_entry = {
            'table': table,
            'data': data,
            'queued_at': datetime.now(timezone.utc).isoformat()
        }
        
        if self.is_connected:
            # Try immediate insert
            if self._insert_to_supabase(log_entry):
                return
            else:
                self.is_connected = False
        
        # Queue for later
        self.log_queue.put(log_entry)
        
        # Periodically save queue to disk
        if self.log_queue.qsize() % 10 == 0:
            self._save_pending_logs()
    
    def log_decision(self, decision_text: str, decision_type: str, decision_date: Optional[str] = None):
        """
        Log a system decision to decision_vault table
        
        Args:
            decision_text: The decision description
            decision_type: Type of decision (Policy, Architecture, Ops, UX, Other)
            decision_date: Date of decision (defaults to today)
        """
        
        if not decision_text or not decision_type:
            print("⚠️ Decision text and type are required")
            return
        
        # Validate decision type
        valid_types = ['Policy', 'Architecture', 'Ops', 'UX', 'Other']
        if decision_type not in valid_types:
            print(f"⚠️ Invalid decision type: {decision_type}. Must be one of: {valid_types}")
            return
        
        # Use provided date or default to today
        if not decision_date:
            decision_date = datetime.now(timezone.utc).date().isoformat()
        
        data = {
            'id': str(uuid.uuid4()),
            'decision': decision_text,
            'type': decision_type,
            'date': decision_date,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'notion_synced': False
        }
        
        self._queue_log('decision_vault', data)
        print(f"📋 Decision logged: {decision_type} - {decision_text[:50]}...")
    
    def log_memory_event(self, event_type: str, description: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Log a significant event to memory_log table
        
        Args:
            event_type: Type of event (error, sync, system_change, backup, etc.)
            description: Detailed description of the event
            metadata: Optional additional data as JSON
        """
        
        if not event_type or not description:
            print("⚠️ Event type and description are required")
            return
        
        data = {
            'id': str(uuid.uuid4()),
            'event_type': event_type,
            'event_description': description,
            'metadata': json.dumps(metadata) if metadata else None,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        self._queue_log('memory_log', data)
        print(f"📝 Event logged: {event_type} - {description[:50]}...")
    
    def log_agent_activity(self, agent_name: str, description: str, status: str = 'completed', metadata: Optional[Dict[str, Any]] = None):
        """
        Log agent activity to agent_activity table
        
        Args:
            agent_name: Name of the agent (sync_agent, backup_agent, etc.)
            description: Description of the activity
            status: Status (started, completed, failed, in_progress)
            metadata: Optional additional data as JSON
        """
        
        if not agent_name or not description:
            print("⚠️ Agent name and description are required")
            return
        
        # Validate status
        valid_statuses = ['started', 'completed', 'failed', 'in_progress']
        if status not in valid_statuses:
            print(f"⚠️ Invalid status: {status}. Must be one of: {valid_statuses}")
            return
        
        data = {
            'id': str(uuid.uuid4()),
            'agent_name': agent_name,
            'activity_description': description,
            'status': status,
            'metadata': json.dumps(metadata) if metadata else None,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        self._queue_log('agent_activity', data)
        print(f"🤖 Agent activity logged: {agent_name} - {status} - {description[:50]}...")
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue and connection status"""
        
        return {
            'connected': self.is_connected,
            'queue_size': self.log_queue.qsize(),
            'supabase_available': SUPABASE_AVAILABLE,
            'last_connection_attempt': self.last_connection_attempt,
            'worker_thread_alive': self.worker_thread.is_alive()
        }
    
    def flush_queue(self) -> bool:
        """Force process all queued logs immediately"""
        
        if not self.is_connected:
            if not self._test_connection():
                print("❌ Cannot flush queue - Supabase not connected")
                return False
            self.is_connected = True
        
        initial_size = self.log_queue.qsize()
        if initial_size == 0:
            print("ℹ️ No logs in queue to flush")
            return True
        
        print(f"🔄 Flushing {initial_size} queued logs...")
        
        # Process all items in queue
        processed = 0
        while not self.log_queue.empty():
            try:
                log_entry = self.log_queue.get_nowait()
                
                if self._insert_to_supabase(log_entry):
                    processed += 1
                    self.log_queue.task_done()
                else:
                    # Put back in queue if insert failed
                    self.log_queue.put(log_entry)
                    break
                    
            except queue.Empty:
                break
        
        print(f"✅ Successfully flushed {processed}/{initial_size} logs")
        return processed == initial_size
    
    def shutdown(self):
        """Shutdown the logging system gracefully"""
        
        print("🔄 Shutting down logging system...")
        
        # Save any remaining logs to disk
        self._save_pending_logs()
        
        # Try to flush queue one more time
        if self.is_connected:
            self.flush_queue()
        
        print("✅ Logging system shutdown complete")


# Global logger instance
_angles_logger: Optional[AnglesLogger] = None


def get_logger() -> AnglesLogger:
    """Get the global Angles logger instance"""
    global _angles_logger
    if _angles_logger is None:
        _angles_logger = AnglesLogger()
    return _angles_logger


# Convenience functions for easy import and use
def log_decision(decision_text: str, decision_type: str, decision_date: Optional[str] = None):
    """Log a system decision - convenience function"""
    logger = get_logger()
    logger.log_decision(decision_text, decision_type, decision_date)


def log_memory_event(event_type: str, description: str, metadata: Optional[Dict[str, Any]] = None):
    """Log a memory event - convenience function"""
    logger = get_logger()
    logger.log_memory_event(event_type, description, metadata)


def log_agent_activity(agent_name: str, description: str, status: str = 'completed', metadata: Optional[Dict[str, Any]] = None):
    """Log agent activity - convenience function"""
    logger = get_logger()
    logger.log_agent_activity(agent_name, description, status, metadata)


def main():
    """Test and demonstration script"""
    
    print("🧪 ANGLES AI UNIVERSE™ LOGGING SYSTEM TEST")
    print("=" * 60)
    
    # Initialize logger
    logger = get_logger()
    
    # Show status
    status = logger.get_queue_status()
    print(f"📊 System Status:")
    print(f"   Connected: {status['connected']}")
    print(f"   Queue Size: {status['queue_size']}")
    print(f"   Supabase Available: {status['supabase_available']}")
    print()
    
    # Test logging functions
    print("🧪 Testing logging functions...")
    
    # Test decision logging
    log_decision(
        "Implement comprehensive logging system for all backend operations",
        "Architecture"
    )
    
    # Test memory event logging
    log_memory_event(
        "system_initialization",
        "Angles AI Universe logging system started successfully",
        {"version": "1.0.0", "timestamp": datetime.now(timezone.utc).isoformat()}
    )
    
    # Test agent activity logging
    log_agent_activity(
        "logging_test_agent",
        "Executed comprehensive logging system test",
        "completed",
        {"test_items": 3, "success": True}
    )
    
    print()
    print("✅ Test logging completed!")
    
    # Show final status
    final_status = logger.get_queue_status()
    print(f"📊 Final Status:")
    print(f"   Queue Size: {final_status['queue_size']}")
    print(f"   Connected: {final_status['connected']}")
    
    if final_status['queue_size'] > 0:
        print(f"ℹ️ {final_status['queue_size']} logs queued for background processing")
    
    print()
    print("🎉 Angles AI Universe™ logging system ready for use!")
    print()
    print("Usage in your code:")
    print("  from angles_logging import log_decision, log_memory_event, log_agent_activity")
    print("  log_decision('Your decision', 'Architecture')")
    print("  log_memory_event('sync_completed', 'Successfully synced 50 records')")
    print("  log_agent_activity('backup_agent', 'Daily backup completed', 'completed')")


if __name__ == "__main__":
    main()