
DIRECTIONS = "north", "east", "south", "west"

knight = MovingCharacter(
    dict(["look_%s" % dir, "/assets/knight/%s.png" % dir for dir in DIRECTIONS])
    faces=["/assets/knight/%s.png" for direction in DIRECTIONS],
    walking_animations=
