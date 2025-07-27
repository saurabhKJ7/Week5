
employees = [
    ("Alice", 70000, "HR"),
    ("Bob", 85000, "Engineering"),
    ("Charlie", 65000, "Marketing"),
    ("David", 90000, "Engineering"),
    ("Eva", 75000, "HR"),
    ("Frank", 80000, "Marketing"),
    ("Grace", 95000, "Engineering")
]

sorted_by_salary_asc = sorted(employees, key=lambda x: x[1])
sorted_by_salary_desc = sorted(employees, key=lambda x: x[1], reverse=True)

print("1. Sorted by Salary (Ascending):")
for emp in sorted_by_salary_asc:
    print(emp)

print("\n1. Sorted by Salary (Descending):")
for emp in sorted_by_salary_desc:
    print(emp)

sorted_by_dept_salary = sorted(employees, key=lambda x: (x[2], x[1]))
print("\n2. Sorted by Department, Then by Salary:")
for emp in sorted_by_dept_salary:
    print(emp)

reversed_employees = list(reversed(employees))
print("\n3. Reversed List of Employees:")
for emp in reversed_employees:
    print(emp)

sorted_by_name_length = sorted(employees, key=lambda x: len(x[0]))
print("\n4. Sorted by Name Length:")
for emp in sorted_by_name_length:
    print(emp)

print("\n5. Demonstrate sorted() vs .sort():")
print("Original list before .sort():")
print(employees)

employees.sort(key=lambda x: x[1])  # Sort by salary ascending
print("\nOriginal list after .sort() by salary (Ascending):")
print(employees)

employees = [
    ("Alice", 70000, "HR"),
    ("Bob", 85000, "Engineering"),
    ("Charlie", 65000, "Marketing"),
    ("David", 90000, "Engineering"),
    ("Eva", 75000, "HR"),
    ("Frank", 80000, "Marketing"),
    ("Grace", 95000, "Engineering")
]
print("\nOriginal list restored:")
print(employees)
