#!/usr/bin/env python3
"""
Test script to verify the scraper setup is correct
"""
import sys
import os

def test_imports():
    """Test that all required packages are installed"""
    print("Testing imports...")
    try:
        import playwright
        print("  ✓ playwright installed")
    except ImportError:
        print("  ✗ playwright not installed - run: pip install -r requirements.txt")
        return False
    
    try:
        import pandas
        print("  ✓ pandas installed")
    except ImportError:
        print("  ✗ pandas not installed - run: pip install -r requirements.txt")
        return False
    
    try:
        import gspread
        print("  ✓ gspread installed")
    except ImportError:
        print("  ✗ gspread not installed - run: pip install -r requirements.txt")
        return False
    
    try:
        import tenacity
        print("  ✓ tenacity installed")
    except ImportError:
        print("  ✗ tenacity not installed - run: pip install -r requirements.txt")
        return False
    
    return True

def test_playwright_browser():
    """Test that Playwright browsers are installed"""
    print("\nTesting Playwright browser...")
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        print("  ✓ Chromium browser installed and working")
        return True
    except Exception as e:
        print(f"  ✗ Chromium browser not installed - run: python3 -m playwright install chromium")
        print(f"    Error: {e}")
        return False

def test_credentials():
    """Test that credentials file exists"""
    print("\nTesting credentials...")
    if os.path.exists('credentials.json'):
        print("  ✓ credentials.json found")
        try:
            import json
            with open('credentials.json', 'r') as f:
                creds = json.load(f)
            if 'client_email' in creds:
                print(f"  ✓ Service account email: {creds['client_email']}")
            else:
                print("  ⚠ credentials.json missing 'client_email' field")
            return True
        except Exception as e:
            print(f"  ✗ Error reading credentials.json: {e}")
            return False
    else:
        print("  ⚠ credentials.json not found")
        print("    This is needed for Google Sheets upload")
        print("    See SETUP.md for instructions")
        return False

def test_google_sheets():
    """Test Google Sheets connection"""
    print("\nTesting Google Sheets connection...")
    if not os.path.exists('credentials.json'):
        print("  ⚠ Skipping (no credentials.json)")
        return False
    
    try:
        import gspread
        gc = gspread.service_account(filename='credentials.json')
        sheet = gc.open_by_key('14UfXJom1i9B9nfTiC0rzelDHM8mGJzw0pnoFxTyGpGo')
        print(f"  ✓ Successfully connected to sheet: {sheet.title}")
        
        try:
            wks = sheet.worksheet('Sarasota County')
            print(f"  ✓ Found worksheet: {wks.title}")
        except:
            print("  ⚠ Worksheet 'Sarasota County' not found (will be created on first run)")
        
        return True
    except Exception as e:
        print(f"  ✗ Error connecting to Google Sheets: {e}")
        print("    Make sure the service account has access to the sheet")
        return False

def main():
    print("=" * 60)
    print("Sarasota County Scraper - Setup Test")
    print("=" * 60)
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("Playwright Browser", test_playwright_browser()))
    results.append(("Credentials", test_credentials()))
    results.append(("Google Sheets", test_google_sheets()))
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:.<40} {status}")
    
    all_passed = all(result[1] for result in results[:2])  # Only require imports and browser
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ Setup is ready! You can run the scraper.")
        print("\nNext steps:")
        print("  1. Add credentials.json if you haven't already")
        print("  2. Run: python3 sarasota_scraper.py --date 2025-10-28")
        return 0
    else:
        print("✗ Setup incomplete. Please fix the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
