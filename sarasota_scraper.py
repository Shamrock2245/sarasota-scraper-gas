#!/usr/bin/env python3
"""
Sarasota County Arrest Scraper
Scrapes arrest data from Sarasota Sheriff's Office and uploads to Google Sheets
"""
import argparse
import json
import re
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import pandas as pd
import gspread

# Configuration
ENTRY_URL = "https://www.sarasotasheriff.org/arrest-reports/index.php"
CREDENTIALS_FILE = 'credentials.json'
GOOGLE_SHEET_ID = '14UfXJom1i9B9nfTiC0rzelDHM8mGJzw0pnoFxTyGpGo'
WORKSHEET_NAME = 'Sarasota County'

# Selector hints for Revize CMS
SELECTOR_HINTS = {
    "date_inputs": [
        'input[type="date"]',
        'input[name*="date" i]',
        'input[id*="date" i]',
        'input[aria-label*="Date" i]',
    ],
    "search_buttons": [
        'button:has-text("Search")',
        'button:has-text("Submit")',
        'button:has-text("Go")',
        'input[type="submit"]',
        'a:has-text("Search")',
    ],
    "result_containers": [
        "table",
        ".results",
        ".list", ".cards", ".card-list",
        '[role="table"]',
        '[data-component*="arrest" i]'
    ],
    "next_buttons": [
        'a:has-text("Next")',
        'button:has-text("Next")',
        'a[rel="next"]',
        'button:has-text("Load More")',
        'a:has-text("Load More")',
    ],
}


@dataclass
class ArrestRow:
    """Data structure for arrest records"""
    arrest_date: Optional[str] = None
    name: Optional[str] = None
    dob: Optional[str] = None
    age: Optional[str] = None
    charges: Optional[str] = None
    agency: Optional[str] = None
    booking_number: Optional[str] = None
    bond: Optional[str] = None
    arrest_time: Optional[str] = None
    source_url: Optional[str] = ENTRY_URL


def normalize_date(d: str) -> str:
    """Normalize date to YYYY-MM-DD format"""
    d = d.strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", d):
        return d
    if re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", d):
        return datetime.strptime(d, "%m/%d/%Y").strftime("%Y-%m-%d")
    raise ValueError(f"Unrecognized date format: {d}")


def daterange(start: str, end: str):
    """Generate date range"""
    s = datetime.strptime(normalize_date(start), "%Y-%m-%d")
    e = datetime.strptime(normalize_date(end), "%Y-%m-%d")
    step = timedelta(days=1)
    while s <= e:
        yield s.strftime("%Y-%m-%d")
        s += step


def try_fill_date(page, date_val: str) -> bool:
    """Try to fill date input fields"""
    for sel in SELECTOR_HINTS["date_inputs"]:
        matches = page.locator(sel)
        if matches.count() > 0:
            try:
                # Use JavaScript to set value and trigger events
                page.evaluate("""(s, v) => {
                    const el = document.querySelector(s);
                    if (!el) return;
                    el.value = v;
                    el.dispatchEvent(new Event('input', {bubbles:true}));
                    el.dispatchEvent(new Event('change', {bubbles:true}));
                }""", sel, date_val)
                
                # Also try mm/dd/yyyy format
                mmddyyyy = datetime.strptime(date_val, "%Y-%m-%d").strftime("%m/%d/%Y")
                page.evaluate("""(s, v) => {
                    const el = document.querySelector(s);
                    if (!el) return;
                    if (!el.value) {
                        el.value = v;
                        el.dispatchEvent(new Event('input', {bubbles:true}));
                        el.dispatchEvent(new Event('change', {bubbles:true}));
                    }
                }""", sel, mmddyyyy)
                return True
            except Exception:
                continue
    return False


def click_search(page) -> bool:
    """Try to click search/submit button"""
    for btn in SELECTOR_HINTS["search_buttons"]:
        loc = page.locator(btn)
        if loc.count() > 0:
            try:
                loc.first.click(timeout=3000)
                return True
            except Exception:
                continue
    
    # Fallback: press Enter on date field
    try:
        for sel in SELECTOR_HINTS["date_inputs"]:
            if page.locator(sel).count() > 0:
                page.locator(sel).first.press("Enter")
                return True
    except Exception:
        pass
    return False


def extract_rows_from_table(table_el) -> List[ArrestRow]:
    """Extract arrest data from HTML table"""
    headers = [h.inner_text().strip().lower() for h in table_el.locator("thead th, thead td").all()]
    rows = []
    
    for tr in table_el.locator("tbody tr").all():
        cells = [c.inner_text().strip() for c in tr.locator("td,th").all()]
        data = dict(zip(headers, cells))
        rows.append(
            ArrestRow(
                arrest_date=data.get("arrest date") or data.get("date"),
                name=data.get("name"),
                dob=data.get("dob") or data.get("date of birth"),
                age=data.get("age"),
                charges=data.get("charges") or data.get("charge"),
                agency=data.get("agency") or data.get("arresting agency"),
                booking_number=data.get("booking #") or data.get("booking number"),
                bond=data.get("bond"),
            )
        )
    return rows


