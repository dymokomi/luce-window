#!/bin/sh
# Portable contract tests always run. GUI tests require a logged-in macOS desktop.
set -eu
cd "$(dirname "$0")/../../.."
mkdir -p build
exec python3 tests/programs/native_window/run.py "${1:-../luce-base/build/luce-base}"
