import pandas as pd
from database import get_connection

def sales_by_day():
    with get_connection() as conn:
        return pd.read_sql_query("""
            SELECT date(created_at) AS day, ROUND(SUM(total),2) AS sales, COUNT(*) AS orders
            FROM sales GROUP BY date(created_at) ORDER BY day
        """, conn)

def best_sellers():
    with get_connection() as conn:
        return pd.read_sql_query("""
            SELECT product_name, SUM(quantity) AS units_sold, ROUND(SUM(line_total),2) AS revenue
            FROM sale_items GROUP BY product_id, product_name
            ORDER BY units_sold DESC LIMIT 10
        """, conn)

def inventory_value():
    with get_connection() as conn:
        return pd.read_sql_query("""
            SELECT category, COUNT(*) AS products, SUM(stock) AS units,
                   ROUND(SUM(stock * price),2) AS inventory_value
            FROM products GROUP BY category ORDER BY category
        """, conn)
