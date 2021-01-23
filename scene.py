import random
from functools import reduce

import pyglet
from pyglet import clock
from pyglet.graphics import Batch
from pyglet.image import SolidColorImagePattern
from pyglet.sprite import Sprite
from pyglet.text import Label
from pyglet.window import key

from knight import Knight, Mage
from map import Map
from new_sprite import Direction
from sprite import MovingSprite, PixelAwareSprite
from util import (faces_from_images, find_path, load_sprite_animation,
                  load_sprite_asset)


class World:

    def __init__(self, window, camera):
        self.window = window
        self.camera = camera
        self.current = None

    def transition(self, scenecls, *args, **kwargs):
        if self.current:
            self.current.unload(self.window)
        scene = scenecls(self, *args, **kwargs)
        self.current = scene
        scene.load(self.window)

    def reload(self, scene):
        if self.current:
            self.current.unload(self.window)
        self.current = scene
        scene.load(self.window)

class Scene:

    WINDOW_EVENTS = ["on_draw", "on_mouse_press", "on_mouse_release",
                     "on_mouse_drag", "on_key_press"]

    def __init__(self, world):
        self.world = world

    @property
    def camera(self):
        return self.world.camera

    @property
    def window(self):
        return self.world.window

    def enter(self):
        pass

    def exit(self):
        pass

    def load(self, window):
        """ For each window event, if this Scene has a handler, attach that
            handler to the window
        """
        # Loads our callbacks
        for event in Scene.WINDOW_EVENTS:
            if hasattr(self, event):
                window.__setattr__(event, self.__getattribute__(event))

        # Call enter to set up the scene if needed
        self.enter()

    def unload(self, window):
        # Cleans out any old callbacks
        for event in Scene.WINDOW_EVENTS:
            window.__setattr__(event, lambda *args: False)

        # Call exit to do whatever if needed
        self.exit()

    def __del__(self):
        print(("Deleting %s" % self))


class MainMenuScene(Scene):

    def __init__(self, world):
        super().__init__(world)
        self.text_batch = Batch()
        self.cursor = Label(">", font_name='Times New Roman', font_size=36,
                            x=200 + self.camera.offset_x,
                            y=300 + self.camera.offset_y,
                            batch=self.text_batch)
        self.cursor_pos = 0
        self.moogle = self._load_moogle()

        self.menu_items = {
            "Start Game"   : self._new_game,
            "About"        : self._launch_about,
            "Quit Program" : self.window.close
        }
        self._generate_text()

        self.key_handlers = {
            (key.ESCAPE, 0) : self.window.close,
            (key.UP, 0)     : lambda: self._move_cursor(1),
            (key.DOWN, 0)   : lambda: self._move_cursor(-1),
            (key.ENTER, 0)  : self._menu_action
        }

    def enter(self):
        black = 0, 0, 0, 0
        pyglet.gl.glClearColor(*black)

    def on_draw(self):
        self.world.window.clear()
        self.moogle.draw()
        self.text_batch.draw()
        self.camera.focus(self.window.width, self.window.height)

    def on_key_press(self, button, modifiers):
        pressed = (button, modifiers)
        handler = self.key_handlers.get(pressed, lambda: None)
        handler()

    def _generate_text(self):
        real_cord = lambda x,y: (x + self.camera.offset_x,
                                 y + self.camera.offset_y)
        title_x, title_y = real_cord(10, 520)
        Label('FF:Tactics.py', font_name='Times New Roman', font_size=56,
                x=title_x, y=title_y, batch=self.text_batch)

        menu_texts = list(self.menu_items.keys())
        for i, text in enumerate(menu_texts):
            text_x, text_y = real_cord(240, 300 - 40 * i)
            Label(text, font_name='Times New Roman', font_size=36,
                    x=text_x, y=text_y, batch=self.text_batch)

        hint_x, hint_y = real_cord(400, 30)
        Label("Use Up and Down Arrows to navigate",
                font_name='Times New Roman', font_size=18,
                x=hint_x, y=hint_y, batch=self.text_batch)
        Label("Use Enter to choose",
                font_name='Times New Roman', font_size=18,
                x=hint_x, y=hint_y - 20, batch=self.text_batch)

    def _load_moogle(self):
        moogle_image = load_sprite_asset("moogle")
        moogle_image.anchor_x = moogle_image.width / 2
        moogle_image.anchor_y = moogle_image.height / 2
        moog_sprite = Sprite(moogle_image,
                        40 + self.camera.offset_x,
                        40 + self.camera.offset_y)
        return moog_sprite

    def _new_game(self):
        self.world.transition(GameScene)

    def _launch_about(self):
        self.world.transition(AboutScene, previous=self)

    def _menu_action(self):
        actions = list(self.menu_items.values())
        actions[self.cursor_pos]()

    def _move_cursor(self, direction):
        self.cursor_pos = (self.cursor_pos - direction) % len(self.menu_items)
        self.cursor.y = 300 + self.camera.offset_y - 40 * self.cursor_pos


