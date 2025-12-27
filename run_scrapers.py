"""
Daily Scraper Scheduler
Runs all scrapers once per day at specified time
"""
import schedule
import time
from datetime import datetime
from daraz_scraper import DarazSeleniumScraper
from amazon_scraper import AmazonSeleniumScraper

def run_all_scrapers(verbose: bool = True, ignore_interval: bool = False):
    """Execute all configured scrapers"""
    if verbose:
        print(f"\n🕐 Scraper run triggered at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run Daraz Selenium scraper
    # Limit: 2 per category (Demonstration Mode)
    daraz = DarazSeleniumScraper()
    # If ignore_interval=True (manual run), we set interval to 0 to force run
    interval = 0 if ignore_interval else 2
    daraz.run(max_products=2, days_interval=interval, verbose=verbose)
    
    # Run Amazon Selenium scraper
    # Limit: 20 per category (Demonstration Mode)
    amazon = AmazonSeleniumScraper()
    amazon.run(max_products=20, days_interval=interval, verbose=verbose)
    
    return True

def run_once_now():
    """Run scrapers immediately with logs (for manual testing/demo)"""
    print("🚀 Running scrapers manually (Verbose Mode)...")
    return run_all_scrapers(verbose=True, ignore_interval=True)

def start_scheduler(schedule_time="02:00"):
    """
    Start the scheduler to run every 2 days
    
    Args:
        schedule_time: Time to run (24-hour format, e.g., "02:00" for 2 AM)
    """
    print(f"⏰ Production Scheduler started.")
    print(f"   Interval: Every 2 days at {schedule_time}")
    print(f"   Mode: Background (Silent)")
    print(f"   Press Ctrl+C to stop script")
    print(f"   Manual Demo: python run_scrapers.py --now\n")
    
    # Schedule to run every 2 days
    # schedule.every(2).days.at(schedule_time).do(run_all_scrapers, verbose=False, ignore_interval=False)
    
    # Note: 'schedule' library every(2).days might offset based on start time.
    # To run specifically at a time every 2 days:
    schedule.every(2).days.at(schedule_time).do(run_all_scrapers, verbose=False, ignore_interval=False)
    
    # Keep running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n⏹ Scheduler stopped by user")

if __name__ == "__main__":
    import sys
    
    # Force silent if requested
    is_silent = "--silent" in sys.argv
    
    if len(sys.argv) > 1 and sys.argv[1] == "--now":
        # Manual run (Always verbose unless --silent added)
        run_all_scrapers(verbose=not is_silent, ignore_interval=True)
    elif len(sys.argv) > 1 and sys.argv[1] == "--schedule":
        # Start scheduler (Background style)
        schedule_time = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else "02:00"
        start_scheduler(schedule_time)
    else:
        print("Usage:")
        print("  python run_scrapers.py --now              # Run immediately (Demo Mode)")
        print("  python run_scrapers.py --schedule [TIME]  # Start 2-day scheduler (Prod Mode)")
        print("  python run_scrapers.py --silent           # Run once silently")
        
        if is_silent:
            run_all_scrapers(verbose=False, ignore_interval=True)
