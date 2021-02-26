class Pipe_api:
	def __init__(self):
		self.r = open('window.txt')
		self.w = open('api.txt','a')
		self.serial = 0
		f = open('api.txt')
		while(1):
			line = f.readline()
			if(line == ''):
				break
			else:
				n = int(line.split(':')[0])
				self.serial = max(self.serial,n)
		self.serial += 1
		self.send('')
	def recv(self):
		while(1):
			line = self.r.readline()
			if(line.startswith(str(self.serial)) or line == ''):
				break
		return ':'.join(line.split(':')[1:])[:-1]
	def send(self,val):
		self.w.write(str(self.serial) + ':' + val + '\n')
		self.w.flush()
class Pipe_window:
	def __init__(self):
		self.r = open('api.txt')
		self.w = open('window.txt','a')
		self.last = ''
	def recv(self):
		line = self.r.readline()
		res = ':'.join(line.split(':')[1:])
		self.last = line.split(':')[0]
		return res[:-1]
	def send(self,val):
		self.w.write(self.last + ':' + val + '\n')
		self.w.flush()
