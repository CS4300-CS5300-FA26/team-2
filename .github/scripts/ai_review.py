# Sends a pull request's changes to OpenAI and saves the review to a file.
# Usage: python ai_review.py <diff file> <output file>
import json
import os
import sys
import urllib.error
import urllib.request

# Which OpenAI model to use (change this if OpenAI retires it)
MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

# Very large diffs are cut off so the request isn't too big
MAX_CHARS = 60000

diff_path, output_path = sys.argv[1], sys.argv[2]

# read the PR's changes
with open(diff_path, encoding="utf-8", errors="replace") as f:
    diff = f.read()

if not diff.strip():
    review = "No code changes to review."
else:
    if len(diff) > MAX_CHARS:
        diff = diff[:MAX_CHARS] + "\n\n[diff cut off because it was too long]"

    # what we ask the AI to do
    instructions = (
        "You are reviewing a pull request for a Django + React student project. "
        "Point out bugs, security problems, missing tests, and unclear code. "
        "Be specific: name the file and explain the fix. Keep it short and friendly. "
        "If everything looks good, say so."
    )

    request_body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": instructions},
            {"role": "user", "content": "Here is the diff:\n\n" + diff},
        ],
    }

    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(request_body).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + os.environ["OPENAI_API_KEY"],
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            result = json.load(response)
        review = result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as error:
        # show OpenAI's error message in the log, then fail this step
        print("OpenAI request failed:", error.code, error.read().decode("utf-8"))
        sys.exit(1)
    except urllib.error.URLError as error:
        print("Could not reach OpenAI:", error.reason)
        sys.exit(1)

# save the review with a heading so it's clear where it came from
with open(output_path, "w", encoding="utf-8") as f:
    f.write("## AI Code Review (OpenAI " + MODEL + ")\n\n" + review + "\n")

print("Review saved to", output_path)