#pylint: disable=too-many-instance-attributes
class GameScene(Scene):

    # Game map constants
    MAP_START_X, MAP_START_Y = 400, 570
    GRID_WIDTH, GRID_HEIGHT = 100, 50
    MAP_WIDTH = MAP_HEIGHT = 10

    # The modes the game scene can be in
    NOTIFY, SELECT_MODE, ACTION_MODE, MOVE_TARGET_MODE, ATTACK_TARGET_MODE = list(range(5))

    def __init__(self, world):
        super().__init__(world)

        self.map_batch  = Batch()
        self.map        = self._generate_map()
        self.players    = self._initialize_teams()
        self.current_turn = 1
        #import knight
        #knight_x, knight_y = self.map.get_coordinates(5, 5)
        #self.characters  = [knight.Knight.Sprite(knight_x, knight_y, 2, 0, 0.0)]
        #self.selected   = None
        self.selected   = 0, 0
        self.selected_character = None
        self.mode = GameScene.SELECT_MODE
        self.turn_notice = None

        # Items for action menu
        self.text_batch = Batch()
        self.cursor_pos = 0
        self.cursor = Label(">", font_name='Times New Roman', font_size=36,
                            x=10 + self.camera.offset_x,
                            y=140 + self.camera.offset_y,
                            batch=self.text_batch)
        self.action_menu_texts = []

        self.action_menu_items = {
                "Move"              : self._initiate_movement,
                "Attack"            : self._initiate_attack,
                "Cancel"            : self._close_action_menu,
        }

        # Sprites which need hilighting from different modes
        self.movement_hilight = []
        self.attack_hilight = []

        self.key_handlers = {
            GameScene.SELECT_MODE : {
                (key.ESCAPE, 0) : self.game_menu,
                (key.LEFT, 0)   : lambda: self.move_hilight(-1, 0),
                (key.RIGHT, 0)  : lambda: self.move_hilight(1, 0),
                (key.UP, 0)     : lambda: self.move_hilight(0, -1),
                (key.DOWN, 0)   : lambda: self.move_hilight(0, 1),
                (key.ENTER, 0)  : self._open_action_menu,
                },
            GameScene.ACTION_MODE : {
                (key.ESCAPE, 0)  : self._close_action_menu,
                (key.UP, 0)     : lambda: self._move_cursor(1),
                (key.DOWN, 0)   : lambda: self._move_cursor(-1),
                (key.ENTER, 0)  : self._menu_action
                },
            GameScene.MOVE_TARGET_MODE : {
                (key.LEFT, 0)   : lambda: self.move_hilight(-1, 0),
                (key.RIGHT, 0)  : lambda: self.move_hilight(1, 0),
                (key.UP, 0)     : lambda: self.move_hilight(0, -1),
                (key.DOWN, 0)   : lambda: self.move_hilight(0, 1),
                (key.ENTER, 0)  : self._execute_move,
                (key.ESCAPE, 0) : self._open_action_menu,
                },
            GameScene.ATTACK_TARGET_MODE : {
                (key.LEFT, 0)   : lambda: self.move_hilight(-1, 0),
                (key.RIGHT, 0)  : lambda: self.move_hilight(1, 0),
                (key.UP, 0)     : lambda: self.move_hilight(0, -1),
                (key.DOWN, 0)   : lambda: self.move_hilight(0, 1),
                (key.ENTER, 0)  : self._execute_attack,
                (key.ESCAPE, 0) : self._open_action_menu,
                },
        }
        self.change_player()

    def _all_characters(self):
        return reduce(lambda chars, player: player + chars, self.players)

    def _other_characters(self):
        if self.current_turn:
            return self.players[0]
        return self.players[1]

    def change_player(self):
        old_turn = self.current_turn
        self.current_turn = (self.current_turn + 1) % 2
        if not self.players[self.current_turn]:
            self.world.transition(VictoryScene, winner=old_turn + 1)
        else:
            self.display_turn_notice(self.current_turn)

    def display_turn_notice(self, current_turn):
        if self.turn_notice is not None:
            self.turn_notice.delete()
        self.turn_notice = Label(
                "Player %s's Turn" % (current_turn + 1),
                font_name='Times New Roman', font_size=36,
                x= 500 + self.camera.offset_x,
                y= 560 + self.camera.offset_y)
        self.turn_notice.color = 255 - (100 * current_turn), 255 - (100 * ((current_turn + 1) % 2)), 255, 255

    def _initialize_teams(self):
        def load_knight(hue):
            knight_x, knight_y = self.map.get_coordinates(9 * hue, 9 * hue)
            direction = Direction.WEST if hue else Direction.SOUTH
            knight = Knight(knight_x, knight_y, direction)
            knight.zindex=10
            knight.color = 255 - (150 * hue), 255 - (150 * ((hue + 1) % 2)), 0
            mage_x, mage_y = self.map.get_coordinates(7 * hue + 1, 7 * hue + 1)
            mage = Mage(mage_x, mage_y, direction)
            mage.zindex=10
            mage.color = 255 - (150 * hue), 255 - (150 * ((hue + 1) % 2)), 255
            return [knight, mage]
        return [load_knight(i) for i in range(2)]

    def move_hilight(self, x, y):
        current_x, current_y = self.selected
        self.selected = max(0, min(x + current_x, GameScene.MAP_WIDTH - 1)),\
                        max(0, min(y + current_y, GameScene.MAP_HEIGHT - 1))
        newx, newy = self.map.get_coordinates(*self.selected)
        self.camera.look_at((newx + self.camera.x) / 2, (newy + self.camera.y) / 2)

    def enter(self):
        blue = 0.6, 0.6, 1, 0.8
        pyglet.gl.glClearColor(*blue)
        clock.schedule(self._update_characters)

    def exit(self):
        clock.unschedule(self._update_characters)

    def on_draw(self):
        self.window.clear()
        selected_x, selected_y = self.map.get_coordinates(*self.selected)
