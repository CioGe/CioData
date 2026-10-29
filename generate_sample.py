# -*- coding: utf-8 -*-
"""生成示例销售数据.xlsx（500条订单），用于快速体验工具。"""
import pandas as pd
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安", "南京", "重庆"]
products = ["笔记本电脑", "无线耳机", "机械键盘", "显示器", "鼠标", "U盘", "摄像头", "智能手表"]
categories = {"笔记本电脑": "电脑", "无线耳机": "音频", "机械键盘": "外设", "显示器": "电脑",
              "鼠标": "外设", "U盘": "存储", "摄像头": "外设", "智能手表": "穿戴"}
channels = ["线上旗舰店", "京东自营", "线下门店", "抖音直播", "天猫超市"]
customer_levels = ["普通会员", "银卡会员", "金卡会员", "钻石会员"]

rows = []
start_date = datetime(2024, 1, 1)
for i in range(500):
    product = random.choice(products)
    price_map = {"笔记本电脑": (4000, 12000), "无线耳机": (200, 2000), "机械键盘": (300, 1500),
                 "显示器": (800, 4000), "鼠标": (50, 500), "U盘": (30, 200),
                 "摄像头": (150, 800), "智能手表": (800, 3000)}
    price_lo, price_hi = price_map[product]
    unit_price = round(random.uniform(price_lo, price_hi), 2)
    qty = random.randint(1, 5)
    cost = round(unit_price * random.uniform(0.5, 0.75), 2)
    discount = round(random.uniform(0.7, 1.0), 2)
    amount = round(unit_price * qty * discount, 2)
    order_date = start_date + timedelta(days=random.randint(0, 364))
    rows.append({
        "订单编号": f"ORD{20240001 + i:08d}",
        "订单日期": order_date.strftime("%Y-%m-%d"),
        "城市": random.choice(cities),
        "渠道": random.choice(channels),
        "商品名称": product,
        "商品类别": categories[product],
        "客户等级": random.choice(customer_levels),
        "单价": unit_price,
        "数量": qty,
        "折扣": discount,
        "成本": cost * qty,
        "销售额": amount,
        "利润": round(amount - cost * qty, 2),
    })

df = pd.DataFrame(rows)
out = Path(__file__).parent / "示例销售数据.xlsx"
df.to_excel(out, index=False, sheet_name="销售订单", engine="openpyxl")
print(f"✅ 已生成示例数据: {out}  ({len(df)}行 × {len(df.columns)}列)")
