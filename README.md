# Price Tracker Scraper

## 🚀 Daily Web Scraper

Automatically scrapes product prices from Daraz.pk once per day and updates your database.

## Features

- ✅ **Daily Scheduling**: Runs once per day to respect website servers
- ✅ **Smart Caching**: Won't run twice in the same day
- ✅ **Selenium Automation**: Uses headless Chrome to handle JavaScript sites
- ✅ **Fast & Efficient**: Only scrapes 5 products per category (30 total)
- ✅ **Anti-Detection**: Rotating user agents and realistic headers
- ✅ **Error Handling**: Automatic retries with exponential backoff
- ✅ **Fallback Data**: Frontend shows static products if scraping fails

## Installation

### 1. Install Python Dependencies
```bash
cd scraper
pip install -r requirements.txt
```

### 2. Install Google Chrome
Selenium requires Chrome browser to be installed:
- **Windows**: Download from [chrome.google.com](https://www.google.com/chrome/)
- **Already installed?** Check by opening Chrome browser

The scraper uses `webdriver-manager` which automatically downloads ChromeDriver.

### 3. Test Installation
```bash
python daraz_scraper.py
```

If you see "🌐 Initializing Chrome WebDriver..." it's working!

## Usage

### Run Immediately (Manual)
```bash
python run_scrapers.py --now
```

### Start Daily Scheduler
```bash
# Run daily at 2 AM (default)
python run_scrapers.py --schedule

# Run daily at custom time (e.g., 10:30 PM)
python run_scrapers.py --schedule "22:30"
```

### Keep Scheduler Running in Background

**Windows** (PowerShell):
```powershell
Start-Process python -ArgumentList "run_scrapers.py --schedule" -WindowStyle Hidden
```

**Mac/Linux**:
```bash
nohup python run_scrapers.py --schedule &
```

## How It Works

1. **Daily Check**: Script checks if it already ran today
2. **Scrape Categories**: Fetches top 3 products per category from Daraz
3. **Send to Backend**: POSTs data to `http://localhost:5000/api/scraper/price`
4. **Update Database**: Backend stores in MongoDB with price history
5. **Sleep Until Tomorrow**: Won't run again until next day

## Supported Categories

- 📱 Phones
- 💻 Laptops
- 🎧 Headphones
- 📲 Tablets
- 🎵 Airpods
- 🔊 Speakers

## File Structure

```
scraper/
├── scraper_base.py      # Base class with common utilities
├── daraz_scraper.py     # Daraz.pk scraper implementation
├── run_scrapers.py      # Scheduler and orchestrator
├── requirements.txt     # Python dependencies
├── last_run.json        # Tracks last run date (auto-generated)
└── venv/                # Virtual environment (if created)
```

## Troubleshooting

### "Already ran today" message
The scraper tracks runs in `last_run.json`. To force a re-run:
```bash
# Delete the tracking file
rm last_run.json  # Mac/Linux
del last_run.json  # Windows

# Then run again
python run_scrapers.py --now
```

### Connection errors
Make sure:
- ✅ Backend server is running (`npm run dev` in `backend/`)
- ✅ MongoDB is connected
- ✅ Internet connection is active

### No products found
This can happen if:
- Daraz changed their HTML structure (needs scraper update)
- Your IP was temporarily blocked (wait 24 hours)
- Internet connectivity issues

## Legal & Ethical Notes

⚠️ **Important**: While this scraper is respectful (runs once daily, has rate limiting), web scraping may violate Terms of Service of some websites.

**For production use:**
- Consider using official APIs (Daraz/Amazon Product API)
- Add proxy rotation for larger scale
- Implement CAPTCHA solving (paid services)
- Consult legal counsel

## Adding More Scrapers

To add Amazon or other sites, create a new file following this pattern:

```python
from scraper_base import BaseScraper

class AmazonScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.scraper_name = "amazon"
    
    def run(self):
        if not self.should_run_today(self.scraper_name):
            return {"status": "skipped"}
        
        # Your scraping logic here
        
        self.mark_run_complete(self.scraper_name)
        return {"status": "success"}
```

Then add to `run_scrapers.py`:
```python
from amazon_scraper import AmazonScraper

def run_all_scrapers():
    daraz = DarazScraper()
    daraz.run()
    
    amazon = AmazonScraper()  # Add this
    amazon.run()              # Add this
```
