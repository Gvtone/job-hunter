from jobspy import scrape_jobs
from pandas import DataFrame
import pandas as pd
import argparse
import json
import sys

SALARY_COLS = ["min_amount", "max_amount", "currency", "interval"]
OUTPUT_COLS = ["id", "site", "job_url", "title", "company", "location", "salary",
               "date_posted", "is_remote", "description", *SALARY_COLS]


class ScrapeError(Exception):
  """Raised when JobSpy fails. Callers decide how to report it (exit code, HTTP status)."""


def get_jobs(sites: list, term: str, results: int, country: str, remote: bool, type: str, offset: int):
  google_search_term = f"{term} jobs in the Philippines since yesterday" if "google" in sites else None
  location = "Philippines" if "linkedin" in sites else None

  try:
    jobs = scrape_jobs(
      site_name=sites,
      search_term=term,
      google_search_term=google_search_term,
      results_wanted=results,
      country_indeed=country,
      location=location,
      linkedin_fetch_description="linkedin" in sites,
      is_remote=remote,
      job_type=type,
      offset=offset,
    )
  except Exception as e:
    raise ScrapeError(str(e)) from e

  return transform_jobs(jobs)


def _format_salary(row):
  lo, hi = row["min_amount"], row["max_amount"]
  if pd.isna(lo) and pd.isna(hi):
    return None

  if pd.notna(lo) and pd.notna(hi):
    amount = f"{lo:,.0f} - {hi:,.0f}"
  else:
    single = lo if pd.notna(lo) else hi
    amount = f"{single:,.0f}"

  currency = row["currency"] if pd.notna(row["currency"]) else ""
  interval = f"/{row['interval']}" if pd.notna(row["interval"]) else ""
  return f"{amount} {currency}{interval}".strip()


def transform_jobs(df: DataFrame):
  if df.empty:
    return []

  # Guarantee every column exists before anything reads it
  for col in OUTPUT_COLS:
    if col not in df.columns:
      df[col] = None

  df["salary"] = df.apply(_format_salary, axis=1)
  df["date_posted"] = df["date_posted"].apply(lambda d: d.isoformat() if pd.notna(d) else None)

  out = df[OUTPUT_COLS].rename(columns={
    "id": "job_id", "site": "source", "job_url": "url", "date_posted": "posted_at",
  })

  # astype(object) first: float columns can't hold None, so pandas would turn it back into NaN
  out = out.astype(object).where(out.notna(), None)

  return out.to_dict(orient="records")


def main():
  parser = argparse.ArgumentParser(description="Job Hunter Scraper")
  parser.add_argument("search_term", type=str, help="String used for searching jobs")
  parser.add_argument("-s", "--site", type=str, nargs="+", default=["indeed"], help="Job sites to search")
  parser.add_argument("-rw", "--results_wanted", type=int, default=20, help="Number of job listings to return")
  parser.add_argument("-c", "--country", type=str, default="philippines", help="Country for Indeed searches")
  parser.add_argument("-jt", "--job_type", type=str, default="fulltime", help="Job type filter")
  parser.add_argument("-r", "--is_remote", action="store_true", help="Remote jobs only")
  parser.add_argument("-o", "--offset", type=int, default=0, help="Start the search from an offset")
  args = parser.parse_args()

  try:
    jobs = get_jobs(sites=args.site, term=args.search_term, results=args.results_wanted,
                    country=args.country, remote=args.is_remote, type=args.job_type, offset=args.offset)
  except ScrapeError as e:
    print(json.dumps({"error": str(e)}), file=sys.stderr)
    sys.exit(1)

  print(json.dumps(jobs, default=str))


if __name__ == "__main__":
  main()