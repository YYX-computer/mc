from tempfile import mkstemp
from pipe import Pipe_api
p = Pipe_api()
class Event:
	def __init__(self,type,*arg):
		self.type = type
		self.__arg = arg
		if(type == 'removeblock' or type == 'setblock'):
			x1,y1,z1,x2,y2,z2 = arg
			self.x,self.y,self.z = float(x1),float(y1),float(z1)
			self.x2,self.y2,self.z2 = float(x2),float(y2),float(z2)
		elif(type == 'keypress'):
			self.key = int(arg[0])
		elif(type == 'mouseclick'):
			x,y,btn = arg
			self.x,self.y,self.button = float(x),float(y),float(btn)
		elif(type == 'mousemove'):
			x1,y1,x2,y2 = arg
			self.x1,self.y1,self.x2,self.y2 = float(x1),float(y1),float(x2),float(y2)
		elif(type == 'mousedrag'):
			x1,y1,x2,y2,btn = arg
			self.x1,self.y1,self.x2,self.y2,self.button = float(x1),float(y1),float(x2),float(y2),float(btn)
		elif(type == 'mousescroll'):
			y1,y2 = arg
			self.y1,self.y2 = float(y1),float(y2)
		else:
			self.type = 'NONE'
	def __str__(self):
		return self.__repr__()
	def __repr__(self):
		arg = ','.join(self.__arg)
		return 'Event(%s,%s)'%(self.type,arg)
class player:
	def __init__(self,ip):
		self.player = ip
	def give(self,blk):
		p.send('give %s %s'%(self.player,blk))
	def get_inventory(self):
		p.send('get_inventory %s'%self.player)
		res = ''
		while(res == ''):
			res = p.recv()
		try:
			return eval(res)
		except:
			return None
	def set_inventory(self,inv):
		p.send('set_inventory %s %s'%(self.player,inv))
	def setPos(self,x,y,z):
		p.send('setPos %s %s %s %s'%(self.player,x,y,z))
	def getPos(self):
		p.send('getPos %s'%self.player)
		res = ''
		while(res == ''):
			res = p.recv()
		try:
			return eval(res)
		except:
			return None
	def getHolding(self):
		p.send('getHolding %s'%self.player)
		res = ''
		while(res == ''):
			res = p.recv()
		try:
			return eval(res)
		except:
			return None
	def setHolding(self,pos):
		p.send('setHolding %s %s'%(self.player,pos))
	def hurt(self):
		p.send('hurt %s'%self.player)
	def hunger(self):
		p.send('hunger %s'%self.player)
	def get_blood(self):
		p.send('get_blood %s'%self.player)
		res = ''
		while(res == ''):
			res = p.recv()
		try:
			return eval(res)
		except:
			return None
	def get_hunger(self):
		p.send('get_blood %s'%self.player)
		res = ''
		while(res == ''):
			res = p.recv()
		try:
			return eval(res)
		except:
			return None
	def kill(self):
		p.send('kill %s'%self.player)
def getSectorSize():
	p.send('getSectorSize')
	res = ''
	while(res == ''):
		res = p.recv()
	try:
		return eval(res)
	except:
		return None
def setSectorSize(x,y,z):
	p.send('setSectorSize %s %s %s'%(x,y,z))
def setblock(x,y,z,blk):
	p.send('setblock %s %s %s %s'%(x,y,z,blk))
def removeblock(x,y,z):
	p.send('removeblock %s %s %s'%(x,y,z))
def getblock(x,y,z):
	p.send('getblock %s %s %s'%(x,y,z))
	res = ''
	while(res == ''):
		res = p.recv()
	return res if(res != ' ') else None
def get_height(x,z):
	p.send('get_height %s %s'%(x,z))
	res = ''
	while(res == ''):
		res = p.recv()
	try:
		return eval(res)
	except:
		return None
def set_config(label,value):
	p.send('set_config %s %s'%(label,value))
def get_config(label):
	p.send('get_config %s'%label)
	res = ''
	while(res == ''):
		res = p.recv()
	return None if(res == ' ') else res
def get_event():
	p.send('get_event')
	res = ''
	while(res == ''):
		res = p.recv()
	ev = Event(*res.split(' '))
	return ev
def change_block_properties(blk,prop,val):
	p.send('change_block_properties %s %s %s'%(blk,prop,val))
def get_block_properties(blk,prop):
	p.send('get_block_properties %s %s'%(blk,prop))
	res = ''
	while(res == ''):
		res = p.recv()
	return None if(res == ' ') else res
def get_window_size():
	p.send('get_window_size')
	res = ''
	while(res == ''):
		res = p.recv()
	return None if(res == ' ') else tuple([int(i) for i in res.split(' ')])