#        if  selected_x <= 100 or selected_x >= 500 \
#                or selected_y <= 100 or selected_y >= 700:
        for sprite in self.map.sprites:
            if (selected_x, selected_y) == (sprite.x, sprite.y):
                sprite.color = 100, 100, 100
            elif sprite in self.movement_hilight:
                sprite.color = 100, 100, 255
            elif sprite in self.attack_hilight:
                sprite.color = 255, 100, 100
            else:
                sprite.color = 255, 255, 255
        self.map_batch.draw()
        if hasattr(self, 'turn_notice'):
            self.turn_notice.x = 500 + self.camera.offset_x
            self.turn_notice.y = 560 + self.camera.offset_y
            self.turn_notice.draw()
        for character in sorted(self._all_characters(), key=lambda c: -int(c.y)):
#            if (selected_x, selected_y) == (character.x, character.y):
#                character.color = 100, 100, 100
#            else:
#                character.color = 255, 255, 255
            character.draw()
#            #character.image.blit(character.x, character.y)
        if self.mode == GameScene.ACTION_MODE:
            self._draw_action_menu()
            self.text_batch.draw()
        self.camera.focus(self.window.width, self.window.height)

    def _menu_action(self):
        actions = list(reversed(list(self.action_menu_items.values())))
        actions[self.cursor_pos]()

    def _move_cursor(self, direction):
        self.cursor_pos = (self.cursor_pos - direction) % len(self.action_menu_items)
        self.cursor.x = 10 + self.camera.offset_x
        self.cursor.y = 150 + self.camera.offset_y - 50 * self.cursor_pos

    def _draw_action_menu(self):
        pattern = SolidColorImagePattern((0, 0, 150, 200))
        overlay_image = pattern.create_image(1000, 200)
        overlay_image.anchor_x = int(overlay_image.width / 2)
        overlay_image.anchor_y = overlay_image.height + 100
        overlay = Sprite(overlay_image, self.camera.x, self.camera.y)
        overlay.draw()

        self._generate_text()

    def _generate_text(self):
        real_cord = lambda x,y: (x + self.camera.offset_x,
                                 y + self.camera.offset_y)

        menu_texts = reversed(list(self.action_menu_items.keys()))
        for label in self.action_menu_texts:
            label.delete()

        for i, text in enumerate(menu_texts):
            text_x, text_y = real_cord(40, 150 - 50 * i)
            self.action_menu_texts.append(
                    Label(text, font_name='Times New Roman', font_size=36,
                        x=text_x, y=text_y, batch=self.text_batch))


