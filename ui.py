import pandas as pd
import streamlit as st
from inventory import get_products, add_product, update_product, record_restock, get_stock_movements
from checkout import checkout
from reports import sales_by_day, best_sellers, inventory_value
from database import get_connection

def money(value):
    return f"₹{float(value):,.2f}"

def render_dashboard():
    products = get_products()
    with get_connection() as conn:
        totals = conn.execute("""
            SELECT COUNT(*) AS products, COALESCE(SUM(stock),0) AS units,
                   COALESCE(SUM(stock*price),0) AS value FROM products
        """).fetchone()
        today = conn.execute(
            "SELECT COALESCE(SUM(total),0) FROM sales WHERE date(created_at)=date('now','localtime')"
        ).fetchone()[0]
        low = conn.execute("SELECT COUNT(*) FROM products WHERE stock <= reorder_level").fetchone()[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Products", totals["products"])
    c2.metric("Units in stock", totals["units"])
    c3.metric("Inventory value", money(totals["value"]))
    c4.metric("Today's sales", money(today))
    st.subheader("Low-stock alerts")
    low_items = products[products["status"] == "LOW STOCK"] if not products.empty else products
    if low_items.empty:
        st.success("No low-stock products.")
    else:
        st.warning(f"{len(low_items)} product(s) need attention.")
        st.dataframe(low_items[["sku","name","category","stock","reorder_level"]], use_container_width=True, hide_index=True)

def render_products():
    st.subheader("Product catalog")
    with st.expander("Add a product", expanded=False):
        with st.form("add_product_form", clear_on_submit=True):
            a,b = st.columns(2)
            sku = a.text_input("Item ID / SKU")
            name = b.text_input("Product name")
            category = a.text_input("Category", value="General")
            price = b.number_input("Unit price (₹)", min_value=0.0, step=1.0, format="%.2f")
            stock = a.number_input("Opening stock", min_value=0, step=1)
            reorder = b.number_input("Minimum stock / reorder point", min_value=0, step=1, value=5)
            submitted = st.form_submit_button("Add product")
            if submitted:
                try:
                    add_product(sku, name, category, price, stock, reorder)
                    st.success("Product added.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not add product: {e}")

    products = get_products()
    st.dataframe(products, use_container_width=True, hide_index=True)
    if not products.empty:
        st.download_button("Export products as CSV", products.to_csv(index=False).encode("utf-8"),
                           "products.csv", "text/csv")
        st.markdown("#### Edit product details")
        choices = {f'{r["sku"]} — {r["name"]} (ID {r["id"]})': int(r["id"]) for _,r in products.iterrows()}
        selected = st.selectbox("Choose product", list(choices))
        row = products[products["id"] == choices[selected]].iloc[0]
        with st.form("edit_product_form"):
            a,b = st.columns(2)
            sku = a.text_input("SKU", value=str(row["sku"]))
            name = b.text_input("Name", value=str(row["name"]))
            category = a.text_input("Category", value=str(row["category"]))
            price = b.number_input("Price (₹)", min_value=0.0, value=float(row["price"]), step=1.0)
            reorder = a.number_input("Reorder level", min_value=0, value=int(row["reorder_level"]), step=1)
            if st.form_submit_button("Save product changes"):
                try:
                    update_product(int(row["id"]), sku, name, category, price, reorder)
                    st.success("Product updated.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not update product: {e}")

def render_stock():
    st.subheader("Stock entry")
    products = get_products()
    if products.empty:
        st.info("Add a product before recording stock.")
        return
    choices = {f'{r["sku"]} — {r["name"]} (stock: {r["stock"]})': int(r["id"]) for _,r in products.iterrows()}
    with st.form("restock_form"):
        selected = st.selectbox("Product", list(choices))
        qty = st.number_input("Quantity received", min_value=1, step=1)
        note = st.text_input("Note / supplier", value="Restock")
        if st.form_submit_button("Record restock"):
            try:
                record_restock(choices[selected], int(qty), note)
                st.success("Stock updated.")
                st.rerun()
            except Exception as e:
                st.error(str(e))
    st.markdown("#### Stock movement history")
    movements = get_stock_movements()
    st.dataframe(movements, use_container_width=True, hide_index=True)
    if not movements.empty:
        st.download_button("Export stock movements", movements.to_csv(index=False).encode("utf-8"),
                           "stock_movements.csv", "text/csv")

def render_checkout():
    st.subheader("Checkout & billing")
    products = get_products()
    if products.empty:
        st.info("Add products before checkout.")
        return
    if "cart" not in st.session_state:
        st.session_state.cart = []
    options = {f'{r["sku"]} — {r["name"]} | {money(r["price"])} | stock {r["stock"]}': r
               for _,r in products.iterrows() if int(r["stock"]) > 0}
    if not options:
        st.warning("No products currently have stock.")
        return
    with st.form("cart_add_form"):
        chosen = st.selectbox("Product", list(options))
        quantity = st.number_input("Quantity", min_value=1, step=1)
        if st.form_submit_button("Add to cart"):
            product = options[chosen]
            already = sum(x["quantity"] for x in st.session_state.cart if x["product_id"] == int(product["id"]))
            if int(quantity) + already > int(product["stock"]):
                st.error(f"Only {int(product['stock'])} unit(s) available, including items already in cart.")
            else:
                st.session_state.cart.append({"product_id": int(product["id"]), "name": str(product["name"]),
                                              "quantity": int(quantity), "price": float(product["price"])})
                st.success("Added to cart.")

    if st.session_state.cart:
        st.markdown("#### Current cart")
        cart_df = pd.DataFrame([{
            "Product": x["name"], "Quantity": x["quantity"], "Unit price": x["price"],
            "Line total": x["quantity"] * x["price"]
        } for x in st.session_state.cart])
        st.dataframe(cart_df, use_container_width=True, hide_index=True)
        subtotal = sum(x["quantity"] * x["price"] for x in st.session_state.cart)
        st.write("Subtotal:", money(subtotal))
        a,b = st.columns(2)
        discount = a.number_input("Discount (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0)
        tax = b.number_input("Tax (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0)
        st.caption(f"Estimated total: {money(subtotal * (1-discount/100) * (1+tax/100))}")
        c1,c2 = st.columns(2)
        if c1.button("Complete sale", type="primary"):
            try:
                receipt = checkout(st.session_state.cart, discount, tax)
                st.session_state.last_receipt = receipt
                st.session_state.cart = []
                st.success(f"Sale complete. Receipt: {receipt['receipt_no']}")
                st.rerun()
            except Exception as e:
                st.error(f"Sale not completed: {e}")
        if c2.button("Clear cart"):
            st.session_state.cart = []
            st.rerun()

    receipt = st.session_state.get("last_receipt")
    if receipt:
        st.markdown("#### Latest receipt")
        receipt_lines = [
            "SMART INVENTORY & ORDER MANAGEMENT SYSTEM",
            f"Receipt: {receipt['receipt_no']}",
            "",
            "Item | Qty | Unit price | Total",
            "-" * 48
        ]
        for x in receipt["lines"]:
            receipt_lines.append(f"{x['name']} | {x['quantity']} | {money(x['unit_price'])} | {money(x['line_total'])}")
        receipt_lines += [
            "-" * 48, f"Subtotal: {money(receipt['subtotal'])}",
            f"Discount: -{money(receipt['discount'])}", f"Tax: {money(receipt['tax'])}",
            f"TOTAL: {money(receipt['total'])}", "", "Thank you!"
        ]
        receipt_text = "\n".join(receipt_lines)
        st.code(receipt_text)
        st.download_button("Download receipt (.txt)", receipt_text, f"{receipt['receipt_no']}.txt", "text/plain")

def render_reports():
    st.subheader("Sales reports")
    daily = sales_by_day()
    if daily.empty:
        st.info("No sales have been recorded yet.")
    else:
        st.markdown("#### Sales by day")
        st.dataframe(daily, use_container_width=True, hide_index=True)
        st.bar_chart(daily.set_index("day")["sales"])
        st.download_button("Export daily sales CSV", daily.to_csv(index=False).encode("utf-8"),
                           "daily_sales.csv", "text/csv")
    st.markdown("#### Best-selling products")
    best = best_sellers()
    if best.empty:
        st.info("Best sellers will appear after the first sale.")
    else:
        st.dataframe(best, use_container_width=True, hide_index=True)
        st.bar_chart(best.set_index("product_name")["units_sold"])
    st.markdown("#### Current inventory value by category")
    values = inventory_value()
    if values.empty:
        st.info("Add products to see inventory value.")
    else:
        st.dataframe(values, use_container_width=True, hide_index=True)
        st.bar_chart(values.set_index("category")["inventory_value"])
