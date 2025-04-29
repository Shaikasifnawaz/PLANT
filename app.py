from playwright.sync_api import sync_playwright
from flask import Flask, jsonify, request
import time

app = Flask(__name__)

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

def scrape_plant_details(page_url):
    plant_details = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = context.new_page()
        
        try:
            page.goto(page_url, timeout=60000, wait_until='domcontentloaded')
            
            # Extracting plant name and scientific name
            plant_details['plant_name'] = page.query_selector('.description-main-left-title').inner_text().strip()
            plant_details['scientific_name'] = page.query_selector('.scientific-name-item-text').inner_text().strip()

            # Extracting other name
            other_name_elem = page.query_selector('.other-name')
            if other_name_elem:
                other_name = other_name_elem.inner_text().strip().split(': ')[1]
                plant_details['other_names'] = [name.strip() for name in other_name.split(',')]
            else:
                plant_details['other_names'] = []

            # Extracting description
            description_elem = page.query_selector('.des-content')
            if description_elem:
                description = description_elem.inner_text().strip().replace('\n', ' ')
                plant_details['description'] = description
            else:
                plant_details['description'] = ''

            # Extracting scientific classification
            scientific_classification = {}
            scientific_items = page.query_selector_all('.scientific-name-item')
            for item in scientific_items:
                title = item.query_selector('.scientific-name-item-title').inner_text().strip().lower()
                text = item.query_selector('.scientific-name-item-text').inner_text().strip()
                scientific_classification[title] = text
            plant_details['scientific_classification'] = scientific_classification

            # Extracting key facts
            key_facts = {}
            key_fact_items = page.query_selector_all('.key-fact')
            for item in key_fact_items:
                title_elem = item.query_selector('.key-fact-title')
                text_elem = item.query_selector('.key-fact-text')
                if title_elem and text_elem:
                    title = title_elem.inner_text().strip().replace('\n', ' ').lower()
                    text = text_elem.inner_text().strip().replace('\n', ' ').lower()
                    key_facts[text] = title
            plant_details['key_facts'] = key_facts

            # Extracting distribution information
            distribution_map_elem = page.query_selector('.layout-wrap-item-content-sub-content')
            if distribution_map_elem:
                distribution_map = distribution_map_elem.inner_text().strip().replace('\n', ' ')
                plant_details['distribution_map'] = distribution_map
            else:
                plant_details['distribution_map'] = ''

            # Extracting habitat
            habitat_elem = page.query_selector('.layout-wrap-item-content-sub-content')
            if habitat_elem:
                habitat = habitat_elem.inner_text().strip().replace('\n', ' ')
                plant_details['habitat'] = habitat
            else:
                plant_details['habitat'] = ''

            # Extracting care guide
            care_guide = {}
            care_guide_items = page.query_selector_all('.layout-wrap-item-content-sub-content')
            for item in care_guide_items:
                title_elem = item.query_selector('b')
                if title_elem:
                    title = title_elem.inner_text().strip().replace(':', '')
                    text = item.inner_text().strip().replace('\n', ' ').split(f'{title}: ')[1]
                    care_guide[title.lower()] = text
            plant_details['care_guide'] = care_guide

            # Extracting common pests and diseases
            pests_diseases = [link.inner_text().strip() for link in page.query_selector_all('.links-wrap-content')]
            plant_details['common_pests_and_diseases'] = pests_diseases

            # Extracting gallery images
            gallery_images = []
            gallery_items = page.query_selector_all('.gallery-item-image')
            for img in gallery_items:
                src = img.get_attribute('src')
                image_url = src.split('?')[0] if src else ''
                gallery_images.append(image_url)
            plant_details['gallery_images'] = gallery_images

        except Exception as e:
            print(f"Error loading page {page_url}: {str(e)}")
        
        browser.close()
        return plant_details

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
            # Fetch detailed information for the plant
            plant_details = scrape_plant_details(plant['page_url'])
            return jsonify(plant_details)
        
        if len(plants_data) == 0:  # No plants found
            return jsonify({"error": "Plant not found"}), 404
        
        page += 1  # Move to the next page

if __name__ == '__main__':
    app.run(debug=True)