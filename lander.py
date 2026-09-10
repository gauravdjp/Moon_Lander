import arcade
import math
import random


def _lerp_pt(a, b, t):
    """Linearly interpolate between two (x, y) points."""
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


class Lander:
    """Moon lander with polygon sprite, fuel enforcement, and thrust flame.

    Physics convention:
        angle is in degrees, positive = counterclockwise (CCW).
        Pressing LEFT increases angle (visual tilt left).
        Pressing RIGHT decreases angle (visual tilt right).
        Thrust is along the lander's "up" axis: (-sin(a), cos(a)) in world space.
    """

    # Shape vertices (local coords, center at origin)
    BODY = [
        (0, 18),      # nose
        (7, 5),       # right shoulder
        (7, -10),     # right base
        (-7, -10),    # left base
        (-7, 5),      # left shoulder
    ]
    NOZZLE = [(-4, -10), (4, -10), (3, -14), (-3, -14)]

    # Legs — tucked (stowed) and deployed positions
    #   Tucked:   legs hang straight down, close to the body
    #   Deployed: legs splay outward like the real Apollo LM
    LEFT_LEG_TUCKED  = [(-7, -10), (-7, -18)]
    LEFT_LEG_DEPLOY  = [(-7, -10), (-14, -20)]
    RIGHT_LEG_TUCKED = [(7, -10), (7, -18)]
    RIGHT_LEG_DEPLOY = [(7, -10), (14, -20)]

    LEFT_FOOT_TUCKED  = [(-8, -18), (-6, -18)]
    LEFT_FOOT_DEPLOY  = [(-16, -20), (-12, -20)]
    RIGHT_FOOT_TUCKED = [(6, -18), (8, -18)]
    RIGHT_FOOT_DEPLOY = [(12, -20), (16, -20)]

    # Altitude thresholds for leg deployment animation
    LEG_DEPLOY_START = 200   # legs begin extending at this altitude
    LEG_DEPLOY_END = 80      # legs fully extended at this altitude

    # Physics constants (per-frame at 60 fps)
    GRAVITY = 0.015
    THRUST_POWER = 0.04         # ~2.7x gravity — enough to brake, not to hover easily
    ROTATION_SPEED = 2.0        # degrees per frame
    FUEL_CONSUMPTION = 0.2      # per frame while thrusting

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.angle = 0.0
        self.fuel = 150.0
        self.max_fuel = 150.0
        self.altitude = 999.0    # set by game each frame
        self.thrust_level = 0.0  # 0.0 (idle) to 1.0 (full thrust)
        self.rotating_left = False
        self.rotating_right = False
        self.thrusting = False
        self.landed = False
        self.crashed = False
        self.wrong_spot = False

    # -- Coordinate helpers --

    def _rot(self, px, py):
        """Rotate local point (px, py) by self.angle CCW and translate to world pos."""
        a = math.radians(self.angle)
        cos_a = math.cos(a)
        sin_a = math.sin(a)
        rx = px * cos_a - py * sin_a
        ry = px * sin_a + py * cos_a
        return self.x + rx, self.y + ry

    def nozzle_pos(self):
        """World position of the nozzle tip (for particle emission)."""
        return self._rot(0, -14)

    @property
    def leg_deploy_factor(self):
        """0.0 = tucked, 1.0 = fully deployed. Smooth transition based on altitude."""
        if self.landed or self.wrong_spot:
            return 1.0
        if self.altitude >= self.LEG_DEPLOY_START:
            return 0.0
        if self.altitude <= self.LEG_DEPLOY_END:
            return 1.0
        # Smooth interpolation between START and END
        t = 1.0 - (self.altitude - self.LEG_DEPLOY_END) / (self.LEG_DEPLOY_START - self.LEG_DEPLOY_END)
        # Ease-in-out for smoother animation
        return t * t * (3 - 2 * t)

    # -- Drawing --

    def draw(self):
        d = self.leg_deploy_factor

        # Body
        body_pts = [self._rot(*p) for p in self.BODY]
        arcade.draw_polygon_filled(body_pts, arcade.color.LIGHT_GRAY)

        # Nozzle
        nozzle_pts = [self._rot(*p) for p in self.NOZZLE]
        arcade.draw_polygon_filled(nozzle_pts, (100, 100, 100))

        # Legs & feet — only visible when deploying
        if d > 0:
            ll0 = _lerp_pt(self.LEFT_LEG_TUCKED[0], self.LEFT_LEG_DEPLOY[0], d)
            ll1 = _lerp_pt(self.LEFT_LEG_TUCKED[1], self.LEFT_LEG_DEPLOY[1], d)
            rl0 = _lerp_pt(self.RIGHT_LEG_TUCKED[0], self.RIGHT_LEG_DEPLOY[0], d)
            rl1 = _lerp_pt(self.RIGHT_LEG_TUCKED[1], self.RIGHT_LEG_DEPLOY[1], d)

            arcade.draw_line(*self._rot(*ll0), *self._rot(*ll1), arcade.color.WHITE, 2)
            arcade.draw_line(*self._rot(*rl0), *self._rot(*rl1), arcade.color.WHITE, 2)

            # Feet
            lf0 = _lerp_pt(self.LEFT_FOOT_TUCKED[0], self.LEFT_FOOT_DEPLOY[0], d)
            lf1 = _lerp_pt(self.LEFT_FOOT_TUCKED[1], self.LEFT_FOOT_DEPLOY[1], d)
            rf0 = _lerp_pt(self.RIGHT_FOOT_TUCKED[0], self.RIGHT_FOOT_DEPLOY[0], d)
            rf1 = _lerp_pt(self.RIGHT_FOOT_TUCKED[1], self.RIGHT_FOOT_DEPLOY[1], d)

            arcade.draw_line(*self._rot(*lf0), *self._rot(*lf1), arcade.color.WHITE, 3)
            arcade.draw_line(*self._rot(*rf0), *self._rot(*rf1), arcade.color.WHITE, 3)

        # Cockpit window
        wx, wy = self._rot(0, 8)
        arcade.draw_circle_filled(wx, wy, 3, arcade.color.LIGHT_BLUE)

        # Thrust flame — scales in length, width, and brightness with thrust_level
        if self.thrust_level > 0.02 and self.fuel > 0:
            tl = self.thrust_level
            # Flame length grows substantially with thrust (e.g. 6px at low thrust to 38px at max thrust)
            base_len = 6 + 28 * tl
            flame_len = random.uniform(base_len * 0.8, base_len * 1.25)
            # Flame width scales with thrust
            base_w = 2 + 5 * tl
            flame_w = random.uniform(base_w * 0.85, base_w * 1.15)
            flame_pts = [
                self._rot(-flame_w, -14),
                self._rot(flame_w, -14),
                self._rot(0, -14 - flame_len),
            ]
            # Colors shift from softer orange at low thrust to bright yellow-white at high thrust
            if tl > 0.7:
                flame_color = random.choice([
                    (255, 255, 120),  # intense bright yellow
                    (255, 240, 80),
                    (255, 200, 40),
                ])
            elif tl > 0.35:
                flame_color = random.choice([
                    (255, 210, 30),
                    (255, 165, 0),
                    (255, 140, 0),
                ])
            else:
                flame_color = random.choice([
                    (255, 120, 0),
                    (240, 80, 0),
                    (220, 60, 0),
                ])
            arcade.draw_polygon_filled(flame_pts, flame_color)

            # Extra inner core for high thrust
            if tl > 0.4:
                core_len = flame_len * 0.55
                core_w = flame_w * 0.45
                core_pts = [
                    self._rot(-core_w, -14),
                    self._rot(core_w, -14),
                    self._rot(0, -14 - core_len),
                ]
                arcade.draw_polygon_filled(core_pts, (255, 255, 220))

    # -- Physics --

    def update(self):
        """Step the lander physics (per-frame, designed for 60 fps).

        Thrust direction is along the lander's local "up" axis.
        After CCW rotation by `angle`, the local (0,1) becomes (-sin(a), cos(a)).
        """
        # Gravity — always pulls down
        self.vy -= self.GRAVITY

        # Rotation
        if self.rotating_left:
            self.angle += self.ROTATION_SPEED
        if self.rotating_right:
            self.angle -= self.ROTATION_SPEED

        # Thrust ramp-up / decay for responsive feel & dynamic visuals
        target_thrust = 1.0 if (self.thrusting and self.fuel > 0) else 0.0
        if self.thrust_level < target_thrust:
            self.thrust_level = min(target_thrust, self.thrust_level + 0.15)  # fast spool up
        elif self.thrust_level > target_thrust:
            self.thrust_level = max(0.0, self.thrust_level - 0.20)  # quick cutoff

        # Thrust force — proportional to thrust_level
        if self.thrust_level > 0 and self.fuel > 0:
            a = math.radians(self.angle)
            eff_power = self.THRUST_POWER * self.thrust_level
            self.vx += eff_power * (-math.sin(a))
            self.vy += eff_power * math.cos(a)
            self.fuel -= self.FUEL_CONSUMPTION * self.thrust_level
            if self.fuel < 0:
                self.fuel = 0
                self.thrust_level = 0.0

        # Position
        self.x += self.vx
        self.y += self.vy