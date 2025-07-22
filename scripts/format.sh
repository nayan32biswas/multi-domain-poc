#!/bin/sh -e

set -x

uv run --extra dev ruff check app cli --fix
uv run --extra dev ruff format app cli
