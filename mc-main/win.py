from threading import Timer as singleTimer
from pipe import Pipe_window
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *
from PIL import Image
from signal import *
import faulthandler
import numpy as np
import requests
import atexit
import socket
import pickle
import copy
import math
import json
import time
import sys
faulthandler.enable(file = open('fault','w+'),all_threads = True)
signal(SIGINT,SIG_IGN)
class Queue:
	def __init__(self,init=[]):
		self.__q = init
	def push(self,*val):
		self.__q.append(val)
	def pop(self):
		return self.__q.pop(0)
class Timer(singleTimer):
	def run(self):
		while(not self.finished.is_set()):
			self.function(*self.args,**self.kwargs)
			self.finished.wait(self.interval)
def exitFunc(win):
	win.save()
class Model:
	def __init__(self):
		self.origin = [0.0,0.0,0.0]
		self.length = 1.
		self.yangle = 0.
		self.zangle = 0.
		self.mouselocation = [0.0,0.0]
		self.offset = 0.01
		self.zangle = 0. if not self.__bthree else math.pi
		glutInit()
		glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)
		glutInitWindowSize(640,480)
		self.window = glutCreateWindow(b'Minecraft')
		self.InitGl()
		self.sector = {}
		self.tex = {}
		self.z = 0.0
		self.y = 0.0
		self.z = 0.0
		self.mx = 0
		self.my = 0
		self.px = 0
		self.py = 0
		self.pz = 0
		self.flyEnabled = True
		self.flying = False
		self.selectFunc = lambda n:0
		self.moveFunc = lambda x,y,z:0
		self.hurtFunc = lambda n:0
		self.digFunc = lambda x,y,z:0
		self.placeFunc = lambda placePoint,pickPoint:0
		self.isEntity = lambda x,y,z:0
		self.wheelpos = 0
		self.dragfrom = (None,None)
		self.evq = Queue()
		self.names = {}
		glutDisplayFunc(self.Draw)
		glutIdleFunc(self.Draw)
		glutKeyboardFunc(self.keypress)
		glutPassiveMotionFunc(self.mouse)
		glutMouseFunc(self.mousePress)
		try:
			glutMouseWheelFunc(self.wheel)
		except:
			pass
	__bthree = False
	def event(self,type,*arg):
		self.evq.push(type,*arg)
	def wheel(self,wheel,dire,x,y):
		self.event('mousescroll',self.wheelpos,self.wheelpos + dire)
		self.wheelpos += dire
	def eye(self):
		return self.origin if not self.__bthree else self.direction()
	def target(self):
		return self.origin if self.__bthree else self.direction()
	def direction(self):
		len = 1. if not self.__bthree else self.length if 0. else 1.
		xy = math.cos(self.yangle) * len
		x = self.origin[0] + xy * math.sin(self.zangle)
		y = self.origin[1] + len * math.sin(self.yangle)
		z = self.origin[2] + xy * math.cos(self.zangle)		
		return [x,y,z]
	def move(self,x,y,z):
		sinz,cosz = math.sin(self.zangle),math.cos(self.zangle)		
		xstep,zstep = x * cosz + z * sinz,z * cosz - x * sinz
		if self.__bthree : 
			xstep = -xstep
			zstep = -zstep
		self.moveFunc(xstep / 2,y / 2,zstep / 2)
		self.origin = [self.origin[0] + xstep,self.origin[1] + y,self.origin[2] + zstep]		
		return x,y,z
	def rotate(self,z,y):
		self.zangle,self.yangle = self.zangle - z,self.yangle + y if not self.__bthree else -y
	def setLookat(self):
		ve,vt = self.eye(),self.target()
		glLoadIdentity()
		gluLookAt(ve[0],ve[1],ve[2],vt[0],vt[1],vt[2],0.0,1.0,0.0)
	def keypress(self,key, x, y):
		self.event('keypress',key)
		if key in (b'w', b'W'):
			move = self.move(0.,0.,-2.)
		elif key in (b'd', b'D'):
			move = self.move(2.,0.,0.)
		elif key in (b'a', b'A'):
			move = self.move(-2,0.,0.)
		elif key in (b's', b'S'):
			move = self.move(0.,0.,2.)
		elif key == b' ':
			move = self.move(0.,2.,0.)
		elif key == b'\t':
			self.flying = not self.flying
			return
		try:
			n = int(key.decode())
			self.selectFunc(n)
			return
		except:
			pass
		_x,_y,_z = self.origin[0],self.origin[1] - 2,self.origin[2]
		if((_x,_y,_z) in self.sector and not self.isEntity(_x,_y,_z)):
			tx,ty,tz = move[0] * -1,move[1] * -1,move[2] * -1
			self.move(tx,ty,tz)
	def mouse(self,x,y):
		self.event('mousemove',*self.mouselocation,x,y)
		rx = (x - self.mouselocation[0]) * self.offset
		ry = (y - self.mouselocation[1]) * self.offset
		self.rotate(rx,ry)
		self.mouselocation = [x,y]
	def hit_test(self,x,y):
		buffer_size = 512
		viewport = glGetIntegerv(GL_VIEWPORT)
		aspect_rat = (viewport[2] - viewport[0]) / (viewport[3] - viewport[1])
		glSelectBuffer(buffer_size)
		glRenderMode(GL_SELECT)
		glInitNames()
		glPushName(0)
		glMatrixMode(GL_PROJECTION)
		glPushMatrix()
		glLoadIdentity()
		gluPickMatrix(x,viewport[3] - y,5,5,viewport)
		self.Draw(True)
		glPopMatrix()
		glMatrixMode(GL_MODELVIEW)
		glFlush()
		buf = list(glRenderMode(GL_RENDER))
		print(buf)
		if(buf):
			pos = self.names[buf[0][2]]
			print(pos)
			return (None,None,None),(None,None,None)
		else:
			return (None,None,None),(None,None,None)
	def mousePress(self,button,state,x,y):
		if(state == GLUT_DOWN):
			self.dragfrom = (x,y)
		else:
			fx,fy = self.dragfrom
			if(self.dragfrom != (x,y)):
				self.event('mousedrag',fx,fy,x,y,button)
			return
		self.event('mouseclick',x,y,button)
		pos,next = self.hit_test(x,y)
		try:
			assert all(next)
			assert all(pos)
		except:
			return
		if(pos == (None,None,None) or button == 1 or state == 1):return
		elif(button == 0):
			self.event('removeblock',*pos)
			self.digFunc(*pos)
		else:
			self.event('setblock',*pos)
			self.placeFunc(next,pos)
	def setSector(self,sector):
		self.sector = {}
		for i in sector:
			j = i[0] * 2,i[1] * 2,i[2] * 2
			self.sector[j] = sector[i]
	def configureSelect(self,func):
		self.selectFunc = func
	def configureMove(self,func):
		self.moveFunc = func
	def configureHurtFunc(self,func):
		self.hurtFunc = func
	def configureDig(self,func):
		self.digFunc = func
	def configurePlace(self,func):
		self.placeFunc = func
	def configureIsEntity(self,func):
		self.isEntity = func
	def _Drawblock(self,name,pos,nameit):
		x,y,z = pos
		vertex = [[[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]],[[-1,-1,-1],[-1,1,-1],[1,1,-1],[1,-1,-1]],[[-1,1,-1],[-1,1,1],[1,1,1],[1,1,-1]],[[-1,-1,-1],[1,-1,-1],[1,-1,1],[-1,-1,1]],[[1,-1,-1],[1,1,-1],[1,1,1],[1,-1,1]],[[-1,-1,-1],[-1,-1,1],[-1,1,1],[-1,1,-1]]]
		for i in range(6):
			for j in range(4):
				vertex[i][j][0] += x
				vertex[i][j][1] += y
				vertex[i][j][2] += z
		for i in range(len(vertex)):
			glBindTexture(GL_TEXTURE_2D, self.tex[name] + i)
			if(nameit):
				name = max(self.names.keys())
				self.names[name] = pos
			glBegin(GL_QUADS)
			glTexCoord2f(0.0, 0.0)
			glVertex3f(*vertex[i][0])
			glTexCoord2f(1.0, 0.0)
			glVertex3f(*vertex[i][1])
			glTexCoord2f(1.0, 1.0)
			glVertex3f(*vertex[i][2])
			glTexCoord2f(0.0, 1.0)
			glVertex3f(*vertex[i][3])
			glEnd()
			if(nameit):
				glLoadName(name)
				glPopName()
	def Draw(self,nameit = False):
		if(nameit):
			glMatrixMode(GL_MODELVIEW)
		#if(not ((int(self.origin[0]),int(self.origin[1]) - 1,int(self.origin[2])) in self.sector or self.flying)):
		#	self.move(0,-2,0)
		#	self.hurtFunc(0.5)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		glLoadIdentity()
		glTranslate(0.0, 0.0, -5.0)
		self.setLookat()
		for i in self.sector:
			try:
				self._Drawblock(self.sector[i],i,nameit)
			except:
				pass
		glutSwapBuffers()
		if(nameit):
			glMatrixMode(GL_PROJECTION)
	def LoadTexture(self,textures):
		n = 0
		for i in textures:
			self.tex[i] = int(n)
			t = ["front", "back", "top",  "bottom", "left", "right"]
			tex = []
			for j in t:
				tex.append(textures[i][j])
			for j in range(len(tex)):
				img = Image.open(tex[j])
				if(j in (1,4)):
					img = img.rotate(270)
				width, height = img.size
				try:
					img = img.tobytes('raw','RGBA',0,-1)
					glGenTextures(2)
					glBindTexture(GL_TEXTURE_2D, n)
					glTexImage2D(GL_TEXTURE_2D, 0, 4,width,height, 0, GL_RGBA,GL_UNSIGNED_BYTE,img)
				except:
					img = img.tobytes('raw','RGB',0,-1)
					glGenTextures(2)
					glBindTexture(GL_TEXTURE_2D, n)
					glTexImage2D(GL_TEXTURE_2D, 0, 4,width,height, 0, GL_RGB,GL_UNSIGNED_BYTE,img)
				glTexParameterf(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S, GL_CLAMP)
				glTexParameterf(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T, GL_CLAMP)
				glTexParameterf(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S, GL_REPEAT)
				glTexParameterf(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T, GL_REPEAT)
				glTexParameterf(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER, GL_NEAREST)
				glTexParameterf(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER, GL_NEAREST)
				glTexEnvf(GL_TEXTURE_ENV,GL_TEXTURE_ENV_MODE, GL_DECAL)
				n += 1
	def InitGl(self):
		glEnable(GL_DEPTH_TEST)
		glEnable(GL_TEXTURE_2D)
		glClearDepth(1.0)
		glDepthFunc(GL_LESS)
		glShadeModel(GL_SMOOTH)
		glEnable(GL_CULL_FACE)
		glCullFace(GL_BACK)
		glEnable(GL_POINT_SMOOTH)
		glEnable(GL_LINE_SMOOTH)
		glEnable(GL_POLYGON_SMOOTH)
		glMatrixMode(GL_PROJECTION)
		glHint(GL_POINT_SMOOTH_HINT,GL_NICEST)
		glHint(GL_LINE_SMOOTH_HINT,GL_NICEST)
		glHint(GL_POLYGON_SMOOTH_HINT,GL_FASTEST)
		glLoadIdentity()
		gluPerspective(45.0,640 / 480, 0.1, 100.0)
		glMatrixMode(GL_MODELVIEW)
	def mainloop(self):
		glutMainLoop()
