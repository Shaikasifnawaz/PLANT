import requests
import random
from math import radians, cos, sin, asin, sqrt

STORES = ["Walmart", "Target", "Costco", "Whole Foods", "Giant Eagle"]

def fetch_item_data(query, zipcode, eco_mode=False):
    results = []

    for store in STORES:
        try:
            # Mock price and availability
            price = f"${round(random.uniform(1, 10), 2)}"
            available = random.choice([True, True, True, False])  # 75% availability

            # Eco label logic
            eco_label = None
            if eco_mode:
                if 'organic' in query.lower():
                    eco_label = "🌱 Organic"
                elif 'local' in query.lower():
                    eco_label = "🏡 Local"

            # Calculate distance
            distance = calculate_distance(zipcode, store)

            results.append({
                "store": store,
                "price": price,
                "available": available,
                "distance": distance,
                "eco": eco_label
            })

        except Exception as e:
            print(f"Error processing {store}: {str(e)}")
            continue

    return {
        "item": query,
        "stores": sorted(results, key=lambda x: float(x['distance'].split()[0]))
    }

def calculate_distance(user_zip, store_name):
    try:
        # Get user location details
        user_url = f"https://nominatim.openstreetmap.org/search?postalcode={user_zip}&format=json&limit=1"
        user_response = requests.get(user_url, headers={"User-Agent": "Mozilla/5.0"})
        user_data = user_response.json()
        
        if not user_data:
            return "9999.99 miles"
        
        user_loc = user_data[0]
        address = user_loc.get('address', {})
        
        # Extract location context
        city = address.get('city') or address.get('town') or address.get('village')
        state = address.get('state')
        if not city or not state:
            return "9999.99 miles"

        # Find nearest store location
        store_query = f"{store_name} in {city}, {state}"
        store_url = f"https://nominatim.openstreetmap.org/search?q={store_query}&format=json&limit=1"
        store_response = requests.get(store_url, headers={"User-Agent": "Mozilla/5.0"})
        store_data = store_response.json()

        if not store_data:
            return "9999.99 miles"

        store_loc = store_data[0]

        # Calculate distance
        lat1, lon1 = float(user_loc['lat']), float(user_loc['lon'])
        lat2, lon2 = float(store_loc['lat']), float(store_loc['lon'])

        dlon = radians(lon2 - lon1)
        dlat = radians(lat2 - lat1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        return f"{round(c * 3956, 2)} miles"

    except Exception as e:
        print(f"Distance error: {str(e)}")
        return "9999.99 miles"