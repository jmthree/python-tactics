from new_sprite import Direction, Frame, Animation, \
        Character, Environment, Image, SoundClip

class Knight(Character):

    health   = 20
    speed    = 3
    range    = 1
    strength = 10
    defense  = 10
    magic    = 0

    profile  = Image("assets/knight/face.png")
    attack_sound = SoundClip("assets/sound/50557__broumbroum__sf3_sfx_menu_back.wav")

    class Sprite(Character.Sprite):

        north_east_face = Image("assets/knight/look_north.png")
        south_west_face = Image("assets/knight/look_west.png")

        faces = {
            Direction.NORTH : north_east_face,
            Direction.EAST  : north_east_face.flipped_about_x,
            Direction.SOUTH : south_west_face,
            Direction.WEST  : south_west_face.flipped_about_x,
            }

        north_east_walk = Animation([
            Frame(Image("assets/knight/walk_north1.png"), duration=0.1),
            Frame(Image("assets/knight/walk_north2.png"), duration=0.1),
            Frame(Image("assets/knight/walk_north3.png"), duration=0.1),
            ], 0.0)

        walking_animations = {
            Direction.NORTH : north_east_walk,
            Direction.EAST  : north_east_walk.flipped_about_x,
            }

class Mage(Character):

    health = 10
    speed  = 2
    range  = 4
    strength = 5
    defense  = 5
    magic    = 5

    profile  = Image("assets/mage/face.png")
    attack_sound = SoundClip("assets/sound/50561__broumbroum__sf3_sfx_menu_select.wav")

    class Sprite(Character.Sprite):

        north_east_face = Image("assets/mage/look_north.png")
        south_west_face = Image("assets/mage/look_west.png")

        faces = {
            Direction.NORTH : north_east_face,
            Direction.EAST  : north_east_face.flipped_about_x,
            Direction.SOUTH : south_west_face,
            Direction.WEST  : south_west_face.flipped_about_x,
            }

        north_east_walk = Animation([
            Frame(Image("assets/mage/walk_north1.png"), duration=0.1),
            Frame(Image("assets/mage/walk_north2.png"), duration=0.1),
            Frame(Image("assets/mage/walk_north3.png"), duration=0.1),
            ], 0.0)

        walking_animations = {
            Direction.NORTH : north_east_walk,
            Direction.EAST  : north_east_walk.flipped_about_x,
            }

class Grass(Environment):

    height = 0
    occupiable = True

    class Sprite(Environment.Sprite):
        face = Image("assets/grass.png")
