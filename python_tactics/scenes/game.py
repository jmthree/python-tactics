import random
from functools import reduce

import pyglet
from pyglet import clock
from pyglet.graphics import Batch
from pyglet.image import SolidColorImagePattern
from pyglet.sprite import Sprite
from pyglet.text import Label
from pyglet.window import key
from python_tactics.characters import Beefy, Ranged
from python_tactics.map import RectangularMap
from python_tactics.scenes import Scene


#pylint: disable=too-many-instance-attributes
class GameScene(Scene):

    # Team constants
    TEAM_SIZE = 2
    TEAM_COUNT = 2

    # Game map constants
    MAP_START_X, MAP_START_Y = 400, 570
    MAP_WIDTH = MAP_DEPTH = 10

    # The modes the game scene can be in
    NOTIFY, SELECT_MODE, ACTION_MODE, MOVE_TARGET_MODE, ATTACK_TARGET_MODE = list(range(5))

    def __init__(self, world):
        super().__init__(world)
        self.map        = RectangularMap(GameScene.MAP_WIDTH, GameScene.MAP_DEPTH, GameScene.MAP_START_X, GameScene.MAP_START_Y)
        self.players    = self._initialize_teams()
        self.current_turn = 1
        self.selected   = 0, 0
        self.selected_character = None
        self.mode = GameScene.SELECT_MODE
        self.turn_notice = None

        # Items for action menu
        self.text_batch = Batch()
        self.cursor_pos = 0
        self.cursor = Label(">", font_name='Times New Roman', font_size=36,
                            x=self.camera.to_x_from_left(10),
                            y=self.camera.to_y_from_bottom(140),
                            batch=self.text_batch)
        self.action_menu_texts = []

        self.action_menu_items = {
                "Move"              : self._initiate_movement,
                "Attack"            : self._initiate_attack,
                "Cancel"            : self._close_action_menu,
        }

        self.key_handlers = {
            GameScene.SELECT_MODE : {
                (key.ESCAPE, 0) : self.game_menu,
                (key.LEFT, 0)   : lambda: self.move_hilight(-1, 0),
                (key.RIGHT, 0)  : lambda: self.move_hilight(1, 0),
                (key.UP, 0)     : lambda: self.move_hilight(0, -1),
                (key.DOWN, 0)   : lambda: self.move_hilight(0, 1),
                (key.TAB, 0)    : self.highlight_next_character_on_current_team,
                (key.ENTER, 0)  : self._open_action_menu,
                },
            GameScene.ACTION_MODE : {
                (key.ESCAPE, 0)  : self._close_action_menu,
                (key.UP, 0)     : lambda: self._move_cursor(1),
                (key.DOWN, 0)   : lambda: self._move_cursor(-1),
                (key.ENTER, 0)  : self._menu_action
                },
            GameScene.MOVE_TARGET_MODE : {
                (key.LEFT, 0)   : lambda: self.move_hilight(-1, 0),
                (key.RIGHT, 0)  : lambda: self.move_hilight(1, 0),
                (key.UP, 0)     : lambda: self.move_hilight(0, -1),
                (key.DOWN, 0)   : lambda: self.move_hilight(0, 1),
                (key.ENTER, 0)  : self._execute_move,
                (key.ESCAPE, 0) : self._open_action_menu,
                },
            GameScene.ATTACK_TARGET_MODE : {
                (key.LEFT, 0)   : lambda: self.move_hilight(-1, 0),
                (key.RIGHT, 0)  : lambda: self.move_hilight(1, 0),
                (key.UP, 0)     : lambda: self.move_hilight(0, -1),
                (key.DOWN, 0)   : lambda: self.move_hilight(0, 1),
                (key.ENTER, 0)  : self._execute_attack,
                (key.ESCAPE, 0) : self._open_action_menu,
                },
        }
        self.change_player()
        self.map.highlight(*self.selected)
        self.camera.focus(self.window.width, self.window.height)

    def _all_characters(self):
        return reduce(lambda chars, player: player + chars, self.players)

    def _other_characters(self):
        if self.current_turn:
            return self.players[0]
        return self.players[1]

    def change_player(self):
        old_turn = self.current_turn
        self.current_turn = (self.current_turn + 1) % GameScene.TEAM_COUNT
        if not self.players[self.current_turn]:
            self.world.transition(VictoryScene, winner=old_turn + 1)
        else:
            self.display_turn_notice()
            self.highlight_next_character_on_current_team()

    def display_turn_notice(self):
        if self.turn_notice is not None:
            self.turn_notice.delete()
        self.turn_notice = Label(
                "Player %s's Turn" % (self.current_turn + 1),
                font_name='Times New Roman', font_size=36,
                x=self.camera.to_x_from_left(10),
                y=self.camera.to_y_from_bottom(10))
        self.turn_notice.color = 255 - (100 * self.current_turn), 255 - (100 * ((self.current_turn + 1) % 2)), 255, 255

    def highlight_next_character_on_current_team(self):
        current_team_positions = [self.map.get_row_column(c.x, c.y) for c in self.players[self.current_turn]]
        if self.selected in current_team_positions:
            if len(current_team_positions) == 1:
                return
            currently_highlighted = current_team_positions.index(self.selected)
            highlighted_position = current_team_positions[(currently_highlighted + 1) % len(current_team_positions)]
        else:
            highlighted_position = current_team_positions[0]
        self.selected = highlighted_position
        self.map.highlight(*self.selected)
        newx, newy = self.map.get_xy(*self.selected)
        self.camera.look_at((newx + self.camera.x) / 2, (newy + self.camera.y) / 2)

    def _initialize_teams(self):
        def create_team(team_number, positions):
            team = []
            for character_count, (i, j, direction) in enumerate(positions):
                cls = Beefy if character_count % 2 == 0 else Ranged
                char_x, char_y = self.map.get_xy(i, j)
                character = cls(char_x, char_y, direction)
                character.zindex = 10
                character.color = 255 - (200 * team_number), 110, 255 - (200 * ((team_number + 1) % GameScene.TEAM_COUNT))
                team.append(character)
            return team
        return [create_team(team_number, positions)
                for team_number, positions
                in enumerate(self.map.get_starting_positions(GameScene.TEAM_SIZE)[0:GameScene.TEAM_COUNT])]

    def move_hilight(self, delta_i, delta_j):
        current_i, current_j = self.selected
        highlight_at = self.map.highlight(current_i + delta_i, current_j + delta_j)
        if highlight_at:
            self.selected = highlight_at
        newx, newy = self.map.get_xy(*self.selected)
        self.camera.look_at((newx + self.camera.x) / 2, (newy + self.camera.y) / 2)

    def enter(self):
        blue = 0.6, 0.6, 1, 0.8
        pyglet.gl.glClearColor(*blue)
        clock.schedule(self._update_characters)

    def exit(self):
        clock.unschedule(self._update_characters)

    def on_draw(self):
        self.window.clear()
        self.map.draw()
        if hasattr(self, 'turn_notice'):
            self.turn_notice.x = self.camera.to_x_from_left(10)
            self.turn_notice.y = self.camera.to_y_from_bottom(10)
            self.turn_notice.draw()
        characters_in_y_order = sorted(self._all_characters(), key=lambda c: -int(c.y))
        for character in characters_in_y_order:
