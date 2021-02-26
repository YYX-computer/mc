import tkinter as tk
import tkinter.messagebox as msg
with open('fault') as f:
	content = f.read()
base = tk.Tk()
base.title("Minecraft(YYX Edition) DEV : Error Report")
base.minsize(640,480)
base.maxsize(640,480)
img = tk.PhotoImage(file = 'Minecraft-devpage.gif')
tk.Label(base,image = img).place(x = 0,y = 0)
t = tk.Text(base,height = 23)
t.insert(1.0,content)
t.configure(state='disabled')
t.place(x = 0,y = 98)
def rep():
	msg.showinfo('Minecraft(YYX Edition) DEV : Error Report','Reported.')
	exit()
def ign():
	msg.showinfo('Minecraft(YYX Edition) DEV : Error Report','Ignored.')
	exit()
tk.Button(base,text='Report',command=rep).place(x = 350,y = 455)
tk.Button(base,text='Ignore',command=ign).place(x = 450,y = 455)
tk.mainloop()
