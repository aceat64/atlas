#!/usr/bin/env bash

# print a trace showing the commands being run
set -x

uv run ruff check . --fix
uv run ruff format .
