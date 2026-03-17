"""
Fetch occupation descriptions from the ESCO API for ISCO-08 coded occupations.

ESCO provides detailed occupation descriptions mapped to ISCO codes, which can
be used as input for LLM scoring (similar to how BLS markdown pages are used for US).

Saves markdown descriptions to data/<region>/pages/<isco_code>.md.

Usage:
    uv run python scrape_esco.py --region be           # Belgium occupations
    uv run python scrape_esco.py --region eu           # EU occupations
    uv run python scrape_esco.py --region be --force   # re-fetch
"""

import argparse
import json
import os
import time
import httpx

from countries import REGIONS, ESCO_API_BASE, ESCO_VERSION, ISCO08_2DIGIT, esco_uri


def fetch_esco_occupation(client, uri):
    """Fetch a single ISCO occupation from ESCO API and return its data."""
    url = f"{ESCO_API_BASE}/resource/occupation"
    params = {
        "uri": uri,
        "language": "en",
        "selectedVersion": ESCO_VERSION,
    }
    resp = client.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def esco_to_markdown(data):
    """Convert ESCO occupation JSON to a markdown description for LLM scoring."""
    md = []

    title = data.get("title", "Unknown Occupation")
    md.append(f"# {title}")
    md.append("")

    code = data.get("code", "")
    if code:
        md.append(f"**ISCO-08 Code:** {code}")
        md.append("")

    # Description
    desc = data.get("description", {})
    en_desc = desc.get("en", {})
    if isinstance(en_desc, dict):
        text = en_desc.get("literal", "")
    else:
        text = str(en_desc)

    if text:
        md.append("## Description")
        md.append("")
        md.append(text)
        md.append("")

    # Sub-occupations (narrower concepts)
    narrower = data.get("narrowerConcepts", [])
    if narrower:
        md.append("## Sub-occupations")
        md.append("")
        for sub in narrower:
            sub_title = sub.get("title", "")
            sub_code = sub.get("code", "")
            if sub_title:
                md.append(f"- **{sub_code}** {sub_title}")
        md.append("")

    return "\n".join(md)


def main():
    parser = argparse.ArgumentParser(description="Fetch ESCO occupation descriptions")
    parser.add_argument("--region", required=True, choices=["be", "eu"],
                        help="Region (determines which occupations to fetch)")
    parser.add_argument("--force", action="store_true",
                        help="Re-fetch even if cached")
    parser.add_argument("--delay", type=float, default=0.5,
                        help="Seconds between API requests")
    args = parser.parse_args()

    region = REGIONS[args.region]
    data_dir = region["data_dir"]
    pages_dir = os.path.join(data_dir, "pages")
    os.makedirs(pages_dir, exist_ok=True)

    # Load occupations list to know which ISCO codes we need
    occ_path = os.path.join(data_dir, "occupations.json")
    if not os.path.exists(occ_path):
        print(f"Error: Run scrape_eurostat.py --region {args.region} first")
        return

    with open(occ_path) as f:
        occupations = json.load(f)

    # Get unique ISCO codes from our occupations
    isco_codes = set()
    for occ in occupations:
        code = "OC" + occ["isco_code"]
        if code in ISCO08_2DIGIT:
            isco_codes.add(code)

    print(f"Fetching ESCO descriptions for {len(isco_codes)} ISCO codes...")

    client = httpx.Client()
    fetched = 0
    cached = 0
    errors = []

    for i, code in enumerate(sorted(isco_codes)):
        slug = code.lower()
        md_path = os.path.join(pages_dir, f"{slug}.md")

        if not args.force and os.path.exists(md_path):
            cached += 1
            continue

        uri = esco_uri(code)
        print(f"  [{i+1}/{len(isco_codes)}] {ISCO08_2DIGIT[code]}...", end=" ", flush=True)

        try:
            data = fetch_esco_occupation(client, uri)
            md = esco_to_markdown(data)

            with open(md_path, "w") as f:
                f.write(md)

            # Also save raw JSON for reference
            json_path = os.path.join(data_dir, "esco_raw", f"{slug}.json")
            os.makedirs(os.path.dirname(json_path), exist_ok=True)
            with open(json_path, "w") as f:
                json.dump(data, f, indent=2)

            print(f"OK ({len(md)} chars)")
            fetched += 1

        except Exception as e:
            print(f"ERROR: {e}")
            errors.append(code)

        if i < len(isco_codes) - 1:
            time.sleep(args.delay)

    client.close()

    print(f"\nDone. Fetched: {fetched}, Cached: {cached}, Errors: {len(errors)}")
    if errors:
        print(f"  Failed: {errors}")


if __name__ == "__main__":
    main()
