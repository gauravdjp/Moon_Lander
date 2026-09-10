import arcade
import random
import math


class Starfield:
    """Randomly placed stars with optional twinkling, drawn in world-space."""

    def __init__(self, width, height, num_stars=200):
        self.stars = []
        for _ in range(num_stars):
            # Distribute across a large area to cover camera movement
            x = random.uniform(-width * 0.5, width * 1.5)
            y = random.uniform(0, height * 3)
            brightness = random.randint(120, 255)
            # ~30% of stars twinkle
            twinkle_speed = random.uniform(1.5, 4.0) if random.random() < 0.3 else 0
            size = random.uniform(0.8, 2.5)
            self.stars.append({
                'x': x,
                'y': y,
                'brightness': brightness,
                'twinkle_speed': twinkle_speed,
                'size': size,
                'phase': random.uniform(0, math.tau),
            })
        self.time = 0.0

    def update(self, dt):
        self.time += dt

    def draw(self):
        for s in self.stars:
            if s['twinkle_speed'] > 0:
                factor = 0.5 + 0.5 * math.sin(
                    self.time * s['twinkle_speed'] + s['phase']
                )
                alpha = int(s['brightness'] * factor)
            else:
                alpha = s['brightness']
            alpha = max(0, min(255, alpha))
            arcade.draw_circle_filled(
                s['x'], s['y'], s['size'], (255, 255, 255, alpha)
            )
