from handleCam import actuCam
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import *
from tank import actuTank
from drone import actuDrone
from ultralytics import YOLO
from PIL import Image
from first_finetuned_YOLO_detect import detect_objects
import math

model = YOLO("./best.pt")
view = False

class MyApp(ShowBase):

    def __init__(self):
        ShowBase.__init__(self)

        # Load the environment model
        self.scene = self.loader.loadModel("models/environment")
        self.scene.reparentTo(self.render)
        self.scene.setScale(0.25, 0.25, 0.25)
        self.scene.setPos(-8, 42, 0)

        #baseDir = "C://Users/Baudoin/PycharmProjects/drone_hackathon"

        # Add tasks
        self.taskMgr.add(self.spinCameraTask, "SpinCameraTask")

        # Key mapping
        self.keyMap = {}
        for i in list("azeqsd") + ["arrow_up", "arrow_down", "arrow_left", "arrow_right"]:
            self.keyMap[i] = False
            self.accept(i, self.keyEvent, [i, True])
            self.accept(i + "-up", self.keyEvent, [i, False])

        # Setup tank
        tank_path0 = Filename.fromOsSpecific("./T80_bas.dae")
        self.tank = self.loader.loadModel(tank_path0)
        self.tank.setScale(100, 100, 100)
        self.tank.reparentTo(self.render)
        self.tank.setPos(0, 0, 0)
        self.tank.setHpr(0, 0, 0)
        self.tank.setColor(0.45, 0.55, 0.3, 1)

        tank_path1 = Filename.fromOsSpecific("./T80_Haut.dae")
        self.inutank = NodePath("jointure")
        self.inutank.reparentTo(self.tank)
        self.inutank.setPos(0, 0, 0)
        self.tank1 = self.loader.loadModel(tank_path1)
        self.tank1.setColor(0.5, 0.5, 0.3, 1)
        self.tank1.reparentTo(self.tank)
        self.tank1.setPos(-4 / 100, -2 / 100, 0.8 / 100)
        self.tank1.setHpr(0, 0, 0)

        # Lighting
        dlight = DirectionalLight('dlight')
        dlight.setColor((0.9, 0.9, 0.9, 1))
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(10, -60, 0)
        self.render.setLight(dlnp)

        ambientLight = AmbientLight('ambientLight')
        ambientLight.setColor((0.2, 0.1, 0.1, 1))
        ambientLightNP = self.render.attachNewNode(ambientLight)
        self.render.setLight(ambientLightNP)

        self.i = 0

        # Setup drone
        drone_path = Filename.fromOsSpecific("./droneModel.dae")
        self.drone = self.loader.loadModel(drone_path)
        self.drone.setScale(10000, 10000, 10000)
        self.drone.reparentTo(self.render)
        self.drone.setPos(0, 0, 10)
        self.drone.setHpr(0, 90, 0)

        # Drone camera
        self.drone_cam = self.makeCamera(self.win, camName="drone_cam")
        self.drone_cam.reparentTo(self.drone)
        self.drone_cam.setPos(0, 0, 0.5)
        self.drone_cam.setHpr(0, 0, 0)

        # --- NOUVEAU: Créer le frustum de la caméra ---
        self.create_camera_frustum()

        self.last_capture_time = 0
        self.capture_interval = 0.4
        self.taskMgr.add(self.capture_task, "CaptureDroneCameraTask")

    def create_camera_frustum(self):
        """Crée une visualisation du champ de vision de la caméra"""

        lines = LineSegs()
        lines.setThickness(3)
        lines.setColor(1, 1, 0, 1)  # Jaune

        # Paramètres dans le repère du DRONE (déjà à l'échelle)
        near = 0.0005  # Distance proche
        far = 0.01  # Distance lointaine
        width = 0.01  # Largeur du frustum

        # Position de la caméra dans le repère du drone
        cam_offset_z = 0.5 / 10000.0  # = 0.00005

        # Origine (position de la caméra)
        ox, oy, oz = 0, 0, cam_offset_z

        # Les 4 coins du rectangle proche
        ntl = (-width / 4, -width / 4, cam_offset_z - near)
        ntr = (width / 4, -width / 4, cam_offset_z - near)
        nbr = (width / 4, width / 4, cam_offset_z - near)
        nbl = (-width / 4, width / 4, cam_offset_z - near)

        # Les 4 coins du rectangle lointain
        ftl = (-width / 2, -width / 2, cam_offset_z - far)
        ftr = (width / 2, -width / 2, cam_offset_z - far)
        fbr = (width / 2, width / 2, cam_offset_z - far)
        fbl = (-width / 2, width / 2, cam_offset_z - far)

        # Lignes depuis l'origine vers les coins lointains
        for point in [ftl, ftr, fbr, fbl]:
            lines.moveTo(ox, oy, oz)
            lines.drawTo(*point)

        # Rectangle lointain
        lines.moveTo(*ftl)
        lines.drawTo(*ftr)
        lines.drawTo(*fbr)
        lines.drawTo(*fbl)
        lines.drawTo(*ftl)

        # Attacher au drone
        self.cam_frustum_node = self.drone.attachNewNode(lines.create())
        self.cam_frustum_node.setLightOff()

        print("Frustum créé avec near={}, far={}".format(near, far))

    def spinCameraTask(self, task):
        #caméra controlée par flèches
        if task.time<10: return Task.cont
        self.actu(task.time)
        #view = True
        if view:
            campos, camOr = actuCam(self.keyMap)
            self.camera.setPos(*campos)
            self.camera.setHpr(camOr[0], camOr[1], 0)

        #caméra collée au drone
        else:
            cp = self.drone.getPos()
            self.camera.setPos(cp.x, cp.y, cp.z - 0.3)
            ch = self.drone.getHpr()
            a, b, c = self.cam_frustum_node.getHpr()
            self.camera.setHpr(ch.x + a, ch.y + b - 90, ch.z + c)


        return Task.cont

    def keyEvent(self, key, val):
        self.keyMap[key] = val

    def actu(self, time):
        actuTank(self, time)
        actuDrone(self, time)

    def capture_task(self, task):
        if task.time - self.last_capture_time >= self.capture_interval and not view:
            self.last_capture_time = task.time

            # tex = Texture()
            # base.win.addRenderTexture(tex, GraphicsOutput.RTMCopyRam)
            tex = self.drone_cam.node().getDisplayRegion(0).getScreenshot()

            filename = f"drone_capture_{int(task.time * 10)}.png"
            # tex.write(filename)
            sx = tex.getXSize()
            sy = tex.getYSize()
            data = tex.getRamImage().getData()
            # Convert Image to Pygame Image
            im = Image.frombytes("RGBA", (sx, sy), data, "raw", "RGBA", 0, -1)

            print(im)

            #print("Captured:", filename)

            # --- RUN YOLO ON THE FRAME ---
            # results = model(im)
            detect_objects(model, im, DEBUG=True)
            # print(results)

        return Task.cont







