
students = ["Alice", "Bob", "Charlie", "David", "Eva"]
scores = [95, 88, 92, 76, 99]

print("1. Numbered List of Students:")
for idx, name in enumerate(students, 1):
    print(f"{idx}. {name}")

print("\n2. Students with Scores:")
for idx, (name, score) in enumerate(zip(students, scores), 1):
    print(f"{idx}. {name}: {score}")

high_scorer_indices = [idx for idx, score in enumerate(scores) if score > 90]
print("\n3. Positions of High Scorers (score > 90):")
print(high_scorer_indices)

position_to_name = {idx: name for idx, name in enumerate(students)}
print("\n4. Position to Student Name Mapping:")
print(position_to_name)
