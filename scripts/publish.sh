#!/usr/bin/env bash
set -euo pipefail

echo "Starting the streetview-dl publishing process..."
echo "============================================="

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

VERSION="$(python -c "from streetview_dl import __version__; print(__version__)")"

if [[ -z "${VERSION}" ]]; then
    echo "Error: Could not determine version from streetview_dl/__init__.py" >&2
    exit 1
fi

echo "You are about to publish version '${VERSION}'."
echo

echo "--- Git Status Check ---"
if ! git diff-index --quiet HEAD --; then
    echo "Warning: Uncommitted changes detected."
    read -p "Continue anyway? (y/n) " -n 1 -r; echo
    [[ $REPLY =~ ^[Yy]$ ]] || { echo "Cancelled."; exit 1; }
fi

echo "--- Pre-flight Checklist ---"
read -p "Have you updated CHANGELOG.md? (y/n) " -n 1 -r; echo
[[ $REPLY =~ ^[Yy]$ ]] || { echo "Cancelled."; exit 1; }

read -p "Have you updated README.md? (y/n) " -n 1 -r; echo
[[ $REPLY =~ ^[Yy]$ ]] || { echo "Cancelled."; exit 1; }

read -p "Have you tested the CLI locally? (y/n) " -n 1 -r; echo
[[ $REPLY =~ ^[Yy]$ ]] || { echo "Cancelled."; exit 1; }

echo "Cleaning old builds..."
rm -rf build dist *.egg-info

echo "Building..."
python -m build

echo "Build complete:"
ls -l dist | cat
echo

echo "What would you like to do?"
select choice in "Publish to TestPyPI" "Publish to PyPI (Official)" "Cancel"; do
    case $choice in
        "Publish to TestPyPI")
            [[ -n "${PYPI_TEST:-}" ]] || { echo "Error: PYPI_TEST is not set"; exit 1; }
            python -m twine upload --repository-url https://test.pypi.org/legacy/ -u __token__ -p "$PYPI_TEST" dist/*
            echo "✅ Published to TestPyPI: https://test.pypi.org/project/streetview-dl/${VERSION}/"
            break;;
        "Publish to PyPI (Official)")
            read -p "Publish to OFFICIAL PyPI? (y/n) " -n 1 -r; echo
            [[ $REPLY =~ ^[Yy]$ ]] || { echo "Cancelled."; exit 1; }
            [[ -n "${PYPI:-}" ]] || { echo "Error: PYPI is not set"; exit 1; }
            python -m twine upload -u __token__ -p "$PYPI" dist/*
            echo "✅ Published to PyPI: https://pypi.org/project/streetview-dl/${VERSION}/"
            break;;
        "Cancel")
            echo "Cancelled."; break;;
        *) echo "Invalid option";;
    esac
done

echo "============================================="
echo "Done."
