"""
Amazon.com Selenium Scraper
Scrapes electronics products from Amazon using Selenium
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from scraper_base import BaseScraper
from typing import List, Dict
import time
import re

class AmazonSeleniumScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.amazon.com"
        self.scraper_name = "amazon_selenium"
        self.driver = None
        
        # Amazon search URLs for different categories
        self.categories = {
            "Phone": "/s?k=smartphone",
            "Laptop": "/s?k=laptop",
            "Headphone": "/s?k=headphones",
            "Tablet": "/s?k=tablet",
            "Airpod": "/s?k=airpods",
            "Speaker": "/s?k=bluetooth+speaker"
        }
    
    def init_driver(self, verbose: bool = True):
        """Initialize Selenium WebDriver with headless Chrome"""
        if self.driver:
            return
        
        if verbose: print("   🌐 Initializing Chrome WebDriver for Amazon...")
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        # Amazon is very sensitive to User-Agents
        chrome_options.add_argument(f'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36')
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            if verbose: print("   ✓ Chrome WebDriver initialized")
        except Exception as e:
            if verbose: print(f"   ✗ Failed to initialize Chrome: {str(e)}")
            raise
    
    def close_driver(self, verbose: bool = True):
        """Close the Selenium WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            if verbose: print("   ✓ Chrome WebDriver closed")
    
    def scrape_category(self, category: str, max_products: int = 10, verbose: bool = True) -> List[Dict]:
        """Scrape products from a specific category using Selenium"""
        if category not in self.categories:
            if verbose: print(f"⚠ Unknown category: {category}")
            return []
        
        url = self.base_url + self.categories[category]
        if verbose:
            print(f"\n🔍 Scraping Amazon - {category}")
            print(f"   URL: {url}")
        
        try:
            self.driver.get(url)
            
            # Slow scroll to trigger lazy loading
            self.slow_scroll()
            
            # Wait for products to load
            wait = WebDriverWait(self.driver, 15)
            
            # Amazon search result selectors
            selectors_to_try = [
                (By.CSS_SELECTOR, '[data-component-type="s-search-result"]'),
                (By.CSS_SELECTOR, '.s-result-item[data-asin]'),
                (By.CSS_SELECTOR, '.s-card-container'),
            ]
            
            elements = []
            for by_type, selector in selectors_to_try:
                try:
                    # Don't wait too long if first one fails
                    elements = self.driver.find_elements(by_type, selector)
                    if elements and len(elements) > 2:
                        if verbose: print(f"   ✓ Found {len(elements)} items. Filtering products...")
                        break
                except:
                    continue
            
            if not elements:
                # Check for CAPTCHA
                if "api-services-support@amazon.com" in self.driver.page_source or "captcha" in self.driver.current_url:
                    if verbose: print(f"   ✗ Amazon CAPTCHA detected. Cannot proceed.")
                else:
                    if verbose: print(f"   ⚠ No products found")
                return []
            
            products = []
            valid_count = 0
            for i, element in enumerate(elements):
                if valid_count >= max_products:
                    break
                    
                try:
                    product = self.extract_product_info_selenium(element, category)
                    if product:
                        products.append(product)
                        valid_count += 1
                        if verbose: print(f"   ✓ Extracted: {product['name'][:40]}...")
                    else:
                        # Log why it failed for the first few items
                        if verbose and i < 3:
                            print(f"   ⚠ Item {i+1} extraction returned None (likely missing name or price)")
                except Exception as e:
                    if verbose and i < 3:
                        print(f"   ⚠ Item {i+1} error: {str(e)}")
                    continue
            
            return products
            
        except Exception as e:
            if verbose: print(f"   ✗ Error scraping {category}: {str(e)}")
            return []

    def slow_scroll(self, scroll_pause_time=0.5):
        """Scroll down the page slowly to trigger lazy loading"""
        total_height = int(self.driver.execute_script("return document.body.scrollHeight"))
        # Scroll in increments of 500px
        for i in range(0, total_height, 500):
            self.driver.execute_script(f"window.scrollTo(0, {i});")
            time.sleep(scroll_pause_time)
        # Scroll back to top
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)

    def extract_product_info_selenium(self, element, category: str) -> Dict:
        """Extract product information from Amazon search result element"""
        try:
            # Name - more robust selectors
            name = ""
            name_selectors = ['h2 a span', 'h2 span', '.a-size-medium', '.a-size-base-plus']
            for selector in name_selectors:
                try:
                    name_elem = element.find_element(By.CSS_SELECTOR, selector)
                    name = name_elem.text.strip()
                    if name: break
                except:
                    continue
            
            if not name:
                return None
                
            # URL
            url = ""
            try:
                link_selectors = ['h2 a', 'a.a-link-normal']
                for selector in link_selectors:
                    try:
                        link_elem = element.find_element(By.CSS_SELECTOR, selector)
                        url = link_elem.get_attribute('href')
                        if url and not url.startswith('http'):
                            url = self.base_url + url
                        if url: break
                    except: continue
            except:
                pass
                
            # Price
            price = 0
            try:
                # Primary method: Whole and fraction
                try:
                    whole = element.find_element(By.CSS_SELECTOR, '.a-price-whole').text.replace('.', '').replace(',', '').strip()
                    if whole:
                        price = int(whole)
                except:
                    pass
                
                # Fallback: Offscreen text (includes PKR/USD)
                if price == 0:
                    try:
                        price_text = element.find_element(By.CSS_SELECTOR, '.a-price .a-offscreen').get_attribute('innerHTML')
                        price = self.extract_price(price_text)
                    except:
                        pass
            except:
                pass
            
            if price == 0:
                return None # Skip items without prices (often ads or out of stock)
                
            # Image
            image = ""
            try:
                img_elem = element.find_element(By.CSS_SELECTOR, 'img.s-image')
                image = img_elem.get_attribute('src')
            except:
                pass
                
            if not image:
                image = "https://via.placeholder.com/400x400.png?text=Amazon+Product"
                
            return {
                "name": name[:100],
                "url": url,
                "brand": self.extract_brand(name),
                "category": category,
                "image": image,
                "description": name, 
                "source": "Amazon",
                "website": "Amazon",
                "price": price
            }
        except:
            return None

    def extract_brand(self, name: str) -> str:
        """Simple brand extraction from name"""
        brands = ["Apple", "Samsung", "Xiaomi", "HP", "Dell", "Sony", "Logitech", "Infinix", "Techno", "Realme", "Oppo", "Vivo", "Anker", "Bose"]
        for brand in brands:
            if brand.lower() in name.lower():
                return brand
        return "Generic"

    def run(self, max_products: int = 10, days_interval: int = 2, verbose: bool = True) -> Dict:
        """Run the scraper for all categories"""
        if not self.should_run(self.scraper_name, days_interval):
            if verbose: print(f"⏭ Amazon scraper already ran within interval ({days_interval} days). Skipping...")
            return {"status": "skipped"}
        
        if verbose: print(f"\n🚀 Starting Amazon Selenium Scraper - {time.ctime()}")
        
        all_products = []
        try:
            self.init_driver(verbose=verbose)
            for category in self.categories.keys():
                products = self.scrape_category(category, max_products=max_products, verbose=verbose)
                for product in products:
                    if self.send_to_backend(product, verbose=verbose):
                        all_products.append(product)
                    time.sleep(0.5)
        except Exception as e:
            if verbose: print(f"✗ Fatal error in Amazon scraper: {str(e)}")
        finally:
            self.close_driver(verbose=verbose)
            
        self.mark_run_complete(self.scraper_name)
        return {"status": "success", "products_scraped": len(all_products)}

if __name__ == "__main__":
    scraper = AmazonSeleniumScraper()
    scraper.run()
