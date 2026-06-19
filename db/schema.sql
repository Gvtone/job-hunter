-- Job Hunter database schema
-- Run with: psql -U <user> -d <database> -f schema.sql
-- Assumes the `app` schema is isolated from n8n's own internal tables (which live in `public`).

CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE app.jobs (
  id           SERIAL PRIMARY KEY,
  job_id       TEXT UNIQUE NOT NULL,
  source       TEXT NOT NULL,
  title        TEXT NOT NULL,
  company      TEXT,
  location     TEXT,
  is_remote    BOOLEAN,
  url          TEXT,
  description  TEXT,
  salary       TEXT,
  posted_at    TIMESTAMPTZ,
  scraped_at   TIMESTAMPTZ DEFAULT NOW(),
  ros_pass     BOOLEAN,
  ros_reason   TEXT,
  llm_score    INTEGER,
  llm_apply    BOOLEAN,
  llm_reason   TEXT,
  llm_flags    TEXT[],
  verdict_at   TIMESTAMPTZ
);

CREATE INDEX idx_jobs_source ON app.jobs(source);
CREATE INDEX idx_jobs_llm_score ON app.jobs(llm_score);
CREATE INDEX idx_jobs_scraped_at ON app.jobs(scraped_at);

CREATE TABLE app.search_offsets (
  term            TEXT PRIMARY KEY,
  current_offset  INTEGER DEFAULT 0
);