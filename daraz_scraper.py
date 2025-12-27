"""
Daraz.pk Selenium Scraper
Scrapes electronics products from Daraz Pakistan using Selenium
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

class DarazSeleniumScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.daraz.pk"
        self.scraper_name = "daraz_selenium"
        self.driver = None
        
        # Simplified search URLs (just search query)
        self.categories = {
            "Phone": "/catalog/?q=smartphone",
            "Laptop": "/catalog/?q=laptop",
            "Headphone": "/catalog/?q=headphones",
            "Tablet": "/catalog/?q=tablet",
            "Airpod": "/catalog/?q=airpods",
            "Speaker": "/catalog/?q=bluetooth+speaker"
        }
    
    def init_driver(self, verbose: bool = True):
        """Initialize Selenium WebDriver with headless Chrome"""
        if self.driver:
            return
        
        if verbose: print("   🌐 Initializing Chrome WebDriver...")
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run without opening browser window
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(f'user-agent={self.get_headers()["User-Agent"]}')
        
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
    
    def slow_scroll(self, scroll_pause_time=0.5, steps=5):
        """Scroll down the page slowly to trigger lazy loading"""
        if not self.driver:
            return
            
        print(f"   ⏳ Scrolling down to load images...")
        total_height = self.driver.execute_script("return document.body.scrollHeight")
        step_size = total_height / steps
        
        for i in range(1, steps + 1):
            self.driver.execute_script(f"window.scrollTo(0, {i * step_size});")
            time.sleep(scroll_pause_time)
        
        # Scroll back to top
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.5)
    
    def scrape_category(self, category: str, max_products: int = 5, verbose: bool = True) -> List[Dict]:
        """Scrape products from a specific category using Selenium"""
        if category not in self.categories:
            if verbose: print(f"⚠ Unknown category: {category}")
            return []
        
        url = self.base_url + self.categories[category]
        if verbose:
            print(f"\n🔍 Scraping Daraz - {category}")
            print(f"   URL: {url}")
        
        try:
            self.driver.get(url)
            
            # Wait for products to load
            wait = WebDriverWait(self.driver, 15)
            
            # Selenium selectors for Daraz
            selectors_to_try = [
                (By.CSS_SELECTOR, '[data-qa-locator="product-item"]'),
                (By.CSS_SELECTOR, '.gridItem--YqX5D'),
                (By.CSS_SELECTOR, '.ant-col-5'),
            ]
            
            elements = []
            for by_type, selector in selectors_to_try:
                try:
                    # wait.until(EC.presence_of_all_elements_located((by_type, selector)))
                    elements = self.driver.find_elements(by_type, selector)
                    if elements and len(elements) > 2:
                        if verbose: print(f"   ✓ Found {len(elements)} items. Filtering products...")
                        break
                except:
                    continue
            
            if not elements:
                if verbose: print(f"   ⚠ No products found")
                return []
            
            # Slow scroll after finding elements to ensure images load
            self.slow_scroll()
            
            # Re-find elements after scroll as they might have been detached
            for by_type, selector in selectors_to_try:
                elements = self.driver.find_elements(by_type, selector)
                if elements and len(elements) > 2:
                    break

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
                except Exception as e:
                    if verbose and i < 3: print(f"   ⚠ Item {i+1} error: {str(e)}")
                    continue
            
            return products
            
        except Exception as e:
            if verbose: print(f"   ✗ Error scraping {category}: {str(e)}")
            return []
    
    def extract_product_info_selenium(self, element, category: str) -> Dict:
        """Extract product information from Selenium WebElement"""
        try:
            # Initialize fields
            name = ""
            image = ""
            description = ""
            url = ""
            price = 0
            try:
                # Find name link
                link_elem = element.find_element(By.CSS_SELECTOR, 'a[href*="/products/"]')
                name = link_elem.text
                if not name:
                    name = link_elem.get_attribute('title')
            except:
                pass
                
            if not name:
                try:
                    name_elem = element.find_element(By.CSS_SELECTOR, '.product-card__name, .title, .name')
                    name = name_elem.text
                except:
                    pass
            
            if not name:
                return None
            
            # Clean name
            if '\n' in name:
                name = name.split('\n')[0]
                
            # Price
            price = 0
            try:
                price_elem = element.find_element(By.CSS_SELECTOR, '.product-card__price-current, .ooOxS, [class*="price"]')
                price_text = price_elem.text
                price = self.extract_price(price_text)
            except:
                pass
            
            if price == 0:
                return None
            
            # Image - CRITICAL FIX: Expanded CDN list and tag scanning
            image = ""
            try:
                img_elems = element.find_elements(By.TAG_NAME, 'img')
                for img_elem in img_elems:
                    potential_image = (img_elem.get_attribute('src') or 
                                     img_elem.get_attribute('data-src') or
                                     img_elem.get_attribute('data-lazysrc') or
                                     img_elem.get_attribute('data-original'))
                    
                    if potential_image:
                        if potential_image.startswith('data:'):
                            continue
                            
                        if potential_image.startswith('//'):
                            potential_image = 'https:' + potential_image
                        elif not potential_image.startswith('http'):
                            potential_image = self.base_url + potential_image
                            
                        # Expanded CDN and extension list
                        valid_patterns = ['.jpg', '.jpeg', '.png', '.webp', '.avif', 'slatic.net', 'alicdn.com', 'lazcdn.com', 'daraz.pk']
                        if any(pattern in potential_image.lower() for pattern in valid_patterns):
                            image = potential_image
                            
                            # CLEAN URL: Remove lazy-loading suffixes like _200x200q80.avif
                            if '.jpg_' in image: image = image.split('.jpg_')[0] + '.jpg'
                            elif '.png_' in image: image = image.split('.png_')[0] + '.png'
                            elif '.jpeg_' in image: image = image.split('.jpeg_')[0] + '.jpeg'
                            
                            # Use the alt of the real product image for description
                            try:
                                description = img_elem.get_attribute('alt')
                            except:
                                pass
                                
                            # Prioritize real product images over badges/icons
                            if any(cdn in image.lower() for cdn in ['slatic.net', 'alicdn.com', 'lazcdn.com']):
                                break
            except:
                pass
            
            if not image:
                image = "https://via.placeholder.com/400x400.png?text=Product+Image"
                
            # Product URL
            url = ""
            try:
                link_elem = element.find_element(By.TAG_NAME, 'a')
                url = link_elem.get_attribute('href')
                if url:
                    if url.startswith('//'):
                        url = 'https:' + url
                    elif not url.startswith('http'):
                        url = self.base_url + url
            except:
                pass
            
            if not url:
                url = f"https://www.daraz.pk/catalog/?q={name.replace(' ', '+')[:50]}"
            
            # Description - Use the alt of the image we picked, or name
            if not description:
                description = name
                
            return {
                "name": name[:100],
                "url": url,
                "brand": self.extract_brand(name),
                "category": category,
                "image": image,
                "description": description,
                "source": "Daraz",
                "website": "Daraz",
                "price": price
            }
        except Exception as e:
            return None

    def extract_brand(self, name: str) -> str:
        """Simple brand extraction from name"""
        brands = ["Apple", "Samsung", "Xiaomi", "HP", "Dell", "Sony", "Logitech", "Infinix", "Techno", "Realme", "Oppo", "Vivo"]
        for brand in brands:
            if brand.lower() in name.lower():
                return brand
        return "Generic"

    def run(self, max_products: int = 5, days_interval: int = 2, verbose: bool = True) -> Dict:
        """Run the scraper for all categories"""
        if not self.should_run(self.scraper_name, days_interval):
            if verbose: print(f"⏭ Daraz scraper already ran within interval ({days_interval} days). Skipping...")
            return {"status": "skipped"}
        
        if verbose: print(f"\n🚀 Starting Daraz Selenium Scraper - {time.ctime()}")
        
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
            if verbose: print(f"✗ Fatal error in Daraz scraper: {str(e)}")
        finally:
            self.close_driver(verbose=verbose)
            
        self.mark_run_complete(self.scraper_name)
        return {"status": "success", "products_scraped": len(all_products)}

if __name__ == "__main__":
    scraper = DarazSeleniumScraper()
    scraper.run()
