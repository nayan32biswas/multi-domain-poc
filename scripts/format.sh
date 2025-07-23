#!/bin/sh -e

set -x

uv run --extra dev ruff check app static_app --fix
uv run --extra dev ruff format app static_app
