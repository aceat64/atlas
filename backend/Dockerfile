FROM python:3.13-slim AS builder

# Install uv
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:0.6.3 /uv /uvx /bin/

# Changing the default UV_LINK_MODE silences warnings about not being able to
# use hard links since the cache and sync target are on separate file systems.
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#caching
ENV UV_LINK_MODE=copy

# Compiling Python source files to bytecode is typically desirable for
# production images as it tends to improve startup time (at the cost of
# increased installation time).
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode
ENV UV_COMPILE_BYTECODE=1

WORKDIR /app

# Install dependencies, temporarily mounting pyproject.toml and uv.lock
RUN --mount=type=cache,target=/root/.cache/uv \
  --mount=type=bind,source=uv.lock,target=uv.lock \
  --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
  uv sync --frozen --no-install-project --no-dev

# Now copy over the project into the image. This is done separately from installing
# dependencies, so that changes to the project files won't invalidate the cache.
COPY . .
# !IMPORTANT!
# Files/folders that would bloat the image should be listed in .dockerignore

# We use COPY instead of ADD since we are only including files from our local context.
# Ref: https://www.docker.com/blog/docker-best-practices-understanding-the-differences-between-add-and-copy-instructions-in-dockerfiles/

# Sync the project (install it)
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-dev


FROM python:3.13-slim

RUN apt-get update && apt-get install --no-install-recommends -y libpq5=15.10-* \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Create the app user and group
RUN groupadd --gid 1000 app && \
  useradd --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin --uid 1000 --gid 1000 app

WORKDIR /app

# Copy the environment, but not the source code
COPY --from=builder --chown=app:app /app /app

# Switch to app user
USER app

ARG GIT_COMMIT

ENV \
  # The OTEL_RESOURCE_ATTRIBUTES environment variable allows resource attributes to be passed to the SDK at process invocation.
  # ref: https://opentelemetry-python.readthedocs.io/en/latest/sdk/environment_variables.html#opentelemetry.sdk.environment_variables.OTEL_RESOURCE_ATTRIBUTES
  OTEL_RESOURCE_ATTRIBUTES="service.git.commit=${GIT_COMMIT:-unknown}" \
  # Immediately write to stdout and stderr instead of buffering the output
  PYTHONUNBUFFERED=1 \
  # Add the app venv to $PATH
  PATH="/app/.venv/bin:${PATH}"

# The command that will be run:
ENTRYPOINT ["atlas-cli"]
# Default arguments if none are given:
CMD ["serve"]


### Container Image Metadata
# These aren't strictly needed, but they help provide info to tools that inspect this container image
EXPOSE 8080/tcp
EXPOSE 9090/tcp