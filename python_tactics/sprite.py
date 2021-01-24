from pyglet.sprite import Sprite

class PixelAwareSprite(Sprite):
    def __init__(self, image, x, y, batch=None, centery=False):
        self.centery = centery
        super().__init__(image, x, y, batch=batch)

    @property
    def half_width(self):
        return self.width / 2

    @property
    def half_height(self):
        return self.height / 2

    @property
    def zindex(self):
        return self._zindex

    @zindex.setter
    def zindex(self, z):
        self._zindex = z

    def contains(self, x, y):
        left_bound, right_bound = self.x - self.half_width, self.x + self.half_width
        if not self.centery:
            bottom_bound, top_bound = self.y, self.y + self.height
        else:
            bottom_bound, top_bound = self.y - self.half_height, self.y + self.half_height
        in_x = left_bound <= x <= right_bound
        in_y = bottom_bound <= y <= top_bound
        return in_x and in_y and self._check_alpha(x, y)

    def _check_alpha(self, x, y):
        reverse = hasattr(self.image, "requires_reverse")
        if not reverse:
            relative_x = (x - self.x + self.half_width) / self.scale
        else:
            relative_x = (self.x + self.half_width - x) / self.scale
        if self.centery:
            relative_y = (y - self.y + self.half_height) / self.scale
        else:
            relative_y = (y - self.y) / self.scale
        pixel = self.image.get_region(relative_x, relative_y, 1, 1)
        raw = pixel.get_image_data()
        alpha = raw.get_data("A", raw.width)
        return alpha != "\0"

    def __str__(self):
        return "<PixelAwareSprite x:%s, y:%s>" % (self.x, self.y)
    __repr__ = __str__

class IsometricSprite(PixelAwareSprite):
    r"""
      north /\ east
       west \/ south
    """

    NORTH, EAST, SOUTH, WEST = list(range(4))

    def __init__(self, x, y, faces, batch=None):
        self.faces  = faces
        self.facing = IsometricSprite.EAST
        super().__init__(
                self.faces[self.facing], x, y, batch=batch)

    def look(self, direction):
        self.facing = direction
        self.image = self.faces[direction]

    def tick(self, time_delta):
        " Nothing to update here "

    def __str__(self):
        return "<IsometricSprite x:%s, y:%s>" % (self.x, self.y)
    __repr__ = __str__

class MovingSprite(IsometricSprite):
    " Isometric sprite that actually moves around "

    def __init__(self, x, y, faces, movements, batch=None):
        super().__init__(x, y, faces, batch=batch)
        self.movement_queue = []
        self.movement_ticks = 0
        self.movement_animations = movements
        self.last_stop = x,y

    def move_to(self, x, y, duration=1):
        self.movement_queue.append((x, y, duration))

    def animate_moving(self, direction):
        self.facing = direction
        self.image = self.movement_animations[direction]

    def tick(self, time_delta):
        if self.movement_queue:
            dest_x, dest_y, time = self.movement_queue[0]
            last_x, last_y = self.last_stop
            if dest_x < last_x and dest_y < last_y:
                self.look(IsometricSprite.WEST)
            elif dest_x < last_x:
                self.look(IsometricSprite.NORTH)
            elif dest_y < last_y:
                self.look(IsometricSprite.SOUTH)
            else:
                self.look(IsometricSprite.EAST)
            self.movement_ticks += time_delta
            self.x += (dest_x - last_x) * (time_delta / time)
            self.y += (dest_y - last_y) * (time_delta / time)

            if self.movement_ticks >= time:
                self.x, self.y = int(dest_x), int(dest_y)
                del self.movement_queue[0]
                self.movement_ticks = 0
                self.last_stop = self.x, self.y
        else:
            self.look(self.facing)

    def __str__(self):
        return "<MovingSprite x:%s, y:%s>" % (self.x, self.y)
    __repr__ = __str__
