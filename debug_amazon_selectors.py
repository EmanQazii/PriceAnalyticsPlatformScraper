from amazon_scraper import AmazonSeleniumScraper
from selenium.webdriver.common.by import By
import os

def debug_amazon():
    scraper = AmazonSeleniumScraper()
    try:
        scraper.init_driver()
        category = "Phone"
        url = scraper.base_url + scraper.categories[category]
        print(f"Loading {url}...")
        scraper.driver.get(url)
        
        # Save full page source for general debug
        with open("amazon_debug_page.html", "w", encoding="utf-8") as f:
            f.write(scraper.driver.page_source)
        print("Saved amazon_debug_page.html")

        # Find elements
        elements = scraper.driver.find_elements(By.CSS_SELECTOR, '[data-component-type="s-search-result"]')
        print(f"Found {len(elements)} elements")
        
        if elements:
            html = elements[0].get_attribute('outerHTML')
            with open("amazon_debug_element.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("Saved amazon_debug_element.html")
            
            # Print some basic stats
            print(f"Element text preview: {elements[0].text[:100]}...")
            
    finally:
        scraper.close_driver()

if __name__ == "__main__":
    debug_amazon()