"""    def create_simple_frustum_on_drone(self, near, far, nw, nh, fw, fh):
        lines = LineSegs()
        lines.setThickness(4)
        lines.setColor(0, 1, 1, 1)  # Cyan vif

        # Dans le repère du drone avec pitch=90, la caméra regarde vers -Z
        # IMPORTANT: Le drone a une échelle de 10000, donc on doit diviser
        drone_scale = 10000.0
        cam_offset = 0.5 / drone_scale  # self.drone_cam.setPos(0, 0, 0.5)

        # Points proches (rectangle à la distance 'near' sous le drone)
        ntr = (nw / 2, nh / 2, cam_offset - near)
        ntl = (-nw / 2, nh / 2, cam_offset - near)
        nbr = (nw / 2, -nh / 2, cam_offset - near)
        nbl = (-nw / 2, -nh / 2, cam_offset - near)

        # Points lointains (rectangle à la distance 'far' sous le drone)
        ftr = (fw / 2, fh / 2, cam_offset - far)
        ftl = (-fw / 2, fh / 2, cam_offset - far)
        fbr = (fw / 2, -fh / 2, cam_offset - far)
        fbl = (-fw / 2, -fh / 2, cam_offset - far)

        # Dessiner depuis l'origine (position caméra)
        origin = (0, 0, cam_offset)

        # Lignes depuis l'origine vers les coins du plan lointain
        lines.moveTo(*origin)
        lines.drawTo(*ftl)
        lines.moveTo(*origin)
        lines.drawTo(*ftr)
        lines.moveTo(*origin)
        lines.drawTo(*fbr)
        lines.moveTo(*origin)
        lines.drawTo(*fbl)

        # Rectangle proche
        lines.moveTo(*ntl)
        lines.drawTo(*ntr)
        lines.drawTo(*nbr)
        lines.drawTo(*nbl)
        lines.drawTo(*ntl)

        # Rectangle lointain
        lines.moveTo(*ftl)
        lines.drawTo(*ftr)
        lines.drawTo(*fbr)
        lines.drawTo(*fbl)
        lines.drawTo(*ftl)

        # Attacher au drone
        self.frustum_drone = self.drone.attachNewNode(lines.create())

        print("Frustum CYAN créé directement sur le drone (orienté vers le bas)")
"""


