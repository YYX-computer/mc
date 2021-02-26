try:
	from tkinter.filedialog import askopenfilename as tkGetFileName,asksaveasfilename as tkGetSaveName
except:
	from tkFileDialog import askopenfilename as tkGetFileName,asksaveasfilename as tkGetSaveName
from pygame.locals import *
try:
	import tkinter.ttk as ttk
	import tkinter as tk
except:
	import ttk
	import Tkinter as tk
from random import *
import socket
import pickle
import pygame
import json
import sys
import re
tkwindow = tk.Tk()
tkwindow.withdraw()
def selectTexture():
	global tkwindow
	tkwindow.destroy()
	tkwindow = tk.Tk()
	tkwindow.title('select Texture')
	tree = ttk.Treeview(tkwindow)
	tree.grid(column=0,row=0)
	lines = []
	olen = 0
	tree['columns'] = ('serial number','texture')
	tree.column('serial number',width = 100)
	tree.column('texture',width = 100)
	tree.heading('serial number',text='serial No.')
	tree.heading('texture',text='texture')
	def updateTreeview():
		nonlocal tree,lines,olen
		for i in range(olen):
			tree.delete(i)
		olen = len(lines)
		for i in range(len(lines)):
			tree.insert("",i,id=i,text=i,values = tuple(lines[i]))
	def add():
		nonlocal lbl,e
		lbl.grid(column=0,row=2)
		e.grid(column=1,row=2)
		def submit():
			nonlocal btn,lines,lbl,e
			if(len(lines) > 0):
				lines.append([lines[-1][0] + 1,e.get()])
			else:
				lines.append([1,e.get()])
			lbl.grid_forget()
			e.grid_forget()
			btn.grid_forget()
			updateTreeview()
		btn = tk.Button(tkwindow,text='submit',command=submit)
		btn.grid(column=2,row=2)
	def remove():
		nonlocal lines,tree
		lines.pop(int(tree.selection()[0]))
		updateTreeview()
	q = False
	def Q():
		nonlocal q
		q = True
	def titan():
		nonlocal q
		q = 'titan'
	lbl = tk.Label(tkwindow,text='input texture name:')
	e = tk.Entry(tkwindow)
	tk.Button(tkwindow,text='+',command=add).grid(column=0,row=1)
	tk.Button(tkwindow,text='-',command=remove).grid(column=1,row=1)
	tk.Button(tkwindow,text='OK',command=Q).grid(column=2,row=1)
	tk.Button(tkwindow,text='titan survival(not suggested)',command=titan).grid(column=3,row=1)
	while(not q):
		try:
			tkwindow.update()
		except:
			q = True
	try:
		tkwindow.withdraw()
		tkwindow.update()
	except:
		tkwindow = tk.Tk()
		tkwindow.withdraw()
	return [i[1] for i in lines] if(q == True) else 'titan'
def selectMods():
	global tkwindow
	tkwindow.destroy()
	tkwindow = tk.Tk()
	tkwindow.title('select Mod')
	tree = ttk.Treeview(tkwindow)
	tree.grid(column=0,row=0)
	lines = []
	olen = 0
	tree['columns'] = ('serial number','path')
	tree.column('serial number',width = 100)
	tree.column('path',width = 300)
	tree.heading('serial number',text='serial No.')
	tree.heading('path',text='path')
	def updateTreeview():
		nonlocal tree,lines,olen
		for i in range(olen):
			tree.delete(i)
		olen = len(lines)
		for i in range(len(lines)):
			tree.insert("",i,id=i,text=i,values = tuple(lines[i]))
	_get = lambda:tkGetFileName(title='open a mod file',filetypes=[('Minecraft Mod File','*.mcMod')])
	def add():
		nonlocal _get
		val = _get()
		if(len(val) < 1):return
		if(len(lines) > 0):
			lines.append([lines[-1][0] + 1,val])
		else:
			lines.append([1,val])
		updateTreeview()
	def remove():
		nonlocal lines,tree
		lines.pop(int(tree.selection()[0]))
		updateTreeview()
	q = False
	def Q():
		nonlocal q
		q = True
	tk.Button(tkwindow,text='+',command=add).grid(column=0,row=1)
	tk.Button(tkwindow,text='-',command=remove).grid(column=1,row=1)
	tk.Button(tkwindow,text='OK',command=Q).grid(column=2,row=1)
	while(not q):
		try:
			tkwindow.update()
		except:
			q = True
	try:
		tkwindow.withdraw()
		tkwindow.update()
	except:
		tkwindow = tk.Tk()
		tkwindow.withdraw()
	return [i[1] for i in lines]
