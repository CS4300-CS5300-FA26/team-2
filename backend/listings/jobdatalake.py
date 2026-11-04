#Sprint 3
# This file talks to the JobDataLake API and saves the jobs it sends back.
#
# How the API works (from their docs):
#   - We send a GET request to https://api.jobdatalake.com/v1/jobs
#   - Our secret key goes in a header called "X-API-Key"
#   - Each request costs 1 credit, and can return up to 100 jobs
#   - It sends back JSON like: {"found": 3800, "jobs": [ {...}, {...} ]}

import json  # turns the API's JSON text into Python lists and dictionaries

# these come with Python, so we don't need to install anything new
from urllib.error import HTTPError, URLError  # errors that can happen when calling a website
from urllib.parse import urlencode  # builds the "?q=...&per_page=..." part of the address
from urllib.request import Request, urlopen  # sends the request and gets the reply

from .models import Listing

# the address of the "search jobs" endpoint
API_URL = "https://api.jobdatalake.com/v1/jobs"


# Our own error type, so the import command can catch it
# and show a friendly message instead of crashing.
class JobDataLakeError(Exception):
    pass


# ------------------------------------------------------------
# Ask JobDataLake for jobs.
# ONE call to this function = ONE credit, no matter how many jobs come back.
# Returns a list of jobs (each job is a dictionary).
# ------------------------------------------------------------
def search_jobs(api_key, query, limit, country):
    # the search options, written the way the API expects them
    options = {
        "q": query,                   # keywords, like "software intern"
        "per_page": limit,            # how many jobs we want back (max 100)
        "countries": country,         # like "US"
        "sort_by": "posted_at:desc",  # newest jobs first
    }

    # build the full address, e.g. .../v1/jobs?q=software+intern&per_page=20&...
    full_url = API_URL + "?" + urlencode(options)

    # headers are extra info sent along with the request:
    #   X-API-Key  = our secret key (that's how the API knows it's us)
    #   User-Agent = the name of our app. JobDataLake's security (Cloudflare)
    #                blocks Python's default name "Python-urllib" with a 403
    #                "error code: 1010", so we give our own name instead.
    headers = {
        "X-API-Key": api_key,
        "User-Agent": "Pathfinder/1.0 (CS4300 student project)",
    }
    request = Request(full_url, headers=headers)

    try:
        # send the request (give up after 30 seconds) and read the JSON reply
        with urlopen(request, timeout=30) as response:
            data = json.load(response)

    except HTTPError as error:
        # the API answered, but with an error code. Turn the codes from
        # their docs into messages a person can understand.
        if error.code == 401:
            raise JobDataLakeError("JobDataLake says the API key is invalid. Check JOBDATALAKE_API_KEY.")
        if error.code == 402:
            raise JobDataLakeError("JobDataLake account is out of credits.")
        if error.code == 429:
            raise JobDataLakeError("Too many requests to JobDataLake. Wait a moment and try again.")
        raise JobDataLakeError(f"JobDataLake error {error.code}.")

    except URLError as error:
        # we couldn't reach the website at all (no internet, site down, etc.)
        raise JobDataLakeError(f"Could not reach JobDataLake: {error.reason}")

    # the jobs are in the "jobs" part of the reply (empty list if it's missing)
    return data.get("jobs", [])


# ------------------------------------------------------------
# Only keep normal web links (http:// or https://).
# This stops a bad link like "javascript:..." from ever reaching our page.
# ------------------------------------------------------------
def safe_link(url):
    if isinstance(url, str) and url.startswith(("https://", "http://")):
        return url[:500]  # our database field holds up to 500 characters
    return ""  # anything else: save no link at all


# ------------------------------------------------------------
# Save the jobs we don't have yet.
# Returns two numbers: (how many we added, how many we skipped).
# ------------------------------------------------------------
def save_jobs(jobs):
    added = 0
    skipped = 0

    for job in jobs:
        # every job has its own ID in JobDataLake, called a "handle"
        handle = job.get("job_handle")

        # skip it if it has no ID, or if we already imported it before
        if not handle or Listing.objects.filter(external_id=handle).exists():
            skipped = skipped + 1
            continue

        # "locations" is a list, like ["Denver, CO", "Remote"].
        # Join it into one piece of text: "Denver, CO; Remote"
        locations = job.get("locations") or []
        location_text = "; ".join(locations)

        # make the new Listing.
        # "or ..." gives a fallback if the API left something blank,
        # and [:200] cuts text to fit our database fields.
        Listing.objects.create(
            external_id=handle,
            title=(job.get("title") or "Untitled job")[:200],
            company=(job.get("company_name") or "Unknown company")[:200],
            location=location_text[:300],
            remote_type=(job.get("remote_type") or "")[:20],
            apply_url=safe_link(job.get("url")),
        )
        added = added + 1

    return added, skipped
