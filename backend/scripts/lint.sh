#!/usr/bin/env bash

# exit script at first failure
set -e
# print a trace showing the commands being run
set -x

mypy app
ruff check app
ruff format app --check