def generate_block(pos,oredict):
	def inrange(n,r):
		indices = []
		r = r.split(',')
		for i in r:
			i = i.split('~')
			if(len(i) == 1):
				try:
					indices.append(int(i[0]))
				except:
					continue
			elif(len(i) == 2):
				l,r = i
				try:
					l,r = int(l),int(r)
				except:
					continue
				indices += range(l,r + 1)
		for i in indices:
			if(i == n):
				return True
		return False
	def rand(dataset):
		factor = 10 ** max([len(str(dataset[i]).split('.')[-1]) for i in dataset])
		samples = []
		for i in dataset:
			for j in range(int(dataset[i] * factor)):
				samples.append(i)
		return choice(samples)
	x,y,z = pos
	possibles = {}
	for i in oredict:
		dist = oredict[i]
		for j in dist:
			if(inrange(y,j)):
				if(i in possibles):
					possibles[i] = max(possibles[i],dist[j])
				else:
					possibles[i] = dist[j]
	selected = []
	for i in possibles:
		prob = possibles[i]
		if(rand({1:prob,0:1 - prob})):
			selected.append(i)
	return choice(selected) if(selected) else None
def get_highest(x,z,map):
	h = float('-inf')
	for X,Y,Z in map:
		if(X == x and Z == z):
			h = max(h,Y)
	return h if(h != float('-inf')) else 0
def genTree():
	with open('tree.mpf','rb') as f:
		return pickle.load(f)
def genMap(t,modlist,structure = None,titan = False):
	'''
	for function input,we have
	- t => the type of the world
	- modlist => a list of mods
	- structure => when `t` is `CUSTOM`,the struct of the world
	and for function output,we have
	- map
	'''
	if(t == 'SMOOTH'):
		'''
		for `SMOOTH` mode,we have
		- grass
		- grass
		- grass
		- bedrock
		and for size we have
		- 3000x3000x4
		'''
		map = {}
		for i in range(1,4):
			for j in range(-1500,1500):
				for k in range(-1500,1500):
					map[(j,i,k)] = 'grass'
		for i in range(-1500,1500):
			for j in range(-1500,1500):
				map[(i,0,j)] = 'bedrock'
		return map
	elif(t == 'CUSTOM'):
		'''
		for `CUSTOM` mode,we have
		- custom
		and for size we have
		- 3000x3000xN(N ≤ 10)
		'''
		if(structure == 'titan'):
			return genMap('CLASSIC',modlist,titan=True)
		map = {}
		for i in range(len(structure)):
			for j in range(-1500,1500):
				for k in range(-1500,1500):
					map[(j,i,k)] = structure[i]
		return map
	else:
		if(titan):
			s,ub = 5000,50
		else:
			s,ub = 1500,15
		'''
		for `CLASSIC` mode,we have
		- moutain
		- sea
		- trees
		- village
		and for size we have
		- 3000x3000xN(1 ≤ N ≤ 10)
		'''
		oredict = {}
		for i in modlist:
			js = json.load(i)
			for j in js:
				if('generating' in js[j]):
					oredict[j] = js[j]['generating']
		map = {}
		for i in range(-s,s):
			for k in range(-s,s):
				rint = randint(1,ub)
				for j in range(rint):
					g = generate_block((i,j,k),oredict)
					if(g != None):
						map[(i,j,k)] = g
		for i in range(randint(1,100000)):
			x = randint(-s,s)
			z = randint(-s,s)
			y = get_highest(x,z,map)
			if((x,y - 1,z) not in map or map[(x,y - 1,z)] != 'grass'):
				continue
			tree = genTree()
			for rx,ry,rz in tree:
				X,Y,Z = rx + x,ry + y,rz + z
				map[(X,Y,Z)] = tree[(rx,ry,rz)]
		return map
