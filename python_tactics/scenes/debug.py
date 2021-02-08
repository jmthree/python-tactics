import pyglet
from pyglet.image import ImageGrid
from pyglet.sprite import Sprite
from pyglet.text import Label
from pyglet.window import key
from python_tactics.scenes import Scene
from python_tactics.util import load_sprite_asset


class AtlasBrowsingScene(Scene):

    blocks = ImageGrid(load_sprite_asset("blocks"), 1, 101)
    unicorns = ImageGrid(load_sprite_asset("unicorn_atlas"), 12, 24)
    spaghettis = ImageGrid(load_sprite_asset("spaghetti_atlas"), 12, 24)

    def __init__(self, world):
        super().__init__(world)
        self.sheets = {"blocks": self.blocks, "unicorns": self.unicorns, "spagettis": self.spaghettis}
        self.sheet = None
        self.sheet_sprite = None
        self.sheet_index = 0
        self.text = Label("", font_name='Times New Roman', font_size=36, x=200, y=300)

    def enter(self):
        black = 0, 0, 0, 0
        pyglet.gl.glClearColor(*black)

    def on_draw(self):
        self.world.window.clear()
        if self.sheet_sprite:
            self.sheet_sprite.draw()
        self.text.draw()

    def on_key_press(self, button, _modifiers):
        if button in (key.UP, key.DOWN):
            self.change_sheet(1 if button == key.DOWN else -1)
        if button in (key.LEFT, key.RIGHT):
            self.cycle_sheet(-1 if button == key.LEFT else 1)

    def get_sheet(self):
        return list(self.sheets.values())[self.sheet]

    def change_sheet(self, direction):
        if self.sheet is None:
            self.sheet = 0
        else:
            self.sheet = (self.sheet + direction) % len(self.sheets)
        self.sheet_index = 0
        self.update_sprite_and_text()

    def cycle_sheet(self, direction):
        if self.sheet is None:
            return
        self.sheet_index = (self.sheet_index + direction) % len(self.get_sheet())
        self.update_sprite_and_text()

    def update_sprite_and_text(self):
        sheet_name = list(self.sheets.keys())[self.sheet]
        old_sprite = self.sheet_sprite
        self.sheet_sprite = Sprite(self.get_sheet()[self.sheet_index])
        if old_sprite:
            old_sprite.delete()
        self.text.text = f"{sheet_name}: {self.sheet_index}"
