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
#   * tick (time) - Return updated sprite, with whatever moves and images changed
#   * @x - The x coordinate of the element
#   * @y - The y coordinate of the element
#   * @image - The current image the element should show

import os
from collections import namedtuple
from enum import Enum
from functools import reduce

from pyglet import graphics, image, media
from pyglet.sprite import Sprite
from pyglet.text import Label

from python_tactics.util import asset_to_file


class Direction(Enum):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

def sound_clip(sound_asset):
    return media.load(asset_to_file(os.path.join("sounds", sound_asset)), streaming=False)

class Image:

    def __init__(self, image_asset):
        self._image = image.load(asset_to_file(os.path.join("images", image_asset)))
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
        return self.frames[0]

    @property
    def flipped_about_x(self):
        return Animation(
                [frame.flipped_about_x for frame in self.frames],
                self.amount_played)


    def tick(self, time_delta):
        return Animation(self.frames, (self.amount_played + time_delta) % self.duration)

SpriteBase = namedtuple("SpriteBase", "x y")

class Health:
    def __init__(self, current_health, max_health, x, y, y_offset):
        self.current_health = current_health
        self.max_health = max_health
        self.y_offset = y_offset
        self.sprite = self._create_sprite(x, y)

    def draw(self):
        self.sprite.draw()

    @property
    def x(self):
        return self.sprite.x

    @property
    def y(self):
        return self.sprite.y

    @x.setter
    def x(self, x):
        self.sprite.x = x

    @y.setter
    def y(self, y):
        self.sprite.y = y + (self.y_offset - 20)

    def hit(self, attack):
        self.current_health = max(0, self.current_health - attack)
        self.sprite.text = self._create_label_text()
        return self.current_health

    def delete(self):
        self.sprite.delete()

    def _create_sprite(self, x, y):
        return Label(text=self._create_label_text(),
                     font_name='Times New Roman',
                     font_size=18,
                     bold=True,
                     x=x,
                     y=y + (self.y_offset - 20),
                     anchor_x='center')

    def _create_label_text(self):
        return f"{self.current_health}/{self.max_health}"


class Character:

    def __init__(self, x, y, facing=Direction.NORTH):
        self.facing = facing
        self.movement_queue = []
        self.movement_ticks = 0
        self.sprite = Sprite(self.Sprite.faces[facing], x, y)
        self.health = Health(self.health, self.health, x, y, self.sprite.height)
        self.last_stop = (self.x, self.y)

    def draw_character(self):
        self.sprite.draw()

    def draw_ui(self):
        self.health.draw()

    def delete(self):
        self.health.delete()
        self.sprite.delete()

    @property
    def x(self):
        return self.sprite.x

    @x.setter
    def x(self, x):
        self.sprite.x = x
        self.health.x = x

    @property
    def y(self):
        return self.sprite.y

    @y.setter
    def y(self, y):
        self.sprite.y = y
        self.health.y = y

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

    def tick(self, time_delta):
        if self.movement_queue:
            dest_x, dest_y, time = self.movement_queue[0]
            last_x, last_y = self.last_stop
            if dest_x < last_x and dest_y < last_y:
                self.look(Direction.WEST)
            elif dest_x < last_x:
                self.look(Direction.NORTH)
            elif dest_y < last_y:
                self.look(Direction.SOUTH)
            else:
                self.look(Direction.EAST)
            self.movement_ticks += time_delta
            self.x += (dest_x - last_x) * (time_delta / time)
            self.y += (dest_y - last_y) * (time_delta / time)

            if self.movement_ticks >= time:
                self.x, self.y = int(dest_x), int(dest_y)
                del self.movement_queue[0]
                self.movement_ticks = 0
                self.last_stop = (self.x, self.y)
        else:
            self.look(self.facing)

    def hit(self, attack):
        return self.health.hit(attack)


    class Sprite(namedtuple("CharacterSprite", "x y facing moving_to internal_clock")):
#
#        @property
#        def image(self):
#            return self.faces[self.facing]
#
#        def tick(self, time_delta):
#            return self.__class__(self.x, self.y, self.facing, self.moving_to, self.internal_clock + dt)
#
#        def move(self, new_x, new_y):
        pass

class Environment:

    def __init__(self):
        self.occupiable = False
        self.height = 0

    @property
    def can_occupy(self):
        return self.occupiable

    @property
    def level(self):
        return self.height

    class Sprite(SpriteBase):

        def tick(self, _time_delta):
            return self

        def move(self, _x, _y):
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
#    def tick(self, time_delta):
#        return self
#
#class TurnableSprite(Sprite):
#
#    def __init__(self, x, y, facing=Direction.NORTH):
#        self.face = self.faces[facing]
#        super().__init__(x, y)
#
#    def turn(self, direction):
#        return TurnableSprite(self.x, self.y, direction)
