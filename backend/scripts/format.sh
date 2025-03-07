#!/usr/bin/env bash

# print a trace showing the commands being run
set -x

ruff check app scripts --fix
ruff format app scripts
