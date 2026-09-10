import arcade
import math
import random


class Moon_Land:
    """Procedurally generated moon terrain with gentle slopes and a landing pad."""

    def __init__(self, width, height, min_x=-1200, max_x=2480):
        self.min_x = min_x
        self.max_x = max_x
        self.total_width = max_x - min_x
        self.points = []
        self.pad_start = 0.0
        self.pad_end = 0.0
        self.pad_y = 0.0

        num_points = 80
        spacing = self.total_width / (num_points - 1)
        base_height = 100

        # Generate terrain with moderate height variation
        for i in range(num_points):
            x = min_x + i * spacing
            y = base_height + random.uniform(-20, 35)
            self.points.append([x, y])

        # Ensure edges aren't too extreme
        self.points[0][1] = base_height + random.uniform(-5, 15)
        self.points[-1][1] = base_height + random.uniform(-5, 15)

        # Create a flat landing pad in the central region (visible and near the starting zone)
        pad_size = 5
        # Pick index roughly in the middle portion (e.g. between 200 and 1000 in x)
        start_idx = int((200 - min_x) / spacing)
        end_idx = int((1000 - min_x) / spacing)
        pad_index = random.randint(max(5, start_idx), min(num_points - pad_size - 5, end_idx))
        pad_height = base_height + random.uniform(-5, 20)
        for j in range(pad_size):
            self.points[pad_index + j][1] = pad_height

        self.pad_start = self.points[pad_index][0]
        self.pad_end = self.points[pad_index + pad_size - 1][0]
        self.pad_y = pad_height

        # Smooth the terrain (3 passes) to reduce steep slopes
        # Skip pad points to keep them flat
        for _ in range(3):
            new_heights = [self.points[0][1]]
            for i in range(1, num_points - 1):
                if pad_index <= i <= pad_index + pad_size - 1:
                    new_heights.append(self.points[i][1])
                else:
                    avg = (self.points[i - 1][1]
                           + self.points[i][1]
                           + self.points[i + 1][1]) / 3.0
                    new_heights.append(avg)
            new_heights.append(self.points[-1][1])
            for i in range(num_points):
                self.points[i][1] = new_heights[i]

        # Smooth the transitions into and out of the pad
        if pad_index > 0:
            self.points[pad_index - 1][1] = (
                self.points[pad_index - 2][1] + pad_height) / 2
        if pad_index + pad_size < num_points - 1:
            self.points[pad_index + pad_size][1] = (
                pad_height + self.points[pad_index + pad_size + 1][1]) / 2

    def draw(self):
        # Terrain polygon (filled down to y=0)
        shape = [(self.min_x, 0)]
        for p in self.points:
            shape.append((p[0], p[1]))
        shape.append((self.max_x, 0))
        arcade.draw_polygon_filled(shape, arcade.color.DARK_SLATE_GRAY)

        # Terrain surface outline for definition
        for i in range(len(self.points) - 1):
            x1, y1 = self.points[i]
            x2, y2 = self.points[i + 1]
            arcade.draw_line(x1, y1, x2, y2, (100, 100, 100), 2)

        # Landing pad highlight
        pad_w = self.pad_end - self.pad_start
        pad_rect = arcade.LBWH(self.pad_start, self.pad_y - 2, pad_w, 4)
        arcade.draw_rect_filled(pad_rect, arcade.color.YELLOW_GREEN)

        # Pad marker lines at edges
        arcade.draw_line(
            self.pad_start, self.pad_y, self.pad_start, self.pad_y + 12,
            arcade.color.YELLOW_GREEN, 2,
        )
        arcade.draw_line(
            self.pad_end, self.pad_y, self.pad_end, self.pad_y + 12,
            arcade.color.YELLOW_GREEN, 2,
        )

    def height_at(self, x):
        """Return interpolated terrain height at the given x coordinate."""
        if x <= self.points[0][0]:
            return self.points[0][1]
        if x >= self.points[-1][0]:
            return self.points[-1][1]
        for i in range(len(self.points) - 1):
            x1, y1 = self.points[i]
            x2, y2 = self.points[i + 1]
            if x1 <= x <= x2:
                if x2 == x1:
                    return y1
                t = (x - x1) / (x2 - x1)
                return y1 + t * (y2 - y1)
        return self.points[-1][1]

    def slope_angle_at(self, x):
        """Return the terrain slope angle in degrees at x (0 = flat)."""
        for i in range(len(self.points) - 1):
            x1, y1 = self.points[i]
            x2, y2 = self.points[i + 1]
            if x1 <= x <= x2:
                return math.degrees(math.atan2(y2 - y1, x2 - x1))
        return 0.0

    def is_on_pad(self, x):
        """Check if x coordinate is within the landing pad bounds."""
        return self.pad_start <= x <= self.pad_end
