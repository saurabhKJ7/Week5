
square = lambda x: x * x
factorial_approx = lambda n: 1 if n == 0 else n * factorial_approx(n - 1)

reverse_string = lambda s: s[::-1]
to_uppercase = lambda s: s.upper()

filter_evens = lambda lst: list(filter(lambda x: x % 2 == 0, lst))
sum_of_list = lambda lst: sum(lst)


print("Square of 5:", square(5))  # Output: 25
print("Factorial approximation of 5:", factorial_approx(5))  # Output: 120

print("Reverse of 'hello':", reverse_string('hello'))  # Output: 'olleh'
print("Uppercase of 'hello':", to_uppercase('hello'))  # Output: 'HELLO'

sample_list = [1, 2, 3, 4, 5, 6]
print("Even numbers in [1,2,3,4,5,6]:", filter_evens(sample_list))  # Output: [2, 4, 6]
print("Sum of [1,2,3,4,5,6]:", sum_of_list(sample_list))  # Output: 21
