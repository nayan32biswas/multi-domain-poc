#!/usr/bin/env bash

set -e
set -x

# mypy app cli
uv run --extra dev ruff check app cli
uv run --extra dev ruff format app cli --check
