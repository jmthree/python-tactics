import random

import pyglet
from pyglet import resource, clock
from pyglet.sprite import Sprite
from pyglet.image import SolidColorImagePattern
from pyglet.graphics import Batch
from pyglet.window import key
from pyglet.text import Label

from util import load_sprite_asset, load_sprite_animation,\
                 faces_from_images, find_path
from sprite import PixelAwareSprite, IsometricSprite, MovingSprite
from map import Map

class World(object):

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

class Scene(object):

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

    def load(self, window):
        """ For each window event, if this Scene has a handler, attach that
            handler to the window
        """
        print "Loaded Scene %s" % self
        # Loads our callbacks
        for event in Scene.WINDOW_EVENTS:
            if hasattr(self, event):
                window.__setattr__(event, self.__getattribute__(event))

        # Call enter to set up the scene if needed
        if hasattr(self, "enter"):
            self.enter()

    def unload(self, window):
        # Cleans out any old callbacks
        for event in Scene.WINDOW_EVENTS:
            window.__setattr__(event, lambda *args: False)

        # Call exit to do whatever if needed
        if hasattr(self, "exit"):
            self.exit()
        print "Unloaded scene %s" % self

    def __del__(self):
        print "Deleting %s" % self


class MainMenuScene(Scene):

    def __init__(self, world):
        super(MainMenuScene, self).__init__(world)
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
        key = (button, modifiers)
        handler = self.key_handlers.get(key, lambda: None)
        handler()

    def _generate_text(self):
        real_cord = lambda x,y: (x + self.camera.offset_x,
                                 y + self.camera.offset_y)
        title_x, title_y = real_cord(10, 520)
        Label('FF:Tactics.py', font_name='Times New Roman', font_size=56,
                x=title_x, y=title_y, batch=self.text_batch)

        menu_texts = self.menu_items.keys()
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
        actions = self.menu_items.values()
        actions[self.cursor_pos]()

    def _move_cursor(self, direction):
        self.cursor_pos = (self.cursor_pos - direction) % len(self.menu_items)
        self.cursor.y = 300 + self.camera.offset_y - 40 * self.cursor_pos


