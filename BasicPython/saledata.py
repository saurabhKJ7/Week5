
quarters = [
    [("Jan", 1000), ("Feb", 1200), ("Mar", 1100)],
    [("Apr", 1300), ("May", 1250), ("Jun", 1400)],
    [("Jul", 1500), ("Aug", 1600), ("Sep", 1550)]
]

print("1. Total Sales per Quarter:")
for i, quarter in enumerate(quarters, 1):
    total = sum(sales for (month, sales) in quarter)
    print(f"  Quarter {i}: {total}")

all_months = [item for quarter in quarters for item in quarter]
max_month, max_sales = max(all_months, key=lambda x: x[1])
print(f"\n2. Month with Highest Sales: {max_month} ({max_sales})")

flat_monthly_sales = all_months
print("\n3. Flat List of Monthly Sales:")
print(flat_monthly_sales)

print("\n4. Unpacking in Loops (Month, Sales, Quarter):")
for q_idx, quarter in enumerate(quarters, 1):
    for month, sales in quarter:
        print(f"Quarter {q_idx}: {month} - {sales}")
