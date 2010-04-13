from pyglet import resource

TOP, MIDDLE, BOTTOM = LEFT, CENTER, RIGHT = 0, 0.5, 1

class image(object):

    def __init__(self, path, anchor_x=LEFT, anchor_y=BOTTOM, batch=None):
        self.image = resource.image(path)
        self.image.anchor_x = self.offset_x = anchor_x * self.image.width
        self.image.anchor_y = self.offset_y = anchor_y * self.image.height

