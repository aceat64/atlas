#!/usr/bin/env bash

# exit script at first failure
set -e
# print a trace showing the commands being run
set -x

coverage run --source=app -m pytest
coverage report --show-missing
coverage html --title "${@-coverage}"