class Map:
	def __init__(self,map,pos = (0,0,0),secSize = (8,8,8)):
		self.map = map
		self.pos = pos
		self.sectorSize = secSize
		self.sector = {}
		self.init()
	def setSectorSize(self,x,y,z):
		self.sectorSize = (x,y,z)
	def getSectorRange(self):
		x,y,z = self.pos
		sx,sy,sz = self.sectorSize
		bx,ex = x - sx,x + sx
		by,ey = y - sy,y + sy
		bz,ez = z - sy,z + sz
		return bx,ex,by,ey,bz,ez
	def getSectorSize(self):
		return self.sectorSize
	def getMap(self):
		return self.map
	def getSector(self):
		return self.sector
	def init(self):
		self.sector = {}
		bx,ex,by,ey,bz,ez = self.getSectorRange()
		for tx in range(bx,ex + 1):
			for ty in range(by,ey + 1):
				for tz in range(bz,ez + 1):
					if((tx,ty,tz) in self.map):
						self.sector[(tx,ty,tz)] = self.map[(tx,ty,tz)]
	def insert(self,block,pos):
		pos = tuple(pos)
		self.map[pos] = block
		bx,ex,by,ey,bz,ez = self.getSectorRange()
		xr = range(bx,ex + 1)
		yr = range(by,ey + 1)
		zr = range(bz,ez + 1)
		x,y,z = pos
		if(x in xr and y in yr and z in zr):
			self.sector[pos] = block
	def pop(self,pos):
		block = self.map.pop(pos)
		if(pos in self.sector):
			self.sector.pop(pos)
		return block
	def __dict_filter(self,d,f):
		items = d.items()
		items = filter(lambda l:f(*l),items)
		d = dict(items)
		return d
	def move(self,dx,dy,dz):
		x,y,z = self.pos
		x,y,z = x + dx,y + dy,z + dz
		self.pos = round(x),round(y),round(z)
		self.init()
