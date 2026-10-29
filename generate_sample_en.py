# -*- coding: utf-8 -*-
"""Generate sample_sales_data_en.xlsx (500 orders) — English version for quick trials."""
import pandas as pd
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

cities = ["New York", "London", "Tokyo", "Berlin", "Sydney",
          "Toronto", "Singapore", "Paris", "Dubai", "Seoul"]
products = ["Laptop", "Wireless Earbuds", "Mechanical Keyboard", "Monitor",
            "Mouse", "USB Drive", "Webcam", "Smart Watch"]
categories = {"Laptop": "Computer", "Wireless Earbuds": "Audio",
              "Mechanical Keyboard": "Peripherals", "Monitor": "Computer",
              "Mouse": "Peripherals", "USB Drive": "Storage",
              "Webcam": "Peripherals", "Smart Watch": "Wearables"}
channels = ["Online Flagship", "JD Self-run", "Offline Store",
            "Livestream", "Tmall Supermarket"]
customer_levels = ["Regular", "Silver", "Gold", "Diamond"]

price_map = {"Laptop": (4000, 12000), "Wireless Earbuds": (200, 2000),
             "Mechanical Keyboard": (300, 1500), "Monitor": (800, 4000),
             "Mouse": (50, 500), "USB Drive": (30, 200),
             "Webcam": (150, 800), "Smart Watch": (800, 3000)}

rows = []
start_date = datetime(2024, 1, 1)
for i in range(500):
    product = random.choice(products)
    lo, hi = price_map[product]
    unit_price = round(random.uniform(lo, hi), 2)
    qty = random.randint(1, 5)
    cost = round(unit_price * random.uniform(0.5, 0.75), 2)
    discount = round(random.uniform(0.7, 1.0), 2)
    amount = round(unit_price * qty * discount, 2)
    order_date = start_date + timedelta(days=random.randint(0, 364))
    rows.append({
        "Order ID": f"ORD{20240001 + i:08d}",
        "Order Date": order_date.strftime("%Y-%m-%d"),
        "City": random.choice(cities),
        "Channel": random.choice(channels),
        "Product": product,
        "Category": categories[product],
        "Customer Level": random.choice(customer_levels),
        "Unit Price": unit_price,
        "Quantity": qty,
        "Discount": discount,
        "Cost": round(cost * qty, 2),
        "Sales Amount": amount,
        "Profit": round(amount - cost * qty, 2),
    })

df = pd.DataFrame(rows)
out = Path(__file__).parent / "sample_sales_data_en.xlsx"
df.to_excel(out, index=False, sheet_name="Sales Orders", engine="openpyxl")
print(f"✅ English sample generated: {out}  ({len(df)} rows x {len(df.columns)} cols)")