#    def on_mouse_press(self, x, y, button, modifiers):
#        real_x, real_y = int(self.camera.offset_x + x),\
#                         int(self.camera.offset_y + y)
#        inside_map = self.map.find_sprite(x, y)
#        inside_chars = [c for c in self.characters if c.contains(real_x, real_y)]
#        taken  = [self.map.get_row_column(c.x, c.y) for c in self.characters]
#
#        # Reset everything
#        if self.selected: self.selected.color = 255, 255, 255
#        for msprite in self.map.sprites:
#            msprite.color = 255, 255, 255
#
#        if inside_chars or inside_map:
#            if inside_chars:
#                selected = inside_chars[0]
#            else:
#                selected = inside_map
#            last, self.selected = self.selected, selected
#            self.selected.color = 100, 100, 100
#            rx = self.selected.x + self.camera.offset_x
#            ry = self.selected.y + self.camera.offset_y
#            column, row = self.map.get_row_column(selected.x, selected.y)
#            if hasattr(self.selected, "is_player"):
#                in_range = self._points_in_range(column, row, 4)
#                for column, row in in_range:
#                    if (column, row) not in taken:
#                        self.map.get_sprite(column, row).color = 100, 100, 255
#            elif hasattr(last, "is_player"):
#                last_column, last_row = self.map.get_row_column(last.x, last.y)
#                last_pair = last_column, last_row
#                new_indexes = self.map.get_row_column(selected.x, selected.y)
#                new_pair  = int(selected.x), int(selected.y)
#                in_range = self._points_in_range(last_column, last_row, 4)
#                if new_indexes in in_range and new_pair not in taken:
#                    self._schedule_movement(last, new_pair)
#        else:
#            self.selected = None

    def _initiate_movement(self):
        self.mode = GameScene.MOVE_TARGET_MODE
        self.movement_hilight = []
        character = self.selected_character
        taken  = [self.map.get_row_column(c.x, c.y) for c in self._all_characters()]
        column, row = self.map.get_row_column(character.x, character.y)
        in_range = self._points_in_range(column, row, character.speed)
        for column, row in in_range:
            if (column, row) not in taken:
                self.movement_hilight.append(self.map.get_sprite(column, row))

    def _execute_move(self):
        taken  = [self.map.get_row_column(c.x, c.y) for c in self._all_characters()]
        if self.selected not in taken:
            sprite = self.map.get_sprite(*self.selected)
            if sprite in self.movement_hilight:
                last = self.map.get_coordinates(*self.selected)
                self._schedule_movement(self.selected_character, last)
                self.movement_hilight = []
                self.change_player()
                self._close_action_menu()

    def _initiate_attack(self):
        self.mode = GameScene.ATTACK_TARGET_MODE
        self.attack_hilight = []
        character = self.selected_character
        column, row = self.map.get_row_column(character.x, character.y)
        in_range = self._points_in_range(column, row, character.range)
        in_range.remove(self.selected)
        for column, row in in_range:
            self.attack_hilight.append(self.map.get_sprite(column, row))

    def _execute_attack(self):
        sprite = self.map.get_sprite(*self.selected)
        attacker = self.selected_character
        attacked = None
        if sprite in self.attack_hilight:
            for character in self._other_characters():
                char_loc = self.map.get_row_column(character.x, character.y)
                if  char_loc == self.selected:
                    attacked = character
        if attacked:
            attack = random.randrange(attacker.strength)
            defense = random.randrange(attacked.defense)
            hit = max(1, defense - attack)
            print("Hit for ", hit)
            attacker.attack_sound.play()
            attacked.current_health = attacked.current_health - hit
            if attacked.current_health <= 0:
                self._other_characters().remove(attacked)
                attacked.delete()
            self.attack_hilight = []
            self.change_player()
            self._close_action_menu()

    def on_key_press(self, button, modifiers):
        pressed = (button, modifiers)
        handler = self.key_handlers[self.mode].get(pressed, lambda: None)
        handler()

    def _generate_map(self):
        x, y = GameScene.MAP_START_X, GameScene.MAP_START_Y
        x_offset, y_offset = self.GRID_WIDTH / 2, self.GRID_HEIGHT / 2
        columns, rows = GameScene.MAP_WIDTH, GameScene.MAP_HEIGHT

        column_starts = [(x + i * x_offset, y - i * y_offset)
                            for i in range(columns)]
        map_points    = [[(x - i * x_offset, y - i * y_offset)
                            for i in range(rows)]
                            for x, y in column_starts]

        gamemap = Map(columns, rows)
        for i, column in enumerate(map_points):
            for j, (x, y) in enumerate(column):
                image = load_sprite_asset("grass")
                image.anchor_x = image.width / 2
                image.anchor_y = image.height / 2
                sprite = PixelAwareSprite(image, x, y,
                            batch=self.map_batch, centery=True)
                sprite.scale = 1
                sprite.zindex = 0
                gamemap.add_sprite(i, j, sprite)
        return gamemap

    def _load_characters(self):
        # Just load the knight for now
        knight_north = load_sprite_asset("knight/look_north")
        knight_west = load_sprite_asset("knight/look_west")
        knight_walk_west  = load_sprite_animation("knight", "walk_west", 8, 0.15)
        knight_walk_north = load_sprite_animation("knight", "walk_north", 8, 0.15)
        #knight_walk_west = knight_walk_north = pyglet.image.load_animation("assets/knight/walk_west.gif")
