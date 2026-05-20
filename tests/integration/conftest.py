import time
import urllib.request
import urllib.error

import pytest
import httpx


def wait_for_api(base_url: str = "http://localhost:8000", timeout: int = 60):
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(f"{base_url}/")
            return
        except urllib.error.URLError:
            time.sleep(1)
    raise RuntimeError(f"API not ready after {timeout}s")


wait_for_api()


@pytest.fixture
def client():
    with httpx.Client(base_url="http://localhost:8000") as c:
        yield c
