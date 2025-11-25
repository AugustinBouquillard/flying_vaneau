from handleCam import actuCam
from direct.showbase.ShowBase import ShowBase

from direct.task import Task
from panda3d.core import *
from tank import actuTank


from drone import actuDrone

# changer les baseDir ligne ~30 dans cette file

class MyApp(ShowBase):

    def __init__(self):

        ShowBase.__init__(self)
        # Load the environment model.
        self.scene = self.loader.loadModel("models/environment")
        # Reparent the model to render.
        self.scene.reparentTo(self.render)
        # Apply scale and position transforms on the model.
        self.scene.setScale(0.25, 0.25, 0.25)
        self.scene.setPos(-8, 42, 0)
        baseDir="C://Users/Baudoin/PycharmProjects/drone_hackathon"
        # Add the spinCameraTask procedure to the task manager.
        self.taskMgr.add(self.spinCameraTask, "SpinCameraTask")
        
        self.keyMap={}
        for i in list("azeqsd")+["arrow_up", "arrow_down", "arrow_left","arrow_right"]:
        	self.keyMap[i]=False
        	self.accept(i, self.keyEvent, [i, True]) # onkeydown
        	self.accept(i+"-up", self.keyEvent, [i, False])
        	
        #setup drone
        tank_path0=Filename.fromOsSpecific(baseDir+"/T80_bas.dae")
        self.tank=self.loader.loadModel(tank_path0)
        self.tank.setScale(100, 100, 100)
        self.tank.reparentTo(self.render)
        self.tank.setPos(0,0,0)
        self.tank.setHpr(0,0,0)
        self.tank.setColor(0.45,0.55,0.3,1)
        s=self
        tank_path1=Filename.fromOsSpecific(baseDir+"/T80_Haut.dae")
        s.inutank=NodePath("jointure")
        s.inutank.reparentTo(s.tank)
        s.inutank.setPos(0,0,0)
        s.tank1=self.loader.loadModel(tank_path1)
        s.tank1.setColor(0.5, 0.5, 0.3, 1)
        s.tank1.reparentTo(self.tank)
        s.tank1.setPos(0,0,0)
        s.tank1.setHpr(0,0,0)
        s.tank1.setPos(-4/100,-2/100,0.8/100)
        
        dlight = DirectionalLight('dlight')
        dlight.setColor((0.9, 0.9, 0.9, 1))
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(10, -60, 0)
        self.render.setLight(dlnp)
        
        ambientLight = AmbientLight('ambientLight')
        ambientLight.setColor((0.2, 0.1, 0.1, 1))
        ambientLightNP = self.render.attachNewNode(ambientLight)
        self.render.setLight(ambientLightNP)
        s.i=0
        #s.render.setShaderAuto()
        #dlnp.node().setShadowCaster(True, 512, 512)

        drone_path=Filename.fromOsSpecific(baseDir+"/droneModel.dae")
        self.drone=self.loader.loadModel(drone_path)
        self.drone.setScale(10000, 10000, 10000)
        self.drone.reparentTo(self.render)
        self.drone.setPos(0,0,10)
        self.drone.setHpr(0,90,0)
        
    def spinCameraTask(self, task):
        self.actu(task.time)
        campos, camOr=actuCam(self.keyMap)
        self.camera.setPos(*campos)
        self.camera.setHpr(camOr[0],camOr[1],0)
        return Task.cont
    def keyEvent(s, key, val):
        s.keyMap[key]=val
    def actu(s, time):
        actuTank(s, time)
        actuDrone(s,time)
        pass

app = MyApp()

app.run()
