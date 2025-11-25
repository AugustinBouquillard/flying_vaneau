from math import pi, cos, sin, tan, atan2, sqrt
import numpy as np

# Configuration caméra
FOV_WIDTH = 46 * pi / 180  # Conversion degrés -> radians
FOV_HEIGHT = 32 * pi / 180

IMG_WIDTH = 4000
IMG_HEIGHT = 3000
CX, CY = IMG_WIDTH / 2, IMG_HEIGHT / 2

# Paramètres physiques
A_MAX = 1.0  # m/s²
FRICTION = 0.1  # coefficient de frottement

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
        self.target_world_pos = None  # Position 3D estimée de la cible

        # Angles vers la cible
        self.theta_target = None  # Offset pitch
        self.phi_target = None  # Offset yaw
        self.theta_total = None  # Pitch absolu vers cible
        self.phi_total = None  # Yaw absolu vers cible

        # États et ordres
        self.mode = "WAIT"  # WAIT, SURVEY, ATTACK
        self.order = "ABOVE"  # ABOVE, ATTACK, FORGET, KEEP
        self.target_lost_timer = 0

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

    def move_circle(self, radius=50, height=30):
        """Pattern circulaire de surveillance"""
        omega = 0.2  # Vitesse angulaire

        # Position cible sur le cercle
        target_pos = np.array([
            radius * cos(self.t * omega),
            radius * sin(self.t * omega),
            height
        ])

        # Contrôle proportionnel vers la position cible
        error = target_pos - self.p
        a = A_MAX * np.clip(error / 10, -1, 1) - FRICTION * self.v

        # Rotation progressive de la caméra vers le centre
        self.camera_pitch += (pi / 6 - self.camera_pitch) * 0.01

        return {
            "a": a,
            "cam_pointer": self.set_pointer(),
            "heading": omega * self.dt
        }

    def move_above_target(self):
        """Se positionne au-dessus de la cible détectée"""
        if self.target_world_pos is None:
            return {"a": np.zeros(3), "cam_pointer": self.pointer, "heading": 0}

        # Vecteur vers la cible (projection horizontale)
        delta = self.target_world_pos[:2] - self.p[:2]
        r = np.linalg.norm(delta)

        if r < 0.1:  # Déjà au-dessus
            a = -2 * FRICTION * self.v
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
        if r > 0.1:
            # Vitesse de convergence du pitch
            pitch_target = atan2(-self.p[2], r)
            self.camera_pitch += (pitch_target - self.camera_pitch) * 0.05

            # Alignement progressif du yaw et heading
            angle_to_target = atan2(delta[1], delta[0])
            heading_error = (angle_to_target - self.heading + pi) % (2 * pi) - pi

            d_heading = heading_error * 0.02  # Converge en ~2s
            self.camera_yaw -= self.camera_yaw * 0.03  # Recentre le yaw

            if self.phi_total is not None:
                self.phi_total -= d_heading
        else:
            d_heading = 0

        return {
            "a": a,
            "cam_pointer": self.set_pointer(),
            "heading": d_heading
        }

    def update_physics(self, a, d_heading):
        """Met à jour position, vitesse et orientation"""
        self.v += a * self.dt
        self.p += self.v * self.dt
        self.heading += d_heading
        self.heading = (self.heading + pi) % (2 * pi) - pi  # Normalisation
        self.t += self.dt

    def main(self, img: np.ndarray | None = None):
        """Boucle principale de contrôle du drone"""

        command = {"a": np.zeros(3), "cam_pointer": self.pointer, "heading": 0}

        # === MODE WAIT : Patrouille et recherche ===
        if self.mode == "WAIT":
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
        elif self.mode == "SURVEY":
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
                           "heading": 0}

        # Mise à jour physique
        self.update_physics(command["a"], command["heading"])

        return command


# === EXEMPLE D'UTILISATION ===
if __name__ == "__main__":
    drone = Drone(position=[0, 0, 30])  # Altitude 30m

    print("🚁 Simulation de drone de surveillance")
    print(f"Position initiale: {drone.p}")

    # Simulation de 1000 frames
    for i in range(1000):
        # Simulation d'image (remplacer par vraie caméra)
        img = np.random.rand(256, 256, 3) if i % 10 == 0 else None

        cmd = drone.main(img)

        # Affichage périodique
        if i % 60 == 0:
            print(f"\n[t={drone.t:.1f}s] Mode: {drone.mode}")
            print(f"  Position: [{drone.p[0]:.1f}, {drone.p[1]:.1f}, {drone.p[2]:.1f}]")
            print(f"  Vitesse: {np.linalg.norm(drone.v):.2f} m/s")
            print(f"  Heading: {drone.heading * 180 / pi:.1f}°")
            print(f"  Camera: pitch={drone.camera_pitch * 180 / pi:.1f}°, yaw={drone.camera_yaw * 180 / pi:.1f}°")