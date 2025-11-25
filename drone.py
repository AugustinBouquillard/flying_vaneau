from math import *

from jupyter_client.consoleapp import classes

from handleCam import v_add, v_mul
from drone_algo import Drone ## baudoin
# gérer le conflit de classes.

droneFVaneau = Drone()

pos=(0,0,10)
v=(0,0,0)


ori=(0,0,0) #orientation du drone 
vrot= (0,0,0)
v = (0, 0, 0)
g = (0, 0, 0)
img = None

def actuDrone(s, time):
        global pos, v, g, ori, vrot
        dt=1/60 #environ
        v=v_add(v, v_mul(g, dt))
        pos=v_add(pos, v_mul(v, dt))
        ori=v_add(ori, v_mul(vrot, dt))
        s.drone.setPos(pos[0],pos[1],pos[2])
        s.drone.setHpr(*ori) # orientation en angles euler, le premier est heading

        d=droneFVaneau.main(pos, v, ori, img)
        g = d["a"]
        ori = d["heading"] #de fait on ne considère qu'un seul ddl
        cam_pointer = d["cam_pointer"]

        
        
