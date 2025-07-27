
products = ["apples", "bananas", "oranges", "grapes"]
prices = [30, 10, 25, 40]
quantities = [15, 8, 20, 5]

product_price_pairs = list(zip(products, prices))
print("1. Product-Price Pairs:")
print(product_price_pairs)

print("\n2. Total Inventory Value for Each Product:")
for product, price, quantity in zip(products, prices, quantities):
    total_value = price * quantity
    print(f"{product}: {total_value}")

product_catalog = {}
for product, price, quantity in zip(products, prices, quantities):
    product_catalog[product] = {"price": price, "quantity": quantity}

print("\n3. Product Catalog Dictionary:")
print(product_catalog)

low_stock = [product for product, quantity in zip(products, quantities) if quantity < 10]
print("\n4. Low Stock Products (quantity < 10):")
print(low_stock)
