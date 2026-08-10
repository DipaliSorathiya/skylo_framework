#!/bin/bash

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

cd "$PROJECT_ROOT"

echo "=============================================="
echo "QA Automation Framework"
echo "=============================================="

echo ""
echo "Checking Python..."

python3 --version

echo ""
echo "Checking virtual environment..."

if [ ! -d "venv" ]; then

    echo "Creating virtual environment..."

    python3 -m venv venv

fi

echo ""
echo "Activating virtual environment..."

source venv/bin/activate

echo ""
echo "Installing dependencies..."

pip install -q -r requirements.txt

echo ""
echo "Running framework..."

python run.py \
    --log logs/bs_log2.txt \
    --min-rate 90