class Config:
	def __init__(self,config):
		self.config = config
		self.__setattr__ = self.setattr_overloading_func
	def __getattr__(self,attr):
		if(attr in self.config):
			return self.config[attr]
		else:
			raise AttributeError('No config about {0}'.format(attr))
	def setattr_overloading_func(self,attr,val):
		if(attr in self.config):
			self.config[attr] = val
		else:
			raise AttributeError('No config about {0}'.format(attr))
class Window:
	def __init__(self,map,path):
		self.__PATH = path
		self.__MAP = map
		config,_map,players,self.mod,mode = map
		self.map = Map(_map)
		self.model = Model()
		self.config = Config(config)
		if(mode == 'SURVIVAL'):
			self.model.flyEnabled = False
			self.model.configureHurtFunc(self.hurt)
		self.model.configureMove(self.map.move)
		self.model.configureDig(self.dig)
		self.model.configurePlace(self.place)
		self.model.configureSelect(self.select)
		self.model.configureIsEntity(self.isEntity)
		self.mainloop = self.model.mainloop
		getIpAddr = lambda:requests.get('https://checkip.amazonaws.com').text.strip()
		self.ip = getIpAddr()
		self.blocks = {}
		if(self.ip not in players):
			players[self.ip] = [10,10,[None] * 10,0,self.config.spawnPoint]
		self.players = players
		self.player = players[self.ip]
		self.init()
		self.pipe = Pipe_window()
		Timer(450,self.hungry).start()
		Timer(0.25,self.updateMap).start()
		Timer(1,self.process).start()
	def isEntity(self,x,y,z):
		blk = self.map.getMap()[(x,y,z)]
		props = self.blocks[blk]
		return 'is_entity' in props and props['is_entity'] != 'yes'
	def splitarg(self,type,arg):
		spl = arg.split(' ')
		if(type == 'set_config'):
			spl = [spl[0],' '.join(spl[1:])]
		elif(type == 'change_block_propeties'):
			spl = [spl[0],spl[1],' '.join(spl[2:])]
		return spl
	def process(self):
		self.players[self.ip] = self.player
		data = self.pipe.recv()
		while(data != ''):
			type,*arg = data.split(' ')
			arg = self.splitarg(type,' '.join(arg))
			if(type == 'give'):
				try:
					p,blk = arg
					pos = 0
					while(pos < 10 and self.players[p][2][pos] != None and self.self.players[p][2][pos][0] != blk):
						pos += 1
					if(pos == 10):
						continue
					elif(self.players[p][2][pos] == None):
						self.players[p][2][pos] = (blk,1)
					else:
						cnt = self.players[p][2][pos][1] + 1
						self.players[p][2][pos] = (blk,cnt
)
				except:
					pass
			elif(type == 'get_inventory'):
				try:
					p = arg[0]
					self.pipe.send(str(self.players[p][2]))
				except:
					self.pipe.send(' ')
			elif(type == 'setPos'):
				try:
					p,x,y,z = arg
					pos = (int(x),int(y),int(z))
					x,y,z = pos
					X,Y,Z = self.players[p][-1]
					dx,dy,dz = x - X,y - Y,z - Z
					self.map.move(dx,dy,dz)
					self.model.origin = [x,y,z]
					self.players[p][-1] = pos
				except:
					pass
			elif(type == 'getPos'):
				try:
					p = arg[0]
					self.pipe.send(str(self.players[p][-1]))
				except:
					self.pipe.send(' ')
			elif(type == 'getHolding'):
				try:
					p = arg[0]
					pos = self.players[p][3]
					self.pipe.send(str(pos))
				except:
					self.pipe.send(' ')
			elif(type == 'hurt'):
				try:
					p = arg[0]
					self.players[p][0] -= 1
				except:
					pass
			elif(type == 'hunger'):
				try:
					p = arg[0]
					self.players[p][1] -= 1
				except:
					pass
			elif(type == 'kill'):
				try:
					p = arg[0]
					self.players[p][0] = 10
					X,Y,Z = self.players[p][-1]
					self.players[p][-1] = self.config.spawnPoint
					self.model.origin = list(self.config.spawnPoint)
					x,y,z = self.config.spawnPoint
					dx,dy,dz = x - X,y - Y,z - Z
					self.map.move(dx,dy,dz)
				except:
					pass
			elif(type == 'get_blood'):
				try:
					p = arg[0]
					self.pipe.send(str(self.players[p][0]))
				except:
					self.pipe.send(' ')
			elif(type == 'get_hunger'):
				try:
					p = arg[0]
					self.pipe.send(str(self.players[p][0]))
				except:
					self.pipe.send(' ')
			elif(type == 'setHolding'):
				try:
					p,val = arg
					pos = int(val)
					self.players[p][3] = pos
				except:
					pass
			elif(type == 'setblock'):
				try:
					x,y,z,blk = arg
					x,y,z = int(x),int(y),int(z)
					try:
						self.map.pop((x,y,z))
					except:
						pass
					self.map.insert(blk,(x,y,z))
				except:
					pass
			elif(type == 'removeblock'):
				try:
					x,y,z = arg
					x,y,z = int(x),int(y),int(z)
					self.map.pop((x,y,z))
				except:
					pass
			elif(type == 'getblock'):
				try:
					x,y,z = arg
					x,y,z = int(x),int(y),int(z)
					blk = self.map.getMap()[(x,y,z)]
					self.pipe.send(str(blk))
				except:
					self.pipe.send(' ')
			elif(type == 'get_height'):
				h = -100
				for x,y,z in self.map.getMap():
					h = max(h,y)
				if(h != -100):
					self.pipe.send(str(h))
				else:
					self.pipe.send(' ')
			elif(type == 'set_config'):
				try:
					label,value = arg
					code_to_excute = 'self.config.%s = value'%label
					exec(code_to_excute)
				except:
					pass
			elif(type == 'get_config'):
				try:
					label = arg[0]
					code_to_eval = 'self.config.%s'%label
					res = eval(code_to_eval)
					self.pipe.send(str(res))
				except:
					self.pipe.send(' ')
			elif(type == 'get_event'):
				try:
					event = self.model.evq.pop()
					evls = [str(i) for i in event]
					evstr = ' '.join(evls)
					self.pipe.send(evstr)
				except:
					pass
			elif(type == 'change_block_properties'):
				try:
					blk,prop,val = arg
					self.blocks[blk][prop] = val
				except:
					pass
			elif(type == 'get_block_properties'):
				try:
					blk,prop = arg
					res = self.blocks[blk][prop]
					self.pipe.send(str(res))
				except:
					self.pipe.send(' ')
			data = self.pipe.recv()
	def select(self,n):
		self.player[3] = n
	def updateMap(self):
		self.model.setSector(self.map.getSector())
	def dig(self,pos):
		_blk = self.map.getMap()[pos]
		if('dig' in self.blocks[_blk] and self.blocks[_blk]['dig'] == 'no'):
			return
		x,y,z = pos
		block = self.map.pop((x,y,z))
		self.model.setSector(self.map.getSector())
		pos = 0
		while(pos < 10 and self.player[2][pos] != None and self.player[2][pos][0] != block):
			pos += 1
		if(pos == 10):
			return
		if(self.player[2][pos] == None):
			self.player[2][pos] = (block,1)
		else:
			self.player[2][pos] = (block,self.player[2][pos][1] + 1)
	def place(self,placePoint,pickPoint):
		x,y,z = placePoint
		_x,_y,_z = pickPoint
		blockPicked = self.map.getSector()[pickPoint]
		block = self.player[2][self.player[3]]
		_map = self.map.getMap()
		if('ignoreright' in self.blocks[block] and self.blocks[block]['ignoreright'] == 'yes'):
			return
		if('use' in self.blocks[blockPicked] and self.blocks[blockPicked]['use'] == 'yes'):
                        return
		elif((x,y,z) not in _map or 'placeConflict' in self.blocks[_map[(_x,_y,_z)]] or 'placeConflict' in self.blocks[block]):
			if('placeConflict' in self.blocks[_map[(_x,_y,_z)]]):
				block = self.blocks[_map[(_x,_y,_z)]]['placeConflict']
			if('placeConflict' in self.blocks[block]):
				block = self.blocks[block]['placeConflict']
			self.map.insert(block,(x,y,z))
			self.model.setSector(self.map.getSector())
	def gameover(self):
		self.model.origin = self.config.spawnPoint
		if(not self.config.keepInventory):
			self.player[2] = [None] * 10
	def hungry(self):
		self.player[1] -= 0.5
		while(self.player[1] == 0 and self.player[0] > 0):
			self.player[0] -= 1
	def hurt(self,n):
		if(sekf.player[0] == 0):
			self.gameover()
		self.player[0] -= n
	def save(self,flag):
		self.model.setSector(self.map.getSector())
		if(flag == 7):self.__MAP = pickle.load(open(self.__PATH,'rb'))
		elif(flag != 0):return
		self.__MAP[1] = self.map.getMap()
		self.__MAP[2][self.getIpAddr()] = self.player
		pickle.dump(self.__MAP,open(self.__PATH,'wb'))
	def init(self):
		self.blocks = {}
		blocks = {}
		for i in self.mod:
			js = json.load(open(i))
			for j in js:
				self.blocks[j] = js[j]
				blocks[j] = js[j]['texture']
		self.model.LoadTexture(blocks)
		self.model.origin = self.player[4]
		self.map.move(*self.player[4])
def main():
	arg = sys.argv[9:]
	if(len(arg) == 0):
		exit()
	else:
		arg = arg[0]
	map = pickle.load(open(arg,'rb'))
	win = Window(map,arg)
	atexit.register(exitFunc,win=win)
	win.mainloop()
if(__name__ == '__main__'):
	main()
