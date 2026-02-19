#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
STUDIO_DIR="$PROJECT_ROOT/src/studio"

if [ ! -d "$STUDIO_DIR" ]; then
    echo "Error: Flutter project not found at $STUDIO_DIR"
    exit 1
fi

cd "$STUDIO_DIR"

echo "Running Flutter app..."
flutter run
