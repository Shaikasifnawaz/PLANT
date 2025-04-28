from playwright.sync_api import sync_playwright
import csv
import time

def scrape_plants():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = context.new_page()
        
        with open('plants_data.csv', 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Plant Name', 'Scientific Name', 'Image URL', 'Page URL'])
            
            page_num = 1
            while True:
                try:
                    url = f"https://www.picturethisai.com/wiki/plants?page={page_num}" if page_num > 1 else "https://www.picturethisai.com/wiki/plants"
                    print(f"Navigating to: {url}")
                    
                    # Retry mechanism for reliability
                    page.goto(url, timeout=60000, wait_until='domcontentloaded')
                    
                    # Wait for main content and Cloudflare check
                    page.wait_for_selector('a.plant-card', timeout=30000)
                    
                    # Scroll to trigger lazy loading
                    page.mouse.wheel(0, 1500)
                    time.sleep(2)  # Allow time for images to load
                    
                    plant_cards = page.query_selector_all('a.plant-card')
                    print(f"Found {len(plant_cards)} plants on page {page_num}")
                    
                    if not plant_cards:
                        print("No more plants found")
                        break
                    
                    for card in plant_cards:
                        try:
                            # Scroll each card into view
                            card.scroll_into_view_if_needed()
                            
                            # Wait for image to load within card
                            img = card.wait_for_selector('img.plant-card-image')
                            src = img.get_attribute('src')
                            image_url = src.split('?')[0] if src else ''
                            
                            plant_name = card.query_selector('.plant-card-content-title').inner_text().strip()
                            scientific_name = card.query_selector('.plant-card-content-description').inner_text().strip()
                            page_url = "https://www.picturethisai.com" + card.get_attribute('href')
                            
                            writer.writerow([plant_name, scientific_name, image_url, page_url])
                        except Exception as e:
                            print(f"Error processing card: {str(e)}")
                            continue
                    
                    page_num += 1
                    time.sleep(3)  # Respectful delay between pages
                    
                except Exception as e:
                    print(f"Stopped at page {page_num}: {str(e)}")
                    break
            
            browser.close()

if __name__ == '__main__':
    scrape_plants()