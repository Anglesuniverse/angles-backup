"""
Configuration module for Angles AI Universe™
Handles environment variables and service availability detection
"""

import os
from typing import Optional


# Environment variables
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
NOTION_API_KEY = os.getenv('NOTION_API_KEY') or os.getenv('NOTION_TOKEN')
NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o')


def has_supabase() -> bool:
    """Check if Supabase credentials are available"""
    return bool(SUPABASE_URL and SUPABASE_KEY)


def has_notion() -> bool:
    """Check if Notion credentials are available"""
    return bool(NOTION_API_KEY and NOTION_DATABASE_ID)


def has_github() -> bool:
    """Check if GitHub credentials are available"""
    return bool(GITHUB_TOKEN and GITHUB_REPO)


def has_openai() -> bool:
    """Check if OpenAI credentials are available"""
    return bool(OPENAI_API_KEY)


def get_missing_config() -> list:
    """Return list of missing critical configurations"""
    missing = []
    if not has_supabase():
        missing.append("SUPABASE_URL/SUPABASE_KEY")
    return missing


def print_config_status():
    """Print configuration status"""
    print("🔧 Angles AI Universe™ Configuration Status:")
    print(f"   ✅ Supabase: {'Available' if has_supabase() else '❌ Missing'}")
    print(f"   {'✅' if has_notion() else 'ℹ️'} Notion: {'Available' if has_notion() else 'Optional - Skipping'}")
    print(f"   {'✅' if has_github() else 'ℹ️'} GitHub: {'Available' if has_github() else 'Optional - Skipping'}")
    print(f"   {'✅' if has_openai() else 'ℹ️'} OpenAI: {'Available' if has_openai() else 'Optional - Skipping'}")
    
    missing = get_missing_config()
    if missing:
        print(f"   ⚠️ Missing critical config: {', '.join(missing)}")
    else:
        print("   ✅ All critical configurations present")