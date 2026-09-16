from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from rag_engine.api.error_handlers import register_error_handlers


def test_http_exception_headers_are_preserved():
    test_app = FastAPI()
    register_error_handlers(test_app)

    @test_app.get("/limited")
    async def limited():
        raise HTTPException(
            status_code=429,
            detail="Too many requests",
            headers={"Retry-After": "17", "X-RateLimit-Limit": "10"},
        )

    response = TestClient(test_app).get("/limited")

    assert response.status_code == 429
    assert response.headers["retry-after"] == "17"
    assert response.headers["x-ratelimit-limit"] == "10"
    assert response.json()["error"]["code"] == "rate_limited"
