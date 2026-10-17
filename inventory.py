import pandas as pd
from database import get_connection

def get_products():
    with get_connection() as conn:
        return pd.read_sql_query(
            "SELECT id, sku, name, category, price, stock, reorder_level, "
            "CASE WHEN stock <= reorder_level THEN 'LOW STOCK' ELSE 'OK' END AS status "
            "FROM products ORDER BY name", conn
        )

def add_product(sku, name, category, price, stock, reorder_level):
    sku, name = sku.strip(), name.strip()
    if not sku or not name:
        raise ValueError("SKU and product name are required.")
    if price < 0 or stock < 0 or reorder_level < 0:
        raise ValueError("Price, stock, and reorder level cannot be negative.")
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO products (sku,name,category,price,stock,reorder_level) VALUES (?,?,?,?,?,?)",
            (sku, name, category.strip() or "General", float(price), int(stock), int(reorder_level))
        )

def update_product(product_id, sku, name, category, price, reorder_level):
    if not sku.strip() or not name.strip():
        raise ValueError("SKU and product name are required.")
    if price < 0 or reorder_level < 0:
        raise ValueError("Price and reorder level cannot be negative.")
    with get_connection() as conn:
        conn.execute(
            "UPDATE products SET sku=?, name=?, category=?, price=?, reorder_level=? WHERE id=?",
            (sku.strip(), name.strip(), category.strip() or "General", float(price), int(reorder_level), int(product_id))
        )

def record_restock(product_id, quantity, note="Restock"):
    if quantity <= 0:
        raise ValueError("Restock quantity must be greater than zero.")
    with get_connection() as conn:
        cur = conn.execute("UPDATE products SET stock=stock+? WHERE id=?", (int(quantity), int(product_id)))
        if cur.rowcount == 0:
            raise ValueError("Product not found.")
        conn.execute(
            "INSERT INTO stock_movements(product_id,movement_type,quantity,note) VALUES(?,?,?,?)",
            (int(product_id), "RESTOCK", int(quantity), note)
        )

def get_stock_movements():
    with get_connection() as conn:
        return pd.read_sql_query("""
            SELECT sm.id, p.sku, p.name, sm.movement_type, sm.quantity, sm.note, sm.created_at
            FROM stock_movements sm JOIN products p ON p.id=sm.product_id
            ORDER BY sm.id DESC
        """, conn)
