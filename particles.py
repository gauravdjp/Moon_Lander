import arcade
import random
import math


class Particle:
    """A single particle with position, velocity, lifetime, and visual properties."""

    __slots__ = ('x', 'y', 'vx', 'vy', 'lifetime', 'max_lifetime', 'color', 'size')

    def __init__(self, x, y, vx, vy, lifetime, color, size):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.color = color
        self.size = size

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy -= 30 * dt  # light gravity on particles
        self.lifetime -= dt

    @property
    def alive(self):
        return self.lifetime > 0

    def draw(self):
        alpha = int(255 * max(0, self.lifetime / self.max_lifetime))
        color = (self.color[0], self.color[1], self.color[2], alpha)
        arcade.draw_circle_filled(self.x, self.y, self.size, color)


class ParticleSystem:
    """Manages collections of particles for thrust and explosion effects."""

    def __init__(self):
        self.particles = []

    def emit_thrust(self, x, y, angle, thrust_level=1.0):
        """Emit thrust exhaust particles from the lander nozzle.

        Args:
            x, y: Nozzle world position.
            angle: Lander angle in degrees (CCW from vertical).
            thrust_level: Current thrust power from 0.0 to 1.0.
        """
        if thrust_level <= 0.02:
            return

        angle_rad = math.radians(angle)
        # Visual "down" direction from the lander
        down_x = math.sin(angle_rad)
        down_y = -math.cos(angle_rad)

        # Scale particle count with thrust (1 at low thrust up to 5 at full power)
        count = max(1, int(1 + 4 * thrust_level))

        for _ in range(count):
            # Spread the exhaust cone (narrower at high power, wider at low)
            spread_max = 0.25 + 0.25 * (1.0 - thrust_level)
            spread = random.uniform(-spread_max, spread_max)
            cos_s = math.cos(spread)
            sin_s = math.sin(spread)
            dir_x = down_x * cos_s - down_y * sin_s
            dir_y = down_x * sin_s + down_y * cos_s

            speed = random.uniform(50 + 70 * thrust_level, 100 + 150 * thrust_level)
            vx = speed * dir_x
            vy = speed * dir_y
            lifetime = random.uniform(0.12, 0.25 + 0.2 * thrust_level)
            if thrust_level > 0.6:
                color = random.choice([
                    (255, 255, 200),  # white-yellow
                    (255, 240, 100),  # bright yellow
                    (255, 180, 50),   # gold
                ])
            else:
                color = random.choice([
                    (255, 150, 20),   # orange
                    (255, 100, 10),   # reddish
                    (220, 60, 0),
                ])
            size = random.uniform(1.5 + 1.5 * thrust_level, 2.5 + 3.0 * thrust_level)
            self.particles.append(Particle(x, y, vx, vy, lifetime, color, size))

    def emit_explosion(self, x, y):
        """Burst of particles on crash."""
        for _ in range(60):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(30, 250)
            vx = speed * math.cos(angle)
            vy = speed * math.sin(angle)
            lifetime = random.uniform(0.5, 1.5)
            color = random.choice([
                (255, 255, 255),  # white
                (255, 165, 0),    # orange
                (255, 255, 0),    # yellow
                (255, 69, 0),     # red-orange
                (255, 0, 0),      # red
            ])
            size = random.uniform(2, 6)
            self.particles.append(Particle(x, y, vx, vy, lifetime, color, size))

    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.alive]

    def draw(self):
        for p in self.particles:
            p.draw()
