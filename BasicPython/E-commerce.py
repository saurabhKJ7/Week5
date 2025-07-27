from collections import defaultdict, Counter

class Product:
    def __init__(self, product_id, name, price, category, stock):
        self.product_id = product_id
        self.name = name
        self.price = price
        self.category = category
        self.stock = stock

    def reduce_stock(self, quantity):
        if quantity > self.stock:
            raise ValueError("Not enough stock available.")
        self.stock -= quantity

    def increase_stock(self, quantity):
        self.stock += quantity

    def __str__(self):
        return f"Product[{self.product_id}] {self.name} | ${self.price:.2f} | {self.category} | Stock: {self.stock}"

class Customer:
    MEMBERSHIP_DISCOUNTS = {
        "Regular": 0.0,
        "Silver": 0.05,
        "Gold": 0.10,
        "Platinum": 0.15
    }

    def __init__(self, customer_id, name, email, membership="Regular"):
        self.customer_id = customer_id
        self.name = name
        self.email = email
        self.membership = membership
        self.orders = []

    def get_discount_rate(self):
        return self.MEMBERSHIP_DISCOUNTS.get(self.membership, 0.0)

    def add_order(self, order):
        self.orders.append(order)

    def get_total_revenue(self):
        return sum(order.total_price for order in self.orders)

    def __str__(self):
        return f"Customer[{self.customer_id}] {self.name} | {self.email} | {self.membership}"

class ShoppingCart:
    def __init__(self):
        self.items = defaultdict(int)  # {Product: quantity}

    def add_item(self, product, quantity=1):
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        if product.stock < quantity:
            raise ValueError("Not enough stock for product.")
        self.items[product] += quantity

    def remove_item(self, product, quantity=1):
        if product not in self.items:
            return
        if quantity >= self.items[product]:
            del self.items[product]
        else:
            self.items[product] -= quantity

    def clear(self):
        self.items.clear()

    def get_total_items(self):
        return sum(self.items.values())

    def get_subtotal(self):
        return sum(product.price * qty for product, qty in self.items.items())

    def get_items(self):
        return [(product, qty) for product, qty in self.items.items()]

class Order:
    def __init__(self, customer, cart):
        self.customer = customer
        self.items = cart.get_items()
        self.total_price = 0
        self.status = "Pending"

    def place_order(self):
        # Check stock and reduce it
        for product, qty in self.items:
            if product.stock < qty:
                self.status = "Failed"
                return False
        for product, qty in self.items:
            product.reduce_stock(qty)
        # Calculate total with discount
        subtotal = sum(product.price * qty for product, qty in self.items)
        discount = self.customer.get_discount_rate()
        self.total_price = subtotal * (1 - discount)
        self.status = "Completed"
        self.customer.add_order(self)
        return True

class ECommerceSystem:
    def __init__(self):
        self.products = {}
        self.customers = {}
        self.orders = []
        self.category_counter = Counter()

    def add_product(self, product):
        self.products[product.product_id] = product

    def add_customer(self, customer):
        self.customers[customer.customer_id] = customer

    def place_order(self, customer_id, cart):
        customer = self.customers.get(customer_id)
        if not customer:
            raise ValueError("Customer not found.")
        order = Order(customer, cart)
        result = order.place_order()
        if result:
            self.orders.append(order)
            for product, qty in order.items:
                self.category_counter[product.category] += qty
        return order

    def get_most_popular_category(self):
        if not self.category_counter:
            return None
        return self.category_counter.most_common(1)[0][0]

    def get_customer_revenue(self, customer_id):
        customer = self.customers.get(customer_id)
        if not customer:
            return 0
        return customer.get_total_revenue()

if __name__ == "__main__":
    laptop = Product("P001", "Laptop", 1200, "Electronics", 10)
    book = Product("P002", "Book", 30, "Books", 50)
    shirt = Product("P003", "Shirt", 25, "Clothing", 20)
    print(laptop)

    # Test Case 2: Create Customer
    customer = Customer("C001", "John Doe", "john@example.com", "Gold")
    print(customer)
    print("Discount rate:", customer.get_discount_rate())

    cart = ShoppingCart()
    cart.add_item(laptop, 1)
    cart.add_item(book, 2)
    cart.add_item(shirt, 1)
    print("Total items in cart:", cart.get_total_items())
    print("Cart subtotal:", cart.get_subtotal())

    system = ECommerceSystem()
    system.add_product(laptop)
    system.add_product(book)
    system.add_product(shirt)
    system.add_customer(customer)
    order = system.place_order("C001", cart)
    print("Order total after discount:", order.total_price)

    print("Laptop stock before:", laptop.stock + 1)  # +1 because 1 was just reduced
    print("Laptop stock after:", laptop.stock)
    print("Order status:", order.status)

    print("Most popular category:", system.get_most_popular_category())
    print("Total revenue by customer:", system.get_customer_revenue("C001"))

    cart.add_item(book, 1)
    cart.remove_item(book, 1)
    print("Items in cart after removing a book:", cart.get_items())
    cart.clear()
    print("Total items after clearing cart:", cart.get_total_items())
