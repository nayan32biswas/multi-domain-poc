#!/usr/bin/env bash

set -e
set -x

# mypy app static_app
uv run --extra dev ruff check app static_app
uv run --extra dev ruff format app static_app --check
