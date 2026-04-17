import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from mcp_memory_service.web.api.mcp import router
from mcp_memory_service.web.dependencies import set_storage
from mcp_memory_service.web.oauth.middleware import (
    AuthenticationResult,
    require_read_access,
)


class _DummyStorage:
    pass


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    set_storage(_DummyStorage())

    async def mock_auth():
        return AuthenticationResult(
            authenticated=True,
            client_id="test-client",
            scope="read write admin",
            auth_method="test",
        )

    app.dependency_overrides[require_read_access] = mock_auth

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_initialized_notification_returns_202_without_body(client):
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        },
    )

    assert response.status_code == 202
    assert response.content == b""


def test_unknown_request_still_returns_jsonrpc_method_not_found(client):
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "bogus/method",
            "params": {},
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "jsonrpc": "2.0",
        "id": 1,
        "error": {
            "code": -32601,
            "message": "Method not found: bogus/method",
        },
    }
