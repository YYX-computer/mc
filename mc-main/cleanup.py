import os
open('api.txt','w').close()
open('window.txt','w').close()
try:
	os.remove('fault')
except:
	pass
