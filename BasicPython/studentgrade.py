from collections import defaultdict

class GradeManager:
    def __init__(self):
        # Structure: {student_name: {subject: [grades]}}
        self.data = defaultdict(lambda: defaultdict(list))

    def add_grade(self, student_name, subject, grade):
        """
        Add a grade for a specific student in a specific subject.
        """
        self.data[student_name][subject].append(grade)

    def get_student_average(self, student_name):
        """
        Calculate the average grade for a specific student across all subjects.
        Returns 0 if the student is not found.
        """
        subjects = self.data.get(student_name)
        if not subjects:
            return 0
        all_grades = []
        for grades in subjects.values():
            all_grades.extend(grades)
        if not all_grades:
            return 0
        return sum(all_grades) / len(all_grades)

    def get_subject_statistics(self, subject):
        """
        Retrieve statistics for a specific subject across all students.
        Returns a dictionary with average, highest, lowest grades, and student count.
        """
        grades = []
        for student in self.data:
            grades.extend(self.data[student].get(subject, []))
        if not grades:
            return {
                "average": 0,
                "highest": 0,
                "lowest": 0,
                "student_count": 0
            }
        return {
            "average": sum(grades) / len(grades),
            "highest": max(grades),
            "lowest": min(grades),
            "student_count": len([student for student in self.data if subject in self.data[student]])
        }

    def get_top_students(self, n=3):
        """
        Retrieve the top N students based on their overall average.
        Returns a list of tuples: (student_name, average_grade)
        """
        averages = []
        for student in self.data:
            avg = self.get_student_average(student)
            averages.append((student, avg))
        averages.sort(key=lambda x: x[1], reverse=True)
        return averages[:n]

    def get_failing_students(self, passing_grade=60):
        """
        Identify students who are failing based on a specified passing grade.
        Returns a list of tuples: (student_name, average_grade)
        """
        failing = []
        for student in self.data:
            avg = self.get_student_average(student)
            if avg < passing_grade:
                failing.append((student, avg))
        return failing

if __name__ == "__main__":
    manager = GradeManager()
    grades_data = {
        "Alice": {"Math": 95, "Science": 88, "English": 92},
        "Bob": {"Math": 67, "Science": 73, "English": 70},
        "Charlie": {"Math": 85, "Science": 90, "English": 87},
        "Diana": {"Math": 58, "Science": 60, "English": 55},
        "Eve": {"Math": 100, "Science": 98, "English": 99}
    }
    for student, subjects in grades_data.items():
        for subject, grade in subjects.items():
            manager.add_grade(student, subject, grade)

    print("Average grade for Alice:", manager.get_student_average("Alice"))
    print("Statistics for Math:", manager.get_subject_statistics("Math"))
    print("Top students:", manager.get_top_students())
    print("Failing students (passing grade 75):", manager.get_failing_students(75))