def getmap():
	CONTINUE_TOKEN = 'continue'
	pygame.init()
	scr = pygame.display.set_mode((640,480),RESIZABLE)
	pygame.display.set_caption("Minecraft")
	icon = pygame.image.load('icon.png')
	pygame.display.set_icon(icon)
	def run():
		nonlocal CONTINUE_TOKEN,scr
		main = pygame.image.load('main.jpg')
		about = pygame.image.load('about.jpg')
		select = pygame.image.load('select.jpg')
		custom = pygame.image.load('custom.jpg')
		loading = pygame.image.load('loading.jpg')
		multiplayer = pygame.image.load('multiplayer.jpg')
		flag = True
		running = True
		while(running):
			pygame.display.update()
			if(flag):
				scr.blit(main,(0,0))
			elif(flag == ''):
                                scr.blit(multiplayer,(0,0))
			else:
				scr.blit(about,(0,0))
			for event in pygame.event.get():
				if(event.type == QUIT or (event.type == MOUSEBUTTONDOWN and event.pos[0] >= 184 and event.pos[1] >= 348 and event.pos[0] <= 424 and event.pos[1] <= 405)):
					exit()
				elif(event.type == MOUSEBUTTONDOWN and event.pos[0] >= 184 and event.pos[1] >= 39 and event.pos[0] <= 424 and event.pos[1] <= 96):
					flag = False
				elif(event.type == MOUSEBUTTONDOWN and event.pos[0] >= 515 and event.pos[1] >= 380 and event.pos[0] <= 626 and event.pos[1] <= 455):
					flag = True
				elif(event.type == MOUSEBUTTONDOWN and event.pos[0] >= 184 and event.pos[1] >= 144 and event.pos[0] <= 424 and event.pos[1] <= 201):
					running = False
					flag = True
				elif(event.type == MOUSEBUTTONDOWN and event.pos[0] >= 184 and event.pos[1] >= 247 and event.pos[0] <= 424 and event.pos[1] <= 304):
					running = False
					flag = False
				elif(event.type == MOUSEBUTTONDOWN and event.pos[0] >= 183 and event.pos[1] >= 418 and event.pos[0] <= 426 and event.pos[1] <= 469):
					flag = ''
		if(flag):
			path = tkGetFileName(title="Select Minecraft Map File",filetypes = [('Minecraft Map File','*.mmf')])
			if(path):
				return path
			else:
				return CONTINUE_TOKEN
		running = True
		flag = 0
		t,m = 'CLASSIC','SURVIVAL'
		while(running):
			if(flag == 0):
				scr.blit(select,(0,0))
			elif(flag == 1):
				running = False
			else:
				scr.blit(loading,(0,0))
				running = False
			pygame.display.update()
			for event in pygame.event.get():
				if(event.type == QUIT):
					exit()
				elif(event.type == MOUSEBUTTONDOWN and event.pos[0] >= 50 and event.pos[1] >= 128 and event.pos[0] <= 260 and event.pos[1] <= 178):
					t = 'CLASSIC'
				elif(event.type == MOUSEBUTTONDOWN and event.pos[0] >= 50 and event.pos[1] >= 270 and event.pos[0] <= 260 and event.pos[1] <= 320):
					t = 'SMOOTH'
				elif(event.type == MOUSEBUTTONDOWN and event.pos[0] >= 50 and event.pos[1] >= 400 and event.pos[0] <= 260 and event.pos[1] <= 450):
					t = 'CUSTOM'
				elif(event.type == MOUSEBUTTONDOWN and event.pos[0] >= 372 and event.pos[1] >= 128 and event.pos[0] <= 582 and event.pos[1] <= 178):
					m = 'SURVIVAL'
				elif(event.type == MOUSEBUTTONDOWN and event.pos[0] >= 372 and event.pos[1] >= 400 and event.pos[0] <= 582 and event.pos[1] <= 450):
					m = 'CREATE'
				elif(event.type == MOUSEBUTTONDOWN and event.pos[0] >= 594 and event.pos[1] >= 12 and event.pos[0] <= 632 and event.pos[1] <= 182):
					return CONTINUE_TOKEN
				elif(event.type == MOUSEBUTTONDOWN and event.pos[0] >= 594 and event.pos[1] >= 210 and event.pos[0] <= 632 and event.pos[1] <= 450):
					if(t == 'CUSTOM'):
						flag = 1
					else:
						flag = 2
		if(flag == 2):
			selectedMods = selectMods()
			map = genMap(t,selectedMods)
			savename = tkGetSaveName(title = 'save as ...',filetypes = [('Minecraft Map File','*.mmf')])
			if(savename == ''):
				return CONTINUE_TOKEN
			pickle.dump([{'spawnPoint':(0,get_highest(0,0,map) + 1,0),'keepInventory':False},map,{},['MinecraftStandardModMinecraft.mcMod'] + selectedMods,m],open(savename,'wb'))
			return savename
		texture = None
		running = True
		while(running):
			pygame.display.update()
			scr.blit(custom,(0,0))
			for event in pygame.event.get():
				if(event.type == QUIT):
					exit()
				elif(event.type == MOUSEBUTTONDOWN and event.pos[0] >= 473 and event.pos[1] >= 379 and event.pos[0] <= 619 and event.pos[1] <= 450):
					return CONTINUE_TOKEN
				elif(event.type == MOUSEBUTTONDOWN and event.pos[0] >= 203 and event.pos[1] >= 99 and event.pos[0] <= 422 and event.pos[1] <= 198):
					texture = selectTexture()
				elif(event.type == MOUSEBUTTONDOWN and event.pos[0] >= 203 and event.pos[1] >= 301 and event.pos[0] <= 422 and event.pos[1] <= 403):
					running = False
		selectedMods = selectMods()
		map = genMap('CUSTOM',selectedMods,texture)
		savename = tkGetSaveName(title = 'save as ...',filetypes = [('Minecraft Map File','*.mmf')])
		if(not savename):
			return CONTINUE_TOKEN
		pickle.dump([{'spawnPoint':(0,get_highest(0,0,map) + 1,0),'keepInventory':False},map,{},['MinecraftStandardModMinecraft.mcMod'] + selectedMods,m],open(savename,'wb'))
		return savename
	while(1):
		result = run()
		if(result != CONTINUE_TOKEN):
			pygame.quit()
			return result
if(__name__ == '__main__'):
	M = getmap()
	try:
		assert isinstance(M,list)
		print(*M)
	except:
		print(M)