#            if (selected_x, selected_y) == (character.x, character.y):
#                character.color = 100, 100, 100
#            else:
#                character.color = 255, 255, 255
            character.draw_character()
#            #character.image.blit(character.x, character.y)
        for character in characters_in_y_order:
            character.draw_ui()
        if self.mode == GameScene.ACTION_MODE:
            self._draw_action_menu()
            self.text_batch.draw()
        self.camera.focus(self.window.width, self.window.height)
        self.camera.draw()

    def _menu_action(self):
        actions = list(reversed(list(self.action_menu_items.values())))
        actions[self.cursor_pos]()

    def _move_cursor(self, direction):
        self.cursor_pos = (self.cursor_pos - direction) % len(self.action_menu_items)
        self.cursor.y = self.camera.to_y_from_bottom(150 - 50 * self.cursor_pos)

    def _draw_action_menu(self):
        pattern = SolidColorImagePattern((0, 0, 150, 200))
        overlay_image = pattern.create_image(1000, 200)
        overlay_image.anchor_x = int(overlay_image.width / 2)
        overlay_image.anchor_y = overlay_image.height + 100
        overlay = Sprite(overlay_image, self.camera.x, self.camera.y)
        overlay.draw()

        self._generate_text()

    def _generate_text(self):
        menu_texts = reversed(list(self.action_menu_items.keys()))
        for label in self.action_menu_texts:
            label.delete()

        for i, text in enumerate(menu_texts):
            text_x, text_y = self.camera.to_xy_from_bottom_left(40, 150 - 50 * i)
            self.action_menu_texts.append(
                    Label(text, font_name='Times New Roman', font_size=36,
                        x=text_x, y=text_y, batch=self.text_batch))


