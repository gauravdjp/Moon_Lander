import arcade


class HUD:
    """Heads-up display drawn in screen-space (unaffected by game camera)."""

    MAX_ALT_DISPLAY = 550.0  # altitude that maps to the top of the scale

    def draw(self, lander, terrain, screen_width, screen_height):
        """Draw the HUD overlay.

        Args:
            lander: The Lander instance (reads x, y, vx, vy, angle, fuel, max_fuel).
            terrain: The Moon_Land instance (for height_at).
            screen_width: Window width in pixels.
            screen_height: Window height in pixels.
        """
        ground_y = terrain.height_at(lander.x)
        altitude = max(0, lander.y - 20 - ground_y)  # bottom of legs to ground

        # ---- Left panel: text readouts + fuel bar ----
        x = 20
        y = screen_height - 30
        spacing = 22

        lines = [
            f"ALT:    {altitude:7.1f}",
            f"H-SPD:  {lander.vx:7.2f}",
            f"V-SPD:  {lander.vy:7.2f}",
            f"ANGLE:  {lander.angle % 360:5.1f} deg",
        ]

        for i, text in enumerate(lines):
            arcade.draw_text(
                text, x, y - i * spacing,
                arcade.color.WHITE, 13,
            )

        # --- Fuel bar ---
        fuel_y = y - len(lines) * spacing - 5
        bar_w = 140
        bar_h = 14
        fuel_pct = max(0.0, lander.fuel / lander.max_fuel)

        # Background
        bg_rect = arcade.LBWH(x, fuel_y, bar_w, bar_h)
        arcade.draw_rect_filled(bg_rect, (40, 40, 40))

        # Coloured fill
        if fuel_pct > 0.5:
            fill_color = arcade.color.GREEN
        elif fuel_pct > 0.2:
            fill_color = arcade.color.YELLOW
        else:
            fill_color = arcade.color.RED

        if fuel_pct > 0:
            fill_rect = arcade.LBWH(x, fuel_y, bar_w * fuel_pct, bar_h)
            arcade.draw_rect_filled(fill_rect, fill_color)

        # Border
        border_rect = arcade.LBWH(x, fuel_y, bar_w, bar_h)
        arcade.draw_rect_outline(border_rect, arcade.color.WHITE, border_width=2)

        # Label
        arcade.draw_text(
            f"FUEL {lander.fuel:.0f}/{lander.max_fuel:.0f}",
            x + bar_w + 10, fuel_y + 1,
            arcade.color.WHITE, 12,
        )

        # ---- Right panel: altitude scale ----
        self._draw_altitude_scale(altitude, screen_width, screen_height)

    def _draw_altitude_scale(self, altitude, screen_width, screen_height):
        """Vertical altitude gauge on the right side of the screen."""
        # Scale dimensions
        scale_x = screen_width - 80          # center of the bar (padded from right edge)
        scale_bottom = 60
        scale_height = screen_height - 120   # leave margin top & bottom
        scale_top = scale_bottom + scale_height
        bar_w = 16

        # Background bar
        bg = arcade.LBWH(scale_x - bar_w / 2, scale_bottom, bar_w, scale_height)
        arcade.draw_rect_filled(bg, (30, 30, 30))
        arcade.draw_rect_outline(bg, (80, 80, 80), border_width=1)

        # Tick marks & labels
        num_ticks = 6
        for i in range(num_ticks + 1):
            frac = i / num_ticks
            tick_y = scale_bottom + frac * scale_height
            alt_val = frac * self.MAX_ALT_DISPLAY

            # Tick line
            arcade.draw_line(
                scale_x - bar_w / 2 - 4, tick_y,
                scale_x - bar_w / 2, tick_y,
                (120, 120, 120), 1,
            )
            # Label
            arcade.draw_text(
                f"{alt_val:.0f}",
                scale_x - bar_w / 2 - 8, tick_y - 5,
                (150, 150, 150), 9,
                anchor_x="right",
            )

        # Fill bar (altitude proportion)
        alt_pct = min(1.0, max(0.0, altitude / self.MAX_ALT_DISPLAY))
        fill_h = alt_pct * scale_height

        # Color: green (high) → yellow (mid) → red (low)
        if alt_pct > 0.4:
            fill_color = arcade.color.GREEN
        elif alt_pct > 0.15:
            fill_color = arcade.color.YELLOW
        else:
            fill_color = arcade.color.RED

        if fill_h > 0:
            fill_rect = arcade.LBWH(scale_x - bar_w / 2, scale_bottom, bar_w, fill_h)
            arcade.draw_rect_filled(fill_rect, fill_color)

        # Marker triangle at current altitude
        marker_y = scale_bottom + alt_pct * scale_height
        tri_x = scale_x + bar_w / 2 + 3
        arcade.draw_polygon_filled([
            (tri_x, marker_y),
            (tri_x + 10, marker_y + 5),
            (tri_x + 10, marker_y - 5),
        ], arcade.color.WHITE)

        # Altitude number next to marker
        arcade.draw_text(
            f"{altitude:.0f}",
            tri_x + 13, marker_y - 6,
            arcade.color.WHITE, 12,
            bold=True,
        )

        # Title
        arcade.draw_text(
            "ALT", scale_x, scale_top + 8,
            arcade.color.WHITE, 11,
            anchor_x="center", bold=True,
        )