#        knight_walk_west.anchor_x = knight_walk_west.width / 2

        knight_x, knight_y = self.map.get_coordinates(5, 5)
        knight_faces = faces_from_images(north=knight_north, west=knight_west)
        knight_walks = [knight_walk_north, knight_walk_west,
                        knight_walk_north, knight_walk_west]
        knight = MovingSprite(knight_x, knight_y, knight_faces, knight_walks)
        knight.scale=1
        knight.is_player=True
        knight.zindex=10

        knight_x, knight_y = self.map.get_coordinates(5, 0)
        knight2 = MovingSprite(knight_x, knight_y, knight_faces, knight_walks)
        knight2.scale=1
        knight2.is_player=True
        knight2.zindex=10
        knight2.look(2)

        return [knight, knight2]

    def _points_in_range(self, column, row, length):
        if not 0 <= column < self.MAP_HEIGHT:
            return []
        if length == 0:
            return [(column, row)]
        return self._points_in_range(column - 1, row, length - 1) +\
                [(column, min(max(0, row - length + i), self.MAP_WIDTH - 1))
                    for i in range(2 * length + 1)] + \
                self._points_in_range(column + 1, row, length - 1)

    def _schedule_movement(self, sprite, pos):
        end_x, end_y = pos
        path = find_path(self.map.coordinates, sprite.x, sprite.y, end_x, end_y)
        for x, y in path:
            sprite.move_to(x, y, 0.3)

    def _update_characters(self, delta):
        for character in self._all_characters():
            character.tick(delta)

    def _close_action_menu(self):
        self.selected_character = None
        self.mode = GameScene.SELECT_MODE

    def _open_action_menu(self):
        if not self.selected_character:
            selected_x, selected_y = self.map.get_coordinates(*self.selected)
            for character in self.players[self.current_turn]:
                if (character.x, character.y) == (selected_x, selected_y):
                    self.selected_character = character
        if self.selected_character:
            self.movement_hilight = []
            self.attack_hilight = []
            self.camera.stop()
            self.cursor_pos = 0
            self.cursor.x = 10 + self.camera.offset_x
            self.cursor.y = 150 + self.camera.offset_y
            self.mode = GameScene.ACTION_MODE
            self.selected = self.map.get_row_column(self.selected_character.x, self.selected_character.y)

    def game_menu(self):
        self.camera.stop()
        self.world.transition(InGameMenuScene, previous=self)


