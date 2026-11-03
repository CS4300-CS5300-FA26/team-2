#!/usr/bin/env python3

# Test the React home page and the Nginx API proxy route
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen


# Read the Docker image name passed in by GitHub Actions
image_name = sys.argv[1]

# Give this test run separate Docker resources
suffix = str(time.time_ns())
network_name = f"gateway-test-network-{suffix}"
backend_name = f"gateway-test-backend-{suffix}"
gateway_name = f"gateway-test-frontend-{suffix}"


# Run one Docker command and stop if it fails
def docker(*arguments):
    subprocess.run(
        ["docker", *arguments],
        check=True,
        stdout=subprocess.DEVNULL,
    )


# Read text from the temporary local website
def get_page(path):
    with urlopen(f"http://localhost:8080{path}", timeout=2) as response:
        return response.read().decode("utf-8")


try:
    # Create a private network so Nginx can find the fake backend
    docker("network", "create", network_name)

    # Start a tiny fake backend that responds only at the API route
    docker(
        "run",
        "--detach",
        "--name",
        backend_name,
        "--network",
        network_name,
        "python:3.12-alpine",
        "sh",
        "-c",
        "mkdir -p /srv/api && "
        "printf 'api backend marker\\n' > /srv/api/index.html && "
        "cd /srv && python -m http.server 8000",
    )

    # Start the frontend gateway and connect it to the fake backend
    docker(
        "run",
        "--detach",
        "--name",
        gateway_name,
        "--network",
        network_name,
        "--env",
        f"BACKEND_HOST={backend_name}",
        "--publish",
        "8080:80",
        image_name,
    )

    # Give the containers a few seconds to start
    for _ in range(10):
        try:
            home_page = get_page("/")
            api_page = get_page("/api/")
            break
        except (URLError, OSError):
            time.sleep(1)
    else:
        raise AssertionError("Gateway did not start")

    # Confirm React is served at the public home page
    assert "Pathfinder" in home_page, "React home page did not load"

    # Confirm the API route reaches the backend through Nginx
    assert "api backend marker" in api_page, "API route did not reach backend"

    print("Gateway integration test passed")
finally:
    # Remove temporary Docker resources after every test run
    subprocess.run(
        ["docker", "rm", "--force", gateway_name, backend_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    subprocess.run(
        ["docker", "network", "rm", network_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )