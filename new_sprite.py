# Tile directions
#        /\
# North /  \ East
#      /    \
#      \    /
# West  \  / South
#        \/

# Types of sprites:
#   StaticSprite - Does not move or turn in the scene.
#       Requires:
#           * 1x image for displaying in all direction
#   TurnableSprite - Does not move, but can be turned.
#       Requires:
#           * 4x image: one image for each direction
#   MoveableSprite (TurnableSprite) - Moves and turns
#       Requires:
#           * 4x image for TurnableSprite


# Element
#   * move (x, y) - Tells the element to move to the set coordinates
#   * update (time) - Return updated sprite, with whatever moves and images changed
#   * @x - The x coordinate of the element
#   * @y - The y coordinate of the element
#   * @image - The current image the element should show

from collections import namedtuple

from pyglet import image
from pyglet import media
from pyglet.sprite import Sprite
from functools import reduce

class Direction(object):
    NORTH, EAST, SOUTH, WEST = 0, 1, 2, 3

def SoundClip(file):
    return media.load(file, streaming=False)

class Image(object):

    def __init__(self, image_file, anchor_x=0, anchor_y=0):
        self._image = image.load(image_file)
        self._image.anchor_x = int(self._image.width / 2)
        self._image.anchor_y = int(self._image.height)

    @property
    def flipped_about_x(self):
        anchor_x, anchor_y = self._image.anchor_x, self._image.anchor_y
        width, height = self._image.width, self._image.height
        self._image = self._image.get_texture().get_transform(flip_x=True)
        self._image.anchor_x = width - anchor_x
        self._image.anchor_y = height - anchor_y
        return self

    def get_texture(self):
        return self._image.get_texture()

    def blit(self, x, y):
        self._image.blit(x, y)

class Frame(namedtuple("Frame", "image duration")):

    @property
    def flipped_about_x(self):
        return Frame(self.image.flipped_about_x, self.duration)

class Animation(namedtuple("Animation", "frames amount_played")):

    @property
    def duration(self):
        return reduce(lambda d, f: f.duration + d, self.frames, 0.0)

    @property
    def image(self):
        accum = 0.0
        for frame in self.frames:
            accum = accum + frame.duration
            if accum > self.amount_played:
                return frame.image

    @property
    def flipped_about_x(self):
        return Animation(
                [frame.flipped_about_x for frame in self.frames],
                self.amount_played)


    def update(self, dt):
        return Animation(self.frames, (self.amount_played + dt) % self.duration)

SpriteBase = namedtuple("SpriteBase", "x y")

class SpriteMovement(object):

    def update(self, dt):
        pass

class Character(object):

    def __init__(self, x, y, facing=Direction.NORTH):
        self.sprite = Sprite(self.Sprite.faces[facing], x, y)
        self.facing = facing
        self.movement_queue = []
        self.movement_ticks = 0

        self.current_health = self.health

    def draw(self):
        self.sprite.draw()

    def delete(self):
        self.sprite.delete()

    @property
    def x(self):
        return self.sprite.x

    @x.setter
    def x(self, nx):
        self.sprite.x = nx

    @property
    def y(self):
        return self.sprite.y

    @y.setter
    def y(self, ny):
        self.sprite.y = ny

    @property
    def color(self):
        return self.sprite.color

    @color.setter
    def color(self, ncolor):
        self.sprite.color = ncolor

    def look(self, direction):
        self.facing = direction
        self.sprite.image = self.Sprite.faces[direction]

    def move_to(self, x, y, duration=1):
        self.movement_queue.append((x, y, duration))

    def update(self, dt):
        if self.movement_queue:
            if self.movement_ticks == 0:
                self.last_stop = self.x, self.y
            ex, ey, time = self.movement_queue[0]
            sx, sy = self.last_stop
            if ex < sx and ey < sy:
                self.look(Direction.WEST)
            elif ex < sx:
                self.look(Direction.NORTH)
            elif ey < sy:
                self.look(Direction.SOUTH)
            else:
                self.look(Direction.EAST)
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


    class Sprite(namedtuple("CharacterSprite", "x y facing moving_to internal_clock")):
#
#        @property
#        def image(self):
#            return self.faces[self.facing]
#
#        def update(self, dt):
#            return self.__class__(self.x, self.y, self.facing, self.moving_to, self.internal_clock + dt)
#
#        def move(self, new_x, new_y):
            pass

class Environment(object):

    @property
    def can_occupy(self):
        return hasattr(self, 'occupiable') and self.occupiable or False

    @property
    def level(self):
        return hasattr(self, 'height') and self.height or 0

    class Sprite(SpriteBase):

        def update(self, dt):
            return self

        def move(self, x, y):
            return self

        @property
        def image(self):
            return self.face

#class Sprite(object):
#
#    def __init__(self, x, y):
#        self.sprite = PygletSprite(self.face, x, y)
#
#    @property
#    def x(self):
#        return self.sprite.x
#
#    @property
#    def y(self):
#        return self.sprite.y
#
#    def draw(self):
#        return self.sprite.draw()
#
#    def turn(self, direction):
#        return self
#
#    def move(self, new_x, new_y):
#        return self
#
#    def update(self, dt):
#        return self
#
#class TurnableSprite(Sprite):
#
#    def __init__(self, x, y, facing=Direction.NORTH):
#        self.face = self.faces[facing]
#        super(TurnableSprite, self).__init__(x, y)
#
#    def turn(self, direction):
#        return TurnableSprite(self.x, self.y, direction)
