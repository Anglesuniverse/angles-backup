CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS vault (
  id SERIAL PRIMARY KEY,
  source TEXT,
  chunk TEXT,
  summary TEXT,
  links TEXT[],
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS decisions (
  id SERIAL PRIMARY KEY,
  topic TEXT NOT NULL,
  options JSONB NOT NULL,        -- [{option, pros, cons}]
  chosen TEXT,                   -- chosen option label
  rationale TEXT,                -- why chosen
  status TEXT DEFAULT 'open',    -- open|approved|declined
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS logs (
  id SERIAL PRIMARY KEY,
  scope TEXT,                    -- "vault" | "decisions" | etc
  level TEXT,                    -- info|warn|error
  message TEXT,
  meta JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);