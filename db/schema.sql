-- Job Hunter database schema
-- Run with: psql -U <user> -d <database> -f schema.sql
-- Assumes the `job_hunter` schema is isolated from n8n's own internal tables (which live in `public`).

CREATE SCHEMA IF NOT EXISTS job_hunter;

CREATE TABLE job_hunter.jobs (
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

CREATE INDEX idx_jobs_source ON job_hunter.jobs(source);
CREATE INDEX idx_jobs_llm_score ON job_hunter.jobs(llm_score);
CREATE INDEX idx_jobs_scraped_at ON job_hunter.jobs(scraped_at);

CREATE TABLE job_hunter.search_offsets (
  term            TEXT PRIMARY KEY,
  current_offset  INTEGER DEFAULT 0
);