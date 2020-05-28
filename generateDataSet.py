import random
MAX = 10
 

for i in range(5):
	for j in range(7):
		file_name = str(MAX) + "data" + str(i) +".txt"
		f = open(file_name, "w")
		f.write(str(random.randint(0,MAX)) + "\n")
		f.close()
		for i in range(MAX):
			f = open(file_name, "a")
			f.write(str(random.randint(0,MAX)) + "\n")
			f.close()
		MAX = MAX * 10
