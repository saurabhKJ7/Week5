square=[]
for i in range (10):
    square.append(i*i)
print(square)

square = [i*i for i in range(10)]
print(square)

odd = [i for i in range(10) if i % 2 == 1]
print(odd)

pair=[(x,y) for x in range(3) for y in range(2)]
print(pair)