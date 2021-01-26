from python_tactics.new_sprite import Direction

class Map:

    def __init__(self, width, height):
        self._width, self._height = width, height
        self._sprites = []
        self._coordinates = []
        for _ in range(width):
            self._sprites.append([None for _ in range(height)])
            self._coordinates.append([None for _ in range(height)])
        self._rowcolumn = {}

    @property
    def sprites(self):
        for column in self._sprites:
            for sprite in column:
                yield sprite

    @property
    def coordinates(self):
        return self._coordinates

    def get_starting_positions(self, team_size):
        """Returns starting positions on this map for a team of size `team_size`.
           Result is pairs of coordinates and a direction, which is the direction towards the center"""
        starting_x = int((self._width - team_size) / 2)
        starting_y = int((self._height - team_size) / 2)
        return [[(x_side, starting_y + y_offset, direction) for y_offset in range(team_size)] for x_side, direction in ((0, Direction.SOUTH), (self._width - 1, Direction.NORTH))] \
             + [[(starting_x + x_offset, y_side, direction) for x_offset in range(team_size)] for y_side, direction in ((0, Direction.WEST), (self._height - 1, Direction.EAST))]


    def add_sprite(self, i, j, sprite):
        " Add the given sprite to the map at ith column and jth row "
        if 0 <= i < self._width and 0 <= j < self._height:
            self._sprites[i][j] = sprite
            self._coordinates[i][j] = (sprite.x, sprite.y)
            self._rowcolumn[(sprite.x, sprite.y)] = (i, j)

    def get_coordinates(self, i, j):
        " Get the x, y coordinates for the ith column and jth row "
        return self._coordinates[i][j]

    def get_row_column(self, x, y):
        " Get the row, column pair for the given x,y "
        return self._rowcolumn[(x, y)]

    def get_sprite(self, i, j):
        " Get the sprite at the ith column and jth row "
        if 0 <= i < self._width and 0 <= j < self._height:
            return self._sprites[i][j]
        return None

    def find_sprite(self, x, y):
        " Get the sprite which the given x,y falls within "
        for column in self._sprites:
            for sprite in column:
                if sprite.contains(x, y):
                    return sprite
        return None
