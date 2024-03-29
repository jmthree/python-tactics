"""
Camera tracks a position, orientation and zoom level, and applies openGL
transforms so that subsequent renders are drawn at the correct place, size
and orientation on screen

Based on code from: https://www.tartley.com/posts/stretching-pyglets-wings/
"""

from math import sin, cos, pi

from pyglet.gl import (
    glLoadIdentity, glMatrixMode, gluLookAt, gluOrtho2D,
    GL_MODELVIEW, GL_PROJECTION,
)

NORMAL, PEPPY, FAST = 1, 2, 3
LEFT, RIGHT, UP, DOWN = -pi/2, pi/2, 0, pi
TARGET_THRESHOLD = 5

class Camera:
    """ Manipulates the OpenGL projection matrix to emulate a moving
        camera in the game.
    """

    def __init__(self, bounds, origin=(0, 0), scale=1, speed=NORMAL):
        """ bounds: (x, y, x', y') Movement boundaries for the camera
            origin: (x, y) Where the camera starts
            scale: float How far away from the ground is the camera?
            speed: NORMAL | PEPPY | FAST
        """
        self.min_x, self.min_y, self.max_x, self.max_y = bounds
        self.origin_x, self.origin_y = origin
        self.x, self.y = self.target_x, self.target_y = origin
        self.scale = self.target_scale = scale
        self.speed = speed

    @property
    def offset_x(self):
        " How far away from the origin the camera has gone "
        return self.x - self.origin_x

    @property
    def offset_y(self):
        " How far away from the origin the camera has gone "
        return self.y -self.origin_y

    def pan_left(self, length):
        " Move the camera left by length "
        self._pan(length, -pi/2)

    def pan_right(self, length):
        " Move the camera right by length "
        self._pan(length, pi/2)

    def pan_up(self, length):
        " Move the camera up by length "
        self._pan(length, 0)

    def pan_down(self, length):
        " Move the camera down by length "
        self._pan(length, pi)

    def _pan(self, length, direction):
        " Does all work for panning. Enforces boundaries "
        possible_x = self.target_x + length * sin(direction)
        possible_y = self.target_y + length * cos(direction)
        self.target_x = min(max(self.min_x, possible_x), self.max_x)
        self.target_y = min(max(self.min_y, possible_y), self.max_y)

    def tick(self, delta_t):
        " Changes position of camera based on change in time "
        self.x = self._tick_towards_target(self.target_x, self.x, delta_t)
        self.y = self._tick_towards_target(self.target_y, self.y, delta_t)
        self.scale = self._tick_towards_target(self.target_scale, self.scale, delta_t)

    def _tick_towards_target(self, target, current, delta_t):
        diff = target - current
        if -TARGET_THRESHOLD <= diff <= TARGET_THRESHOLD:
            return target
        return current + int(diff * delta_t * self.speed)

    def focus(self, width, height):
        "Set projection and model view matrices ready for rendering"
        # Set projection matrix suitable for 2D rendering"
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = width / height
        left, right, bottom, top = -self.scale * aspect, +self.scale * aspect, -self.scale, +self.scale
        gluOrtho2D(left, right, bottom, top)

        # Set model view matrix to move, scale & rotate to camera position"
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(
            self.x, self.y, 1.0,
            self.x, self.y, -1.0,
            0.0,    1.0,    0.0)

    #pylint: disable=no-self-use
    def hud_mode(self, width, height):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, width, 0, height)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def stop(self):
        self.target_x, self.target_y = self.x, self.y

    def look_at(self, x, y):
        " Sets up camera to focus on target x and y "
        self.target_x, self.target_y = int(x), int(y)

    def to_y_from_bottom(self, y):
        "Returns a y that is y pixels above the bottom the window"
        return self.y - 300 + y

    def to_x_from_left(self, x):
        "Returns a x that is x pixels right of left of the window"
        return self.x - 400 + x

    def to_xy_from_bottom_left(self, x, y):
        "Returns a tuple of x and y that are x pixels right of and y pixels above the bottom left of the window"
        return self.to_x_from_left(x), self.to_y_from_bottom(y)

    def draw(self):
        # Useful for visualizing where the camera currently is
        # Want to draw a bounding box next
        #Label("x", font_name="Times New Roman", font_size=12, x=self.x, y=self.y).draw()
        #Label("x", font_name="Times New Roman", color=(255, 0, 0, 255), font_size=12, x=self.target_x, y=self.target_y).draw()
        #Label("x", font_name="Times New Roman", color=(0, 0, 255, 255), font_size=12, x=self.origin_x, y=self.origin_y).draw()
        pass