class VictoryScene(Scene):

    def __init__(self, world, winner):
        super().__init__(world)
        self.winner = winner
        self.text_batch = Batch()
        self.cursor = Label(">", font_name='Times New Roman', font_size=36,
                            x=280 + self.camera.offset_x,
                            y=200 + self.camera.offset_y,
                            batch=self.text_batch)
        self.cursor_pos = 0

        self.menu_items = {
            "Main Menu" : self._main_menu
        }
        self._generate_text()

        self.key_handlers = {
            (key.UP, 0)     : lambda: self._move_cursor(1),
            (key.DOWN, 0)   : lambda: self._move_cursor(-1),
            (key.ENTER, 0)  : self._menu_action
        }

    def on_draw(self):
        self.window.clear()
        # Display the previous scene, then tint it
        self.text_batch.draw()

    def on_key_press(self, button, modifiers):
        pressed = (button, modifiers)
        handler = self.key_handlers.get(pressed, lambda: None)
        handler()

    def _draw_overlay(self):
        pattern = SolidColorImagePattern((0, 0, 100, 200))
        overlay_image = pattern.create_image(1000, 1000)
        overlay_image.anchor_x = int(overlay_image.width / 2)
        overlay_image.anchor_y = int(overlay_image.height / 2)
        overlay = Sprite(overlay_image, self.camera.x, self.camera.y)
        overlay.draw()

    def _generate_text(self):
        real_cord = lambda x,y: (x + self.camera.offset_x,
                                 y + self.camera.offset_y)
        menu_texts = reversed(list(self.menu_items.keys()))
        for i, text in enumerate(menu_texts):
            text_x, text_y = real_cord(300, 200 - 40 * i)
            Label(text, font_name='Times New Roman', font_size=36,
                    x=text_x, y=text_y, batch=self.text_batch)

        hint_x, hint_y = real_cord(400, 30)
        Label("Use Up and Down Arrows to navigate",
                font_name='Times New Roman', font_size=18,
                x=hint_x, y=hint_y, batch=self.text_batch)
        Label("Use Enter to choose",
                font_name='Times New Roman', font_size=18,
                x=hint_x, y=hint_y - 20, batch=self.text_batch)
        Label("Player %s Won!" % self.winner,
                font_name='Times New Roman', font_size=48,
                x=hint_x - 150, y=hint_y + 370, batch=self.text_batch)

    def _menu_action(self):
        actions = list(reversed(list(self.menu_items.values())))
        actions[self.cursor_pos]()

    def _move_cursor(self, direction):
        self.cursor_pos = (self.cursor_pos - direction) % len(self.menu_items)
        self.cursor.y = 500 + self.camera.offset_y - 40 * self.cursor_pos

    def _main_menu(self):
        self.world.transition(MainMenuScene)

