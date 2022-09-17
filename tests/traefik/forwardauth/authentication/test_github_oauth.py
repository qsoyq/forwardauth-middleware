from fastapi.testclient import TestClient

from tests import client


def test_github_oauth(client: TestClient):
    endpoint = '/traefik/forwardauth/authentication/github'
    forward_request_headers = {
        'X-Forwarded-Method': 'get',
        'X-Forwarded-Proto': 'http',
        'X-Forwarded-Host': 'localhost',
        'X-Forwarded-Uri': f"{endpoint}",
        "X-Forwarded-For": "127.0.0.1",
    }
    params = {"use_whitelist": False}
    res = client.get(endpoint, headers=forward_request_headers, params=params, allow_redirects=False)
    assert res.status_code == 307, res.text
    assert res.headers.get('location'), res.headers
