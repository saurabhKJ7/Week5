
school = {
    "ClassA": {
        "teacher": "Mrs. Smith",
        "students": {
            "Alice": 88,
            "Bob": 92,
            "Charlie": 79
        }
    },
    "ClassB": {
        "teacher": "Mr. Johnson",
        "students": {
            "David": 85,
            "Eva": 95,
            "Frank": 90
        }
    },
    "ClassC": {
        "teacher": "Ms. Lee",
        "students": {
            "Grace": 91,
            "Helen": 87,
            "Ian": 93
        }
    }
}

print("1. Teacher Names:")
for class_info in school.values():
    print(class_info["teacher"])

print("\n2. Class Average Grades:")
for class_name, class_info in school.items():
    grades = list(class_info["students"].values())
    avg = sum(grades) / len(grades)
    print(f"{class_name}: {avg:.2f}")

top_student = None
top_grade = -1
for class_info in school.values():
    for student, grade in class_info["students"].items():
        if grade > top_grade:
            top_grade = grade
            top_student = student

print(f"\n3. Top Student Across All Classes: {top_student} ({top_grade})")

print("\n4. Student Names and Grades (using unpacking):")
for class_name, class_info in school.items():
    print(f"{class_name}:")
    for student, grade in class_info["students"].items():
        # Unpacking student and grade
        print(f"  {student}: {grade}")
