from flask import Flask, request, jsonify
import jobspy_scraper

app = Flask(__name__)


@app.route("/health")
def health():
  return {"ok": True}


@app.route("/scrape")
def scrape():
  sites = request.args.get("sites", "indeed").split(",")
  term = request.args.get("term", "backend developer")
  results = request.args.get("results", 20, type=int)
  country = request.args.get("country", "philippines")
  remote = request.args.get("remote", "true").lower() == "true"
  type = request.args.get("type", "fulltime")
  offset = request.args.get("offset", 0, type=int)

  try:
    jobs = jobspy_scraper.get_jobs(sites=sites, term=term, results=results, country=country,
                                   remote=remote, type=type, offset=offset)
  except jobspy_scraper.ScrapeError as e:
    app.logger.exception("Scrape failed for term=%r sites=%r", term, sites)
    return jsonify({"error": str(e), "term": term, "sites": sites}), 502

  return jsonify(jobs)


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000)