Assignment #3
John Mendelewski

[Execution]
To execute the code, navigate to the directory with the code installed
and execute:
    python ./tactics.py

Use the arrow keys and enter to start a new game. From there, you can
click on the unit to see which possible squares he can move to. If you
click and drag, your cursor will change, and if you drop the unit in a
highlighted square, he will move to that spot

[Known Bugs / Incompleteness]
My project falls short of my functional spec I wrote up. I wanted to have
a full game, and I only have some pieces of it. In order to get it to
run on the linux machines, I chose a framework which is just a tad about
pure OpenGL. I got caught up in figuring things out, and never fleshed
out all my ideas for this project.
However, I do feel I meet the requirements. There are menus, image loading,
translations/rotations and manipulation of things on the screen.
I am going to continue to work on this so I have something worth showing
people, though I know any work after today will not count.

[Extra Features]
I was able to use OpenGL transformations to mimic a camera in my environment.
Alpha channels on images count towards the sprite's bounding box, i.e. Sprites
have actual outlines as shown on the screen, not some imaginary box surrounding
it.
