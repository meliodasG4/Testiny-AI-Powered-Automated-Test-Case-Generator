from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from urllib.parse import urlparse
import time
import json

def extract_website_data(start_url, max_pages=6):
    """
    Extract all elements from a website using Microsoft Edge
    
    Args:
        start_url: The URL to start crawling from
        max_pages: Maximum number of pages to crawl
        
    Returns:
        dict: Web data with pages, inputs, buttons, links
    """
    edge_options = Options()
    edge_options.add_argument('--headless')
    edge_options.add_argument('--no-sandbox')
    edge_options.add_argument('--disable-dev-shm-usage')
    edge_options.add_argument('--disable-gpu')
    edge_options.add_argument('--window-size=1920,1080')

    driver = None
    
    try:
        from webdriver_manager.microsoft import EdgeChromiumDriverManager
        driver = webdriver.Edge(
            service=Service(EdgeChromiumDriverManager().install()),
            options=edge_options
        )
        print("Edge driver initialized with webdriver-manager")
    except ImportError:
        print("webdriver-manager not installed")
        print("Installing now... run: pip install webdriver-manager")
        raise
    except Exception as e:
        print(f"webdriver-manager failed: {e}")
        try:
            driver = webdriver.Edge(options=edge_options)
            print("Edge driver initialized directly")
        except Exception as e2:
            print(f"Error: {e2}")
            print("\nPlease install webdriver-manager:")
            print("pip install webdriver-manager")
            raise
    
    visited = set()
    global_seen_inputs = set()
    global_seen_buttons = set()
    global_seen_hrefs = {f"{start_url}/#main", start_url}
    
    pages = {}
    
    to_visit = [start_url]
    domain = urlparse(start_url).netloc
    
    page_count = 0
    
    while to_visit and page_count < max_pages:
        current_url = to_visit.pop(0)
        
        if current_url in visited:
            continue
        visited.add(current_url)
        
        if urlparse(current_url).netloc != domain:
            continue
        
        print(f"\nCrawling ({page_count + 1}/{max_pages}): {current_url}")
        
        try:
            driver.get(current_url)
            
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Skipped: {e}")
            continue
        
        page_inputs = []
        page_buttons = []
        page_links = []

        try:
            for inp in driver.find_elements(By.TAG_NAME, "input"):
                name = inp.get_attribute("name") or ""
                input_type = inp.get_attribute("type") or ""
                placeholder = inp.get_attribute("placeholder") or ""
                
                sig = (name, input_type, placeholder)
                
                if sig not in global_seen_inputs:
                    global_seen_inputs.add(sig)
                    
                    if not name and not placeholder:
                        continue
                    
                    page_inputs.append({
                        "name": name,
                        "type": input_type,
                        "placeholder": placeholder
                    })
        except Exception as e:
            print(f"Error extracting inputs: {e}")
        
        try:
            for btn in driver.find_elements(By.TAG_NAME, "button"):
                text = btn.text.strip()
                btn_type = btn.get_attribute("type") or ""
                
                sig = (text, btn_type)
                
                if sig not in global_seen_buttons:
                    global_seen_buttons.add(sig)
                    
                    if not text:
                        continue
                    
                    page_buttons.append({
                        "text": text,
                        "type": btn_type
                    })
        except Exception as e:
            print(f" Error extracting buttons: {e}")
        
        try:
            for a in driver.find_elements(By.TAG_NAME, "a"):
                href = a.get_attribute("href")
                text = a.text.strip()
                
                if not href:
                    continue
                
                if href not in global_seen_hrefs:
                    global_seen_hrefs.add(href)
                    
                    page_links.append({
                        "text": text,
                        "href": href
                    })
        except Exception as e:
            print(f"Error extracting links: {e}")

        pages[current_url] = {
            "inputs": page_inputs,
            "buttons": page_buttons,
            "links": page_links
        }
        

        for link in page_links:
            href = link["href"]
            if href not in visited and urlparse(href).netloc == domain:
                to_visit.append(href)
        
        page_count += 1
    
    driver.quit()
    
    print(f"\n Extraction complete: {len(pages)} pages")
    

    return {
        "basic_info": {
            "url": start_url,
            "title": "Web Application",
            "pages_crawled": len(pages)
        },
        "pages": pages
    }



if __name__ == "__main__":
    start_url = "https://demo.nopcommerce.com"
    web_data = extract_website_data(start_url)
    

    with open("clean_pages.json", "w") as f:
        json.dump(web_data["pages"], f, indent=2)
    
    print(f"\n Saved to clean_pages.json")