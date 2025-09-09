#!/usr/bin/env bash

# print a trace showing the commands being run
set -x

npx @tailwindcss/cli --input app/frontend/static/tailwind.input.css --output app/frontend/static/tailwind.css "$@"