
fruit_list = ["apple", "banana", "orange", "grape"]
fruit_tuple = ("apple", "banana", "orange", "grape")
fruit_set = {"apple", "banana", "orange", "grape"}
fruit_dict = {"apple": 10, "banana": 5, "orange": 8, "grape": 12}

structures = [
    ("List", fruit_list),
    ("Tuple", fruit_tuple),
    ("Set", fruit_set),
    ("Dict", fruit_dict)
]

print("1. Membership Test for 'apple':")
for name, struct in structures:
    if isinstance(struct, dict):
        present = "apple" in struct
    else:
        present = "apple" in struct
    print(f"{name}: {present}")

print("\n2. Length of Each Structure:")
for name, struct in structures:
    print(f"{name}: {len(struct)}")

print("\n3. Iterate and Print Elements:")
for name, struct in structures:
    print(f"{name}:")
    if isinstance(struct, dict):
        for key, value in struct.items():
            print(f"  {key}: {value}")
    else:
        for item in struct:
            print(f"  {item}")

print("\n4. Membership Testing Performance:")
print("Sets and dictionaries provide O(1) average time complexity for membership checks,")
print("while lists and tuples provide O(n) time complexity. This is because sets and dicts")
print("use hash tables for fast lookups, whereas lists and tuples require scanning each element.")

print("\n5. Different Iteration Patterns:")
print("List: for item in fruit_list")
for item in fruit_list:
    print(f"  {item}")

print("Tuple: for item in fruit_tuple")
for item in fruit_tuple:
    print(f"  {item}")

print("Set: for item in fruit_set")
for item in fruit_set:
    print(f"  {item}")

print("Dict: for key, value in fruit_dict.items()")
for key, value in fruit_dict.items():
    print(f"  {key}: {value}")
