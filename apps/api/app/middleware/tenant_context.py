import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from db.session import db_session

class TenantContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        tenant_id = getattr(request.state, "tenant_id", None)
        
        # If no tenant ID is present (e.g., public endpoints), just continue
        if not tenant_id:
            return await call_next(request)

        # Set app.tenant_id for the database via db_session context manager
        # Since this is an async framework but db_session is synchronous context manager
        # and SQLAlchemy queries will be synchronous in Phase 1 setup (psycopg2/psycopg), 
        # we have to consider thread-safety. But FastAPI uses threadpools for sync endpoints.
        # However, BaseHTTPMiddleware runs async.
        # Wait, db_session yields a session, but how do we provide it to the route handlers?
        # A better pattern in FastAPI is using Depends(get_db) rather than middleware opening the session.
        # But Phase 2 spec says: 
        # "app/middleware/tenant_context.py that, after auth, sets app.tenant_id on the database session for the duration of the request via the db_session helper from Phase 1."
        
        try:
            with db_session(tenant_id) as session:
                request.state.db = session
                response = await call_next(request)
                return response
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise e
