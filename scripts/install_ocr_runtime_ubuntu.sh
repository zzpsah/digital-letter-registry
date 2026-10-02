#!/usr/bin/env bash
set -euo pipefail

if ! command -v apt-get >/dev/null 2>&1; then
  echo "This installer supports Debian/Ubuntu apt runtimes only." >&2
  exit 2
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Installing OCR runtime packages (sudo authorization may be required)..."
sudo apt-get update
sudo apt-get install -y \
  tesseract-ocr \
  tesseract-ocr-hin \
  tesseract-ocr-eng \
  ocrmypdf

echo
echo "Verifying OCR runtime..."
PYTHONPATH="$repo_root/src" python3 "$repo_root/scripts/check_runtime_dependencies.py"
