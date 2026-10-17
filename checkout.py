from datetime import datetime
from database import get_connection

def checkout(cart, discount_percent=0.0, tax_percent=0.0):
    """
    cart: list of dictionaries with product_id and quantity.
    Stock validation and sale recording happen in one database transaction.
    """
    if not cart:
        raise ValueError("Add at least one item to the cart.")
    if not 0 <= discount_percent <= 100:
        raise ValueError("Discount must be between 0 and 100%.")
    if not 0 <= tax_percent <= 100:
        raise ValueError("Tax must be between 0 and 100%.")

    receipt_no = "INV-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    lines = []
    subtotal = 0.0

    with get_connection() as conn:
        for item in cart:
            product_id = int(item["product_id"])
            quantity = int(item["quantity"])
            if quantity <= 0:
                raise ValueError("Every item quantity must be greater than zero.")
            product = conn.execute(
                "SELECT id, name, price, stock FROM products WHERE id=?", (product_id,)
            ).fetchone()
            if product is None:
                raise ValueError("A selected product no longer exists.")
            if product["stock"] < quantity:
                raise ValueError(f"Not enough stock for {product['name']}. Available: {product['stock']}.")
            line_total = float(product["price"]) * quantity
            subtotal += line_total
            lines.append({
                "product_id": product_id, "name": product["name"],
                "quantity": quantity, "unit_price": float(product["price"]),
                "line_total": line_total
            })

        discount = round(subtotal * discount_percent / 100, 2)
        taxable_amount = subtotal - discount
        tax = round(taxable_amount * tax_percent / 100, 2)
        total = round(taxable_amount + tax, 2)

        cur = conn.execute(
            "INSERT INTO sales(receipt_no,subtotal,discount,tax,total) VALUES(?,?,?,?,?)",
            (receipt_no, round(subtotal, 2), discount, tax, total)
        )
        sale_id = cur.lastrowid

        for line in lines:
            conn.execute("UPDATE products SET stock=stock-? WHERE id=?",
                         (line["quantity"], line["product_id"]))
            conn.execute(
                "INSERT INTO sale_items(sale_id,product_id,product_name,quantity,unit_price,line_total) "
                "VALUES(?,?,?,?,?,?)",
                (sale_id, line["product_id"], line["name"], line["quantity"],
                 line["unit_price"], line["line_total"])
            )
            conn.execute(
                "INSERT INTO stock_movements(product_id,movement_type,quantity,note) VALUES(?,?,?,?)",
                (line["product_id"], "SALE", -line["quantity"], receipt_no)
            )

    return {
        "receipt_no": receipt_no, "lines": lines, "subtotal": round(subtotal, 2),
        "discount": discount, "tax": tax, "total": total
    }

def get_sales():
    import pandas as pd
    with get_connection() as conn:
        return pd.read_sql_query(
            "SELECT id, receipt_no, subtotal, discount, tax, total, created_at FROM sales ORDER BY id DESC",
            conn
        )

def get_sale_items(sale_id):
    import pandas as pd
    with get_connection() as conn:
        return pd.read_sql_query(
            "SELECT product_name, quantity, unit_price, line_total FROM sale_items WHERE sale_id=?",
            conn, params=(int(sale_id),)
        )
