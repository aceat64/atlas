#!/usr/bin/env bash

# print a trace showing the commands being run
set -x

uv run mypy .
uv run ruff check .
uv run ruff format . --check
