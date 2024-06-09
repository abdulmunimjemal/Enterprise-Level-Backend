from httpx import Response
from starlette.testclient import TestClient


def make_request(client: TestClient, endpoint: str) -> Response:
    return client.get(endpoint)
