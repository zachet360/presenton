from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from utils.get_env import get_api_secret_key_env, get_can_change_keys_env
from utils.user_config import update_env_with_user_config


class UserConfigEnvUpdateMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if get_can_change_keys_env() != "false":
            update_env_with_user_config()
        return await call_next(request)


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Optional Bearer token authentication for API endpoints.

    Only active when API_SECRET_KEY env var is set.
    Protects /api/v1/ppt/ endpoints.
    """

    # Paths that don't require auth (docs, health checks)
    EXEMPT_PATHS = {"/docs", "/openapi.json", "/redoc"}

    async def dispatch(self, request: Request, call_next):
        api_secret = get_api_secret_key_env()

        # If no API_SECRET_KEY is set, skip auth (backwards compatible)
        if not api_secret:
            return await call_next(request)

        path = request.url.path

        # Only protect /api/v1/ppt/ endpoints
        if not path.startswith("/api/v1/ppt/"):
            return await call_next(request)

        # Check exempt paths
        if path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Validate Bearer token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid Authorization header"},
            )

        token = auth_header[7:]  # Strip "Bearer "
        if token != api_secret:
            return JSONResponse(
                status_code=403,
                content={"detail": "Invalid API token"},
            )

        return await call_next(request)
