#!/usr/bin/env bash

# exit script at first failure
set -e
# print a trace showing the commands being run
set -x

uv run coverage run --source=app -m pytest
uv run coverage report --show-missing
uv run coverage html --title "${@-coverage}"
