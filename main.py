import arcade
import math
import random

from lander import Lander
from moon_land import Moon_Land
from particles import ParticleSystem
from starfield import Starfield
from hud import HUD
from sounds import SoundManager

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720


# ---------------------------------------------------------------------------
# Menu View
# ---------------------------------------------------------------------------

class MenuView(arcade.View):
    """Title screen shown on launch and when returning from game."""

    def __init__(self):
        super().__init__()
        self.starfield = Starfield(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.camera = None
        self._text_title = None
        self._text_play = None
        self._text_controls = None
        self._text_pad = None
        self._text_exit = None

    def on_show_view(self):
        arcade.set_background_color(arcade.color.BLACK)
        self.camera = arcade.Camera2D()
        self._create_texts()

    def _create_texts(self):
        w = self.window.width
        h = self.window.height
        self._text_title = arcade.Text(
            "MOON LANDER", w / 2, h / 2 + 80,
            arcade.color.WHITE, 52,
            anchor_x="center", anchor_y="center",
            bold=True, font_name="Arial"
        )
        self._text_play = arcade.Text(
            "Press ENTER to play", w / 2, h / 2 - 10,
            (210, 210, 210), 20,
            anchor_x="center", anchor_y="center",
            font_name="Arial"
        )
        self._text_controls = arcade.Text(
            "UP: Thrust   LEFT/RIGHT: Rotate",
            w / 2, h / 2 - 60,
            (160, 160, 160), 15,
            anchor_x="center", anchor_y="center",
            font_name="Arial"
        )
        self._text_pad = arcade.Text(
            "Land on the green pad!",
            w / 2, h / 2 - 90,
            arcade.color.YELLOW_GREEN, 16,
            anchor_x="center", anchor_y="center",
            font_name="Arial"
        )
        self._text_exit = arcade.Text(
            "F11: Toggle Fullscreen   |   ESC: Exit",
            w / 2, h / 2 - 130,
            (140, 140, 140), 14,
            anchor_x="center", anchor_y="center",
            font_name="Arial"
        )

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        if self.camera:
            self.camera.match_window()
        self._create_texts()

    def on_draw(self):
        self.clear()
        if self.camera:
            self.camera.use()
        self.starfield.draw()

        if self._text_title:
            self._text_title.draw()
            self._text_play.draw()
            self._text_controls.draw()
            self._text_pad.draw()
            self._text_exit.draw()

    def on_update(self, delta_time):
        self.starfield.update(delta_time)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.RETURN:
            game = GameView()
            game.setup()
            self.window.show_view(game)
        elif key == arcade.key.F11:
            self.window.set_fullscreen(not self.window.fullscreen)
        elif key == arcade.key.ESCAPE:
            arcade.exit()


# ---------------------------------------------------------------------------
# Game View
# ---------------------------------------------------------------------------

class GameView(arcade.View):
    """Main gameplay view with camera, particles, HUD, and game flow."""

    def __init__(self):
        super().__init__()
        self.lander = None
        self.terrain = None
        self.particles = None
        self.starfield = None
        self.hud = None
        self.sounds = None

        # Camera
        self.game_camera = None
        self.hud_camera = None
        self.cam_x = WINDOW_WIDTH / 2
        self.cam_y = WINDOW_HEIGHT / 2

        # Screen shake
        self.shake_timer = 0.0
        self.shake_intensity = 12.0

        # State flags
        self.explosion_triggered = False
        self.result_sound_played = False

    def setup(self):
        w = self.window.width if self.window else WINDOW_WIDTH
        h = self.window.height if self.window else WINDOW_HEIGHT

        self.lander = Lander(w / 2, h * 0.8)
        self.terrain = Moon_Land(w, h, min_x=-w * 1.5, max_x=w * 2.5)
        self.particles = ParticleSystem()
        self.starfield = Starfield(w, h)
        self.hud = HUD()
        self.sounds = SoundManager()

        self.game_camera = arcade.Camera2D()
        self.hud_camera = arcade.Camera2D()

        # Start camera centred on lander
        self.cam_x = self.lander.x
        self.cam_y = self.lander.y

        self.shake_timer = 0.0
        self.explosion_triggered = False
        self.result_sound_played = False

    def on_show_view(self):
        arcade.set_background_color(arcade.color.BLACK)

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        if self.game_camera:
            self.game_camera.match_window()
        if self.hud_camera:
            self.hud_camera.match_window()

    # -- Drawing --------------------------------------------------------

    def on_draw(self):
        self.clear()

        # World-space drawing (game camera)
        self.game_camera.use()
        self.starfield.draw()
        self.terrain.draw()
        self.lander.draw()
        self.particles.draw()

        # Screen-space drawing (HUD camera)
        self.hud_camera.use()
        w = self.window.width
        h = self.window.height
        self.hud.draw(self.lander, self.terrain, w, h)

        # Result text overlay
        if self.lander.landed:
            arcade.draw_text(
                "LANDED!", w / 2, h / 2 + 40,
                arcade.color.YELLOW_GREEN, 48,
                anchor_x="center", anchor_y="center",
                bold=True,
            )
            arcade.draw_text(
                f"Fuel remaining: {self.lander.fuel:.0f}",
                w / 2, h / 2 - 10,
                arcade.color.WHITE, 18,
                anchor_x="center", anchor_y="center",
            )
            arcade.draw_text(
                "Press R to restart  |  ESC for menu",
                w / 2, h / 2 - 50,
                (180, 180, 180), 16,
                anchor_x="center", anchor_y="center",
            )
        elif self.lander.crashed:
            arcade.draw_text(
                "CRASHED!", w / 2, h / 2 + 40,
                arcade.color.RED, 48,
                anchor_x="center", anchor_y="center",
                bold=True,
            )
            arcade.draw_text(
                "Press R to restart  |  ESC for menu",
                w / 2, h / 2 - 10,
                (180, 180, 180), 16,
                anchor_x="center", anchor_y="center",
            )
        elif self.lander.wrong_spot:
            arcade.draw_text(
                "WRONG SPOT!", w / 2, h / 2 + 40,
                arcade.color.YELLOW, 48,
                anchor_x="center", anchor_y="center",
                bold=True,
            )
            arcade.draw_text(
                "Land on the green pad!",
                w / 2, h / 2 - 10,
                arcade.color.YELLOW_GREEN, 18,
                anchor_x="center", anchor_y="center",
            )
            arcade.draw_text(
                "Press R to restart  |  ESC for menu",
                w / 2, h / 2 - 40,
                (180, 180, 180), 16,
                anchor_x="center", anchor_y="center",
            )

    # -- Update ---------------------------------------------------------

    def on_update(self, delta_time):
        self.starfield.update(delta_time)
        self.particles.update(delta_time)

        if not (self.lander.landed or self.lander.crashed or self.lander.wrong_spot):
            # Feed altitude to lander for leg deployment animation
            ground_y = self.terrain.height_at(self.lander.x)
            self.lander.altitude = max(0, self.lander.y - 20 - ground_y)

            self.lander.update()

            # Thrust particles & sound (proportional to thrust_level)
            if self.lander.thrust_level > 0.02 and self.lander.fuel > 0:
                self.sounds.start_thrust(volume=0.15 + 0.35 * self.lander.thrust_level)
                nx, ny = self.lander.nozzle_pos()
                self.particles.emit_thrust(nx, ny, self.lander.angle, self.lander.thrust_level)
            else:
                self.sounds.stop_thrust()

            self._check_landing_or_crash()
        else:
            self.sounds.stop_thrust()

            # One-shot result sound
            if not self.result_sound_played:
                if self.lander.crashed:
                    self.sounds.play_crash()
                elif self.lander.landed or self.lander.wrong_spot:
                    self.sounds.play_land()
                self.result_sound_played = True

            # Explosion particles (only on crash, not wrong_spot)
            if self.lander.crashed and not self.explosion_triggered:
                self.particles.emit_explosion(self.lander.x, self.lander.y)
                self.shake_timer = 0.5
                self.explosion_triggered = True

        # --- Smooth camera follow ---
        lerp = 0.06
        self.cam_x += (self.lander.x - self.cam_x) * lerp
        self.cam_y += (self.lander.y - self.cam_y) * lerp

        # Clamp camera so viewport stays within the wide terrain bounds
        w = self.window.width
        h = self.window.height
        min_cam_y = h / 2
        self.cam_y = max(self.cam_y, min_cam_y)
        min_cam_x = self.terrain.min_x + w / 2
        max_cam_x = self.terrain.max_x - w / 2
        self.cam_x = max(min_cam_x, min(self.cam_x, max_cam_x))

        final_x = self.cam_x
        final_y = self.cam_y

        # Screen shake
        if self.shake_timer > 0:
            self.shake_timer -= delta_time
            t = max(0, self.shake_timer / 0.5)  # fade-out factor
            intensity = self.shake_intensity * t
            final_x += random.uniform(-intensity, intensity)
            final_y += random.uniform(-intensity, intensity)

        self.game_camera.position = (final_x, final_y)

    # -- Input ----------------------------------------------------------

    def on_key_press(self, key, modifiers):
        if key == arcade.key.LEFT:
            self.lander.rotating_left = True
        elif key == arcade.key.RIGHT:
            self.lander.rotating_right = True
        elif key == arcade.key.UP:
            self.lander.thrusting = True
        elif key in (arcade.key.R, arcade.key.RETURN):
            if self.lander.landed or self.lander.crashed or self.lander.wrong_spot:
                self.setup()
        elif key == arcade.key.F11:
            self.window.set_fullscreen(not self.window.fullscreen)
        elif key == arcade.key.ESCAPE:
            self.sounds.stop_thrust()
            self.window.show_view(MenuView())

    def on_key_release(self, key, modifiers):
        if key == arcade.key.LEFT:
            self.lander.rotating_left = False
        elif key == arcade.key.RIGHT:
            self.lander.rotating_right = False
        elif key == arcade.key.UP:
            self.lander.thrusting = False

    # -- Collision / landing logic --------------------------------------

    def _check_landing_or_crash(self):
        l = self.lander
        ground_y = self.terrain.height_at(l.x)

        # Bottom of lander legs is at y - 20
        if l.y - 20 <= ground_y:
            safe_speed = abs(l.vy) < 2.0 and abs(l.vx) < 1.5
            safe_angle = abs(l.angle % 360) < 15 or abs(l.angle % 360) > 345
            on_pad = self.terrain.is_on_pad(l.x)

            if safe_speed and safe_angle and on_pad:
                l.landed = True
                self._snap_to_terrain(l, ground_y)
            elif safe_speed and safe_angle and not on_pad:
                l.wrong_spot = True
                self._snap_to_terrain(l, ground_y)
            else:
                l.crashed = True

    def _snap_to_terrain(self, l, ground_y):
        """Position and tilt the lander to sit naturally on the terrain."""
        slope_deg = self.terrain.slope_angle_at(l.x)
        slope_rad = math.radians(slope_deg)
        l.angle = slope_deg
        # Offset the center so feet sit on the surface (accounting for tilt)
        l.y = ground_y + 20 * math.cos(slope_rad)
        l.vx = 0
        l.vy = 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    window = arcade.Window(
        WINDOW_WIDTH,
        WINDOW_HEIGHT,
        title="Moon Lander",
        fullscreen=False,
        resizable=True,
    )
    window.show_view(MenuView())
    arcade.run()


if __name__ == "__main__":
    main()