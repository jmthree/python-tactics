"""
Camera tracks a position, orientation and zoom level, and applies openGL
transforms so that subsequent renders are drawn at the correct place, size
and orientation on screen

Based on code from: http://tartley.com/files/stretching_pyglets_wings/
"""
from __future__ import division
from math import sin, cos, pi

from pyglet.gl import (
    glLoadIdentity, glMatrixMode, gluLookAt, gluOrtho2D,
    GL_MODELVIEW, GL_PROJECTION,
)

NORMAL, PEPPY, FAST = 1, 2, 3
LEFT, RIGHT, UP, DOWN = -pi/2, pi/2, 0, pi

class Camera(object):
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

    def update(self, delta_t):
        " Changes position of camera based on change in time "
        new_x     = self.target_x - self.x
        new_y     = self.target_y - self.y
        new_scale = self.target_scale - self.scale
        self.x     += new_x * delta_t * self.speed
        self.y     += new_y * delta_t * self.speed
        self.scale += new_scale * delta_t * self.speed

    def focus(self, width, height):
        "Set projection and model view matrices ready for rendering"
        # Set projection matrix suitable for 2D rendering"
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = width / height
        gluOrtho2D(
            -self.scale * aspect,
            +self.scale * aspect,
            -self.scale,
            +self.scale)

        # Set model view matrix to move, scale & rotate to camera position"
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(
            self.x, self.y, 1.0,
            self.x, self.y, -1.0,
            0.0,    1.0,    0.0)

    def hud_mode(self, width, height):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, width, 0, height)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def look_at(self, x, y):
        " Sets up camera to focus on target x and y "
        self.target_x, self.target_y = x, y
