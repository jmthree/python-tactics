import pyglet
from python_tactics.new_sprite import (Animation, Character, Direction,
                                       Environment, Image, sound_clip)
from python_tactics.util import load_sprite_asset

def anchor(img):
    img.anchor_x = int(img.width / 2)
    img.anchor_y = 25
    return img

class Beefy(Character):

    health   = 20
    speed    = 3
    range    = 1
    strength = 10
    defense  = 10
    magic    = 0

    profile  = Image("knight/face.png")
    attack_sound = sound_clip("50557__broumbroum__sf3_sfx_menu_back.wav")

    class Sprite(Character.Sprite):

        sprite_sheet = pyglet.image.ImageGrid(load_sprite_asset("spaghetti_atlas"), 12, 24)

        faces = {
            Direction.NORTH : anchor(sprite_sheet[43]),
            Direction.EAST  : anchor(sprite_sheet[41]),
            Direction.SOUTH : anchor(sprite_sheet[45]),
            Direction.WEST  : anchor(sprite_sheet[46]),
            }

        north_east_walk = Animation([
            # This references images i've removed. Will replace with things from atlas
            # Frame(Image("knight/walk_north1.png"), duration=0.1),
            # Frame(Image("knight/walk_north2.png"), duration=0.1),
            # Frame(Image("knight/walk_north3.png"), duration=0.1),
            ], 0.0)

        walking_animations = {
            Direction.NORTH : north_east_walk,
            Direction.EAST  : north_east_walk.flipped_about_x,
            }

class Ranged(Character):
    # unicorn_atlas
    # 13, 45 SE
    # 14, 46 SW
    # 9,  41 NE
    # 11, 43 NW

    health = 10
    speed  = 2
    range  = 4
    strength = 5
    defense  = 5
    magic    = 5

    profile  = Image("mage/face.png")
    attack_sound = sound_clip("50561__broumbroum__sf3_sfx_menu_select.wav")

    class Sprite(Character.Sprite):

        sprite_sheet = pyglet.image.ImageGrid(load_sprite_asset("unicorn_atlas"), 12, 24)

        faces = {
            Direction.NORTH : anchor(sprite_sheet[43]),
            Direction.EAST  : anchor(sprite_sheet[41]),
            Direction.SOUTH : anchor(sprite_sheet[45]),
            Direction.WEST  : anchor(sprite_sheet[46]),
            }

        north_east_walk = Animation([
            # This references images i've removed. Will replace with things from atlas
            # Frame(Image("mage/walk_north1.png"), duration=0.1),
            # Frame(Image("mage/walk_north2.png"), duration=0.1),
            # Frame(Image("mage/walk_north3.png"), duration=0.1),
            ], 0.0)

        walking_animations = {
            Direction.NORTH : north_east_walk,
            Direction.EAST  : north_east_walk.flipped_about_x,
            }
