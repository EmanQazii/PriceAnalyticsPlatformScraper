"""
Base Scraper Class
Provides common functionality for all e-commerce scrapers
"""
import requests
import time
import json
import os
from datetime import datetime, timedelta
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from typing import List, Dict, Optional

class BaseScraper:
    def __init__(self, backend_url: str = "http://localhost:5000/api/scraper/price"):
        self.backend_url = backend_url
        self.ua = UserAgent()
        self.session = requests.Session()
        self.last_run_file = "last_run.json"  # Fixed: removed 'scraper/' prefix
        
    def get_headers(self) -> Dict[str, str]:
        """Generate realistic headers with rotating user agent"""
        return {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
    
    def should_run(self, scraper_name: str, days_interval: int = 1) -> bool:
        """Check if scraper has run within the specified interval"""
        if not os.path.exists(self.last_run_file):
            return True
        
        try:
            with open(self.last_run_file, 'r') as f:
                data = json.load(f)
                last_run = data.get(scraper_name)
                
                if not last_run:
                    return True
                
                last_run_date = datetime.fromisoformat(last_run).date()
                today = datetime.now().date()
                
                days_since_last_run = (today - last_run_date).days
                return days_since_last_run >= days_interval
        except:
            return True
    
    def mark_run_complete(self, scraper_name: str):
        """Mark that scraper has run today"""
        data = {}
        if os.path.exists(self.last_run_file):
            try:
                with open(self.last_run_file, 'r') as f:
                    data = json.load(f)
            except:
                pass
        
        data[scraper_name] = datetime.now().isoformat()
        
        with open(self.last_run_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def send_to_backend(self, product_data: Dict, verbose: bool = True) -> bool:
        """Send scraped product to backend API"""
        try:
            if verbose: print(f"DEBUG: Sending data: {json.dumps(product_data, indent=2)}")
            response = self.session.post(
                self.backend_url,
                json=product_data,
                timeout=10
            )
            
            if response.status_code == 201:
                if verbose:
                    print(f"✓ Sent: {product_data['name']} - Rs {product_data['price']}")
                    print(f"  Backend response: {response.text}")
                return True
            else:
                if verbose:
                    print(f"✗ Failed: {product_data['name']} - Status {response.status_code}")
                    print(f"  Response: {response.text}")
                return False
        except Exception as e:
            if verbose: print(f"✗ Error sending {product_data['name']}: {str(e)}")
            return False
    
    def safe_delay(self, min_seconds: float = 2.0, max_seconds: float = 5.0):
        """Add random delay to avoid detection"""
        import random
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def fetch_page(self, url: str, max_retries: int = 3) -> Optional[BeautifulSoup]:
        """Fetch and parse a web page with retries"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(
                    url,
                    headers=self.get_headers(),
                    timeout=15
                )
                
                if response.status_code == 200:
                    return BeautifulSoup(response.content, 'lxml')
                
                print(f"⚠ Attempt {attempt + 1}: Status {response.status_code}")
                
            except Exception as e:
                print(f"⚠ Attempt {attempt + 1} failed: {str(e)}")
            
            if attempt < max_retries - 1:
                self.safe_delay(3, 6)  # Longer delay on retry
        
        return None
    
    def extract_price(self, price_text: str) -> int:
        """Extract numeric price from text (handles Rs, commas, periods, etc.)"""
        import re
        # Remove ALL non-digit characters (Rs., commas, spaces, etc.)
        cleaned = re.sub(r'\D', '', price_text)  # \D means "not a digit"
        try:
            return int(cleaned) if cleaned else 0
        except:
            return 0
