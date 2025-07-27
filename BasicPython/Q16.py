try:
    age = int(input("Enter your age (1-120): "))
    if(age>120):
        print("Out of range. Please enter a number between 1 and 120.")
    else:
        print(f"Age: {age}")

except Exception as e:
    print("Invalid input. Please enter a valid number.")


