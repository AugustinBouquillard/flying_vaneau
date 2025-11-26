from math import pi, cos, sin, tan, atan2, sqrt
import numpy as np

from tank import direction

# Configuration caméra
FOV_WIDTH = 46 * pi / 180  # Conversion degrés -> radians
FOV_HEIGHT = 32 * pi / 180

IMG_WIDTH = 4000
IMG_HEIGHT = 3000
CX, CY = IMG_WIDTH / 2, IMG_HEIGHT / 2

# Paramètres physiques
A_MAX = 4.0  # m/s²
FRICTION = 0.2  # coefficient de frottement

# Limites de la caméra
PITCH_MIN = -pi / 4
PITCH_MAX = pi / 2
YAW_RANGE = pi / 2  # ±90°

class Drone:
    """Drone de surveillance avec caméra stabilisée et IA de détection"""

    def __init__(self, position=np.zeros(3), dt=1 / 60):
        # Position et dynamique
        self.p = np.array(position, dtype=float)
        self.v = np.zeros(3)
        self.t = 0
        self.dt = dt  # Pas de temps de simulation

        # Orientation caméra (gimbal)
        self.camera_pitch = 0.0  # Bas/Haut
        self.camera_yaw = 0.0  # Gauche/Droite
        self.camera_roll = 0.0  # Inclinaison latérale

        # Orientation drone
        self.heading = 0.0  # Direction du drone (boussole)

        # Vecteur pointeur caméra (dans repère drone)
        self.pointer = np.array([1.0, 0.0, 0.0])

        # Données de cible
        self.coord = None  # Coordonnées image de la cible
        self.target_world_pos = (0, 0, 0)  # Position 3D estimée de la cible

        # Angles vers la cible
        self.theta_target = None  # Offset pitch
        self.phi_target = None  # Offset yaw
        self.theta_total = None  # Pitch absolu vers cible
        self.phi_total = None  # Yaw absolu vers cible

        # États et ordres
        self.mode = "WAIT"  # WAIT, SURVEY, ATTACK
        self.order = "ABOVE"  # ABOVE, ATTACK, FORGET, KEEP
        self.target_lost_timer = 0
        self.origin = (0, 0)

        # Image courante
        self.img = None

    def img_analyse(self, img):
        """Simule la détection ML - remplacer par vrai modèle"""
        # Pour test : retourne une détection aléatoire
        # Dans la vraie implémentation : appel au modèle ML
        if img is not None:
            # Simulation : détecte quelque chose au centre avec probabilité
            import random
            if random.random() < 0.1:  # 10% de chance de détection
                return (CX + random.randint(-200, 200),
                        CY + random.randint(-200, 200))
        return None

    def set_pointer(self):
        """Calcule le vecteur de visée de la caméra dans le repère drone"""
        self.pointer = np.array([
            cos(self.camera_pitch) * cos(self.camera_yaw),
            cos(self.camera_pitch) * sin(self.camera_yaw),
            sin(self.camera_pitch)
        ])
        return self.pointer

    def target_pointer(self):
        """Calcule les offsets angulaires pour centrer la cible"""
        if self.coord is None:
            return (0, 0)

        # Décalage en pixels par rapport au centre
        dx_pix = self.coord[0] - CX
        dy_pix = self.coord[1] - CY

        # Conversion en angles (tenant compte du FOV)
        d_yaw = (dx_pix / IMG_WIDTH) * FOV_WIDTH
        d_pitch = (dy_pix / IMG_HEIGHT) * FOV_HEIGHT

        # Correction par le roll (rotation image)
        d_yaw_corr = cos(self.camera_roll) * d_yaw - sin(self.camera_roll) * d_pitch
        d_pitch_corr = sin(self.camera_roll) * d_yaw + cos(self.camera_roll) * d_pitch

        return (d_pitch_corr, d_yaw_corr)

    def convert_data(self):
        """Met à jour les angles absolus vers la cible"""
        self.theta_target, self.phi_target = self.target_pointer()
        self.theta_total = self.camera_pitch + self.theta_target
        self.phi_total = self.camera_yaw + self.phi_target

        # Normalisation des angles
        self.theta_total = np.clip(self.theta_total, PITCH_MIN, PITCH_MAX)
        self.phi_total = (self.phi_total + pi) % (2 * pi) - pi

    def estimate_target_position(self):
        """Estime la position 3D de la cible au sol (z=0)"""
        if self.theta_total is None:
            return None

        # Distance horizontale à la cible (projection au sol)
        if abs(sin(self.theta_total)) < 0.01:  # Évite division par zéro
            return None

        r = self.p[2] / abs(sin(self.theta_total))

        # Position dans le repère monde
        angle_world = self.phi_total + self.heading
        target_pos = np.array([
            self.p[0] + cos(angle_world) * r,
            self.p[1] + sin(angle_world) * r,
            0.0
        ])

        return target_pos

    def move_circle(self, radius=50):
        """Pattern circulaire de surveillance"""
        omega = A_MAX / (FRICTION * radius)  # Vitesse angulaire

        # Position cible sur le cercle
        direction = np.array([
            cos(self.t * omega),
            sin(self.t * omega),
            0
        ])
        a = A_MAX * direction - FRICTION * self.v

        # Permuter v1 et v2 pour obtenir un drone qui regarde toujours au centre, mais là il tourne son front en sens anti parcours.
        h = -10 * np.linalg.det([[self.v[1], self.v[0]], [cos(pi * self.heading/180), sin(pi * self.heading/180)]])

        self.camera_pitch = cos(self.t/2) * 20 - 45

        return {
            "a": a,
            "cam_pointer": np.array([0, self.camera_pitch, 0]), #self.set_pointer(),
            "heading": np.array([h, 0, 0])
        }

    def move_above_target(self):
        """Se positionne au-dessus de la cible détectée"""
        if self.target_world_pos is None:
            return {"a": np.zeros(3), "cam_pointer": self.pointer, "heading": np.zeros(3)}

        # Vecteur vers la cible (projection horizontale)
        delta = self.target_world_pos[:2] - self.p[:2]
        r = np.linalg.norm(delta)

        if r < 2:  # Déjà au-dessus
            a = - 2 * FRICTION * self.v
        else:
            # Direction vers la cible
            direction = delta / r if r > 0 else np.zeros(2)

            # Accélération proportionnelle à la distance
            gain = min(1.0, r / 20)  # Ralentit en approchant
            a = np.array([
                A_MAX * gain * direction[0],
                A_MAX * gain * direction[1],
                0
            ]) - FRICTION * self.v

        # Ajustement de la caméra pour suivre la cible
        if r > 1:
            # Vitesse de convergence du pitch
            self.camera_pitch = 180 * atan2(-self.p[2], r) / pi

            heading_error = - np.linalg.det([[delta[0], delta[1]], [cos(pi * self.heading / 180), - sin(pi * self.heading / 180)]])/r

            v_heading = 200 * heading_error
        else:
            v_heading = 0

        return {
            "a": a,
            "cam_pointer": np.array([0, self.camera_pitch, 0]), #self.set_pointer(),
            "heading": np.array([v_heading, 0, 0])
        }

    def main(self, pos, v, ori, t, img: np.ndarray | None = None):
        """Boucle principale de contrôle du drone"""
        self.v = np.array(v)
        self.p = np.array(pos)
        self.heading = ori[0]
        self.t = t

        command = {"a": np.zeros(3), "cam_pointer": self.pointer, "heading": np.zeros(3)}

        # === MODE WAIT : Patrouille et recherche ===
        if self.mode == "WAIT" and t<=15:
            if img is not None:
                self.coord = self.img_analyse(img)
                if self.coord is not None:
                    self.mode = "SURVEY"
                    self.convert_data()
                    self.target_world_pos = self.estimate_target_position()
                    self.target_lost_timer = 0
                    print(f"🎯 Cible détectée ! Position: {self.target_world_pos}")

            if self.mode == "WAIT":
                command = self.move_circle()

        # === MODE SURVEY : Suivi et approche de la cible ===
        elif self.mode == "SURVEY" or t>= 14:
            # Mise à jour de la détection
            if img is not None:
                new_coord = self.img_analyse(img)
                if new_coord is not None:
                    self.coord = new_coord
                    self.convert_data()
                    self.target_world_pos = self.estimate_target_position()
                    self.target_lost_timer = 0
                else:
                    self.target_lost_timer += 1

            # Perte de la cible
            if self.target_lost_timer > 180:  # 3s à 60fps
                print("❌ Cible perdue, retour en patrouille")
                self.mode = "WAIT"
                self.coord = None
                self.target_world_pos = None
                return self.move_circle()

            # Exécution de l'ordre
            if self.order == "ABOVE":
                command = self.move_above_target()

            elif self.order == "KEEP":
                # Maintient la distance actuelle
                command = {"a": -FRICTION * self.v,
                           "cam_pointer": self.set_pointer(),
                           "heading": np.zeros(3)}

        return command