def extract_rows_from_cards(container) -> List[ArrestRow]:
    """Extract arrest data from card/list layout"""
    items = container.locator(".card, .result, .list-item, li, .row")
    rows = []
    
    for it in items.all():
        text = it.inner_text()
        
        # Extract fields using regex patterns
        name = re.search(r"Name:\s*(.+)", text, re.I)
        arrest_date = re.search(r"Arrest\s*Date:\s*([0-9/\-: ]+)", text, re.I)
        dob = re.search(r"(DOB|Date of Birth):\s*([0-9/\-]+)", text, re.I)
        age = re.search(r"Age:\s*(\d{1,3})", text, re.I)
        booking = re.search(r"(Booking\s*(No\.|#|Number)):\s*([A-Za-z0-9\-]+)", text, re.I)
        agency = re.search(r"(Agency|Arresting Agency):\s*(.+)", text, re.I)
        bond = re.search(r"Bond:\s*([^\n]+)", text, re.I)
        
        charges = None
        ch = re.search(r"(Charge|Charges):\s*(.+)", text, re.I)
        if ch:
            charges = ch.group(2).strip()
        
        rows.append(
            ArrestRow(
                arrest_date=arrest_date.group(1).strip() if arrest_date else None,
                name=name.group(1).strip() if name else None,
                dob=dob.group(2).strip() if dob else None,
                age=age.group(1).strip() if age else None,
                charges=charges,
                agency=agency.group(2).strip() if agency else None,
                booking_number=(booking.group(3).strip() if booking else None),
                bond=bond.group(1).strip() if bond else None,
            )
        )
    return rows


def try_extract_rows(page) -> List[ArrestRow]:
    """Try to extract arrest rows from page"""
    # Try table first
    for sel in SELECTOR_HINTS["result_containers"]:
        loc = page.locator(sel)
        if loc.count() == 0:
            continue
        
        for el in loc.all():
            try:
                if el.evaluate("e => e.tagName && e.tagName.toLowerCase() === 'table'"):
                    if el.locator("tbody tr").count() > 0:
                        return extract_rows_from_table(el)
                else:
                    # Try card parsing
                    rows = extract_rows_from_cards(el)
                    if rows:
                        return rows
            except Exception:
                continue
    
    # Last resort: parse any table on page
    if page.locator("table").count() > 0:
        return extract_rows_from_table(page.locator("table").first)
    
    return []


def paginate(page):
    """Click through pagination"""
    while True:
        clicked = False
        for sel in SELECTOR_HINTS["next_buttons"]:
            btn = page.locator(sel)
            if btn.count() > 0 and btn.first.is_enabled():
                try:
                    btn.first.click(timeout=2000)
                    page.wait_for_timeout(800)
                    clicked = True
                    break
                except Exception:
                    continue
        if not clicked:
            break