app = MyApp()
app.run()
"""
from handleCam import actuCam
from direct.showbase.ShowBase import ShowBase

from direct.task import Task
from panda3d.core import *
from tank import actuTank

from drone import actuDrone
#from ultralytics import YOLO

#model = YOLO("best.pt")


class MyApp(ShowBase):

    def __init__(self):
        # --- Drone camera setup ---
        ShowBase.__init__(self)
        # Load the environment model.
        self.scene = self.loader.loadModel("models/environment")
        # Reparent the model to render.
        self.scene.reparentTo(self.render)
        # Apply scale and position transforms on the model.
        self.scene.setScale(0.25, 0.25, 0.25)
        self.scene.setPos(-8, 42, 0)
        baseDir = "C://Users/Baudoin/PycharmProjects/drone_hackathon"
        # Add the spinCameraTask procedure to the task manager.
        self.taskMgr.add(self.spinCameraTask, "SpinCameraTask")

        self.keyMap = {}
        for i in list("azeqsd") + ["arrow_up", "arrow_down", "arrow_left", "arrow_right"]:
            self.keyMap[i] = False
            self.accept(i, self.keyEvent, [i, True])  # onkeydown
            self.accept(i + "-up", self.keyEvent, [i, False])

        # setup drone
        tank_path0 = Filename.fromOsSpecific(baseDir + "/T80_bas.dae")
        self.tank = self.loader.loadModel(tank_path0)
        self.tank.setScale(100, 100, 100)
        self.tank.reparentTo(self.render)
        self.tank.setPos(0, 0, 0)
        self.tank.setHpr(0, 0, 0)
        self.tank.setColor(0.45, 0.55, 0.3, 1)
        s = self
        tank_path1 = Filename.fromOsSpecific(baseDir + "/T80_Haut.dae")
        s.inutank = NodePath("jointure")
        s.inutank.reparentTo(s.tank)
        s.inutank.setPos(0, 0, 0)
        s.tank1 = self.loader.loadModel(tank_path1)
        s.tank1.setColor(0.5, 0.5, 0.3, 1)
        s.tank1.reparentTo(self.tank)
        s.tank1.setPos(0, 0, 0)
        s.tank1.setHpr(0, 0, 0)
        s.tank1.setPos(-4 / 100, -2 / 100, 0.8 / 100)

        dlight = DirectionalLight('dlight')
        dlight.setColor((0.9, 0.9, 0.9, 1))
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(10, -60, 0)
        self.render.setLight(dlnp)

        ambientLight = AmbientLight('ambientLight')
        ambientLight.setColor((0.2, 0.1, 0.1, 1))
        ambientLightNP = self.render.attachNewNode(ambientLight)
        self.render.setLight(ambientLightNP)
        s.i = 0
        # s.render.setShaderAuto()
        # dlnp.node().setShadowCaster(True, 512, 512)

        drone_path = Filename.fromOsSpecific(baseDir + "/droneModel.dae")
        self.drone = self.loader.loadModel(drone_path)
        self.drone.setScale(10000, 10000, 10000)
        self.drone.reparentTo(self.render)
        self.drone.setPos(0, 0, 10)
        self.drone.setHpr(0, 90, 0)

        self.drone_cam = self.makeCamera(self.win, camName="drone_cam")
        self.drone_cam.reparentTo(self.drone)
        self.drone_cam.setPos(0, 0, 0.5)
        self.drone_cam.setHpr(0, 0, 0)
        self.last_capture_time = 0
        self.capture_interval = 0.5  # seconds
        #self.taskMgr.add(self.capture_task, "CaptureDroneCameraTask")

    def spinCameraTask(self, task):
        self.actu(task.time)
        campos, camOr = actuCam(self.keyMap)
        self.camera.setPos(*campos)
        self.camera.setHpr(camOr[0], camOr[1], 0)
        return Task.cont

    def keyEvent(s, key, val):
        s.keyMap[key] = val

    def actu(s, time):
        actuTank(s, time)
        actuDrone(s, time)
        pass

    # load once

    #def capture_task(self, task):
    #    if task.time - self.last_capture_time >= self.capture_interval:
   #         self.last_capture_time = task.time

<<<<<<< HEAD
  #          tex = Texture()
 #           self.win.addRenderTexture(tex, GraphicsOutput.RTMCopyRam) #il y avait base.win
#            self.drone_cam.node().getDisplayRegion(0).capture_tex(tex)
=======
            #tex = Texture()
            #base.win.addRenderTexture(tex, GraphicsOutput.RTMCopyRam)
            tex = self.drone_cam.node().getDisplayRegion(0).getScreenshot()

            #filename = f"drone_capture_{int(task.time * 10)}.png"
            #tex.write(filename)
            sx = tex.getXSize()
            sy = tex.getYSize()
            data = tex.getRamImage().getData()
            #Convert Image to Pygame Image
            im = Image.frombytes("RGBA", (sx, sy), data,"raw","RGBA",0,-1)
            
            print(im)

            #print("Captured:", filename)
>>>>>>> main

            #filename = f"drone_capture_{int(task.time * 10)}.png"
           # tex.write(filename)
          #  print("Captured:", filename)
            # --- RUN YOLO ON THE FRAME ---
  #          results = model(filename)
 #           print(results)
#
 #       return Task.cont
#

app = MyApp()

app.run()
"""