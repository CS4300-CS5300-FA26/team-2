# Sprint 3
# A command that imports real jobs from JobDataLake into our feed.
#
# Run it like this (from the backend folder):
#   python manage.py import_jobs
#   python manage.py import_jobs --query "software intern" --limit 20
#
# Django finds this command because the file lives in
# listings/management/commands/, and the command name is the file name.

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from listings.jobdatalake import JobDataLakeError, save_jobs, search_jobs


class Command(BaseCommand):
    # shown when someone runs: python manage.py help import_jobs
    help = "Import job listings from the JobDataLake API (uses 1 credit per run)."

    # the options you can type after the command name
    def add_arguments(self, parser):
        # Sprint 3: "*" means any job title (--function below narrows it to tech jobs)
        parser.add_argument("--query", default="*", help='keywords to search for ("*" = any)')
        # keep this small: each NEW listing also gets an AI credibility score (an OpenAI call)
        parser.add_argument("--limit", type=int, default=20, help="how many jobs to fetch (1-100)")
        parser.add_argument("--country", default="US", help="country code, like US")
        # Sprint 3: tech jobs by default. Use --function "" for every kind of job.
        parser.add_argument("--function", default="eng", help='job type, like eng or data ("" = all)')

    # this is what runs when you type the command
    def handle(self, *args, **options):
        # the key comes from backend/.env (locally) or Azure settings (production)
        api_key = settings.JOBDATALAKE_API_KEY
        if not api_key:
            # CommandError stops the command and prints this message
            raise CommandError("JOBDATALAKE_API_KEY is not set. Add it to backend/.env.")

        # the API only allows 1 to 100 jobs per request, so keep the number in that range
        limit = options["limit"]
        if limit < 1:
            limit = 1
        if limit > 100:
            limit = 100

        # ask JobDataLake for jobs (this is the 1 credit)
        try:
            # .lower() turns "ENG" into "eng", the way the API expects it
            job_function = options["function"].lower()
            jobs = search_jobs(api_key, options["query"], limit, options["country"], job_function)
        except JobDataLakeError as error:
            # turn our error into a clear message instead of a crash
            raise CommandError(str(error))

        # save the new ones and report how it went
        added, skipped = save_jobs(jobs)
        self.stdout.write(self.style.SUCCESS(
            f"Imported {added} new jobs ({skipped} already saved or missing an ID)."
        ))
