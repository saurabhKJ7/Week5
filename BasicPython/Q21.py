
def custom_map(func, iterable):
    result = []
    for item in iterable:
        result.append(func(item))
    return result

def custom_filter(func, iterable):
    result = []
    for item in iterable:
        if func(item):
            result.append(item)
    return result

def custom_reduce(func, iterable, initializer=None):
    it = iter(iterable)
    if initializer is None:
        try:
            value = next(it)
        except StopIteration:
            raise TypeError('reduce() of empty sequence with no initial value')
    else:
        value = initializer
    for item in it:
        value = func(value, item)
    return value


numbers = [1, 2, 3, 4, 5]

squared = custom_map(lambda x: x * x, numbers)
print("Squared:", squared)  # Output: [1, 4, 9, 16, 25]

evens = custom_filter(lambda x: x % 2 == 0, numbers)
print("Evens:", evens)  # Output: [2, 4]

total = custom_reduce(lambda x, y: x + y, numbers)
print("Sum:", total)  # Output: 15
