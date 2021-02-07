import pyglet
from pyglet.sprite import Sprite
from pyglet.text import Label
from pyglet.window import key
from python_tactics.scenes import Scene
from python_tactics.util import load_sprite_asset


class AtlasBrowsingScene(Scene):

    def __init__(self, world):
        super().__init__(world)
        self.dude_frame = 0
        self.dude_sheet = self._load_dude_sheet()
        self.dude = self._load_dude()
        self.frame_text = self._load_frame_text()

    def enter(self):
        black = 0, 0, 0, 0
        pyglet.gl.glClearColor(*black)

    def on_draw(self):
        self.world.window.clear()
        self.dude.draw()


    def _load_dude_sheet(self):
        img = load_sprite_asset("unicorn_atlas")
        sprite_grid = pyglet.image.ImageGrid(img, 12, 24)
        return sprite_grid

    def _load_dude(self):
        return Sprite(self.dude_sheet[self.dude_frame])

    def _load_frame_text(self):
        return Label(f"{self.dude_frame}", font_name='Times New Roman', font_size=36, x=200, y=300)

    def on_key_press(self, button, _modifiers):
        if button in (key.LEFT, key.RIGHT):
            modifier = 1 if button == key.LEFT else -1
            self.dude_frame = (self.dude_frame - modifier) % 288
            self.dude = self._load_dude()
            self.frame_text = self._load_frame_text()
