
def add_item(cart, item):
    cart.append(item)
    print(f'Added "{item}" to the cart.')

def remove_item(cart, item):
    if item in cart:
        cart.remove(item)
        print(f'Removed "{item}" from the cart.')
    else:
        print(f'Item "{item}" not found in the cart.')

def remove_last_item(cart):
    if cart:
        removed = cart.pop()
        print(f'Removed last added item: "{removed}"')
    else:
        print("Cart is already empty.")

def display_sorted(cart):
    print("Cart items in alphabetical order:")
    for item in sorted(cart):
        print(item)

def display_with_indices(cart):
    print("Cart contents with indices:")
    for idx, item in enumerate(cart):
        print(f"{idx}: {item}")


cart = []

add_item(cart, "apples")
add_item(cart, "bread")
add_item(cart, "milk")
add_item(cart, "eggs")

remove_item(cart, "bread")

remove_last_item(cart)

display_sorted(cart)

display_with_indices(cart)
