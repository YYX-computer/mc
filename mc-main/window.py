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
import os
faulthandler.enable(file = open('fault','w+'),all_threads = True)
signal(SIGINT,SIG_IGN)
class Queue:
	def __init__(self):
		self.__q = []
	def empty(self):
		return not self.__q
	def push(self,*val):
		if(len(val) == 1):
			self.__q.append(val[0])
		else:
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
		self.isTransparentFunc = lambda name:0
		self.wheelpos = 0
		self.dragfrom = (None,None)
		self.evq = Queue()
		self.names = {}
		self.vert = {}
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
		elif key in (b'e',b'E'):
			move = self.move(0.,-2.,0.)
		try:
			n = int(key.decode()) - 1
			self.selectFunc(n)
			return
		except:
			pass
		_x,_y,_z = self.origin[0],self.origin[1],self.origin[2]
		_round = lambda x,y,z:(round(x),round(y),round(z))
		if(_round(_x,_y,_z) in self.sector and not self.isEntity(_x,_y,_z)):
			tx,ty,tz = move[0] * -1,move[1] * -1,move[2] * -1
			self.move(tx,ty,tz)
	def mouse(self,x,y):
		self.event('mousemove',*self.mouselocation,x,y)
		rx = (x - self.mouselocation[0]) * self.offset
		ry = (y - self.mouselocation[1]) * self.offset
		self.rotate(rx,ry)
		self.mouselocation = [x,y]
	def hit_test(self):
		_round = lambda x,y,z:(round(x),round(y),round(z))
		_round2 = lambda x,y,z:(round(x / 2),round(y / 2),round(z / 2))
		vx,vy,vz = self.target()
		x,y,z = self.origin
		bx,by,bz = (vx - x) * 2,(vy - y) * 2,(vz - z) * 2
		dist = 0
		while(dist < 16 and _round(x,y,z) not in self.sector):
			x,y,z = x + bx,y + by,z + bz
			dist += 1
		if(dist == 16):
			return (None,None,None),(None,None,None)
		else:
			return _round2(x,y,z),_round2(x - bx,y - by,z - bz)
	def mousePress(self,button,state,x,y):
		if(state == GLUT_DOWN):
			self.dragfrom = (x,y)
		else:
			fx,fy = self.dragfrom
			if(self.dragfrom != (x,y)):
				self.event('mousedrag',fx,fy,x,y,button)
			return
		self.event('mouseclick',x,y,button)
		pos,next = self.hit_test()
		if((None,None,None) in (pos,next) or 1 in (button,state)):return
		if(button == 0):
			self.event('removeblock',*pos)
			self.digFunc(pos)
		else:
			self.event('setblock',*pos,*next)
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
	def configureIsTransparent(self,func):
		self.isTransparentFunc = func
	def _draw_vertex(self,name,pos):
		if(self.isTransparentFunc(name)):
			glClearDepth(1.0)
			glEnable(GL_BLEND)
			glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		x,y,z = pos
		t = ["front", "back", "top",  "bottom", "left", "right"]
		vertex = {}
		for i in self.vert[name]:
			pos = [(j[0] + x,j[1] + y,j[2] + z) for j in i]
			vertex[pos] = t.index(self.vert[name][i])
		for i in vertex:
			glBindTexture(GL_TEXTURE_2D,self.tex[name] + vertex[i])
			glBegin(GL_QUADS)
			glTexCoord2f(0.0, 0.0)
			glVertex3f(*i[0])
			glTexCoord2f(1.0, 0.0)
			glVertex3f(*i[1])
			glTexCoord2f(1.0, 1.0)
			glVertex3f(*i[2])
			glTexCoord2f(0.0, 1.0)
			glVertex3f(*i[3])
		if(self.isTransparentFunc(name)):
			glDisable(GL_BLEND)
	def _Drawblock(self,name,pos):
		if(self.isTransparentFunc(name)):
			glClearDepth(1.0)
			glEnable(GL_BLEND)
			glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		x,y,z = pos
		vertex = [[[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]],[[-1,-1,-1],[-1,1,-1],[1,1,-1],[1,-1,-1]],[[-1,1,-1],[-1,1,1],[1,1,1],[1,1,-1]],[[-1,-1,-1],[1,-1,-1],[1,-1,1],[-1,-1,1]],[[1,-1,-1],[1,1,-1],[1,1,1],[1,-1,1]],[[-1,-1,-1],[-1,-1,1],[-1,1,1],[-1,1,-1]]]
		if(name in self.vert):
			return self._draw_vertex(name,pos)
		for i in range(6):
			for j in range(4):
				vertex[i][j][0] += x
				vertex[i][j][1] += y
				vertex[i][j][2] += z
		for i in range(len(vertex)):
			glBindTexture(GL_TEXTURE_2D, self.tex[name] + i)
			glBegin(GL_QUADS)
			glTexCoord2f(0.0, 0.0)
			glVertex3f(*vertex[i][0])
			glTexCoord2f(1.0, 0.0)
			glVertex3f(*vertex[i][1])
			glTexCoord2f(1.0, 1.0)
			glVertex3f(*vertex[i][2])
			glTexCoord2d(0.0, 1.0)
			glVertex3f(*vertex[i][3])
			glEnd()
		if(self.isTransparentFunc(name)):
			glDisable(GL_BLEND)
	def Draw(self):
		if(not ((round(self.origin[0]),round(self.origin[1]) - 1,round(self.origin[2])) in self.sector or self.flying)):
			self.move(0,-2,0)
			self.hurtFunc(0.5)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		glLoadIdentity()
		glTranslate(0.0, 0.0, -5.0)
		self.setLookat()
		for i in self.sector:
			try:
				self._Drawblock(self.sector[i],i)
			except:
				pass
		glutSwapBuffers()
	def loadVertex(self,vertex):
		for i in vertex:
			with open(vertex[i]) as f:
				vertex[i] = {}
				while(1):
					line = f.readline()
					if(not line):
						break
					keypart,val = [i.strip() for i in line.split('->')]
					key = [eval(i) for i in keypart.split(' ')]
					vertex[i][key] = val
		self.vert = vertex
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
				glTexEnvf(GL_TEXTURE_ENV,GL_TEXTURE_ENV_MODE, GL_REPLACE)
				n += 1
	def InitGl(self):
		glEnable(GL_DEPTH_TEST)
		glEnable(GL_TEXTURE_2D)
		glClearColor(0.49411764705882352941176470588235, 0.67058823529411764705882352941176, 1.0, 0.0)
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
	def setSectorSize(self,x,y,z):
		self.sectorSize = (x,y,z)
		self.init()
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
		self.model.configureIsTransparent(self.isTransparent)
		self.mainloop = self.model.mainloop
		getIpAddr = lambda:requests.get('https://checkip.amazonaws.com').text.strip()
		self.ip = getIpAddr()
		self.blocks = {}
		if(self.ip not in players):
			players[self.ip] = [10,10,[None] * 10,0,self.config.spawnPoint]
		pos = [i * 2 for i in players[self.ip][4]]
		self.model.origin = tuple(pos)
		self.players = players
		self.player = players[self.ip]
		self.init()
		self.pipe = Pipe_window()
		Timer(450,self.hungry).start()
		Timer(0.25,self.updateMap).start()
		Timer(1,self.process).start()
	def isTransparent(self,name):
		return 'transparent' in self.blocks[name] and self.blocks[name]['transparent'] == 'yes'
	def isEntity(self,x,y,z):
		blk = self.map.getMap()[(x,y,z)]
		props = self.blocks[blk]
		return 'is_entity' in props and props['is_entity'] != 'yes'
	def splitarg(self,type,arg):
		spl = arg.split(' ')
		if(type in ('set_config','draw_picture')):
			spl = [spl[0],' '.join(spl[1:])]
		elif(type == 'change_block_propeties'):
			spl = [spl[0],spl[1],' '.join(spl[2:])]
		return spl
	def process(self):
		self.players[self.ip] = self.player
		data = self.pipe.recv()
		while(data != ''):
			try:
				type,*arg = data.split(' ')
			except:
				type = arg = None
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
			elif(type == 'set_inventory'):
				try:
					p,inv = arg[:2]
					self.players[p][2] = eval(inv)
				except:	
					pass
			elif(type == 'get_inventory'):
				try:
					p = arg[0]
					self.pipe.send(str(self.players[p][2]))
				except:
					self.pipe.send(' ')
			elif(type == 'getSectorSize'):
				try:
					size = self.map.getSectorSize()
					pipe.send(str(size))
				except:
					pipe.send(' ')
			elif(type == 'setSectorSize'):
				try:
					x,y,z = arg
					x,y,z = int(x),int(y),int(z)
					self.map.setSectorSize(x,y,z)
				except:
					pass
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
			elif(type == 'get_window_size'):
				try:
					w = glutGet(GLUT_WINDOW_WIDTH);
					h = glutGet(GLUT_WINDOW_HEIGHT);
					self.pipe.send('%s %s'%(w,h))
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
		if(block == None):return
		else:block = block[0]
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
		vertex = {}
		for i in self.mod:
			js = json.load(open(i))
			for j in js:
				self.blocks[j] = js[j]
				blocks[j] = js[j]['texture']
				if('vertex' in js[j]):
					vertex[j] = js[j]['vertex']
		self.model.LoadTexture(blocks)
		self.model.loadVertex(vertex)
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