#    def on_mouse_press(self, x, y, button, modifiers):
#        real_x, real_y = int(self.camera.offset_x + x),\
#                         int(self.camera.offset_y + y)
#        inside_map = self.map.find_sprite(x, y)
#        inside_chars = [c for c in self.characters if c.contains(real_x, real_y)]
#        taken  = [self.map.get_row_column(c.x, c.y) for c in self.characters]
#
#        # Reset everything
#        if self.selected: self.selected.color = 255, 255, 255
#        for msprite in self.map.sprites:
#            msprite.color = 255, 255, 255
#
#        if inside_chars or inside_map:
#            if inside_chars:
#                selected = inside_chars[0]
#            else:
#                selected = inside_map
#            last, self.selected = self.selected, selected
#            self.selected.color = 100, 100, 100
#            rx = self.selected.x + self.camera.offset_x
#            ry = self.selected.y + self.camera.offset_y
#            column, row = self.map.get_row_column(selected.x, selected.y)
#            if hasattr(self.selected, "is_player"):
#                in_range = self._points_in_range(column, row, 4)
#                for column, row in in_range:
#                    if (column, row) not in taken:
#                        self.map.get_sprite(column, row).color = 100, 100, 255
#            elif hasattr(last, "is_player"):
#                last_column, last_row = self.map.get_row_column(last.x, last.y)
#                last_pair = last_column, last_row
#                new_indexes = self.map.get_row_column(selected.x, selected.y)
#                new_pair  = int(selected.x), int(selected.y)
#                in_range = self._points_in_range(last_column, last_row, 4)
#                if new_indexes in in_range and new_pair not in taken:
#                    self._schedule_movement(last, new_pair)
#        else:
#            self.selected = None

    def _initiate_movement(self):
        self.mode = GameScene.MOVE_TARGET_MODE
        character = self.selected_character
        taken  = [self.map.get_row_column(c.x, c.y) for c in self._all_characters()]
        column, row = self.map.get_row_column(character.x, character.y)
        self.map.radius_highlight(column, row, character.speed, taken)

    def _execute_move(self):
        if self.map.is_highlighted(*self.selected):
            last = self.map.get_xy(*self.selected)
            self._schedule_movement(self.selected_character, last)
            self.map.reset_radius_highlight()
            self.change_player()
            self._close_action_menu()

    def _initiate_attack(self):
        self.mode = GameScene.ATTACK_TARGET_MODE
        character = self.selected_character
        column, row = self.map.get_row_column(character.x, character.y)
        self.map.radius_highlight(column, row, character.range, [self.selected])

    def _execute_attack(self):
        attacker = self.selected_character
        attacked = None
        if self.map.is_highlighted(*self.selected):
            for character in self._other_characters():
                char_loc = self.map.get_row_column(character.x, character.y)
                if  char_loc == self.selected:
                    attacked = character
        if attacked:
            attack = random.randrange(attacker.strength)
            defense = random.randrange(attacked.defense)
            hit = max(1, defense - attack)
            print("Hit for ", hit)
            attacker.attack_sound.play()
            remaining_health = attacked.hit(hit)
            if remaining_health == 0:
                self._other_characters().remove(attacked)
                attacked.delete()
            self.map.reset_radius_highlight()
            self.change_player()
            self._close_action_menu()

    def on_key_press(self, button, modifiers):
        pressed = (button, modifiers)
        handler = self.key_handlers[self.mode].get(pressed, lambda: None)
        handler()

    def _schedule_movement(self, sprite, pos):
        end_x, end_y = pos
        path = self.map.find_path(sprite.x, sprite.y, end_x, end_y)
        for x, y in path:
            sprite.move_to(x, y, 0.3)

    def _update_characters(self, delta):
        for character in self._all_characters():
            character.tick(delta)

    def _close_action_menu(self):
        self.selected_character = None
        self.mode = GameScene.SELECT_MODE

    def _open_action_menu(self):
        if not self.selected_character:
            selected_x, selected_y = self.map.get_xy(*self.selected)
            for character in self.players[self.current_turn]:
                if (character.x, character.y) == (selected_x, selected_y):
                    self.selected_character = character
        if self.selected_character:
            self.map.reset_radius_highlight()
            self.camera.stop()
            self.cursor_pos = 0
            self.cursor.x = self.camera.to_x_from_left(10)
            self.cursor.y = self.camera.to_y_from_bottom(150)
            self.mode = GameScene.ACTION_MODE
            self.selected = self.map.get_row_column(self.selected_character.x, self.selected_character.y)
            self.map.highlight(*self.selected)

    def game_menu(self):
        self.camera.stop()
        self.world.transition(InGameMenuScene, previous=self)


