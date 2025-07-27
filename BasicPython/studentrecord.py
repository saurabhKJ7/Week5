
students = [
    (101, "Alice", 85, 20),
    (102, "Bob", 92, 21),
    (103, "Charlie", 78, 19),
    (104, "David", 88, 22),
    (105, "Eva", 95, 20)
]

top_student = max(students, key=lambda x: x[2])
print("1. Student with the Highest Grade:")
print(top_student)

name_grade_list = [(name, grade) for (_, name, grade, _) in students]
print("\n2. Name-Grade List:")
print(name_grade_list)

print("\n3. Demonstrate Tuple Immutability:")
try:
    students[0][2] = 90
except TypeError as e:
    print("Error:", e)
    print("Tuples are immutable, so you cannot change their elements directly.")
    print("Tuples are preferred for immutable records like student data because they prevent accidental modification.")

updated_student = (students[0][0], students[0][1], 90, students[0][3])
print("\nIf you need to update, create a new tuple:", updated_student)
