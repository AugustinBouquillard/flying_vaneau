from math import *
campos=(-59.65196283868856, -75.62041174624332, 145)
camOr=(-24, -53) ## phi, theta
vitTranslation=1
vitAngulaire=1

def actuCam(keys):
	global camOr, campos
	phi, theta=camOr
	ausol=(-sin(phi*pi/180), cos(phi*pi/180),0)
	perp=(ausol[1],-ausol[0],0)
	diff=[0,0,0]# translation
	dor=[0,0]#orienattion
	if keys["z"]: diff[1]+=1
	if keys["s"]: diff[1]-=1
	if keys["q"]: diff[0]-=1
	if keys["d"]: diff[0]+=1
	if keys["a"]: diff[2]+=1
	if keys["e"]: diff[2]-=1

	if keys["arrow_up"]: dor[1]+=1
	if keys["arrow_down"]: dor[1]-=1
	if keys["arrow_left"]: dor[0]+=1
	if keys["arrow_right"]: dor[0]-=1
	diff=[i*vitTranslation for i in diff]
	diff=v_add(v_mul(ausol, diff[1]),v_mul(perp, diff[0]),(0,0,vitTranslation*diff[2]))

	campos=(campos[0]+diff[0],campos[1]+diff[1], campos[2]+diff[2])
	
	camOr=[camOr[0]+dor[0]*vitAngulaire,camOr[1]+dor[1]*vitAngulaire]

	return (campos, camOr)

def v_add(*a):
	rep=[i for i in a[0]]
	n=len(rep)
	for i in a[1:]:
		for k in range(n): rep[k]+=i[k]
	return rep
def v_mul(a, v):
	return [s*v for s in a]
