#!/usr/bin/env bash

# print a trace showing the commands being run
set -x

mypy app
ruff check app
ruff format app --check
