-- Job Hunter database schema
-- Run with: psql -U <user> -d <database> -v ON_ERROR_STOP=1 -f schema.sql
-- The `job_hunter` schema is isolated from n8n's internal tables (which live in `public`).

CREATE SCHEMA IF NOT EXISTS job_hunter;

CREATE TABLE job_hunter.jobs (
  id                      SERIAL PRIMARY KEY,
  job_id                  TEXT UNIQUE NOT NULL,          -- ID from the job board (dedup key)
  source                  TEXT NOT NULL,
  title                   TEXT NOT NULL,
  company                 TEXT,
  location                TEXT,
  is_remote               BOOLEAN,                       -- job board's label; unreliable, not used in decisions
  url                     TEXT,
  description             TEXT,
  salary                  TEXT,                          -- human-readable, as shown to the LLM
  posted_at               TIMESTAMPTZ,
  scraped_at              TIMESTAMPTZ DEFAULT NOW(),

  -- LLM judgments
  ros_status              TEXT CHECK (ros_status IN ('pass', 'unverified', 'fail')),
  ros_reason              TEXT,
  score_stack             SMALLINT,                      -- 0-3
  score_experience        SMALLINT,                      -- 0-2
  score_flags             SMALLINT,                      -- 0-3
  llm_reason              TEXT,
  llm_model               TEXT,

  -- Computed in code (Compute Verdict node), not by the LLM
  work_setup              TEXT CHECK (work_setup IN ('remote', 'hybrid', 'onsite', 'unclear')),
  office_days_per_week    SMALLINT,                      -- hybrid only
  score_salary            SMALLINT,                      -- 0-2, from salary_monthly_php
  llm_flags               TEXT[],                        -- LLM judgment flags + code-derived flags
  llm_score               INTEGER,                       -- sum of subscores, 0 if gated
  llm_apply               BOOLEAN,
  salary_monthly_php      INTEGER,                       -- lowest stated pay, normalized to monthly PHP
  salary_source           TEXT,                          -- 'jobspy' | 'llm' | NULL
  rules_version           SMALLINT,                      -- Compute Verdict rules that produced this verdict
  verdict_at              TIMESTAMPTZ,

  -- Legacy: kept in sync as (ros_status <> 'fail') for rows scored before ros_status existed
  ros_pass                BOOLEAN
);

CREATE INDEX idx_jobs_source     ON job_hunter.jobs(source);
CREATE INDEX idx_jobs_llm_score  ON job_hunter.jobs(llm_score);
CREATE INDEX idx_jobs_scraped_at ON job_hunter.jobs(scraped_at);

CREATE TABLE job_hunter.search_offsets (
  term            TEXT PRIMARY KEY,
  current_offset  INTEGER DEFAULT 0
);

CREATE TABLE job_hunter.applications (
  job_id      integer PRIMARY KEY REFERENCES job_hunter.jobs(id) ON DELETE RESTRICT,
  status      text NOT NULL CHECK (status IN
                ('interested', 'applied', 'interviewing', 'offer', 'rejected', 'withdrawn')),
  applied_at  timestamptz,
  updated_at  timestamptz NOT NULL DEFAULT now(),
  note        text
);

CREATE VIEW job_hunter.application_status AS
SELECT a.*,
       j.title, j.company, j.url,
       CASE WHEN a.status = 'applied' AND a.applied_at < now() - interval '21 days'
            THEN 'ghosted' ELSE a.status END AS effective_status
FROM job_hunter.applications a
JOIN job_hunter.jobs j ON j.id = a.job_id;