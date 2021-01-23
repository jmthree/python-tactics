from pyglet.sprite import Sprite

class PixelAwareSprite(Sprite):
    def __init__(self, image, x, y, batch=None, centery=False):
        self.centery = centery
        super(PixelAwareSprite, self).__init__(image, x, y, batch=batch)

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
        x1, x2 = self.x - self.half_width, self.x + self.half_width
        if not self.centery:
            y1, y2 = self.y, self.y + self.height
        else:
            y1, y2 = self.y - self.half_height, self.y + self.half_height
        in_x = x1 <= x <= x2
        in_y = y1 <= y <= y2
        return in_x and in_y and self._check_alpha(x, y)

    def _check_alpha(self, x, y):
        reverse = hasattr(self.image, "requires_reverse")
        if not reverse:
            px = (x - self.x + self.half_width) / self.scale
        else:
            px = (self.x + self.half_width - x) / self.scale
        if self.centery:
            py = (y - self.y + self.half_height) / self.scale
        else:
            py = (y - self.y) / self.scale
        pixel = self.image.get_region(px, py, 1, 1)
        raw = pixel.get_image_data()
        alpha = raw.get_data("A", raw.width)
        return alpha != "\0"

    def __str__(self):
        return "<PixelAwareSprite x:%s, y:%s>" % (self.x, self.y)
    __repr__ = __str__

class IsometricSprite(PixelAwareSprite):
    """
      north /\ east
       west \/ south
    """

    NORTH, EAST, SOUTH, WEST = list(range(4))

    def __init__(self, x, y, faces, batch=None):
        self.faces  = faces
        self.facing = IsometricSprite.EAST
        super(IsometricSprite, self).__init__(
                self.faces[self.facing], x, y, batch=batch)

    def look(self, direction):
        self.facing = direction
        self.image = self.faces[direction]

    def update(self, dt):
        " Nothing to update here "
        pass

    def __str__(self):
        return "<IsometricSprite x:%s, y:%s>" % (self.x, self.y)
    __repr__ = __str__

class MovingSprite(IsometricSprite):
    " Isometric sprite that actually moves around "

    def __init__(self, x, y, faces, movements, batch=None):
        self.movement_queue = []
        self.movement_ticks = 0
        self.movement_animations = movements
        super(MovingSprite, self).__init__(x, y, faces, batch=batch)

    def move_to(self, x, y, duration=1):
        self.movement_queue.append((x, y, duration))

    def animate_moving(self, direction):
        self.facing = direction
        self.image = self.movement_animations[direction]

    def update(self, dt):
        if self.movement_queue:
            if self.movement_ticks == 0:
                self.last_stop = self.x, self.y
            ex, ey, time = self.movement_queue[0]
            sx, sy = self.last_stop
            if ex < sx and ey < sy:
                self.animate_moving(IsometricSprite.WEST)
            elif ex < sx:
                self.animate_moving(IsometricSprite.NORTH)
            elif ey < sy:
                self.animate_moving(IsometricSprite.SOUTH)
            else:
                self.animate_moving(IsometricSprite.EAST)
            self.movement_ticks += dt
            ex, ey, time = self.movement_queue[0]
            sx, sy = self.last_stop
            self.x += (ex - sx) * (dt / time)
            self.y += (ey - sy) * (dt / time)

            if self.movement_ticks >= time:
                self.x, self.y = int(ex), int(ey)
                del self.movement_queue[0]
                self.movement_ticks = 0
        else:
            self.look(self.facing)

    def __str__(self):
        return "<MovingSprite x:%s, y:%s>" % (self.x, self.y)
    __repr__ = __str__
