from math import *
from handleCam import v_add, v_mul
from drone_algo import main as callBaudoin ## baudoin

pos=(0,0,10)
v=(0,0,0)


ori=(0,0,0) #orientation du drone 
vrot= (0,0,0)

def actuDrone(s, time):
        global pos, v, g, ori, vrot
        dt=1/60 #environ
        #v=v_add(v, v_mul(g, dt))
        pos=v_add(pos, v_mul(v, dt))
        ori=v_add(ori, v_mul(vrot, dt))
        s.drone.setPos(pos[0],pos[1],pos[2])
        s.drone.setHpr(*ori) # orientation en angles euler, le preier est haeding
        
        
        evolution=callBaudoin(pos,v, ori, vrot)
        
        
