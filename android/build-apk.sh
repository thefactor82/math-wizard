#!/bin/bash
# Build the Math Wizard APK with Buildozer in Docker.
# Run this from a Linux/WSL2 shell inside the project root (the repo root,
# where buildozer.spec lives). The image caches SDK/NDK under ~/.buildozer
# so subsequent builds are much faster.
#
# Usage:
#   android/build-apk.sh          -> debug APK (arch from buildozer.spec, arm64-v8a)
#   REL=1 android/build-apk.sh    -> release (signed) APK
#
# For the Android emulator, temporarily set android.archs = x86_64 in buildozer.spec.
# The APK is written to bin/ inside the project.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="kivy/buildozer-math-wizard"

if [ "${REL:-0}" = "1" ]; then
    CMD="android release"
else
    CMD="android debug"
fi

echo ">> Building image (first time only)..."
docker build --tag "$IMAGE" "$ROOT"

echo ">> Building APK (command='$CMD')..."
mkdir -p "$HOME/.buildozer" "$HOME/.gradle"

docker run --rm \
  -u "$(id -u):$(id -g)" \
  -v "$HOME/.buildozer":/home/user/.buildozer \
  -v "$HOME/.gradle":/home/user/.gradle \
  -v "$ROOT":/home/user/hostcwd \
  "$IMAGE" -v $CMD

echo ">> Done. APK:"
ls -lh "$ROOT/bin"/*.apk
