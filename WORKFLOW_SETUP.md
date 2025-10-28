# GitHub Actions Workflow Setup

The workflow file needs to be added to enable automated scraping on a schedule.

## Add via GitHub Web Interface

1. Go to https://github.com/Shamrock2245/sarasota-scraper-gas
2. Click "Add file" → "Create new file"
3. Name the file: `.github/workflows/scraper.yml`
4. Paste the following content:

```yaml
name: Sarasota County Scraper

on:
  # Run daily at 6 AM UTC (adjust as needed)
  schedule:
    - cron: '0 6 * * *'
  
  # Allow manual trigger
  workflow_dispatch:
    inputs:
      date:
        description: 'Date to scrape (YYYY-MM-DD) - leave empty for yesterday'
        required: false
        type: string

jobs:
  scrape:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Install Playwright browsers
      run: |
        playwright install chromium
        playwright install-deps chromium
    
    - name: Create credentials file from secret
      env:
        GOOGLE_CREDENTIALS: ${{ secrets.GOOGLE_CREDENTIALS }}
      run: |
        echo "$GOOGLE_CREDENTIALS" > credentials.json
    
    - name: Run scraper
      run: |
        if [ -n "${{ github.event.inputs.date }}" ]; then
          python sarasota_scraper.py --date "${{ github.event.inputs.date }}"
        else
          python sarasota_scraper.py --date $(date -d "yesterday" +%Y-%m-%d)
        fi
    
    - name: Clean up credentials
      if: always()
      run: |
        rm -f credentials.json
```

5. Commit the file

## After Adding the Workflow

### 1. Add Google Credentials Secret

1. Go to repository Settings → Secrets and variables → Actions
2. Add a new secret:
   - Name: `GOOGLE_CREDENTIALS`
   - Value: Contents of your `credentials.json` file
3. Click "Add secret"

### 2. Verify Workflow

1. Go to the Actions tab to verify the workflow is available
2. You should see "Sarasota County Scraper" in the workflows list

### 3. Manual Trigger Test

1. Click on "Sarasota County Scraper" workflow
2. Click "Run workflow" button
3. Optionally enter a specific date (YYYY-MM-DD format)
4. Click "Run workflow"
5. Monitor the execution in the workflow run page

## Schedule Options

The cron expression `'0 6 * * *'` runs daily at 6 AM UTC. You can adjust this:

- `0 6 * * *` - Daily at 6 AM UTC
- `0 */6 * * *` - Every 6 hours
- `0 9 * * 1-5` - Weekdays at 9 AM UTC
- `0 0 * * *` - Daily at midnight UTC
- `0 12 * * *` - Daily at noon UTC

### Convert to Your Timezone

If you want to run at 6 AM Eastern Time (ET):
- EST (UTC-5): `0 11 * * *` (11 AM UTC = 6 AM EST)
- EDT (UTC-4): `0 10 * * *` (10 AM UTC = 6 AM EDT)

## Workflow Features

### Automatic Daily Scraping

The workflow automatically runs daily and scrapes **yesterday's** arrests. This ensures:
- Data is complete (full day has passed)
- Avoids partial data from "today"
- Consistent timing

### Manual Trigger with Custom Date

You can manually trigger the workflow and specify any date:
1. Go to Actions → Sarasota County Scraper
2. Click "Run workflow"
3. Enter a date like `2025-10-28`
4. Click "Run workflow"

### Error Handling

The workflow includes:
- Automatic retry logic (built into the scraper)
- Credential cleanup (always runs, even on failure)
- Error logging in the workflow run

## Monitoring

### Check Workflow Status

1. Go to the Actions tab
2. Click on the latest workflow run
3. Review the logs for each step

### Email Notifications

GitHub automatically sends email notifications for:
- Failed workflow runs
- First successful run after failures

You can configure this in: Settings → Notifications → Actions

## Troubleshooting

### Workflow doesn't appear

- Ensure the file is in `.github/workflows/` directory
- Check that the YAML syntax is valid
- Refresh the Actions tab

### Workflow fails immediately

- Check that `GOOGLE_CREDENTIALS` secret is set
- Verify the secret contains valid JSON
- Review the workflow logs for specific errors

### Playwright installation fails

The workflow includes `playwright install-deps` which installs system dependencies. If this fails:
- Check the Ubuntu version in `runs-on`
- Review Playwright documentation for system requirements

### Scraper finds no data

- The website structure may have changed
- Run the scraper locally with `--headful` to debug
- Update selectors in `sarasota_scraper.py`

## Advanced Configuration

### Run Multiple Times Per Day

```yaml
schedule:
  - cron: '0 6,18 * * *'  # 6 AM and 6 PM UTC
```

### Run on Weekdays Only

```yaml
schedule:
  - cron: '0 6 * * 1-5'  # Monday through Friday
```

### Add Slack/Discord Notifications

You can add notification steps to alert you of successes/failures:

```yaml
- name: Notify on success
  if: success()
  run: |
    # Add your notification command here
    echo "Scraper completed successfully"
```

## Cost Considerations

GitHub Actions is free for public repositories with generous limits:
- 2,000 minutes/month for free accounts
- Unlimited for public repositories

This workflow typically uses 2-5 minutes per run, so daily runs are well within limits.
