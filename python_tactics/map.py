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
