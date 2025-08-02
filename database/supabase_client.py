"""
Supabase client wrapper for database operations
Handles connection management and basic CRUD operations
"""

import asyncio
from typing import Dict, Any, List, Optional
from supabase import create_client, Client
import json

from utils.logger import setup_logger
from utils.retry import retry_async


class SupabaseClient:
    """Wrapper class for Supabase operations"""
    
    def __init__(self, config):
        self.config = config
        self.logger = setup_logger(__name__, config.LOG_LEVEL)
        self.client: Optional[Client] = None
        self._semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_OPERATIONS)
    
    async def initialize(self):
        """Initialize the Supabase client"""
        try:
            self.client = create_client(
                self.config.SUPABASE_URL,
                self.config.SUPABASE_KEY
            )
            
            # Test the connection
            await self.test_connection()
            self.logger.info("Supabase client initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise
    
    @retry_async(max_retries=3, delay=2)
    async def test_connection(self):
        """Test the database connection"""
        if not self.client:
            raise RuntimeError("Supabase client not initialized")
            
        try:
            # Simple query to test connection
            result = self.client.table("conversations").select("id").limit(1).execute()
            self.logger.debug("Database connection test successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Database connection test failed: {str(e)}")
            raise
    
    @retry_async(max_retries=3, delay=2)
    async def insert_data(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert data into specified table"""
        async with self._semaphore:
            try:
                if not self.client:
                    raise RuntimeError("Supabase client not initialized")
                
                self.logger.debug(f"Inserting data into table '{table_name}': {json.dumps(data, default=str)}")
                
                result = self.client.table(table_name).insert(data).execute()
                
                if result.data:
                    self.logger.info(f"Successfully inserted data into '{table_name}' table")
                    return result.data[0] if isinstance(result.data, list) else result.data
                else:
                    raise RuntimeError(f"Insert operation returned no data: {result}")
                    
            except Exception as e:
                self.logger.error(f"Failed to insert data into '{table_name}': {str(e)}")
                raise
    
    @retry_async(max_retries=3, delay=2)
    async def insert_batch(self, table_name: str, data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Insert multiple records in batch"""
        async with self._semaphore:
            try:
                if not self.client:
                    raise RuntimeError("Supabase client not initialized")
                
                self.logger.debug(f"Batch inserting {len(data_list)} records into '{table_name}'")
                
                result = self.client.table(table_name).insert(data_list).execute()
                
                if result.data:
                    self.logger.info(f"Successfully batch inserted {len(result.data)} records into '{table_name}'")
                    return result.data
                else:
                    raise RuntimeError(f"Batch insert returned no data: {result}")
                    
            except Exception as e:
                self.logger.error(f"Failed to batch insert into '{table_name}': {str(e)}")
                raise
    
    @retry_async(max_retries=3, delay=2)
    async def query_data(self, table_name: str, filters: Optional[Dict[str, Any]] = None, 
                        limit: Optional[int] = None, order_by: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query data from specified table"""
        async with self._semaphore:
            try:
                if not self.client:
                    raise RuntimeError("Supabase client not initialized")
                
                query = self.client.table(table_name).select("*")
                
                # Apply filters
                if filters:
                    for column, value in filters.items():
                        query = query.eq(column, value)
                
                # Apply ordering
                if order_by:
                    query = query.order(order_by)
                
                # Apply limit
                if limit:
                    query = query.limit(limit)
                
                result = query.execute()
                
                self.logger.debug(f"Queried {len(result.data) if result.data else 0} records from '{table_name}'")
                return result.data or []
                
            except Exception as e:
                self.logger.error(f"Failed to query data from '{table_name}': {str(e)}")
                raise
    
    @retry_async(max_retries=3, delay=2)
    async def update_data(self, table_name: str, filters: Dict[str, Any], 
                         updates: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Update data in specified table"""
        async with self._semaphore:
            try:
                if not self.client:
                    raise RuntimeError("Supabase client not initialized")
                
                query = self.client.table(table_name).update(updates)
                
                # Apply filters
                for column, value in filters.items():
                    query = query.eq(column, value)
                
                result = query.execute()
                
                updated_count = len(result.data) if result.data else 0
                self.logger.info(f"Updated {updated_count} records in '{table_name}'")
                return result.data or []
                
            except Exception as e:
                self.logger.error(f"Failed to update data in '{table_name}': {str(e)}")
                raise
    
    @retry_async(max_retries=3, delay=2)
    async def delete_data(self, table_name: str, filters: Dict[str, Any]) -> int:
        """Delete data from specified table"""
        async with self._semaphore:
            try:
                if not self.client:
                    raise RuntimeError("Supabase client not initialized")
                
                query = self.client.table(table_name).delete()
                
                # Apply filters
                for column, value in filters.items():
                    query = query.eq(column, value)
                
                result = query.execute()
                
                deleted_count = len(result.data) if result.data else 0
                self.logger.info(f"Deleted {deleted_count} records from '{table_name}'")
                return deleted_count
                
            except Exception as e:
                self.logger.error(f"Failed to delete data from '{table_name}': {str(e)}")
                raise
    
    async def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get information about a table structure"""
        try:
            # This is a basic implementation - in practice you might want to use
            # Supabase's schema inspection capabilities
            schema = self.config.get_table_schema(table_name)
            if schema:
                return schema
            else:
                self.logger.warning(f"No schema found for table '{table_name}'")
                return {}
                
        except Exception as e:
            self.logger.error(f"Failed to get table info for '{table_name}': {str(e)}")
            return {}
