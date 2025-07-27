class Student:
    def __init__(self, student_id, name, email, program):
        self.student_id = student_id
        self.name = name
        self.email = email
        self.program = program
        self.courses = {}  # {course: grade}

    def enroll(self, course):
        if course.is_full():
            course.add_to_waitlist(self)
            return False
        course.add_student(self)
        self.courses[course] = None
        return True

    def add_grade(self, course, grade):
        if course in self.courses:
            self.courses[course] = grade

    def get_gpa(self):
        grades = [g for g in self.courses.values() if g is not None]
        if not grades:
            return 0.0
        return sum(grades) / len(grades)

    def get_transcript(self):
        return {course.name: grade for course, grade in self.courses.items()}

    def __str__(self):
        return f"Student[{self.student_id}] {self.name} | {self.program}"

class Course:
    def __init__(self, name, instructor, enrollment_limit):
        self.name = name
        self.instructor = instructor
        self.enrollment_limit = enrollment_limit
        self.students = []
        self.waitlist = []
        self.grades = {}  # {student: grade}

    def add_student(self, student):
        if not self.is_full():
            self.students.append(student)
            self.grades[student] = None
            return True
        else:
            self.add_to_waitlist(student)
            return False

    def add_to_waitlist(self, student):
        if student not in self.waitlist:
            self.waitlist.append(student)

    def is_full(self):
        return len(self.students) >= self.enrollment_limit

    def add_grade(self, student, grade):
        if student in self.students:
            self.grades[student] = grade
            student.add_grade(self, grade)

    def get_enrollment_count(self):
        return len(self.students)

    def get_grades(self):
        return {student.name: grade for student, grade in self.grades.items() if grade is not None}

    def __str__(self):
        return f"Course: {self.name} | Instructor: {self.instructor} | Enrolled: {len(self.students)}/{self.enrollment_limit}"

class University:
    def __init__(self):
        self.students = []
        self.courses = []

    def add_student(self, student):
        self.students.append(student)

    def add_course(self, course):
        self.courses.append(course)

    def get_total_enrollments(self):
        return sum(len(course.students) for course in self.courses)

    def get_average_gpa(self):
        gpas = [student.get_gpa() for student in self.students if student.courses]
        if not gpas:
            return 0.0
        return sum(gpas) / len(gpas)

if __name__ == "__main__":
    # 1. Course Creation with Enrollment Limits
    math_course = Course("Mathematics", "Dr. Euler", 2)
    physics_course = Course("Physics", "Dr. Newton", 2)
    cs_course = Course("Computer Science", "Dr. Turing", 3)

    alice = Student("S001", "Alice", "alice@univ.edu", "Mathematics")
    bob = Student("S002", "Bob", "bob@univ.edu", "Physics")
    carol = Student("S003", "Carol", "carol@univ.edu", "CS")

    alice.enroll(math_course)
    bob.enroll(math_course)
    print("Math course enrollment:", math_course.get_enrollment_count())

    math_course.add_grade(alice, 90)
    math_course.add_grade(bob, 80)
    print("Alice GPA:", alice.get_gpa())
    print("Alice transcript:", alice.get_transcript())

    print("Math course grades:", math_course.get_grades())

    university = University()
    university.add_student(alice)
    university.add_student(bob)
    university.add_student(carol)
    university.add_course(math_course)
    university.add_course(physics_course)
    university.add_course(cs_course)
    print("Total enrollments:", university.get_total_enrollments())
    print("Average GPA:", university.get_average_gpa())

    for i in range(4, 7):
        s = Student(f"S00{i}", f"Student{i}", f"student{i}@univ.edu", "Math")
        enrolled = s.enroll(math_course)
        if not enrolled:
            print(f"{s.name} added to waitlist for {math_course.name}")
    print("Waitlist for Math:", [s.name for s in math_course.waitlist])
