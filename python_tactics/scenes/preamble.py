import pyglet
from pyglet.graphics import Batch
from pyglet.sprite import Sprite
from pyglet.text import Label
from pyglet.window import key
from python_tactics.scenes import Scene
from python_tactics.scenes.game import GameScene
from python_tactics.util import load_sprite_asset


class MainMenuScene(Scene):

    def __init__(self, world):
        super().__init__(world)
        self.text_batch = Batch()
        self.cursor = Label(">", font_name='Times New Roman', font_size=36,
                            x=self.camera.to_x_from_left(200),
                            y=self.camera.to_y_from_bottom(300),
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
        title_x, title_y = self.camera.to_xy_from_bottom_left(10, 520)
        Label('FF:Tactics.py', font_name='Times New Roman', font_size=56,
                x=title_x, y=title_y, batch=self.text_batch)

        menu_texts = list(self.menu_items.keys())
        for i, text in enumerate(menu_texts):
            text_x, text_y = self.camera.to_xy_from_bottom_left(240, 300 - 40 * i)
            Label(text, font_name='Times New Roman', font_size=36,
                    x=text_x, y=text_y, batch=self.text_batch)

        hint_x, hint_y = self.camera.to_xy_from_bottom_left(400, 30)
        Label("Use Up and Down Arrows to navigate",
                font_name='Times New Roman', font_size=18,
                x=hint_x, y=hint_y, batch=self.text_batch)
        Label("Use Enter to choose",
                font_name='Times New Roman', font_size=18,
                x=hint_x, y=hint_y - 20, batch=self.text_batch)

    def _load_moogle(self):
        moogle_image = load_sprite_asset("moogle")
        moogle_image.anchor_x = int(moogle_image.width / 2)
        moogle_image.anchor_y = int(moogle_image.height / 2)
        moog_sprite = Sprite(moogle_image,
                        self.camera.to_x_from_left(40),
                        self.camera.to_y_from_bottom(40))
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
        self.cursor.y = self.camera.to_y_from_bottom(300 - 40 * self.cursor_pos)


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
        author_x, author_y = self.camera.to_xy_from_bottom_left(200, 500)
        Label("Written by John Mendelewski",
                font_name='Times New Roman', font_size=36,
                x=author_x, y=author_y - 20, batch=self.text_batch)

        hint_x, hint_y = self.camera.to_xy_from_bottom_left(400, 30)
        Label("Use Escape to return to the menu",
                font_name='Times New Roman', font_size=18,
                x=hint_x, y=hint_y - 20, batch=self.text_batch)
