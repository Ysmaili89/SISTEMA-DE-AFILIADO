import requests
from app import db
from models import Product, Subcategory
from utils import slugify

def fetch_and_update_products_from_external_api(api_url):
    """
    Fetches and updates products from an external API.
    Handles both existing product updates and new product additions.
    """
    try:
        # --- REAL WORLD SCENARIO (uncomment and modify for actual API integration) ---
        response = requests.get(api_url, timeout=10)  # Add a timeout
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        external_data = response.json()  # Assuming the API returns JSON
        simulated_external_products = external_data  # Use the actual data from the API

    except requests.exceptions.Timeout:
        raise ConnectionError("Request to the external API has timed out (10 seconds).")
    except requests.exceptions.ConnectionError:
        raise ConnectionError(f"Could not connect to the API URL: {api_url}. Check the address or your connection.")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error fetching data from API: {e}")
    except ValueError as e:
        raise ValueError(f"Error parsing API response as JSON: {e}")

    # --- SIMULATED EXTERNAL API RESPONSE (for demonstration - REMOVE IN PRODUCTION) ---
    if "platformA" in api_url:
        simulated_external_products = [
            {
                "external_id": "EXT001",
                "name": "Ultrabook Laptop X1 (Updated from A)",
                "external_price": "$1180",
                "external_description": "Powerful professional laptop with 16GB RAM and 1TB SSD. Synced from Platform A.",
                "external_image": "/static/img/laptop_a.jpg",
                "external_link": "https://example.com/platformA/laptop-x1"
            },
            {
                "external_id": "EXT005",
                "name": "Pro Curved Monitor",
                "external_price": "$450",
                "external_description": "27-inch 144Hz curved monitor for gaming.",
                "external_image": "/static/img/monitor.jpg",
                "external_link": "https://example.com/platformA/monitor-curvo"
            }
        ]
    elif "platformB" in api_url:
        simulated_external_products = [
            {
                "external_id": "EXT002",
                "name": "Bluetooth Headphones Z2 (Updated from B)",
                "external_price": "$75",
                "external_description": "Noise-cancelling headphones with improved battery. Synced from Platform B.",
                "external_image": "/static/img/headphones_b.jpg",
                "external_link": "https://example.com/platformB/auriculares-z2"
            },
            {
                "external_id": "EXT006",
                "name": "RGB Mechanical Keyboard",
                "external_price": "$120",
                "external_description": "Mechanical keyboard with red switches and RGB backlighting.",
                "external_image": "/static/img/keyboard.jpg",
                "external_link": "https://example.com/platformB/teclado-rgb"
            }
        ]
    else:
        simulated_external_products = [
            {
                "external_id": "EXT001",
                "name": "Ultrabook Laptop X1 (Default Sim.)",
                "external_price": "$1150",
                "external_description": "Powerful professional laptop, now with 1TB SSD.",
                "external_image": "/static/img/laptop_new.jpg",
                "external_link": "https://example.com/laptop-x1-updated"
            },
            {
                "external_id": "EXT004",
                "name": "Smartwatch Pro S",
                "external_price": "$250",
                "external_description": "Advanced smartwatch with health monitoring.",
                "external_image": "/static/img/smartwatch.jpg",
                "external_link": "https://example.com/smartwatch-pro-s"
            },
            {
                "external_id": "EXT002",
                "name": "Bluetooth Headphones Z2",
                "external_price": "$79",
                "external_description": "Noise-cancelling headphones with 20 hours of battery.",
                "external_image": "/static/img/headphones.jpg",
                "external_link": "https://example.com/auriculares-z2"
            }
        ]

    updated_count = 0
    default_subcategory = Subcategory.query.first()

    for external_p_data in simulated_external_products:
        product = Product.query.filter_by(external_id=external_p_data["external_id"]).first()
        try:
            processed_price = float(external_p_data['external_price'].replace('$', '').replace('€', '').replace(',', ''))
        except ValueError:
            print(f"Warning: Could not convert price '{external_p_data['external_price']}' for product '{external_p_data['name']}'. Using 0.0.")
            processed_price = 0.0

        if product:
            product.name = external_p_data['name']
            product.slug = slugify(external_p_data['name'])
            product.price = processed_price
            product.description = external_p_data['external_description']
            product.image = external_p_data['external_image']
            product.link = external_p_data['external_link']
            updated_count += 1
        else:
            if not default_subcategory:
                print("Warning: No subcategories defined. Cannot add new products from the API.")
                continue

            new_product = Product(
                name=external_p_data['name'],
                slug=slugify(external_p_data['name']),
                price=processed_price,
                description=external_p_data['external_description'],
                image=external_p_data['external_image'],
                link=external_p_data['external_link'],
                subcategory_id=default_subcategory.id,
                external_id=external_p_data['external_id']
            )
            db.session.add(new_product)
            updated_count += 1
    db.session.commit()
    return updated_count