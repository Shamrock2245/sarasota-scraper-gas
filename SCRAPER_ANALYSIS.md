# Sarasota Scraper Analysis - Timeout Issue

## Problem Summary

The scraper is timing out when trying to load the Sarasota Sheriff's arrest reports page. The workflow completes successfully but returns 0 records.

## Error Details

```
❌ [2025-10-27] ERROR: Timeout 30000ms exceeded.
🔍 Scraping arrests for 2025-10-27...
"load" event fired
📊 Total records scraped: 0
```

## Root Cause Analysis

### 1. **Page Load Timeout**
- The page is taking longer than 30 seconds to load
- Even with `wait_until="domcontentloaded"`, the page isn't becoming interactive
- The `networkidle` state is never reached

### 2. **Possible Causes**

#### A. Website Architecture Issues
- **JavaScript-heavy site**: The Sarasota Sheriff's site likely uses heavy client-side rendering
- **Dynamic content loading**: Arrest data may be loaded via AJAX/XHR after initial page load
- **API-based**: The site might fetch data from a backend API that we're not capturing

#### B. Bot Detection
- The site may detect Playwright/automation and intentionally slow down or block
- GitHub Actions IP addresses might be rate-limited or blocked
- User-agent detection might be triggering anti-bot measures

#### C. Incorrect Entry URL
- The URL `https://www.sarasotasheriff.org/arrest-reports/index.php` might not be the correct entry point
- The site structure may have changed
- There might be a redirect or different URL for the actual search interface

### 3. **What's Working**
- ✅ Playwright installation successful
- ✅ Browser launches correctly
- ✅ Page navigation initiates
- ✅ Credentials and Google Sheets connection ready
- ❌ Page never finishes loading/becomes interactive

## Proposed Solutions

### Solution 1: Investigate the Actual Website Structure
**Action**: Manually visit the site and inspect the network traffic
- Open https://www.sarasotasheriff.org/arrest-reports/ in a browser
- Open DevTools → Network tab
- Look for XHR/Fetch requests that load arrest data
- Identify the actual API endpoint being called
- Check if there's a direct JSON/API endpoint we can use instead

### Solution 2: Bypass the UI and Use Direct API
If the site has an API endpoint (likely), we can:
- Skip Playwright entirely
- Make direct HTTP requests to the API
- Parse JSON responses (much faster and more reliable)
- Example: Many sheriff sites use endpoints like `/api/arrests?date=2025-10-27`

### Solution 3: Improve Playwright Configuration
Add more anti-detection measures:
```python
browser = p.chromium.launch(
    headless=headless,
    args=[
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-web-security",
        "--disable-features=IsolateOrigins,site-per-process"
    ]
)
context = browser.new_context(
    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    viewport={'width': 1920, 'height': 1080},
    locale='en-US',
    timezone_id='America/New_York'
)
```

### Solution 4: Wait for Specific Elements Instead of Full Page Load
Instead of waiting for the entire page:
```python
# Wait for the specific arrest table/container
page.wait_for_selector('table#arrests', timeout=60000)
# Or wait for any table
page.wait_for_selector('table', timeout=60000)
```

### Solution 5: Use Selenium Instead of Playwright
Some sites work better with Selenium:
- Different fingerprint
- More mature anti-detection tools available
- Can use undetected-chromedriver

## Recommended Next Steps

### Immediate Actions (Tonight/Tomorrow)

1. **Manual Investigation** (5 minutes)
   - Visit https://www.sarasotasheriff.org/arrest-reports/
   - Check if the page loads normally
   - Look for actual arrest data
   - Inspect Network tab for API calls

2. **Test Locally** (10 minutes)
   ```bash
   cd sarasota-scraper-gas
   python3 sarasota_scraper.py --date 2025-10-27 --headful
   ```
   - Watch what happens in the browser
   - See if it's a bot detection issue
   - Check if selectors are correct

3. **Try Different URL** (5 minutes)
   - The site might have moved to a different URL
   - Try: https://www.sarasotasheriff.org/arrests
   - Try: https://www.sarasotasheriff.org/inmate-search
   - Try: https://www.sarasotasheriff.org/booking

### If API Endpoint is Found

Rewrite the scraper to use direct HTTP requests:
```python
import requests
from datetime import datetime

def scrape_via_api(date_str):
    url = f"https://www.sarasotasheriff.org/api/arrests?date={date_str}"
    response = requests.get(url)
    data = response.json()
    return data
```

This would be:
- ✅ 10x faster
- ✅ More reliable
- ✅ No timeout issues
- ✅ No bot detection
- ✅ Easier to maintain

### If No API Exists

Implement Solution 3 + 4:
- Add better anti-detection
- Wait for specific elements
- Increase timeouts even more
- Add retry logic with different strategies

## Testing Plan

1. **Local test with headful mode** - See what's happening
2. **Check for API endpoint** - Inspect network traffic
3. **Try different URLs** - Find the correct entry point
4. **Test with different user agents** - Bypass detection
5. **Add element-specific waits** - Don't wait for full page

## Files to Update

- `sarasota_scraper.py` - Main scraper logic
- `.github/workflows/scraper.yml` - May need environment variables
- `SELECTOR_HINTS` - Update if we find the correct selectors

## Notes

- The Hendry County scraper uses Selenium and works fine
- This suggests the issue is specific to how Playwright interacts with Sarasota's site
- We may need to switch to Selenium for consistency
- Or find the API endpoint and skip browser automation entirely

---

**Status**: Waiting for manual investigation of the actual website
**Priority**: High - Scraper currently non-functional
**Next Review**: After local testing with --headful mode
