from jobspy import scrape_jobs
from pandas import DataFrame
import json
import argparse
import sys


def get_jobs(sites:list, term:str, results:int, country:str, remote:bool, type:str, offset:int):
  try:
    google_search_term = None
    if ("google" in sites):
      google_search_term = f"{term} jobs in the Philippines since yesterday"

    location = None
    linkedin_fetch_description = "linkedin" in sites
    if ("linkedin" in sites):
      location = "Philippines"

    jobs = scrape_jobs(
      site_name=sites,
      search_term=term,
      google_search_term=google_search_term,
      results_wanted=results,
      country_indeed=country,
      location=location,
      linkedin_fetch_description=linkedin_fetch_description,
      is_remote=remote,
      job_type=type,
      offset=offset
    )

    return transform_jobs(jobs)
  
  except Exception as e:
    print(json.dumps({"error": str(e)}), file=sys.stderr)
    sys.exit(1)  

def transform_jobs(df: DataFrame):
  if "min_amount" in df.columns:
    df["salary"] = df.apply(
      lambda row: f"{row['min_amount']} - {row['max_amount']} {row['currency']}/{row['interval']}"
      if row["min_amount"] is not None
      else None,
      axis=1)
  else:
    df["salary"] = None

  expected_cols = ["id", "site", "job_url", "title", "company", "location", "salary", "date_posted", "is_remote", "description"]
  for col in expected_cols:
    if col not in df.columns:
      df[col] = None

  new_df = df[expected_cols]
  renamed_df = new_df.rename(columns={"id": "job_id", "site": "source", "job_url": "url", "date_posted": "posted_at"})

  # Replace any NaN with None so JSON serialization produces valid null
  renamed_df = renamed_df.where(renamed_df.notnull(), None)

  return renamed_df.to_dict(orient="records")


def main():
  parser = argparse.ArgumentParser(description="Job Hunter Scraper")

  parser.add_argument("search_term", type=str, help="String used for searching jobs")
  parser.add_argument("-s", "--site", type=str, nargs="+", default=["indeed"], help="Accepts may job sites" )
  parser.add_argument("-rw", "--results_wanted", type=int, default=20, help="Amount of job listing to show")
  parser.add_argument("-c", "--country", type=str, default="philippines", help="Which country should the job be based in")
  parser.add_argument("-jt", "--job_type", type=str, default="fulltime", help="Type of job it should show")
  parser.add_argument("-r", "--is_remote", action="store_true", help="Remote jobs")
  parser.add_argument("-o", "--offset", type=int, default=0, help="Start the search from an offset")

  args = parser.parse_args()

  print(get_jobs(
    sites=args.site,
    term=args.search_term,
    results=args.results_wanted,
    country=args.country,
    remote=args.is_remote,
    type=args.job_type,
    offset=args.offset
    ))

if __name__ == "__main__":
  main()

