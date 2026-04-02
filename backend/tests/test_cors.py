from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.main import app


class CorsMiddlewareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def test_obsidian_preflight_to_health_is_allowed(self) -> None:
        response = self.client.options(
            "/health",
            headers={
                "Origin": "app://obsidian.md",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "content-type",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            response.headers.get("access-control-allow-origin"),
            {"*", "app://obsidian.md"},
        )
        allow_headers = response.headers.get("access-control-allow-headers", "")
        self.assertTrue(
            allow_headers == "*" or "content-type" in allow_headers.lower()
        )


if __name__ == "__main__":
    unittest.main()
