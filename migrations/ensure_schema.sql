
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
