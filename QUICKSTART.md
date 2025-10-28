# Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites

- Python 3.11 or higher
- Git
- Google Service Account (see SETUP.md for details)

## Installation

### Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/Shamrock2245/sarasota-scraper-gas.git
cd sarasota-scraper-gas

# Run the quick start script
./quick_start.sh
```

### Option 2: Manual Setup

```bash
# Clone the repository
git clone https://github.com/Shamrock2245/sarasota-scraper-gas.git
cd sarasota-scraper-gas

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
python3 -m playwright install chromium

# Test your setup
python3 test_setup.py
```

## Add Your Credentials

1. Get your `credentials.json` from Google Cloud Console (see SETUP.md)
2. Place it in the project root directory
3. The file is already in `.gitignore` so it won't be committed

## Test It Out

```bash
# Scrape a single date (no upload to test)
python3 sarasota_scraper.py --date 2025-10-28 --no-upload --output test.json

# Watch it run in a visible browser
python3 sarasota_scraper.py --date 2025-10-28 --headful --no-upload

# Run for real (uploads to Google Sheets)
python3 sarasota_scraper.py --date 2025-10-28
```

## Using Make Commands

If you have `make` installed:

```bash
make help        # Show all available commands
make setup       # Install everything
make test        # Test scraper without uploading
make run         # Run scraper for yesterday
make clean       # Clean up temporary files
```

## VSCode Setup

If you use VSCode:

1. Open the project folder
2. Install recommended extensions (Python, Pylance, etc.)
3. Press F5 to run with debugger
4. Choose from pre-configured launch options:
   - Scrape Today
   - Scrape Today (Headful)
   - Test Setup

## Verify Everything Works

```bash
python3 test_setup.py
```

This will check:
- ✓ All Python packages installed
- ✓ Playwright browser installed
- ✓ Credentials file present
- ✓ Google Sheets connection working

## Common Issues

### "playwright: command not found"

Use: `python3 -m playwright install chromium`

### "Permission denied" on scripts

Run: `chmod +x quick_start.sh test_setup.py`

### Can't connect to Google Sheets

1. Make sure `credentials.json` is in the project root
2. Verify the service account email has Editor access to the sheet
3. Check the sheet ID in `sarasota_scraper.py`

## Next Steps

- Read SETUP.md for detailed Google Cloud setup
- Read WORKFLOW_SETUP.md for GitHub Actions automation
- Customize selectors in `sarasota_scraper.py` if needed

## Daily Usage

```bash
# Scrape yesterday's arrests and upload
python3 sarasota_scraper.py --date $(date -d "yesterday" +%Y-%m-%d)

# Or use make
make run
```

## Need Help?

- Check SETUP.md for detailed instructions
- Run `python3 test_setup.py` to diagnose issues
- Open an issue on GitHub