class VictoryScene(Scene):

    def __init__(self, world, winner):
        super().__init__(world)
        self.winner = winner
        self.text_batch = Batch()
        self.cursor = Label(">", font_name='Times New Roman', font_size=36,
                            x=280 + self.camera.offset_x,
                            y=200 + self.camera.offset_y,
                            batch=self.text_batch)
        self.cursor_pos = 0

        self.menu_items = {
            "Main Menu" : self._main_menu
        }
        self._generate_text()

        self.key_handlers = {
            (key.UP, 0)     : lambda: self._move_cursor(1),
            (key.DOWN, 0)   : lambda: self._move_cursor(-1),
            (key.ENTER, 0)  : self._menu_action
        }

    def on_draw(self):
        self.window.clear()
        # Display the previous scene, then tint it
        self.text_batch.draw()

    def on_key_press(self, button, modifiers):
        pressed = (button, modifiers)
        handler = self.key_handlers.get(pressed, lambda: None)
        handler()

    def _draw_overlay(self):
        pattern = SolidColorImagePattern((0, 0, 100, 200))
        overlay_image = pattern.create_image(1000, 1000)
        overlay_image.anchor_x = int(overlay_image.width / 2)
        overlay_image.anchor_y = int(overlay_image.height / 2)
        overlay = Sprite(overlay_image, self.camera.x, self.camera.y)
        overlay.draw()

    def _generate_text(self):
        menu_texts = reversed(list(self.menu_items.keys()))
        for i, text in enumerate(menu_texts):
            text_x, text_y = self.camera.to_xy_from_bottom_left(300, 200 - 40 * i)
            Label(text, font_name='Times New Roman', font_size=36,
                    x=text_x, y=text_y, batch=self.text_batch)

        hint_x, hint_y = self.camera.to_xy_from_bottom_left(400, 30)
        Label("Use Up and Down Arrows to navigate",
                font_name='Times New Roman', font_size=18,
                x=hint_x, y=hint_y, batch=self.text_batch)
        Label("Use Enter to choose",
                font_name='Times New Roman', font_size=18,
                x=hint_x, y=hint_y - 20, batch=self.text_batch)
        Label("Player %s Won!" % self.winner,
                font_name='Times New Roman', font_size=48,
                x=hint_x - 150, y=hint_y + 370, batch=self.text_batch)

    def _menu_action(self):
        actions = list(reversed(list(self.menu_items.values())))
        actions[self.cursor_pos]()

    def _move_cursor(self, direction):
        self.cursor_pos = (self.cursor_pos - direction) % len(self.menu_items)
        self.cursor.y = 500 + self.camera.offset_y - 40 * self.cursor_pos

    def _main_menu(self):
        #pylint: disable=import-outside-toplevel
        from python_tactics.scenes.preamble import MainMenuScene
        self.world.transition(MainMenuScene)


