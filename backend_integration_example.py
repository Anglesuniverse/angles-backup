#!/usr/bin/env python3
"""
Angles AI Universe™ Backend Integration Example
Shows how to integrate the logging system into existing backend code

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import sys
from pathlib import Path

# Import the logging functions
from angles_logging import log_decision, log_memory_event, log_agent_activity


def example_sync_operation():
    """Example showing logging integration during a sync operation"""
    
    # Log the start of a sync operation
    log_agent_activity(
        agent_name="sync_agent",
        description="Starting bidirectional Supabase-Notion sync",
        status="started",
        metadata={"batch_size": 100, "timeout": 30}
    )
    
    try:
        # Simulate sync work here...
        records_processed = 42
        
        # Log memory event for successful sync
        log_memory_event(
            event_type="sync_completed",
            description=f"Successfully synced {records_processed} records between Supabase and Notion",
            metadata={
                "records_processed": records_processed,
                "duration_seconds": 12.5,
                "errors": 0
            }
        )
        
        # Log agent completion
        log_agent_activity(
            agent_name="sync_agent",
            description=f"Completed sync operation: {records_processed} records processed",
            status="completed",
            metadata={"success": True, "records": records_processed}
        )
        
        print(f"✅ Sync completed successfully - {records_processed} records")
        
    except Exception as e:
        # Log memory event for sync error
        log_memory_event(
            event_type="sync_error",
            description=f"Sync operation failed: {str(e)}",
            metadata={"error_type": type(e).__name__, "error_message": str(e)}
        )
        
        # Log agent failure
        log_agent_activity(
            agent_name="sync_agent",
            description=f"Sync operation failed: {str(e)}",
            status="failed",
            metadata={"error": str(e)}
        )
        
        print(f"❌ Sync failed: {e}")


def example_system_decision():
    """Example showing decision logging"""
    
    # Log an architecture decision
    log_decision(
        decision_text="Implement comprehensive logging system with local queuing for reliability",
        decision_type="Architecture"
    )
    
    # Log a policy decision
    log_decision(
        decision_text="All agent activities must be logged for audit purposes",
        decision_type="Policy"
    )
    
    # Log an ops decision
    log_decision(
        decision_text="Set up automated daily backups at 02:00 UTC",
        decision_type="Ops"
    )
    
    print("✅ System decisions logged")


def example_memory_events():
    """Example showing memory event logging"""
    
    # Log system startup
    log_memory_event(
        event_type="system_startup",
        description="Angles AI Universe backend system started successfully",
        metadata={"version": "1.0.0", "environment": "production"}
    )
    
    # Log configuration change
    log_memory_event(
        event_type="config_change",
        description="Updated sync interval from 30 to 15 minutes",
        metadata={"old_value": 30, "new_value": 15, "setting": "sync_interval"}
    )
    
    # Log backup completion
    log_memory_event(
        event_type="backup_completed",
        description="Daily automated backup completed successfully",
        metadata={"backup_size_mb": 145.7, "duration_seconds": 23.4}
    )
    
    print("✅ Memory events logged")


def example_agent_activities():
    """Example showing agent activity logging"""
    
    # Log backup agent activity
    log_agent_activity(
        agent_name="backup_agent",
        description="Executing daily backup procedure",
        status="in_progress",
        metadata={"backup_type": "incremental", "target": "memory_backups"}
    )
    
    # Log config monitor activity
    log_agent_activity(
        agent_name="config_monitor",
        description="Detected configuration file changes",
        status="completed",
        metadata={"files_changed": 3, "auto_commit": True}
    )
    
    # Log memory sync agent activity
    log_agent_activity(
        agent_name="memory_sync_agent",
        description="Synchronized 15 decisions to Notion database",
        status="completed",
        metadata={"records_synced": 15, "notion_pages_created": 5}
    )
    
    print("✅ Agent activities logged")


def integrate_into_existing_code():
    """Example of integrating logging into existing backend functions"""
    
    # Example: Modify your existing sync function
    def your_existing_sync_function():
        log_agent_activity("sync_service", "Starting data synchronization", "started")
        
        try:
            # Your existing sync logic here...
            success = True  # Replace with actual sync logic
            
            if success:
                log_memory_event("sync_success", "Data synchronization completed")
                log_agent_activity("sync_service", "Data sync completed successfully", "completed")
            
        except Exception as e:
            log_memory_event("sync_error", f"Sync failed: {e}")
            log_agent_activity("sync_service", f"Sync failed: {e}", "failed")
            raise
    
    # Example: Modify your existing decision recording
    def record_architecture_decision(decision_text):
        # Your existing logic...
        
        # Add logging
        log_decision(decision_text, "Architecture")
        log_memory_event("decision_made", f"New architecture decision recorded: {decision_text[:50]}...")
    
    # Example: Modify your existing backup function
    def your_existing_backup_function():
        log_agent_activity("backup_service", "Starting backup operation", "started")
        
        try:
            # Your existing backup logic...
            log_memory_event("backup_success", "Backup completed successfully")
            log_agent_activity("backup_service", "Backup completed", "completed")
            
        except Exception as e:
            log_memory_event("backup_error", f"Backup failed: {e}")
            log_agent_activity("backup_service", f"Backup failed: {e}", "failed")
            raise
    
    print("✅ Examples of integrating logging into existing code")


def main():
    """Run all integration examples"""
    
    print("🚀 ANGLES AI UNIVERSE™ BACKEND INTEGRATION EXAMPLES")
    print("=" * 60)
    
    print("\n1. 📊 Logging System Decisions...")
    example_system_decision()
    
    print("\n2. 📝 Logging Memory Events...")
    example_memory_events()
    
    print("\n3. 🤖 Logging Agent Activities...")
    example_agent_activities()
    
    print("\n4. 🔄 Simulating Sync Operation...")
    example_sync_operation()
    
    print("\n5. 🔧 Integration Examples...")
    integrate_into_existing_code()
    
    print("\n🎉 All integration examples completed!")
    print("\nTo integrate into your existing backend:")
    print("1. Import: from angles_logging import log_decision, log_memory_event, log_agent_activity")
    print("2. Add logging calls at key points in your code")
    print("3. Use appropriate event types and statuses")
    print("4. Include relevant metadata for debugging and analysis")
    
    # Show how to check logging system status
    from angles_logging import get_logger
    
    logger = get_logger()
    status = logger.get_queue_status()
    
    print(f"\n📊 Current Logging System Status:")
    print(f"   Connected to Supabase: {status['connected']}")
    print(f"   Logs in queue: {status['queue_size']}")
    print(f"   Worker thread active: {status['worker_thread_alive']}")


if __name__ == "__main__":
    main()