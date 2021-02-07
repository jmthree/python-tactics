import pyglet
from pyglet.gl import (GL_NEAREST, GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER,
                       GL_TEXTURE_MIN_FILTER,
                       glTexParameteri)
from pyglet.graphics import Batch

from python_tactics.new_sprite import Direction
from python_tactics.sprite import PixelAwareSprite
from python_tactics.util import find_path, load_sprite_asset


class RectangularMap:
    NORMAL_COLOR = 255, 255, 255
    SINGLE_HIGHLIGHT_COLOR = 100, 100, 100
    RADIUS_HIGHLIGHT_COLOR = 150, 150, 150

    r"""
    Creates a game map of size width by depth. The map lives in the (x, y) of the game, but thinks in terms of (i, j).
                      /\
                     /  \
               >    / i0 \    <
              /    /\ j0 /\    \
             i    /  \  /  \    j
            /    / i1 \/ i0 \    \
           <    /\ j0 /\ j1 /\    >
               /  \  /  \  /  \
              / i2 \/ i1 \/ i0 \
             /\ j0 /\ j1 /\ j2 /\
    The origin of the map is the top most corner, and all coordinates work down from there.
    Width is in terms of i, and depth is in terms of j.
    """

    blocks_sheet = pyglet.image.ImageGrid(load_sprite_asset("blocks"), 1, 101)
    grass_img = blocks_sheet[12]

    def __init__(self, width, depth, start_x, start_y):
        self._width, self._depth = width, depth
        self._start_x, self._start_y = start_x, start_y
        self._sprite_batch = Batch()
        self._sprites, self._ij_to_xy, self._xy_to_ij = self._generate()
        self._last_highlighted = None
        self._radius_highlights = []

    def _generate(self):
        # These values are based on our grass image, which is currently a 64*64 isomatric block
        # Each tile in our map shifts to the left or right a full 1/2 of the grass image
        # but as it moves down our map, it's only moving 1/4 of the image up or down.
        # This is because the top face of the tile only takes up 1/2 of the image, so 1/2 * 1/2
        x_offset, y_offset = self.grass_img.width / 2, self.grass_img.height / 4
        # The center of it's top face is 1/2 way over from the left and 3/4 from the top of the image
        self.grass_img.anchor_x = int(self.grass_img.width / 2)
        self.grass_img.anchor_y = int(self.grass_img.height * (3/4))
        sprites = {}
        ij_to_xy = {}
        xy_to_ij = {}
        grid = [(i, j) for i in range(self._width) for j in range(self._depth)]
        for i, j in grid:
            x = self._start_x + ((i - j) * x_offset)
            y = self._start_y - ((i + j) * y_offset)
            sprites[(i, j)] = PixelAwareSprite(self.grass_img, x, y, batch=self._sprite_batch)
            ij_to_xy[(i, j)] = (x, y)
            xy_to_ij[(x, y)] = (i, j)
        return sprites, ij_to_xy, xy_to_ij

    def draw(self):
        self._sprite_batch.draw()
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

    def highlight(self, i, j):
        if i < 0  or i >= self._width or j < 0 or j >= self._depth:
            return None
        if self._last_highlighted:
            color = self.RADIUS_HIGHLIGHT_COLOR if self._last_highlighted in self._radius_highlights else self.NORMAL_COLOR
            self._sprites[self._last_highlighted].color = color
        self._sprites[(i, j)].color = self.SINGLE_HIGHLIGHT_COLOR
        self._last_highlighted = (i, j)
        return i, j

    def radius_highlight(self, start_i, start_j, radius, exempt):
        in_range = self._points_in_range(start_i, start_j, radius)
        for ij in in_range:
            if ij not in exempt:
                self._radius_highlights.append(ij)
                self._sprites[ij].color = self.RADIUS_HIGHLIGHT_COLOR

    def reset_radius_highlight(self):
        for ij in self._radius_highlights:
            self._sprites[ij].color = self.NORMAL_COLOR
        self._radius_highlights = []

    def is_highlighted(self, i, j):
        return (i, j) in self._radius_highlights

    def get_starting_positions(self, team_size):
        """Returns starting positions on this map for a team of size `team_size`.
           Result is pairs of coordinates and a direction, which is the direction towards the center"""
        starting_x = int((self._width - team_size) / 2)
        starting_y = int((self._depth - team_size) / 2)
        return [[(x_side, starting_y + y_offset, direction) for y_offset in range(team_size)] for x_side, direction in ((0, Direction.SOUTH), (self._width - 1, Direction.NORTH))] \
             + [[(starting_x + x_offset, y_side, direction) for x_offset in range(team_size)] for y_side, direction in ((0, Direction.WEST), (self._depth - 1, Direction.EAST))]

    def find_path(self, start_x, start_y, target_x, target_y):
        coordinates_raw = {}
        for ij, xy in self._ij_to_xy.items():
            arr = coordinates_raw.get(ij[0], [])
            arr.append(xy)
            coordinates_raw[ij[0]] = arr
        coordinates = list(coordinates_raw.values())
        return find_path(coordinates, start_x ,start_y, target_x, target_y)

    def get_xy(self, i, j):
        " Get the x, y coordinates for the ith column and jth row "
        return self._ij_to_xy[(i, j)]

    def get_row_column(self, x, y):
        " Get the row, column pair for the given x,y "
        return self._xy_to_ij[(x, y)]

    def get_sprite(self, i, j):
        " Get the sprite at the ith column and jth row "
        if 0 <= i < self._width and 0 <= j < self._depth:
            return self._sprites[(i, j)]
        return None

    def find_sprite(self, x, y):
        " Get the sprite which the given x,y falls within "
        for column in self._sprites:
            for sprite in column:
                if sprite.contains(x, y):
                    return sprite
        return None

    def _points_in_range(self, column, row, length):
        if not 0 <= column < self._depth:
            return []
        if length == 0:
            return [(column, row)]
        return self._points_in_range(column - 1, row, length - 1) +\
                [(column, min(max(0, row - length + i), self._width - 1))
                    for i in range(2 * length + 1)] + \
                self._points_in_range(column + 1, row, length - 1)
