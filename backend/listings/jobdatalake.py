# Sprint 3
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
def search_jobs(api_key, query, limit, country, job_function=""):
    # the search options, written the way the API expects them
    options = {
        "q": query,                   # keywords, like "software intern"
        "per_page": limit,            # how many jobs we want back (max 100)
        "countries": country,         # like "US"
        "sort_by": "posted_at:desc",  # newest jobs first
    }

    # Sprint 3: only this kind of job, like "eng" for tech/engineering jobs.
    # If it's empty we leave it out, so every kind of job comes back.
    if job_function:
        options["job_function"] = job_function

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
    except TimeoutError:
        # Sprint 3: no answer within 30 seconds
        raise JobDataLakeError("JobDataLake took too long to answer. Try again later.")
    except ValueError:
        # Sprint 3: the reply wasn't JSON at all (for example, an error web page)
        raise JobDataLakeError("JobDataLake sent back something we couldn't read.")

    # Sprint 3: check the reply looks like the docs say: {"jobs": [ ... ]}
    # isinstance(x, dict) asks "is x a dictionary?", and list means "a list".
    # "jobs" must be there: if it's missing, data.get("jobs") gives None,
    # which isn't a list, so we stop instead of pretending there were 0 jobs.
    # If it doesn't look right, stop BEFORE saving anything.
    if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
        raise JobDataLakeError("JobDataLake sent back a reply in an unexpected format.")

    # the jobs are in the "jobs" part of the reply
    return data["jobs"]


# ------------------------------------------------------------
# Only keep normal web links (http:// or https://).
# This stops a bad link like "javascript:..." from ever reaching our page.
# ------------------------------------------------------------
def safe_link(url):
    if isinstance(url, str) and url.startswith(("https://", "http://")):
        return url[:500]  # our database field holds up to 500 characters
    return ""  # anything else: save no link at all


# ------------------------------------------------------------
# Sprint 3: only keep real text.
# If the API sends a number, a list, or nothing where we expect text,
# we use "" (empty text) instead, so nothing crashes.
# ------------------------------------------------------------
def as_text(value):
    if isinstance(value, str):
        return value
    return ""


# ------------------------------------------------------------
# Save the jobs we don't have yet.
# Returns two numbers: (how many we added, how many we skipped).
# ------------------------------------------------------------
def save_jobs(jobs):
    added = 0
    skipped = 0

    for job in jobs:
        # Sprint 3: skip anything that isn't a job (a job is a dictionary)
        if not isinstance(job, dict):
            skipped = skipped + 1
            continue

        # every job has its own ID in JobDataLake, called a "handle"
        # ([:200] cuts it to fit our database field)
        handle = as_text(job.get("job_handle"))[:200]

        # skip it if it has no ID
        if not handle:
            skipped = skipped + 1
            continue

        # "locations" is a list, like ["Denver, CO", "Remote"].
        # Join it into one piece of text: "Denver, CO; Remote"
        # Sprint 3: if it isn't a list, use an empty one,
        # and only join the places that are real text
        locations = job.get("locations")
        if not isinstance(locations, list):
            locations = []
        location_text = "; ".join(place for place in locations if isinstance(place, str))

        # make the new Listing.
        # "or ..." gives a fallback if the API left something blank,
        # and [:200] cuts text to fit our database fields.
        # Sprint 3: get_or_create looks for a Listing with this ID and only makes
        # a new one if there isn't one yet. Unlike "check, then create", it still
        # works if two imports run at the same time (it never makes a duplicate).
        # "defaults" are only used when it makes a new Listing.
        # It gives back the Listing and True if it was new (False if it was already saved).
        listing, created = Listing.objects.get_or_create(
            external_id=handle,
            defaults={
                "title": (as_text(job.get("title")) or "Untitled job")[:200],
                "company": (as_text(job.get("company_name")) or "Unknown company")[:200],
                "location": location_text[:300],
                "remote_type": as_text(job.get("remote_type"))[:20],
                "apply_url": safe_link(job.get("url")),
            },
        )
        if created:
            added = added + 1
        else:
            skipped = skipped + 1  # we already had it

    return added, skipped
