FROM python:3.12

ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  UV_REQUESTS_TIMEOUT=100 \
  UV_PROJECT_ENVIRONMENT=/usr/local

# Install uv
ADD https://astral.sh/uv/0.6.10/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

WORKDIR /code

COPY pyproject.toml uv.lock /code/

RUN uv sync --extra dev --locked

ADD . /code
