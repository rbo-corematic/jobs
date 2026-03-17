"""
Country/region configuration for the job market visualizer.

Defines data sources, ISCO occupation codes, and region-specific settings.
Each region has its own data directory under data/<region_id>/.
"""

# ISCO-08 two-digit occupation codes and their labels (used by Eurostat & ESCO)
ISCO08_2DIGIT = {
    "OC11": "Chief executives, senior officials and legislators",
    "OC12": "Administrative and commercial managers",
    "OC13": "Production and specialised services managers",
    "OC14": "Hospitality, retail and other services managers",
    "OC21": "Science and engineering professionals",
    "OC22": "Health professionals",
    "OC23": "Teaching professionals",
    "OC24": "Business and administration professionals",
    "OC25": "Information and communications technology professionals",
    "OC26": "Legal, social and cultural professionals",
    "OC31": "Science and engineering associate professionals",
    "OC32": "Health associate professionals",
    "OC33": "Business and administration associate professionals",
    "OC34": "Legal, social, cultural and related associate professionals",
    "OC35": "Information and communications technicians",
    "OC41": "General and keyboard clerks",
    "OC42": "Customer services clerks",
    "OC43": "Numerical and material recording clerks",
    "OC44": "Other clerical support workers",
    "OC51": "Personal service workers",
    "OC52": "Sales workers",
    "OC53": "Personal care workers",
    "OC54": "Protective services workers",
    "OC61": "Market-oriented skilled agricultural workers",
    "OC62": "Market-oriented skilled forestry, fishery and hunting workers",
    "OC63": "Subsistence farmers, fishers, hunters and gatherers",
    "OC71": "Building and related trades workers, excluding electricians",
    "OC72": "Metal, machinery and related trades workers",
    "OC73": "Handicraft and printing workers",
    "OC74": "Electrical and electronic trades workers",
    "OC75": "Food processing, wood working, garment and other craft and related trades workers",
    "OC81": "Stationary plant and machine operators",
    "OC82": "Assemblers",
    "OC83": "Drivers and mobile plant operators",
    "OC91": "Cleaners and helpers",
    "OC92": "Agricultural, forestry and fishery labourers",
    "OC93": "Labourers in mining, construction, manufacturing and transport",
    "OC94": "Food preparation assistants",
    "OC95": "Street and related sales and service workers",
    "OC96": "Refuse workers and other elementary workers",
    "OC01": "Commissioned armed forces officers",
    "OC02": "Non-commissioned armed forces officers",
    "OC03": "Armed forces occupations, other ranks",
}

# ISCO-08 major groups (1-digit) for categorization
ISCO08_MAJOR = {
    "1": "Managers",
    "2": "Professionals",
    "3": "Technicians and associate professionals",
    "4": "Clerical support workers",
    "5": "Service and sales workers",
    "6": "Skilled agricultural, forestry and fishery workers",
    "7": "Craft and related trades workers",
    "8": "Plant and machine operators and assemblers",
    "9": "Elementary occupations",
    "0": "Armed forces occupations",
}

# Map 2-digit ISCO code to its major group category
def isco_category(isco_code):
    """Return major group label for a 2-digit ISCO code like 'OC25' -> 'Professionals'."""
    digit = isco_code.replace("OC", "")[0]
    return ISCO08_MAJOR.get(digit, "Other")


# ESCO API URI pattern for ISCO codes
def esco_uri(isco_code):
    """Return ESCO API URI for an ISCO code like 'OC25' -> 'http://data.europa.eu/esco/isco/C25'."""
    code = isco_code.replace("OC", "")
    return f"http://data.europa.eu/esco/isco/C{code}"


# Region definitions
REGIONS = {
    "us": {
        "name": "United States",
        "short_name": "USA",
        "source": "bls",
        "description": "342 occupations from the Bureau of Labor Statistics Occupational Outlook Handbook",
        "source_url": "https://www.bls.gov/ooh/",
        "data_dir": "data/us",
    },
    "be": {
        "name": "Belgium",
        "short_name": "Belgium",
        "source": "eurostat",
        "geo_code": "BE",
        "description": "Occupations from Eurostat Labour Force Survey (ISCO-08)",
        "source_url": "https://ec.europa.eu/eurostat/databrowser/view/lfsa_egai2d/default/table",
        "data_dir": "data/be",
    },
    "eu": {
        "name": "European Union",
        "short_name": "EU",
        "source": "eurostat",
        "geo_code": "EU27_2020",
        "description": "Occupations from Eurostat Labour Force Survey (ISCO-08), EU-27 aggregate",
        "source_url": "https://ec.europa.eu/eurostat/databrowser/view/lfsa_egai2d/default/table",
        "data_dir": "data/eu",
    },
}

# Eurostat API configuration
EUROSTAT_API_BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
EUROSTAT_DATASET = "lfsa_egai2d"

# ESCO API configuration
ESCO_API_BASE = "https://ec.europa.eu/esco/api"
ESCO_VERSION = "v1.2.0"
