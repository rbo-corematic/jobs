"""
Build compact JSON for the website by merging occupation data with AI exposure scores.

Supports multiple regions:
  - US: merges occupations.csv + scores.json -> site/data.json
  - BE/EU: merges data/<region>/occupations.json + data/<region>/scores.json -> site/data_<region>.json

Usage:
    uv run python build_site_data.py                # build US (default, backward-compatible)
    uv run python build_site_data.py --region be    # build Belgium
    uv run python build_site_data.py --region eu    # build EU
    uv run python build_site_data.py --all          # build all regions
"""

import argparse
import csv
import json
import os

from countries import REGIONS


def build_us():
    """Build site data for US (original BLS pipeline)."""
    # Load AI exposure scores
    scores = {}
    if os.path.exists("scores.json"):
        with open("scores.json") as f:
            scores = {s["slug"]: s for s in json.load(f)}

    # Load CSV stats
    with open("occupations.csv") as f:
        rows = list(csv.DictReader(f))

    data = []
    for row in rows:
        slug = row["slug"]
        score = scores.get(slug, {})
        data.append({
            "title": row["title"],
            "slug": slug,
            "category": row["category"],
            "pay": int(row["median_pay_annual"]) if row["median_pay_annual"] else None,
            "jobs": int(row["num_jobs_2024"]) if row["num_jobs_2024"] else None,
            "outlook": int(row["outlook_pct"]) if row["outlook_pct"] else None,
            "outlook_desc": row["outlook_desc"],
            "education": row["entry_education"],
            "exposure": score.get("exposure"),
            "exposure_rationale": score.get("rationale"),
            "url": row.get("url", ""),
        })

    return data


def build_eurostat(region_id):
    """Build site data for a Eurostat-based region (BE, EU)."""
    region = REGIONS[region_id]
    data_dir = region["data_dir"]

    occ_path = os.path.join(data_dir, "occupations.json")
    if not os.path.exists(occ_path):
        print(f"  Error: {occ_path} not found. Run scrape_eurostat.py --region {region_id} first.")
        return []

    with open(occ_path) as f:
        occupations = json.load(f)

    # Load scores if available
    scores = {}
    scores_path = os.path.join(data_dir, "scores.json")
    if os.path.exists(scores_path):
        with open(scores_path) as f:
            scores = {s["slug"]: s for s in json.load(f)}

    data = []
    for occ in occupations:
        slug = occ["slug"]
        score = scores.get(slug, {})
        data.append({
            "title": occ["title"],
            "slug": slug,
            "category": occ["category"],
            "pay": None,  # Eurostat doesn't provide pay data at this level
            "jobs": occ.get("jobs"),
            "outlook": None,  # No projection data from Eurostat
            "outlook_desc": "",
            "education": "",
            "exposure": score.get("exposure"),
            "exposure_rationale": score.get("rationale"),
            "url": f"https://ec.europa.eu/esco/portal/occupation?uri={occ.get('esco_uri', '')}",
        })

    return data


def write_site_data(data, output_path, region_name):
    """Write data to JSON and print summary."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f)

    total_jobs = sum(d["jobs"] for d in data if d["jobs"])
    print(f"  {region_name}: {len(data)} occupations, {total_jobs:,} jobs -> {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Build website data")
    parser.add_argument("--region", choices=list(REGIONS.keys()),
                        help="Build for a specific region")
    parser.add_argument("--all", action="store_true",
                        help="Build for all available regions")
    args = parser.parse_args()

    os.makedirs("site", exist_ok=True)

    regions_to_build = []
    if args.all:
        regions_to_build = list(REGIONS.keys())
    elif args.region:
        regions_to_build = [args.region]
    else:
        # Default: build US only (backward-compatible)
        regions_to_build = ["us"]

    # Build a manifest of available regions for the frontend
    manifest = {}

    for region_id in regions_to_build:
        region = REGIONS[region_id]

        if region_id == "us":
            if not os.path.exists("occupations.csv"):
                print(f"  Skipping US: occupations.csv not found")
                continue
            data = build_us()
            output_path = "site/data.json"  # backward-compatible
        else:
            data = build_eurostat(region_id)
            output_path = f"site/data_{region_id}.json"

        if data:
            write_site_data(data, output_path, region["name"])
            manifest[region_id] = {
                "name": region["name"],
                "short_name": region["short_name"],
                "file": os.path.basename(output_path),
                "description": region["description"],
                "source_url": region["source_url"],
                "count": len(data),
                "total_jobs": sum(d["jobs"] for d in data if d["jobs"]),
            }

    # Write manifest
    manifest_path = "site/regions.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nWrote region manifest to {manifest_path}")


if __name__ == "__main__":
    main()
