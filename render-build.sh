#!/usr/bin/env bash
# ==============================================================================
# Render.com Build Script for Loan Intelligence Platform
# ==============================================================================
set -o errexit

echo "==> [1/3] Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "==> [2/3] Building React + TypeScript Frontend..."
cd frontend
npm install
npm run build
cd ..

echo "==> [3/3] Checking Database and Baseline Data..."
if [ ! -f "loan_platform.db" ]; then
  echo "Database file not detected. Generating baseline synthetic dataset (starter profile)..."
  python generator/generate.py --profile starter
else
  echo "Operational database found (loan_platform.db)."
fi

echo "==> Build completed successfully! Ready for launch."
