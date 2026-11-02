from flask import Flask, request, jsonify
from prometheus_flask_exporter import PrometheusMetrics
import psycopg2
import psycopg2.extras
import redis
import json
import time

from prometheus_client import Counter

sales_counter = Counter('inventory_sales_total', 'Total product sales', ['product_id'])

app = Flask(__name__)
metrics = PrometheusMetrics(app)

redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)
DB_CONFIG = {
    'host': 'postgres',
    'database': 'transactions',
    'user': 'postgres',
    'password': 'postgres'
}

def get_db():
    return psycopg2.connect(**DB_CONFIG)

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": "inventory"}), 200

@app.route("/products")
def get_products():
    # Try cache first
    cached = redis_client.get("products:all")
    if cached:
        return jsonify({
            "products": json.loads(cached),
            "source": "cache"
        }), 200
    
    # Query database
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM products ORDER BY id")
    products = cur.fetchall()
    cur.close()
    conn.close()
    
    # Convert to JSON-serializable
    products_list = []
    for p in products:
        products_list.append({
            'id': p['id'],
            'name': p['name'],
            'description': p['description'],
            'price': float(p['price']),
            'stock': p['stock']
        })
    
    # Cache for 5 minutes
    redis_client.setex("products:all", 300, json.dumps(products_list))
    
    return jsonify({
        "products": products_list,
        "source": "database"
    }), 200

@app.route("/product/<int:product_id>")
def get_product(product_id):
    # Try cache
    cache_key = f"product:{product_id}"
    cached = redis_client.get(cache_key)
    if cached:
        return jsonify(json.loads(cached)), 200
    
    # Query database
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cur.fetchone()
    cur.close()
    conn.close()
    
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    product_data = {
        'id': product['id'],
        'name': product['name'],
        'description': product['description'],
        'price': float(product['price']),
        'stock': product['stock']
    }
    
    # Cache for 1 minute (stock changes frequently)
    redis_client.setex(cache_key, 60, json.dumps(product_data))
    
    return jsonify(product_data), 200

@app.route("/product/<int:product_id>/reserve", methods=['POST'])
def reserve_stock(product_id):
    data = request.json
    quantity = data.get('quantity', 1)
    
    if quantity <= 0:
        return jsonify({"error": "Invalid quantity"}), 400
    
    conn = get_db()
    cur = conn.cursor()
    
    # Check stock
    cur.execute("SELECT stock FROM products WHERE id = %s", (product_id,))
    result = cur.fetchone()
    
    if not result:
        cur.close()
        conn.close()
        return jsonify({"error": "Product not found"}), 404
    
    current_stock = result[0]
    
    if current_stock < quantity:
        cur.close()
        conn.close()
        return jsonify({"error": "Insufficient stock"}), 400
    
    # Reserve stock
    cur.execute("""
        UPDATE products 
        SET stock = stock - %s 
        WHERE id = %s
    """, (quantity, product_id))

    sales_counter.labels(product_id=str(product_id)).inc(quantity)
    
    conn.commit()
    cur.close()
    conn.close()
    
    # Invalidate cache
    redis_client.delete(f"product:{product_id}")
    redis_client.delete("products:all")

    
    
    return jsonify({
        "reserved": quantity,
        "product_id": product_id
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8003)