from sympy.vector.orienters import Orienter
from handleCam import v_add, v_mul
from drone_algo import Drone
import numpy as np

droneFVaneau = Drone()

pos = (-10, 10, 30)
v = (0, 0, 0)
ori = (0, 90, 0)  # orientation en degrés

vrot = (0, 0, 0)
g = (0, 0, 0)
img = None
heading = np.array([0, 0, 0])

dt = 1 / 60  # environ 60 FPS


def actuDrone(s, time):
        """Met à jour la position et l'orientation du drone"""
        global pos, v, g, ori, vrot, heading

        # Mise à jour de la vitesse avec l'accélération
        v = v_add(v, v_mul(g, dt))

        # Mise à jour de la position avec la vitesse
        pos = v_add(pos, v_mul(v, dt))

        # Mise à jour de l'orientation avec la vitesse de rotation
        ori = v_add(ori, v_mul(vrot, dt))

        # Appliquer la position au modèle 3D
        s.drone.setPos(pos[0], pos[1], pos[2])

        # Appliquer l'orientation (heading, pitch, roll)
        s.drone.setHpr(*ori)

        # Récupérer les commandes de l'algorithme du drone
        d = droneFVaneau.main(pos, v, ori, time, img)
        g = d["a"]  # Accélération
        vrot = d["heading"]  # Vitesse de rotation en degrés/s
        cam_pointer = d["cam_pointer"]  # Pointeur de la caméra (si utilisé)

        # --- NOUVEAU: Mettre à jour la visualisation du frustum ---
        # Le frustum est déjà attaché à drone_cam, donc il suit automatiquement
        # Vous pouvez ajouter ici du code pour modifier dynamiquement le frustum
        # par exemple en fonction de cam_pointer si nécessaire

        # Appliquer la rotation à la caméra (pas au drone)
        s.cam_frustum_node.setHpr(*cam_pointer)


        return cam_pointer