FROM python:3.12

# Environment variables (adjusted for uv)
ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  UV_REQUESTS_TIMEOUT=100

# Install uv
ADD https://astral.sh/uv/0.6.10/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

WORKDIR /code

# Copy dependency files
COPY pyproject.toml uv.lock /code/

# Install dependencies with uv
RUN uv sync --extra dev --locked --no-install-project --no-editable

# Copy the rest of the application code
ADD . /code
