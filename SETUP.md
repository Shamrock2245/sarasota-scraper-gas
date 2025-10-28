# Detailed Setup Guide

## Prerequisites

- Python 3.11 or higher
- Git
- Google Cloud account
- GitHub account

## Step-by-Step Setup

### 1. Google Cloud Setup

#### Create a Google Cloud Project

1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Name it "Sarasota-Scraper" (or your preferred name)
4. Click "Create"

#### Enable Google Sheets API

1. In the Google Cloud Console, go to "APIs & Services" → "Library"
2. Search for "Google Sheets API"
3. Click on it and press "Enable"

#### Create Service Account

1. Go to "APIs & Services" → "Credentials"
2. Click "+ CREATE CREDENTIALS" → "Service Account"
3. Fill in the details:
   - Service account name: `sarasota-scraper`
   - Service account ID: (auto-generated)
   - Click "Create and Continue"
4. Skip the optional steps (Grant access, Grant users access)
5. Click "Done"

#### Generate Service Account Key

1. In the Credentials page, find your service account under "Service Accounts"
2. Click on the service account email
3. Go to the "Keys" tab
4. Click "Add Key" → "Create new key"
5. Select "JSON" format
6. Click "Create"
7. The JSON file will download automatically
8. **Important**: Rename this file to `credentials.json`

#### Share Google Sheet with Service Account

1. Open the downloaded `credentials.json` file
2. Find the `client_email` field (looks like: `sarasota-scraper@project-id.iam.gserviceaccount.com`)
3. Copy this email address
4. Open your Google Sheet:
   - [Sarasota County Sheet](https://docs.google.com/spreadsheets/d/14UfXJom1i9B9nfTiC0rzelDHM8mGJzw0pnoFxTyGpGo)
5. Click "Share" button
6. Paste the service account email
7. Set permission to "Editor"
8. Uncheck "Notify people"
9. Click "Share"

### 2. Local Development Setup

#### Clone the Repository

```bash
git clone https://github.com/Shamrock2245/sarasota-scraper-gas.git
cd sarasota-scraper-gas
```

#### Create Virtual Environment (Recommended)

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

#### Install Python Dependencies

```bash
pip install -r requirements.txt
```

#### Install Playwright Browsers

```bash
playwright install chromium
```

This downloads the Chromium browser that Playwright will use for automation.

#### Add Credentials

1. Copy your `credentials.json` file to the project root directory
2. Verify it's in the `.gitignore` file (it should be)

#### Test the Scraper

```bash
# Test with today's date
python sarasota_scraper.py --date $(date +%Y-%m-%d)

# Or test with a specific date
python sarasota_scraper.py --date 2025-10-28

# Watch it run (opens browser window)
python sarasota_scraper.py --date 2025-10-28 --headful
```

### 3. GitHub Actions Setup (Automated Scheduling)

#### Add Google Credentials as GitHub Secret

1. Go to your GitHub repository: https://github.com/Shamrock2245/sarasota-scraper-gas
2. Click "Settings" → "Secrets and variables" → "Actions"
3. Click "New repository secret"
4. Name: `GOOGLE_CREDENTIALS`
5. Value: Paste the **entire contents** of your `credentials.json` file
6. Click "Add secret"

#### Add Workflow File

See `WORKFLOW_SETUP.md` for instructions on adding the GitHub Actions workflow file.

The workflow will:
- Run daily at 6 AM UTC
- Can be triggered manually from the Actions tab
- Install all dependencies including Playwright
- Run the scraper for yesterday's date
- Upload results to Google Sheets
- Clean up credentials after execution

### 4. Customization

#### Adjust Schedule

Edit `.github/workflows/scraper.yml`:

```yaml
schedule:
  - cron: '0 6 * * *'  # Change this line
```

Cron format: `minute hour day month weekday`

Examples:
- `0 6 * * *` - Daily at 6 AM UTC
- `0 */6 * * *` - Every 6 hours
- `0 9 * * 1-5` - Weekdays at 9 AM UTC

#### Update Selectors

If the website structure changes, update `SELECTOR_HINTS` in `sarasota_scraper.py`:

```python
SELECTOR_HINTS = {
    "date_inputs": [
        'input[type="date"]',
        # Add new selectors here
    ],
    "search_buttons": [
        'button:has-text("Search")',
        # Add new selectors here
    ],
    # ... etc
}
```

#### Change Google Sheet

Update these variables in `sarasota_scraper.py`:

```python
GOOGLE_SHEET_ID = 'your-sheet-id'
WORKSHEET_NAME = 'your-tab-name'
```

### 5. Advanced Usage

#### Scrape Date Ranges

```bash
# Scrape the last 7 days
python sarasota_scraper.py --start $(date -d "7 days ago" +%Y-%m-%d) --end $(date +%Y-%m-%d)

# Scrape a specific range
python sarasota_scraper.py --start 2025-10-01 --end 2025-10-31
```

#### Export to JSON

```bash
# Save to file without uploading to Sheets
python sarasota_scraper.py --date 2025-10-28 --no-upload --output arrests.json
```

#### Debugging

```bash
# Run with visible browser to see what's happening
python sarasota_scraper.py --date 2025-10-28 --headful

# Check Playwright installation
playwright --version

# Reinstall browsers if needed
playwright install --force chromium
```

## Troubleshooting

### Scraper fails to load data

- Check if the website is accessible
- Verify the ENTRY_URL is correct
- Run with `--headful` to see browser behavior
- Check if selectors need updating

### Google Sheets upload fails

- Verify the service account email has Editor access to the sheet
- Check that the sheet ID is correct
- Ensure the worksheet/tab name matches exactly
- Verify credentials.json is valid JSON

### GitHub Actions fails

- Check that `GOOGLE_CREDENTIALS` secret is set correctly
- Review the Actions log for specific error messages
- Ensure the secret contains valid JSON
- Verify Playwright installation step completes

### Playwright errors

```bash
# Clear Playwright cache and reinstall
rm -rf ~/.cache/ms-playwright
playwright install chromium

# Or use system browser (if available)
playwright install-deps
```

## Security Best Practices

1. **Never commit credentials.json** - It's in `.gitignore` for a reason
2. **Use GitHub Secrets** - For automated workflows
3. **Rotate credentials** - If accidentally exposed
4. **Limit permissions** - Service account should only have Sheets access
5. **Monitor usage** - Check Google Cloud Console for unexpected activity
6. **Use environment variables** - For production deployments

## Performance Tips

1. **Use date ranges wisely** - Scraping large date ranges can take time
2. **Respect the website** - Add delays between requests if needed
3. **Monitor rate limits** - Some sites may block excessive requests
4. **Use headless mode** - Faster and uses less resources
5. **Cache results** - Save to JSON for backup/analysis

## Support

For issues or questions, please open an issue on GitHub.
