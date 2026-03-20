"""
Fetch employment data by ISCO-08 occupation from the Eurostat API.

Uses the lfsa_egai2d dataset (employed persons by detailed occupation, 2-digit ISCO-08).
No authentication required. Data returned in JSON-stat format.

Saves to data/<region>/occupations.json with employment counts in thousands.

Usage:
    uv run python scrape_eurostat.py --region be          # Belgium
    uv run python scrape_eurostat.py --region eu          # EU-27
    uv run python scrape_eurostat.py --region be --force  # re-fetch
"""

import argparse
import json
import os
import httpx

from countries import (
    REGIONS, EUROSTAT_API_BASE, EUROSTAT_DATASET,
    ISCO08_2DIGIT, isco_category, esco_uri,
)


def fetch_eurostat(geo_code):
    """Fetch employment data from Eurostat for a given geo code."""
    # Build ISCO filter for all 2-digit codes
    isco_params = "&".join(f"isco08={code}" for code in ISCO08_2DIGIT)

    url = (
        f"{EUROSTAT_API_BASE}/{EUROSTAT_DATASET}"
        f"?lang=EN&geo={geo_code}&sex=T&age=Y_GE15"
        f"&lastTimePeriod=1&{isco_params}"
    )

    print(f"Fetching Eurostat data for {geo_code}...")
    print(f"  URL: {url[:120]}...")

    resp = httpx.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def parse_eurostat_response(data):
    """Parse JSON-stat response into a list of occupation records."""
    isco_dim = data["dimension"]["isco08"]["category"]
    isco_index = isco_dim["index"]  # {"OC11": 0, "OC12": 1, ...}
    isco_labels = isco_dim["label"]  # {"OC11": "Chief executives...", ...}

    # Reverse index: position -> code
    pos_to_code = {v: k for k, v in isco_index.items()}

    values = data["value"]  # {"0": 19.3, "1": 402.5, ...}

    # Extract year from time dimension
    time_dim = data["dimension"]["time"]["category"]["label"]
    year = list(time_dim.keys())[0]

    status = data.get("status", {})

    occupations = []
    for pos_str, value in values.items():
        pos = int(pos_str)
        code = pos_to_code.get(pos)
        if not code or code not in ISCO08_2DIGIT:
            continue

        # Skip unreliable data (marked with "u")
        reliability = status.get(pos_str, "")

        # Value is in thousands of persons
        jobs_thousands = value
        jobs = int(round(jobs_thousands * 1000))

        occupations.append({
            "title": isco_labels[code],
            "isco_code": code.replace("OC", ""),
            "slug": code.lower(),
            "category": isco_category(code),
            "jobs": jobs,
            "jobs_year": year,
            "reliability": reliability,
            "esco_uri": esco_uri(code),
        })

    # Sort by jobs descending
    occupations.sort(key=lambda x: -x["jobs"])
    return occupations


def main():
    parser = argparse.ArgumentParser(description="Fetch Eurostat employment data")
    parser.add_argument("--region", required=True, choices=["be", "eu"],
                        help="Region to fetch (be=Belgium, eu=EU-27)")
    parser.add_argument("--force", action="store_true",
                        help="Re-fetch even if cached")
    args = parser.parse_args()

    region = REGIONS[args.region]
    data_dir = region["data_dir"]
    output_path = os.path.join(data_dir, "occupations.json")

    if not args.force and os.path.exists(output_path):
        print(f"Cached: {output_path} (use --force to re-fetch)")
        return

    os.makedirs(data_dir, exist_ok=True)

    raw = fetch_eurostat(region["geo_code"])

    # Save raw response for debugging
    raw_path = os.path.join(data_dir, "eurostat_raw.json")
    with open(raw_path, "w") as f:
        json.dump(raw, f, indent=2)
    print(f"  Raw response saved to {raw_path}")

    occupations = parse_eurostat_response(raw)

    with open(output_path, "w") as f:
        json.dump(occupations, f, indent=2)

    total_jobs = sum(o["jobs"] for o in occupations)
    print(f"\nWrote {len(occupations)} occupations to {output_path}")
    print(f"Total employment: {total_jobs:,}")
    print(f"\nTop 10 by employment:")
    for o in occupations[:10]:
        flag = " (low reliability)" if o["reliability"] == "u" else ""
        print(f"  {o['title']}: {o['jobs']:,}{flag}")


if __name__ == "__main__":
    main()
