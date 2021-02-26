import json
import os
def walk(dir):
        res = []
        for i in os.listdir(dir):
                fullpath = os.path.join(dir,i)
                if(os.path.isdir(fullpath) and (not i.startswith('.'))):
                        res.append(fullpath)
        return res
def load(dir,js):
        img1 = os.path.join(dir,'1.png')
        img2 = os.path.join(dir,'2.png')
        tex = os.path.split(dir)[-1]
        texlist = json.load(open(js))
        if(tex not in texlist):
                texlist[tex] = {}
                texlist[tex]['texture'] = {'top':img1,'bottom':img1,'left':img2,'right':img2,'front':img2,'back':img2}
        json.dump(texlist,open(js,'w'))
dir = input('[batch:root] dir:# ')
js = input('[batch:root] mod:# ')
ls = walk(dir)
print(ls)
for i in ls:
        load(i,js)
