from fastapi.testclient import TestClient

from tests import client


def test_settraceid(client: TestClient):
    endpoint = '/traefik/forwardauth/tracing/settraceid'
    res = client.get(endpoint)
    assert res.status_code == 200, res.text

    assert res.headers.get("X-Trace-Id"), res.headers
