import requests
from app import db
from models import Product, Subcategory
from utils import slugify

def fetch_and_update_products_from_external_api(api_url):
    """
    Obtiene y actualiza productos desde una API externa.
    Maneja tanto las actualizaciones de productos existentes como las adiciones de nuevos productos.
    """
    try:
        # --- REAL WORLD SCENARIO (uncomment and modify for actual API integration) ---
        response = requests.get(api_url, timeout=10) # Add a timeout
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        external_data = response.json() # Assuming the API returns JSON
        simulated_external_products = external_data # Use the actual data from the API

    except requests.exceptions.Timeout:
        raise ConnectionError("La solicitud a la API externa ha excedido el tiempo de espera (10 segundos).")
    except requests.exceptions.ConnectionError:
        raise ConnectionError(f"No se pudo conectar a la URL de la API: {api_url}. Verifique la dirección o su conexión.")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error al obtener datos de la API: {e}")
    except ValueError as e:
        raise ValueError(f"Error al parsear la respuesta de la API como JSON: {e}")

    # --- SIMULATED EXTERNAL API RESPONSE (for demonstration - REMOVE IN PRODUCTION) ---
    if "platformA" in api_url:
        simulated_external_products = [
            {
                "external_id": "EXT001",
                "name": "Laptop Ultrabook X1 (Actualizado de A)",
                "external_price": "$1180",
                "external_description": "Potente laptop para profesionales con 16GB RAM y 1TB SSD. Sincronizado de Plataforma A.",
                "external_image": "/static/img/laptop_a.jpg",
                "external_link": "https://example.com/platformA/laptop-x1"
            },
            {
                "external_id": "EXT005",
                "name": "Monitor Curvo Pro",
                "external_price": "$450",
                "external_description": "Monitor de 27 pulgadas curvo 144Hz para gaming.",
                "external_image": "/static/img/monitor.jpg",
                "external_link": "https://example.com/platformA/monitor-curvo"
            }
        ]
    elif "platformB" in api_url:
        simulated_external_products = [
            {
                "external_id": "EXT002",
                "name": "Auriculares Bluetooth Z2 (Actualizado de B)",
                "external_price": "$75",
                "external_description": "Auriculares con cancelación de ruido, batería mejorada. Sincronizado de Plataforma B.",
                "external_image": "/static/img/headphones_b.jpg",
                "external_link": "https://example.com/platformB/auriculares-z2"
            },
            {
                "external_id": "EXT006",
                "name": "Teclado Mecánico RGB",
                "external_price": "$120",
                "external_description": "Teclado mecánico con switches rojos y retroiluminación RGB.",
                "external_image": "/static/img/keyboard.jpg",
                "external_link": "https://example.com/platformB/teclado-rgb"
            }
        ]
    else:
        simulated_external_products = [
            {
                "external_id": "EXT001",
                "name": "Laptop Ultrabook X1 (Default Sim.)",
                "external_price": "$1150",
                "external_description": "Potente laptop para profesionales, ahora con SSD de 1TB.",
                "external_image": "/static/img/laptop_new.jpg",
                "external_link": "https://example.com/laptop-x1-updated"
            },
            {
                "external_id": "EXT004",
                "name": "Smartwatch Pro S",
                "external_price": "$250",
                "external_description": "Smartwatch avanzado con monitoreo de salud.",
                "external_image": "/static/img/smartwatch.jpg",
                "external_link": "https://example.com/smartwatch-pro-s"
            },
            {
                "external_id": "EXT002",
                "name": "Auriculares Bluetooth Z2",
                "external_price": "$79",
                "external_description": "Auriculares con cancelación de ruido y 20 horas de batería.",
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
            print(f"Advertencia: No se pudo convertir el precio '{external_p_data['external_price']}' para el producto '{external_p_data['name']}'. Se usará 0.0.")
            processed_price = 0.0

        if product: # Corregido: 'Si el producto:' a 'if product:'
            product.name = external_p_data['name'] # Corregido: 'nombre' a 'name'
            product.slug = slugify(external_p_data['name']) # Corregido: 'nombre' a 'name'
            product.price = processed_price # Corregido: 'producto.precio' a 'product.price'
            product.description = external_p_data['external_description']
            product.image = external_p_data['external_image']
            product.link = external_p_data['external_link']
            updated_count += 1
        else: # Corregido: 'más:' a 'else:'
            if not default_subcategory: # Corregido: 'si no' a 'if not'
                print("Advertencia: No hay subcategorías definidas. No se pueden añadir nuevos productos de la API.")
                continue # Corregido: 'continuar'

            new_product = Product( # Corregido: 'Producto' a 'Product'
                name=external_p_data['name'], # Corregido: 'nombre' a 'name'
                slug=slugify(external_p_data['name']), # Corregido: 'nombre' a 'name'
                price=processed_price, # Corregido: 'precio' a 'price'
                description=external_p_data['external_description'],
                image=external_p_data['external_image'],
                link=external_p_data['external_link'],
                subcategory_id=default_subcategory.id,
                external_id=external_p_data['external_id']
            )
            db.session.add(new_product)
            updated_count += 1
    db.session.commit() # Corregido: 'db.sesión.commit()' a 'db.session.commit()'
    return updated_count # Corregido: 'devolver updated_count' a 'return updated_count'