squareEven=[i*i for i in range(10) if i%2==0]
print(squareEven)

squareOdd = [i*i for i in range (10) if i%2==1]
print(squareOdd)

animal=["cat", "window", "dog", "table"]


filteranimal= [ i for i in animal if len(i)>3]

print(filteranimal)

capitalAnimal=list(map(str.capitalize,filteranimal))
print(capitalAnimal)
print(list(map(str.upper,capitalAnimal)))


print(sum(squareEven))


words = ["leet","code"]
x="e"
index_pos=[]
print(2**7)