class InGameMenuScene(Scene):

    def __init__(self, world, previous):
        super().__init__(world)
        self.text_batch = Batch()
        self.old_scene = previous
        self.cursor = Label(">", font_name='Times New Roman', font_size=36,
                            x=360 + self.camera.offset_x,
                            y=500 + self.camera.offset_y,
                            batch=self.text_batch)
        self.cursor_pos = 0

        self.menu_items = {
            "Resume"            : self._resume_game,
            "Help"              : self._launch_help,
            "Quit Current Game" : self._quit_game
        }
        self._generate_text()

        self.key_handlers = {
            (key.ESCAPE, 0) : self._resume_game,
            (key.UP, 0)     : lambda: self._move_cursor(1),
            (key.DOWN, 0)   : lambda: self._move_cursor(-1),
            (key.ENTER, 0)  : self._menu_action
        }

    def on_draw(self):
        self.window.clear()
        # Display the previous scene, then tint it
        self.old_scene.on_draw()
        self._draw_overlay()
        self.text_batch.draw()

    def on_key_press(self, button, modifiers):
        pressed = (button, modifiers)
        handler = self.key_handlers.get(pressed, lambda: None)
        handler()

    def _draw_overlay(self):
        pattern = SolidColorImagePattern((0, 0, 0, 200))
        overlay_image = pattern.create_image(1000, 1000)
        overlay_image.anchor_x = int(overlay_image.width / 2)
        overlay_image.anchor_y = int(overlay_image.height / 2)
        overlay = Sprite(overlay_image, self.camera.x, self.camera.y)
        overlay.draw()

    def _generate_text(self):
        real_cord = lambda x,y: (x + self.camera.offset_x,
                                 y + self.camera.offset_y)
        pause_x, pause_y = real_cord(10, 10)
        Label('Paused', font_name='Times New Roman', font_size=56,
                x=pause_x, y=pause_y, batch=self.text_batch)

        menu_texts = reversed(list(self.menu_items.keys()))
        for i, text in enumerate(menu_texts):
            text_x, text_y = real_cord(400, 500 - 40 * i)
            Label(text, font_name='Times New Roman', font_size=36,
                    x=text_x, y=text_y, batch=self.text_batch)

        hint_x, hint_y = real_cord(400, 30)
        Label("Use Up and Down Arrows to navigate",
                font_name='Times New Roman', font_size=18,
                x=hint_x, y=hint_y, batch=self.text_batch)
        Label("Use Enter to choose",
                font_name='Times New Roman', font_size=18,
                x=hint_x, y=hint_y - 20, batch=self.text_batch)

    def _menu_action(self):
        actions = list(reversed(list(self.menu_items.values())))
        actions[self.cursor_pos]()

    def _move_cursor(self, direction):
        self.cursor_pos = (self.cursor_pos - direction) % len(self.menu_items)
        self.cursor.y = 500 + self.camera.offset_y - 40 * self.cursor_pos

    def _resume_game(self):
        self.world.reload(self.old_scene)

    def _launch_help(self):
        pass

    def _quit_game(self):
        self.world.transition(MainMenuScene)

class AboutScene(Scene):

    def __init__(self, world, previous):
        super().__init__(world)
        self.old_scene = previous
        self.text_batch = Batch()
        self._generate_text()

        self.key_handlers = {
            (key.ESCAPE, 0) : self._resume
        }

    def on_draw(self):
        self.window.clear()
        # Display the previous scene, then tint it
        self.text_batch.draw()

    def on_key_press(self, button, modifiers):
        pressed = (button, modifiers)
        handler = self.key_handlers.get(pressed, lambda: None)
        handler()

    def _resume(self):
        self.world.reload(self.old_scene)

    def _generate_text(self):
        real_cord = lambda x,y: (x + self.camera.offset_x,
                                 y + self.camera.offset_y)
        author_x, author_y = real_cord(200, 500)
        Label("Written by John Mendelewski",
                font_name='Times New Roman', font_size=36,
                x=author_x, y=author_y - 20, batch=self.text_batch)

        hint_x, hint_y = real_cord(400, 30)
        Label("Use Escape to return to the menu",
                font_name='Times New Roman', font_size=18,
                x=hint_x, y=hint_y - 20, batch=self.text_batch)
