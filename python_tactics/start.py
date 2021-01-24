""" Runs ff:tactics.py
    Code has similar structure to examples of pyglets provided
    on the pyglets site
"""
import pyglet
from pyglet import clock
from pyglet.gl import (GL_BLEND, GL_ONE_MINUS_SRC_ALPHA, GL_SRC_ALPHA,
                       glBlendFunc, glEnable)
from pyglet.window import Window

from python_tactics.camera import PEPPY, Camera
from python_tactics.scenes import MainMenuScene, World

glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

def start():
    # Create the main window
    window = Window(800, 600, visible=False,
                    caption="FF:Tactics.py", style='dialog')
    # Create the default camera and have it always updating
    camera = Camera((-600, -300, 1400, 600), (400, 300), 300, speed=PEPPY)
    clock.schedule(camera.tick)

    # Load the first scene
    world = World(window, camera)
    world.transition(MainMenuScene)

    # centre the window on whichever screen it is currently on
    window.set_location(int(window.screen.width/2 - window.width/2),
                        int(window.screen.height/2 - window.height/2))
    # clear and flip the window
    # otherwise we see junk in the buffer before the first frame
    window.clear()
    window.flip()

    # make the window visible at last
    window.set_visible(True)

    # finally, run the application
    pyglet.app.run()
