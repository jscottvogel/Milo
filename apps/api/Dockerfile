FROM public.ecr.aws/lambda/python:3.12

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create a working directory
WORKDIR /var/task

# Copy workspace config
COPY pyproject.toml uv.lock ./

# Copy all packages and apps
COPY packages/ packages/
COPY apps/ apps/

# Install dependencies system-wide for Lambda by exporting from the lockfile
RUN uv export --no-dev > requirements.txt && uv pip install --system -r requirements.txt

# We must set PYTHONPATH so Lambda can find our modules
ENV PYTHONPATH=/var/task/apps/api:/var/task/packages/db:/var/task/packages/shared-schemas:/var/task/packages/agent

# Set the CMD to your handler (path relative to PYTHONPATH or module path)
CMD ["apps.api.lambda_handler.handler"]
