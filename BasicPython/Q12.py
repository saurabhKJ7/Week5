

item1=int(input("Enter item 1: "))
quantity1=int(input("Enter quantity of item 1: "))
item2=int(input("Enter item 2: "))
quantity2=int(input("Enter quantity of item 2: "))
item3=int(input("Enter item 3: "))
quantity3=int(input("Enter quantity of item 3: "))

print(f"Item 1: {item1} x {quantity1} = {item1 * quantity1}")
print(f"Item 2: {item2} x {quantity2} = {item2 * quantity2}")
print(f"Item 3: {item3} x {quantity3} = {item3 * quantity3}")
subtotal=item1 * quantity1 + item2 * quantity2 + item3 * quantity3
tax=subtotal/8.5
total=subtotal + tax
print(f"Subtotal: {subtotal}")
print(f"Tax (8.5%): {tax}")
print(f"Total: {total}")


