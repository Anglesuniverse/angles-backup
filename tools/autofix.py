import os, subprocess, textwrap

REQUIRED_PACKAGES=["openai","supabase","requests","psutil","schedule","cryptography","python-dotenv","tenacity"]

SCHEMA_SQL = """
-- Angles AI Universe™ base schema
create extension if not exists pgcrypto;
create table if not exists decision_vault(
  id uuid default gen_random_uuid() primary key,
  category text, status text, content text,
  date_added timestamptz default now(),
  last_updated timestamptz default now(),
  tags text[], notion_synced boolean default false
);
create table if not exists system_logs(
  id uuid default gen_random_uuid() primary key,
  level text, message text, ts timestamptz default now()
);
create table if not exists file_snapshots(
  id uuid default gen_random_uuid() primary key,
  file_path text, content text, ts timestamptz default now()
);
create table if not exists run_artifacts(
  id uuid default gen_random_uuid() primary key,
  artifact_name text, artifact_type text, ts timestamptz default now()
);
"""

def ensure_packages():
    print("📦 Package check (Nix environment - packages managed via packager tool)")
    for p in REQUIRED_PACKAGES:
        try: 
            __import__(p.replace("-","_"))
            print(f"  ✅ {p}: Available")
        except Exception: 
            print(f"  ⚠️  {p}: Not available (install via packager tool if needed)")

def write_schema_file():
    os.makedirs("migrations", exist_ok=True)
    with open("migrations/ensure_schema.sql","w",encoding="utf-8") as f:
        f.write(SCHEMA_SQL)
    print("⚠ Schema written to migrations/ensure_schema.sql — run it once in Supabase SQL Editor if tables are missing.")

if __name__=="__main__":
    ensure_packages()
    write_schema_file()
