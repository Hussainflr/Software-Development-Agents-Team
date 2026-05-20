from __future__ import annotations

import re
from dataclasses import dataclass, field


ROUTE_PATTERN = re.compile(r"@app\.(?:get|post|put|patch|delete)\(\s*[\"']([^\"']+)[\"']")
FRONTEND_CALL_PATTERN = re.compile(r"requests\.(?:get|post|put|patch|delete)\(\s*f?[\"'][^\"']*\{?API_URL\}?([^\"']*)[\"']")
TEST_CALL_PATTERN = re.compile(r"client\.(?:get|post|put|patch|delete)\(\s*[\"']([^\"']+)[\"']")


@dataclass(frozen=True)
class EndpointConsistencyResult:
    passed: bool
    backend_routes: set[str] = field(default_factory=set)
    referenced_routes: set[str] = field(default_factory=set)
    missing_routes: set[str] = field(default_factory=set)

    @property
    def summary(self) -> str:
        if self.passed:
            return "Endpoint consistency passed."
        missing = ", ".join(sorted(self.missing_routes))
        return f"Endpoint consistency failed. Referenced routes missing from backend: {missing}."


class EndpointConsistencyChecker:
    """Checks that frontend/test API references exist in generated backend routes."""

    def check(self, artifacts: dict[str, str]) -> EndpointConsistencyResult:
        backend = artifacts.get("generated_backend/main.py", "")
        frontend = artifacts.get("generated_frontend/app.py", "")
        tests = "\n\n".join(
            content for path, content in artifacts.items() if path.startswith("generated_tests/") and path.endswith(".py")
        )

        backend_routes = {self._normalize_route(route) for route in ROUTE_PATTERN.findall(backend)}
        frontend_routes = {self._normalize_route(route) for route in FRONTEND_CALL_PATTERN.findall(frontend)}
        test_routes = {self._normalize_route(route) for route in TEST_CALL_PATTERN.findall(tests)}
        referenced_routes = {route for route in frontend_routes | test_routes if route}

        missing = {
            route
            for route in referenced_routes
            if not self._route_is_declared(route, backend_routes)
        }
        return EndpointConsistencyResult(
            passed=not missing,
            backend_routes=backend_routes,
            referenced_routes=referenced_routes,
            missing_routes=missing,
        )

    @staticmethod
    def _normalize_route(route: str) -> str:
        cleaned = route.strip()
        if not cleaned.startswith("/"):
            cleaned = f"/{cleaned}"
        cleaned = cleaned.split("?")[0]
        return re.sub(r"/+$", "", cleaned) or "/"

    @staticmethod
    def _route_is_declared(route: str, backend_routes: set[str]) -> bool:
        if route in backend_routes:
            return True
        for backend_route in backend_routes:
            pattern = re.sub(r"\{[^/]+\}", r"[^/]+", backend_route)
            if re.fullmatch(pattern, route):
                return True
        return False
