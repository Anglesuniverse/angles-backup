#!/usr/bin/env python3
"""
Main entry point for GPT Assistant Output Processor
Automatically processes GPT outputs and manages Supabase operations
"""

import asyncio
import sys
import signal
from typing import Optional
from datetime import datetime

from config import Config
from utils.logger import setup_logger
from processors.memory_processor import MemoryProcessor
from database.supabase_client import SupabaseClient


class GPTProcessorApp:
    """Main application class for GPT output processing"""
    
    def __init__(self):
        self.config = Config()
        self.logger = setup_logger(__name__, self.config.LOG_LEVEL)
        self.processor: Optional[MemoryProcessor] = None
        self.running = False
        
    async def initialize(self):
        """Initialize the application components"""
        try:
            self.logger.info("Initializing GPT Processor Application...")
            
            # Initialize Supabase client
            supabase_client = SupabaseClient(self.config)
            await supabase_client.initialize()
            
            # Initialize memory processor
            self.processor = MemoryProcessor(self.config, supabase_client)
            await self.processor.initialize()
            
            self.logger.info("Application initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize application: {str(e)}")
            raise
    
    async def start(self):
        """Start the main processing loop"""
        if not self.processor:
            raise RuntimeError("Application not initialized")
            
        self.running = True
        self.logger.info("Starting GPT output processing...")
        
        try:
            while self.running:
                await self.processor.process_pending_outputs()
                await asyncio.sleep(self.config.PROCESSING_INTERVAL)
                
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal, shutting down...")
        except Exception as e:
            self.logger.error(f"Unexpected error in main loop: {str(e)}")
            raise
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Graceful shutdown of the application"""
        self.running = False
        self.logger.info("Shutting down application...")
        
        if self.processor:
            await self.processor.shutdown()
            
        self.logger.info("Application shutdown complete")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}")
            self.running = False
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Main entry point"""
    app = GPTProcessorApp()
    
    try:
        app.setup_signal_handlers()
        await app.initialize()
        await app.start()
        
    except Exception as e:
        print(f"Fatal error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    # Run the application
    asyncio.run(main())
