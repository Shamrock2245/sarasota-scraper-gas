#!/bin/bash
# Quick start script for Sarasota County Scraper

echo "======================================"
echo "Sarasota County Scraper - Quick Start"
echo "======================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt
echo ""

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
python3 -m playwright install chromium
echo ""

# Check for credentials
if [ ! -f "credentials.json" ]; then
    echo "⚠️  credentials.json not found"
    echo ""
    echo "To complete setup:"
    echo "  1. Follow instructions in SETUP.md to create a Google Service Account"
    echo "  2. Download credentials.json and place it in this directory"
    echo "  3. Share your Google Sheet with the service account email"
    echo ""
    echo "Then run: python3 test_setup.py"
else
    echo "✓ credentials.json found"
    echo ""
    echo "Running setup test..."
    python3 test_setup.py
fi

echo ""
echo "======================================"
echo "Setup complete!"
echo "======================================"
echo ""
echo "Usage examples:"
echo "  python3 sarasota_scraper.py --date 2025-10-28"
echo "  python3 sarasota_scraper.py --start 2025-10-20 --end 2025-10-28"
echo "  python3 sarasota_scraper.py --date 2025-10-28 --headful"
echo ""
