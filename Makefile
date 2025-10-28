.PHONY: help install setup test run clean

help:
	@echo "Sarasota County Scraper - Available Commands:"
	@echo ""
	@echo "  make install    - Install Python dependencies"
	@echo "  make setup      - Install dependencies and Playwright browsers"
	@echo "  make test       - Run scraper for today's date (no upload)"
	@echo "  make run        - Run scraper for yesterday and upload to Sheets"
	@echo "  make clean      - Remove cache and temporary files"
	@echo ""

install:
	pip install -r requirements.txt

setup: install
	python3 -m playwright install chromium

test:
	python3 sarasota_scraper.py --date $$(date +%Y-%m-%d) --no-upload --output test_output.json
	@echo "Test output saved to test_output.json"

run:
	python3 sarasota_scraper.py --date $$(date -d "yesterday" +%Y-%m-%d 2>/dev/null || date -v-1d +%Y-%m-%d)

clean:
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .playwright
	rm -f *.pyc
	rm -f test_output.json
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
