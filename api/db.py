import os
import psycopg2
from typing import Optional

# Use existing Supabase database
DB_URL = os.getenv("DATABASE_URL")

def get_conn():
    """Get database connection using existing Supabase DATABASE_URL."""
    if not DB_URL:
        raise ValueError("DATABASE_URL environment variable not set")
    return psycopg2.connect(DB_URL)