def celsius_to_fahrenheit(celsius):
    return celsius * 9 / 5 + 32

def fahrenheit_to_kelvin(fahrenheit):
    return (fahrenheit - 32) * 5 / 9 + 273.15

def kelvin_to_celsius(kelvin):
    return kelvin - 273.15


print("celsius_to_fahrenheit  ->", celsius_to_fahrenheit(0))        
print("fahrenheit_to_kelvin  ->", fahrenheit_to_kelvin(32))
print("kelvin_to_celsius ->", kelvin_to_celsius(300))