def maybe_pick_quick_link(page):
    """Try to click quick link to arrests page"""
    for txt in ["Arrests & Inmates", "Arrests & Inmates Search", "Arrest Inquiry"]:
        link = page.locator(f'a:has-text("{txt}")')
        if link.count() > 0:
            try:
                link.first.click(timeout=2500)
                page.wait_for_load_state("networkidle")
                return True
            except Exception:
                pass
    return False


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=6),
    retry=retry_if_exception_type(PWTimeoutError),
)
def scrape_for_date(date_str: str, headless: bool = True) -> List[Dict]:
    """Scrape arrests for a specific date"""
    print(f"🔍 Scraping arrests for {date_str}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context()
        page = context.new_page()
        
        # Navigate to entry page
        page.goto(ENTRY_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_load_state("networkidle", timeout=30000)
        maybe_pick_quick_link(page)
        
        # Capture JSON responses
        json_payloads = []
        def handle_response(resp):
            try:
                ctype = resp.headers.get("content-type", "")
                if "application/json" in ctype.lower():
                    url = resp.url
                    if re.search(r"arrest|inmate|search|booking", url, re.I):
                        data = resp.json()
                        json_payloads.append({"url": url, "data": data})
            except Exception:
                pass
        
        context.on("response", handle_response)
        
        # Fill date
        date_val = normalize_date(date_str)
        ok = try_fill_date(page, date_val)
        
        if not ok:
            # Try filling first two date inputs (from/to)
            inputs = []
            for sel in SELECTOR_HINTS["date_inputs"]:
                for el in page.locator(sel).all():
                    inputs.append(el)
            if inputs:
                try:
                    inputs[0].fill(date_val)
                    if len(inputs) > 1:
                        inputs[1].fill(date_val)
                    ok = True
                except Exception:
                    pass
        
        # Click search
        clicked = click_search(page)
        if not clicked:
            page.wait_for_timeout(1000)
        
        # Wait for results and paginate
        page.wait_for_timeout(1500)
        paginate(page)
        rows = try_extract_rows(page)
        
        # Try JSON fallback if DOM parsing failed
        if not rows and json_payloads:
            payload = json_payloads[-1]["data"]
            flat = []
            
            def norm(v):
                if v is None:
                    return None
                return str(v).strip()
            
            if isinstance(payload, dict) and "results" in payload:
                items = payload["results"]
            elif isinstance(payload, list):
                items = payload
            else:
                items = []
            
            for it in items:
                flat.append(ArrestRow(
                    arrest_date=norm(it.get("arrest_date") or it.get("arrestDate") or it.get("date")),
                    name=norm(it.get("name") or f"{it.get('last_name','')} {it.get('first_name','')}".strip()),
                    dob=norm(it.get("dob") or it.get("date_of_birth")),
                    age=norm(it.get("age")),
                    charges=norm(it.get("charges") or it.get("charge_summary") or it.get("charge")),
                    agency=norm(it.get("agency") or it.get("arresting_agency")),
                    booking_number=norm(it.get("booking_number") or it.get("bookingNo") or it.get("booking")),
                    bond=norm(it.get("bond")),
                ))
            rows = flat
        
        context.close()
        browser.close()
        
        # Deduplicate
        seen = set()
        out = []
        for r in rows:
            key = (r.name, r.arrest_date, r.booking_number, r.charges)
            if key in seen:
                continue
            seen.add(key)
            out.append(asdict(r))
        
        print(f"✅ Found {len(out)} arrest records for {date_str}")
        return out


def upload_to_google_sheets(records: List[Dict]):
    """Upload records to Google Sheets"""
    if not records:
        print("⚠️ No records to upload")
        return
    
    try:
        print("📤 Uploading to Google Sheets...")
        
        # Authorize with gspread
        gc = gspread.service_account(filename=CREDENTIALS_FILE)
        spreadsheet = gc.open_by_key(GOOGLE_SHEET_ID)
        
        # Get or create worksheet
        try:
            wks = spreadsheet.worksheet(WORKSHEET_NAME)
        except:
            wks = spreadsheet.add_worksheet(title=WORKSHEET_NAME, rows=1000, cols=20)
        
        # Convert to DataFrame
        df = pd.DataFrame(records)
        
        # Reorder columns for readability
        col_order = ['arrest_date', 'name', 'dob', 'age', 'booking_number', 
                     'agency', 'bond', 'arrest_time', 'charges', 'source_url']
        cols = [c for c in col_order if c in df.columns]
        df = df[cols]
        
        # Prepare data with headers
        data_to_upload = [df.columns.tolist()] + df.values.tolist()
        
        # Clear and update
        wks.clear()
        wks.update('A1', data_to_upload, value_input_option='USER_ENTERED')
        
        print(f"✅ Successfully uploaded {len(records)} records to Google Sheets")
        
    except Exception as e:
        print(f"❌ Error uploading to Google Sheets: {e}")
        raise


def main():
    """Main execution function"""
    ap = argparse.ArgumentParser(description="Scrape Sarasota County arrests by date")
    ap.add_argument("--date", help="Single date YYYY-MM-DD or MM/DD/YYYY")
    ap.add_argument("--start", help="Start date (inclusive) for range")
    ap.add_argument("--end", help="End date (inclusive) for range")
    ap.add_argument("--headful", action="store_true", help="Run with visible browser")
    ap.add_argument("--no-upload", action="store_true", help="Skip Google Sheets upload")
    ap.add_argument("--output", help="Save to JSON file")
    args = ap.parse_args()
    
    if not args.date and not (args.start and args.end):
        ap.error("Provide --date or both --start and --end")
    
    dates = [args.date] if args.date else list(daterange(args.start, args.end))
    all_records = []
    
    for d in dates:
        try:
            recs = scrape_for_date(d, headless=not args.headful)
            all_records.extend(recs)
            time.sleep(0.5)
        except Exception as e:
            print(f"❌ [{d}] ERROR: {e}", file=sys.stderr)
    
    print(f"\n📊 Total records scraped: {len(all_records)}")
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(all_records, f, ensure_ascii=False, indent=2)
        print(f"💾 Saved to {args.output}")
    
    # Upload to Google Sheets
    if not args.no_upload and all_records:
        upload_to_google_sheets(all_records)
    
    print("\n✨ Sarasota County Scraper completed successfully! ✨")


if __name__ == "__main__":
    main()
