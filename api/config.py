"""
Angles OS™ Configuration Management
Reads from Replit Secrets at runtime with fallbacks for local development
"""
import os
from typing import Optional

class Config:
    """Application configuration loaded from environment variables"""
    
    def __init__(self):
        # Database
        self.postgres_url: str = os.getenv('POSTGRES_URL') or os.getenv('DATABASE_URL') or \
                                'postgresql://postgres:postgres@localhost:5432/angles_os'
        
        # Cache/Queue
        self.redis_url: str = os.getenv('REDIS_URL', 'redis://localhost:6379')
        
        # External Services - Read from Replit Secrets
        self.supabase_url: Optional[str] = os.getenv('SUPABASE_URL')
        self.supabase_anon_key: Optional[str] = os.getenv('SUPABASE_ANON_KEY')
        self.supabase_service_key: Optional[str] = os.getenv('SUPABASE_SERVICE_KEY')
        self.notion_api_key: Optional[str] = os.getenv('NOTION_API_KEY')
        self.openai_api_key: Optional[str] = os.getenv('OPENAI_API_KEY')
        self.github_token: Optional[str] = os.getenv('GITHUB_TOKEN')
        
        # Application
        self.log_level: str = os.getenv('LOG_LEVEL', 'INFO')
        self.env: str = os.getenv('ENV', 'development')
        self.debug: bool = self.env == 'development'
        
    @property
    def is_production(self) -> bool:
        return self.env == 'production'
    
    def has_openai(self) -> bool:
        return bool(self.openai_api_key)
    
    def has_supabase(self) -> bool:
        return bool(self.supabase_url and self.supabase_anon_key)
    
    def has_notion(self) -> bool:
        return bool(self.notion_api_key)
    
    def has_github(self) -> bool:
        return bool(self.github_token)

# Global configuration instance
settings = Config()