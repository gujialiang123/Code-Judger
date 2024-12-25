import os
import time

for id in range(1, 21):
	print(id)
	os.system("gen")
	os.system("std")
	os.system("ren in.txt "+str(id)+".in")
	os.system("ren out.txt "+str(id)+".ans")
	time.sleep(1)
