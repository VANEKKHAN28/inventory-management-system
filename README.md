# Smart Inventory & Order Management System

A local inventory and billing application built with Python, Streamlit, SQLite (`sqlite3`), and Pandas.

## Features
- Product catalog: SKU, name, category, unit price, quantity, reorder threshold
- Stock restocking and movement history
- Low-stock alerts on the dashboard
- Checkout with quantity validation, discounts, and tax
- Stock deduction and sales records in a single database transaction
- Downloadable text receipts
- CSV exports and sales/best-seller/inventory-value reports
- SQLite database created automatically as `inventory.db`

## Requirements
- Python 3.10 or newer recommended
- Internet connection for the first install of dependencies

## Setup on Windows (VS Code)
1. Extract `inventory_app.zip`.
2. Open the extracted `inventory_app` folder in VS Code.
3. Open Terminal → New Terminal.
4. (Optional but recommended) create a virtual environment:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   If PowerShell blocks activation, use Command Prompt and run:
   ```bat
   .venv\Scripts\activate.bat
   ```
5. Install packages:
   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```
6. Start the app:
   ```bash
   python -m streamlit run main.py
   ```
7. Streamlit opens a local browser tab. If it does not, copy the local URL printed in the terminal (usually `http://localhost:8501`).

## First use
1. Open **Products** and add products with unique SKUs.
2. Use **Stock Entry** to record new deliveries.
3. Use **Checkout & Receipts** to add items to the cart and complete a sale.
4. Download the receipt after checkout.
5. Use **Dashboard** for low-stock alerts and **Reports** for summaries.

## Database
`inventory.db` is created beside `main.py` automatically on first run. Back it up regularly. Deleting it removes the stored application data.

## Notes
- Tax is a configurable percentage and defaults to 0%; enter the rate appropriate for your project/demo.
- Inventory value is current on-hand stock multiplied by current unit price. It is not a historical inventory valuation chart.
- This is a starter project for a small local shop/demo. It does not include user login, cloud sync, or multi-user concurrency controls.