class GameScene(Scene):

    # Game map constants
    MAP_START_X, MAP_START_Y = 400, 570
    GRID_WIDTH, GRID_HEIGHT = 100, 50
    MAP_WIDTH = MAP_HEIGHT = 10

    def __init__(self, world):
        super(GameScene, self).__init__(world)

        self.map_batch  = Batch()
        self.map        = self._generate_map()
        self.characters = self._load_characters()
        self.selected   = None

        self.key_handlers = {
            (key.ESCAPE, 0) : self.game_menu,
            (key.LEFT, 0)   : lambda: self.camera.pan_left(self.camera.scale),
            (key.RIGHT, 0)  : lambda: self.camera.pan_right(self.camera.scale),
            (key.UP, 0)     : lambda: self.camera.pan_up(self.camera.scale),
            (key.DOWN, 0)   : lambda: self.camera.pan_down(self.camera.scale)
        }

    def enter(self):
        blue = 0.6, 0.6, 1, 0.8
        pyglet.gl.glClearColor(*blue)
        clock.schedule(self._update_characters)

    def exit(self):
        clock.unschedule(self._update_characters)

    def on_draw(self):
        self.window.clear()
        self.map_batch.draw()
        for character in sorted(self.characters, lambda c,d: int(d.y - c.y)):
            character.draw()
        self.camera.focus(self.window.width, self.window.height)

    def on_mouse_press(self, x, y, button, modifiers):
        real_x, real_y = int(self.camera.offset_x + x),\
                         int(self.camera.offset_y + y)
        inside_map = self.map.find_sprite(x, y)
        inside_chars = [c for c in self.characters if c.contains(real_x, real_y)]
        taken  = [self.map.get_row_column(c.x, c.y) for c in self.characters]

        # Reset everything
        if self.selected: self.selected.color = 255, 255, 255
        for msprite in self.map.sprites:
            msprite.color = 255, 255, 255

        if inside_chars or inside_map:
            if inside_chars:
                selected = inside_chars[0]
            else:
                selected = inside_map
            last, self.selected = self.selected, selected
            self.selected.color = 100, 100, 100
            rx = self.selected.x + self.camera.offset_x
            ry = self.selected.y + self.camera.offset_y
            column, row = self.map.get_row_column(selected.x, selected.y)
            if hasattr(self.selected, "is_player"):
                in_range = self._points_in_range(column, row, 4)
                for column, row in in_range:
                    if (column, row) not in taken:
                        self.map.get_sprite(column, row).color = 100, 100, 255
            elif hasattr(last, "is_player"):
                last_column, last_row = self.map.get_row_column(last.x, last.y)
                last_pair = last_column, last_row
                new_indexes = self.map.get_row_column(selected.x, selected.y)
                new_pair  = int(selected.x), int(selected.y)
                in_range = self._points_in_range(last_column, last_row, 4)
                if new_indexes in in_range and new_pair not in taken:
                    self._schedule_movement(last, new_pair)
        else:
            self.selected = None

    def on_key_press(self, button, modifiers):
        key = (button, modifiers)
        handler = self.key_handlers.get(key, lambda: None)
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

        map = Map(columns, rows)
        for i, column in enumerate(map_points):
            for j, (x, y) in enumerate(column):
                image = load_sprite_asset("grass")
                image.anchor_x = image.width / 2
                image.anchor_y = image.height / 2
                sprite = PixelAwareSprite(image, x, y,
                            batch=self.map_batch, centery=True)
                sprite.scale = 1
                sprite.zindex = 0
                map.add_sprite(i, j, sprite)
        return map

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

        return [knight]

    def _points_in_range(self, column, row, length):
        if not 0 <= column < self.MAP_HEIGHT:
            return []
        if length == 0:
            return [(column, row)]
        else:
            return self._points_in_range(column - 1, row, length - 1) +\
                   [(column, min(max(0, row - length + i), self.MAP_WIDTH - 1))
                        for i in range(2 * length + 1)] + \
                   self._points_in_range(column + 1, row, length - 1)

    def _schedule_movement(self, sprite, pos):
        end_x, end_y = pos
        path = find_path(self.map.coordinates, sprite.x, sprite.y, end_x, end_y)
        for x, y in path:
            sprite.move_to(self.world.camera.offset_x + x,
                           self.world.camera.offset_y + y,
                           0.3)

    def _update_characters(self, dt):
        for character in self.characters:
            character.update(dt)

    def game_menu(self):
        self.world.transition(InGameMenuScene, previous=self)


class InGameMenuScene(Scene):

    def __init__(self, world, previous):
        super(InGameMenuScene, self).__init__(world)
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
        key = (button, modifiers)
        handler = self.key_handlers.get(key, lambda: None)
        handler()

    def _draw_overlay(self):
        pattern = SolidColorImagePattern((0, 0, 0, 200))
        overlay_image = pattern.create_image(1000, 1000)
        overlay_image.anchor_x = overlay_image.width / 2
        overlay_image.anchor_y = overlay_image.height / 2
        overlay = Sprite(overlay_image, self.camera.x, self.camera.y)
        overlay.draw()

    def _generate_text(self):
        real_cord = lambda x,y: (x + self.camera.offset_x,
                                 y + self.camera.offset_y)
        pause_x, pause_y = real_cord(10, 10)
        Label('Paused', font_name='Times New Roman', font_size=56,
                x=pause_x, y=pause_y, batch=self.text_batch)

        menu_texts = reversed(self.menu_items.keys())
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
        actions = list(reversed(self.menu_items.values()))
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
        super(AboutScene, self).__init__(world)
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
        key = (button, modifiers)
        handler = self.key_handlers.get(key, lambda: None)
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
