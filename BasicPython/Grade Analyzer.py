# grade_analyzer.py

grades = [85, 92, 78, 90, 88, 76, 94, 89, 87, 91]

# 1. Slice grades from index 2 to 7
sliced_grades = grades[2:8]
print("1. Sliced grades (index 2 to 7):", sliced_grades)

# 2. List comprehension to find grades above 85
grades_above_85 = [g for g in grades if g > 85]
print("2. Grades above 85:", grades_above_85)

# 3. Replace the grade at index 3 with 95
grades[3] = 95
print("3. Grades after replacing index 3 with 95:", grades)

# 4. Append three new grades
grades.extend([82, 97, 88])
print("4. Grades after appending three new grades:", grades)

# 5. Sort in descending order and display the top 5 grades
sorted_desc = sorted(grades, reverse=True)
top_5 = sorted_desc[:5]
print("5. Top 5 grades (descending order):", top_5)
