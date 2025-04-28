from flask_cors import CORS
from flask import Flask, jsonify, request
from playwright.sync_api import sync_playwright
import time
import os

app = Flask(__name__)

# Apply CORS to the entire app
CORS(app)

def scrape_plants_page(page_num):
    plants = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = context.new_page()
        
        url = f"https://www.picturethisai.com/wiki/plants?page={page_num}" if page_num > 1 else "https://www.picturethisai.com/wiki/plants"
        print(f"Scraping page: {url}")
        
        try:
            page.goto(url, timeout=60000, wait_until='domcontentloaded')
            page.wait_for_selector('a.plant-card', timeout=30000)

            page.mouse.wheel(0, 1500)  # Scroll to load images
            time.sleep(2)  # Allow time for images to load

            plant_cards = page.query_selector_all('a.plant-card')
            print(f"Found {len(plant_cards)} plants on page {page_num}")

            for card in plant_cards:
                try:
                    card.scroll_into_view_if_needed()

                    img = card.wait_for_selector('img.plant-card-image')
                    src = img.get_attribute('src')
                    image_url = src.split('?')[0] if src else ''
                    
                    plant_name = card.query_selector('.plant-card-content-title').inner_text().strip()
                    scientific_name = card.query_selector('.plant-card-content-description').inner_text().strip()
                    page_url = "https://www.picturethisai.com" + card.get_attribute('href')
                    
                    plants.append({
                        'plant_name': plant_name,
                        'scientific_name': scientific_name,
                        'image_url': image_url,
                        'page_url': page_url
                    })
                except Exception as e:
                    print(f"Error processing card: {str(e)}")
                    continue

        except Exception as e:
            print(f"Error loading page {page_num}: {str(e)}")
        
        browser.close()
        return plants

# API Endpoints
@app.route('/plants', methods=['GET'])
def get_plants():
    page = request.args.get('page', 1, type=int)  # Default to page 1 if no page param is provided
    plants_data = scrape_plants_page(page)
    
    if not plants_data:
        return jsonify({"error": "No plants found on this page"}), 404
    
    return jsonify(plants_data)

@app.route('/plant/<string:plant_name>', methods=['GET'])
def get_plant(plant_name):
    page = 1  # Start from page 1 for each search
    while True:
        plants_data = scrape_plants_page(page)
        plant = next((p for p in plants_data if plant_name.lower() in p['plant_name'].lower()), None)
        
        if plant:
            return jsonify(plant)
        
        if len(plants_data) == 0:  # No plants found
            return jsonify({"error": "Plant not found"}), 404
        
        page += 1  # Move to the next page

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
