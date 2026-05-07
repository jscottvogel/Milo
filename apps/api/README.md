# Milo API

FastAPI backend for the Milo Platform. 

## Local Development

The API uses `uv` for dependency management and runs on Python 3.12.

### Running Locally

You can spin up the development server on port 8000 using the Makefile target from the repository root:

```bash
make dev-api
```

This runs `uvicorn app.main:app --reload`.

### Authentication & Testing

The API expects a valid Amazon Cognito JWT. However, for local development, you can bypass the Cognito JWKS check by using a mock dev token.

Send a request with the header:
```
Authorization: Bearer dev_<tenant_id>
```
The authentication middleware will extract the tenant ID and simulate an authenticated request.

### Adding New Endpoints

When adding a new endpoint:
1. Define the router in `app/routers/` and include it in `app/main.py`.
2. Ensure the route requires authentication if appropriate (this is enforced automatically by the global `AuthMiddleware` unless explicitly excluded).
3. Any route making database queries must have `app.tenant_id` set via the `TenantContextMiddleware`. You can access the DB session from `request.state.db`.
4. Export the updated OpenAPI schema for the frontend:
   ```bash
   make export-openapi
   ```
