#!/usr/bin/env bash

# print a trace showing the commands being run
set -x

uv run mypy app
uv run ruff check app
uv run ruff format app --check
