import streamlit as st
from database import init_db
from ui import render_dashboard, render_products, render_stock, render_checkout, render_reports

st.set_page_config(page_title="Smart Inventory Manager", page_icon="📦", layout="wide")
init_db()

st.title("📦 Smart Inventory & Order Management System")
st.caption("Manage products, stock, billing, receipts, and sales reports.")

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Products", "Stock Entry", "Checkout & Receipts", "Reports"]
)

if page == "Dashboard":
    render_dashboard()
elif page == "Products":
    render_products()
elif page == "Stock Entry":
    render_stock()
elif page == "Checkout & Receipts":
    render_checkout()
elif page == "Reports":
    render_reports()

st.sidebar.divider()
st.sidebar.caption("Local app • Python + Streamlit + SQLite")
