# Sarasota County Arrest Scraper

This project scrapes arrest data from the Sarasota County Sheriff's Office arrest reports page and uploads it to Google Sheets.

## Workflow

VSCode → GitHub → Google Apps Script

## Features

- Scrapes arrest data from https://www.sarasotasheriff.org/arrest-reports/
- Uses Playwright for reliable browser automation (handles JavaScript-rendered content)
- Supports single date or date range scraping
- Automatically handles pagination and multiple page layouts
- Uploads data directly to Google Sheets
- Includes retry logic and error handling
- Can export to JSON for backup/analysis

## Technology Stack

- **Playwright**: Modern browser automation (more reliable than Selenium for dynamic sites)
- **Tenacity**: Automatic retry with exponential backoff
- **Pandas**: Data processing and CSV export
- **gspread**: Google Sheets API integration

## Setup Instructions

### 1. Google Service Account Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (e.g., "Sarasota-Scraper")
3. Enable the "Google Sheets API" for this project
4. Create Service Account Credentials:
   - Navigate to APIs & Services > Credentials
   - Click "Create Credentials" and choose "Service Account"
   - Give it a name (e.g., sheets-writer)
   - Download the generated JSON key file
5. Save the JSON file as `credentials.json` in the project root directory
6. Share your Google Sheet with the service account email (found in credentials.json as `client_email`) as an Editor

### 2. Local Development Setup

```bash
# Clone the repository
git clone https://github.com/Shamrock2245/sarasota-scraper-gas.git
cd sarasota-scraper-gas

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Add your credentials.json file to the project root

# Run the scraper
python sarasota_scraper.py --date 2025-10-28
```

### 3. Usage Examples

```bash
# Scrape a single date
python sarasota_scraper.py --date 2025-10-28

# Scrape a date range
python sarasota_scraper.py --start 2025-10-20 --end 2025-10-28

# Watch the browser (useful for debugging)
python sarasota_scraper.py --date 10/28/2025 --headful

# Save to JSON file without uploading to Sheets
python sarasota_scraper.py --date 2025-10-28 --no-upload --output arrests.json

# Scrape yesterday's arrests (useful for daily automation)
python sarasota_scraper.py --date $(date -d "yesterday" +%Y-%m-%d)
```

## Google Sheets

- **Sheet ID**: `14UfXJom1i9B9nfTiC0rzelDHM8mGJzw0pnoFxTyGpGo`
- **Sheet Name**: shamrock-leads-sarasota-county
- **Worksheet**: Sarasota County
- **Link**: [View Sheet](https://docs.google.com/spreadsheets/d/14UfXJom1i9B9nfTiC0rzelDHM8mGJzw0pnoFxTyGpGo)

## Deployment

This project is designed to run on a schedule. You can deploy it using:

- GitHub Actions (recommended for this workflow)
- Google Cloud Functions
- AWS Lambda
- Local cron job

### GitHub Actions Setup

A workflow file will be added to `.github/workflows/` to run the scraper on a schedule.

**Note**: Store your `credentials.json` as a GitHub Secret for security.

## Configuration

Edit the following variables in `sarasota_scraper.py`:

```python
ENTRY_URL = "https://www.sarasotasheriff.org/arrest-reports/index.php"
GOOGLE_SHEET_ID = '14UfXJom1i9B9nfTiC0rzelDHM8mGJzw0pnoFxTyGpGo'
WORKSHEET_NAME = 'Sarasota County'
```

## Why Playwright?

Playwright offers several advantages over Selenium:
- More reliable for JavaScript-heavy sites
- Better handling of modern web frameworks
- Built-in auto-waiting (reduces flaky tests)
- Faster execution
- Better debugging tools
- Native async support

## Security Notes

- Never commit `credentials.json` to the repository
- Use GitHub Secrets for storing credentials in CI/CD
- The `.gitignore` file is configured to exclude sensitive files

## Troubleshooting

### Scraper fails to find elements

- The site's HTML structure may have changed
- Update `SELECTOR_HINTS` in the script
- Run with `--headful` to see what's happening

### Google Sheets upload fails

- Verify the service account email has Editor access
- Check that the sheet ID is correct
- Ensure the worksheet name matches exactly

### Playwright installation issues

```bash
# Reinstall Playwright browsers
playwright install --force chromium
```

## License

MIT
