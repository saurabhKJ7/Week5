
inventory = {
    "apples": {"price": 10, "quantity": 120},
    "bananas": {"price": 5, "quantity": 80},
    "oranges": {"price": 8, "quantity": 150}
}

def add_product(name, price, quantity):
    inventory[name] = {"price": price, "quantity": quantity}
    print(f"Added product: {name}, Price: {price}, Quantity: {quantity}")

add_product("grapes", 15, 60)

def update_price(name, new_price):
    if name in inventory:
        inventory[name]["price"] = new_price
        print(f"Updated price of {name} to {new_price}")
    else:
        print(f"Product {name} not found.")

update_price("bananas", 7)

def sell_product(name, quantity_sold):
    if name in inventory and inventory[name]["quantity"] >= quantity_sold:
        inventory[name]["quantity"] -= quantity_sold
        print(f"Sold {quantity_sold} {name}. Remaining: {inventory[name]['quantity']}")
    else:
        print(f"Not enough {name} in stock or product not found.")

sell_product("apples", 25)

def total_inventory_value():
    total = sum(item["price"] * item["quantity"] for item in inventory.values())
    print(f"Total inventory value: {total}")
    return total

total_inventory_value()

def low_stock_products(threshold=100):
    low_stock = [name for name, item in inventory.items() if item["quantity"] < threshold]
    print(f"Low stock products (quantity < {threshold}): {low_stock}")
    return low_stock

low_stock_products()
