#!/usr/bin/env python3
"""
Sarasota County Sheriff's Office Arrest Scraper - Version 2
Handles iframe-based search interface
"""
import argparse
import json
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
import gspread
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configuration
ENTRY_URL = "https://www.sarasotasheriff.org/arrest-reports/index.php"
GOOGLE_SHEET_ID = "14UfXJom1i9B9nfTiC0rzelDHM8mGJzw0pnoFxTyGpGo"
WORKSHEET_NAME = "Sarasota County"

def print_status(message: str, emoji: str = "🔍"):
    """Print formatted status message"""
    print(f"{emoji} {message}")

def print_error(message: str):
    """Print formatted error message"""
    print(f"❌ {message}")

def print_success(message: str):
    """Print formatted success message"""
    print(f"✅ {message}")

@retry(
    reraise=True,
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=1, max=6),
    retry=retry_if_exception_type(PWTimeoutError),
)
def scrape_for_date(date_str: str, headless: bool = True) -> List[Dict]:
    """
    Scrape arrests for a specific date using iframe-based interface
    """
    print_status(f"Scraping arrests for {date_str}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ]
        )
        
        # Create context with realistic settings
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='America/New_York'
        )
        
        page = context.new_page()
        
        try:
            # Navigate to main page
            print_status("Loading main page...")
            page.goto(ENTRY_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(3000)  # Give page time to settle
            
            # Wait for iframe to appear
            print_status("Waiting for search iframe...")
            page.wait_for_selector('iframe', timeout=30000)
            
            # Get all iframes
            iframes = page.frames
            print_status(f"Found {len(iframes)} frames on page")
            
            # Find the iframe with the search interface
            search_frame = None
            for frame in iframes:
                try:
                    # Check if this frame has the search interface
                    if frame.locator('input[placeholder*="date"]').count() > 0:
                        search_frame = frame
                        print_success("Found search interface iframe!")
                        break
                except:
                    continue
            
            if not search_frame:
                # Try alternate approach - look for iframe by src
                print_status("Trying alternate iframe detection...")
                iframe_element = page.query_selector('iframe')
                if iframe_element:
                    src = iframe_element.get_attribute('src')
                    print_status(f"Iframe src: {src}")
                    # Wait for iframe content to load
                    page.wait_for_timeout(5000)
                    search_frame = page.frame(iframe_element.get_attribute('name') or src)
            
            if not search_frame:
                raise Exception("Could not find search interface iframe")
            
            # Now work within the iframe
            print_status("Interacting with search form...")
            
            # Convert date format from YYYY-MM-DD to MM/DD/YYYY
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%m/%d/%Y")
            
            # Find and fill the date input
            date_input = search_frame.locator('input[type="date"], input[placeholder*="date"]').first
            date_input.fill(formatted_date)
            print_status(f"Entered date: {formatted_date}")
            
            # Click search button
            search_button = search_frame.locator('button:has-text("SEARCH"), input[type="submit"]').first
            search_button.click()
            print_status("Clicked search button")
            
            # Wait for results to load
            print_status("Waiting for results...")
            page.wait_for_timeout(5000)
            
            # Try to extract results from the iframe
            results = []
            
            # Look for table rows
            rows = search_frame.locator('table tr, .result-row, .inmate-row').all()
            print_status(f"Found {len(rows)} potential result rows")
            
            for row in rows:
                try:
                    text = row.inner_text()
                    if text and len(text) > 10:  # Skip empty or header rows
                        # Extract data - this will need to be adjusted based on actual structure
                        results.append({
                            "arrest_date": date_str,
                            "raw_text": text,
                            "scraped_at": datetime.now().isoformat()
                        })
                except:
                    continue
            
            # If no structured results, try to get all text content
            if not results:
                print_status("No structured results found, extracting all text...")
                all_text = search_frame.locator('body').inner_text()
                if "no results" not in all_text.lower() and len(all_text) > 100:
                    # Split by lines and look for data
                    lines = [l.strip() for l in all_text.split('\n') if l.strip()]
                    for line in lines:
                        if len(line) > 20:  # Likely contains data
                            results.append({
                                "arrest_date": date_str,
                                "raw_text": line,
                                "scraped_at": datetime.now().isoformat()
                            })
            
            print_success(f"Extracted {len(results)} records")
            return results
            
        except Exception as e:
            print_error(f"[{date_str}] ERROR: {str(e)}")
            raise
        finally:
            browser.close()

def upload_to_sheets(data: List[Dict], sheet_id: str, worksheet_name: str):
    """Upload data to Google Sheets"""
    if not data:
        print_status("No data to upload")
        return
    
    print_status(f"Uploading {len(data)} records to Google Sheets...")
    
    try:
        gc = gspread.service_account(filename='credentials.json')
        sheet = gc.open_by_key(sheet_id)
        
        try:
            worksheet = sheet.worksheet(worksheet_name)
        except:
            worksheet = sheet.add_worksheet(title=worksheet_name, rows=1000, cols=20)
            print_success(f"Created new worksheet: {worksheet_name}")
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Get existing data
        existing = worksheet.get_all_records()
        
        if existing:
            # Append to existing data
            worksheet.append_rows(df.values.tolist())
        else:
            # Write headers and data
            worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        
        print_success(f"Successfully uploaded {len(data)} records to Google Sheets!")
        
    except Exception as e:
        print_error(f"Failed to upload to Google Sheets: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Scrape Sarasota County arrest records")
    parser.add_argument("--date", help="Date to scrape (YYYY-MM-DD)")
    parser.add_argument("--headful", action="store_true", help="Run browser in visible mode")
    parser.add_argument("--no-upload", action="store_true", help="Don't upload to Google Sheets")
    parser.add_argument("--output", help="Save results to JSON file")
    
    args = parser.parse_args()
    
    # Default to yesterday if no date provided
    if not args.date:
        yesterday = datetime.now() - timedelta(days=1)
        args.date = yesterday.strftime("%Y-%m-%d")
    
    print("=" * 60)
    print("Sarasota County Arrest Scraper v2")
    print("=" * 60)
    print()
    
    try:
        # Scrape data
        results = scrape_for_date(args.date, headless=not args.headful)
        
        print()
        print(f"📊 Total records scraped: {len(results)}")
        print()
        
        # Save to JSON if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print_success(f"Saved results to {args.output}")
        
        # Upload to Google Sheets unless disabled
        if not args.no_upload and results:
            upload_to_sheets(results, GOOGLE_SHEET_ID, WORKSHEET_NAME)
        
        print()
        print("✨ Sarasota County Scraper completed successfully! ✨")
        return 0
        
    except Exception as e:
        print()
        print_error(f"Scraper failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
