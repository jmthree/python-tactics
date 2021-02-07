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
