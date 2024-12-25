import math
import time
time.sleep(0.5)
m, n, a = map(int, input().split())
print(math.ceil(m/a) * math.ceil(n/a))

