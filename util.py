"""
    Helper functions for loading files into pyglet for this project
"""
from math import atan2, pi

from pyglet import resource
from pyglet.image import Animation, AnimationFrame

def load_sprite_asset(name):
    " Loads png files from the assets folder, with anchor in middle "
    image = resource.image("assets/%s.png" % name)
    image.anchor_x = image.width / 2
    return image

def load_sprite_animation(name, action, frames=8, duration=0.1):
    " Creates an animation from files in the assets folder "
    images = [resource.image("assets/%s/%s%d.png" % (name, action, i))
                for i in range(1, frames + 1)]
    for image in images:
        image.anchor_x = image.width / 2
    frames = [AnimationFrame(i, duration) for i in images]
    return Animation(frames)

def faces_from_images(north=None, east=None, south=None, west=None):
    """ Creates the proper standing sprites for a Character given at
        least two of the stances
    """
    if not west and not south:
        raise Exception("Invalid sprite. Needs either east or south")
    if not east and not north:
        raise Exception("Invalid sprite. Needs either west or north")
    if not north:
        north = east.get_texture().get_transform(flip_x=True)
        north.requires_reverse = True
    if not east:
        east = north.get_texture().get_transform(flip_x=True)
        east.requires_reverse = True
    if not west:
        west = south.get_texture().get_transform(flip_x=True)
        west.requires_reverse = True
    if not south:
        south = west.get_texture().get_transform(flip_x=True)
        south.requires_reverse = True
    return north, east, south, west

def find_path(map_points, start_x, start_y, end_x, end_y):
    """ Given a list of lists with (x, y) values, and a start
        and end pairs, find the isometric path between start
        and end. That is, if x, y is in row r, you can only
        move to spots within row r. To move in another direction,
        you must move to an adjacent list of x, y values, keeping
        your same position.
    """
    def index_of(x, y):
        for column_num, column in enumerate(map_points):
            if (x, y) in column:
                return column_num, column.index((x, y))
    dy, dx = end_y - start_y, end_x - start_x
    if not dx and not dy:
        return []
    else:
        angle = atan2(dy, dx)
        col, row = index_of(start_x, start_y)
        if 0 <= angle <= pi/2:
            # "going east"
            next_col, next_row = col, row - 1
        elif pi/2 < angle <= pi:
            # "going north"
            next_col, next_row = col - 1, row
        elif -pi/2 <= angle <= 0:
            # "going south"
            next_col, next_row = col + 1, row
        else:
            # "going west"
            next_col, next_row = col, row + 1
        next_x, next_y = map_points[next_col][next_row]
        return [(next_x, next_y)] +\
               find_path(map_points, next_x, next_y, end_x, end_y)

