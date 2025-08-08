"""
Configuration module for Supabase connection
Manages environment variables and client initialization
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class SupabaseConfig:
    """Configuration class for Supabase client"""
    
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        self._client = None
        
        if not self.url:
            raise ValueError("SUPABASE_URL environment variable is required")
        if not self.key:
            raise ValueError("SUPABASE_KEY environment variable is required")
    
    @property
    def client(self) -> Client:
        """Get or create Supabase client instance"""
        if self._client is None:
            # Type checking: url and key are guaranteed to be strings due to __init__ validation
            assert self.url is not None and self.key is not None
            self._client = create_client(self.url, self.key)
        return self._client
    
    def test_connection(self) -> bool:
        """Test the Supabase connection"""
        try:
            # Simple test query
            self.client.auth.get_user()
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False

# Global configuration instance
supabase_config = SupabaseConfig()

# Export the client for easy importing
supabase = supabase_config.client