class InGameMenuScene(Scene):

    def __init__(self, world, previous):
        super().__init__(world)
        self.text_batch = Batch()
        self.old_scene = previous
        self.cursor = Label(">", font_name='Times New Roman', font_size=36,
                            x=self.camera.to_x_from_left(360),
                            y=self.camera.to_y_from_bottom(500),
                            batch=self.text_batch)
        self.cursor_pos = 0

        self.menu_items = {
            "Resume"            : self._resume_game,
            "Help"              : self._launch_help,
            "Quit Current Game" : self._quit_game
        }
        self._generate_text()

        self.key_handlers = {
            (key.ESCAPE, 0) : self._resume_game,
            (key.UP, 0)     : lambda: self._move_cursor(1),
            (key.DOWN, 0)   : lambda: self._move_cursor(-1),
            (key.ENTER, 0)  : self._menu_action
        }

    def on_draw(self):
        self.window.clear()
        # Display the previous scene, then tint it
        self.old_scene.on_draw()
        self._draw_overlay()
        self.text_batch.draw()

    def on_key_press(self, button, modifiers):
        pressed = (button, modifiers)
        handler = self.key_handlers.get(pressed, lambda: None)
        handler()

    def _draw_overlay(self):
        pattern = SolidColorImagePattern((0, 0, 0, 200))
        overlay_image = pattern.create_image(self.world.window.width + 200, self.world.window.height + 200)
        overlay_image.anchor_x = int(overlay_image.width / 2)
        overlay_image.anchor_y = int(overlay_image.height / 2)
        overlay = Sprite(overlay_image, self.camera.x, self.camera.y)
        overlay.draw()

    def _generate_text(self):
        pause_x, pause_y = self.camera.to_xy_from_bottom_left(10, 10)
        Label('Paused', font_name='Times New Roman', font_size=56,
                x=pause_x, y=pause_y, batch=self.text_batch)

        menu_texts = reversed(list(self.menu_items.keys()))
        for i, text in enumerate(menu_texts):
            text_x, text_y = self.camera.to_xy_from_bottom_left(400, 500 - 40 * i)
            Label(text, font_name='Times New Roman', font_size=36,
                    x=text_x, y=text_y, batch=self.text_batch)

        hint_x, hint_y = self.camera.to_xy_from_bottom_left(400, 30)
        Label("Use Up and Down Arrows to navigate",
                font_name='Times New Roman', font_size=18,
                x=hint_x, y=hint_y, batch=self.text_batch)
        Label("Use Enter to choose",
                font_name='Times New Roman', font_size=18,
                x=hint_x, y=hint_y - 20, batch=self.text_batch)

    def _menu_action(self):
        actions = list(reversed(list(self.menu_items.values())))
        actions[self.cursor_pos]()

    def _move_cursor(self, direction):
        self.cursor_pos = (self.cursor_pos - direction) % len(self.menu_items)
        self.cursor.y = self.camera.to_y_from_bottom(500 - 40 * self.cursor_pos)

    def _resume_game(self):
        self.world.reload(self.old_scene)

    def _launch_help(self):
        pass

    def _quit_game(self):
        #pylint: disable=import-outside-toplevel
        from python_tactics.scenes.preamble import MainMenuScene
        self.world.transition(MainMenuScene)
