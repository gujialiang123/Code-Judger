import math
m, n, a = map(int, input().split())
while(1):
    a=a+1
print(math.ceil(m/a) * math.ceil(n/a))

