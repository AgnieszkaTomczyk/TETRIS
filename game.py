import sys
import os
import time
import json
import random
import copy

import pygame

COLOR_WHITE = (255, 255, 255)
COLOR_BLUE = (0, 0, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_SILVER = (140, 140, 140)
COLOR_RED = (255, 0, 0)

GRID_COLOR = (177, 177, 177)

WINDOW_WIDTH = 500
WINDOW_HEIGHT = 540

BOARD_X = 100
BOARD_Y = 50
BOARD_WIDTH = 300
BOARD_HEIGHT = 460
BOARD_GEOMETRY = (BOARD_X, BOARD_Y, BOARD_WIDTH, BOARD_HEIGHT)
BOX_SIZE = 20

COLOR_SMALL_BLOCK = (255, 120, 115)
COLOR_LONG_BLOCK = (255, 200, 105)
COLOR_STATIC_BOX = (200, 200, 50)
COLOR_BIG_BLOCK = (200, 200, 250)
COLOR_BG_GAME_OVER = (30, 30, 30)
COLOR_BLOCK_GAME_OVER = (200, 200, 200)
COLOR_T_BLOCK = (170, 170, 0)
COLOR_L_BLOCK = (200, 100, 30)
COLOR_S_BLOCK = (250, 250, 100)
COLOR_Z_BLOCK = (100, 250, 200)
PLAYER_SPEED = 380

EVENT_FULL_LINES = 'FULL_LINES'
SOUNDS_DIR = './sounds'
SETTING_FILE = 'settings.json'
GAME_STATE_FILE = 'save.json'


def get_gravity(level):
    if level == 1:
        return 80
    elif level == 2:
        return 180
    else:
        return 280


class EventEmitter:

    def __init__(self):
        self.listeners = {}

    def add_listener(self, event, listener):
        if event not in self.listeners:
            self.listeners[event] = []
        self.listeners[event].append(listener)

    def emit(self, event, *args, **kwargs):
        if event in self.listeners:
            for listener in self.listeners[event]:
                listener(*args, **kwargs)


class Item:

    def on_keydown(self, key):
        pass

    def on_keyup(self, key):
        pass

    def on_click(self, x, y):
        pass

    def on_mouse(self, x, y):
        pass

    def update(self, delta_time):
        pass

    def render(self, screen):
        raise NotImplemented()


class Activity:
    supported_events = ()

    def add_listener(self, event, listener):
        pass

    def prepare(self):
        pass

    def on_mouse(self, x, y):
        pass

    def on_keydown(self, key):
        pass

    def on_keyup(self, key):
        pass

    def on_click(self, x, y):
        pass

    def update(self, delta_time):
        pass

    def render(self, screen):
        for items in self.get_items():
            items.render(screen)

    def get_items(self):
        return []

    def get_state(self):
        pass

    def set_state(self, state):
        pass


class TetrisActivity(Activity):

    def __init__(self):
        super().__init__()
        self.level_activity = LevelActivity()
        self.play_activity = PlayActivity()
        self.menu_activity = MenuActivity()
        self.curr_activity = self.level_activity

    def add_sound_listener(self, listener):
        self.play_activity.add_sound_listener(listener)

    def add_exit_listener(self, listener):
        self.menu_activity.add_exit_listener(listener)

    def add_save_listener(self, listener):
        self.menu_activity.add_save_listener(listener)

    def add_load_listener(self, listener):
        self.menu_activity.add_load_listener(listener)

    def add_toggle_mute_listener(self, listener):
        self.menu_activity.add_toggle_mute_listener(listener)

    def add_listener(self, event, listener):
        if event in self.play_activity.supported_events:
            self.play_activity.add_listener(event, listener)
        if event in self.menu_activity.supported_events:
            self.menu_activity.add_listener(event, listener)

    def prepare(self):
        self.level_activity.prepare()
        self.level_activity.add_run_level_listener(self.run_game)
        self.play_activity.prepare()
        self.menu_activity.prepare()
        self.menu_activity.add_resume_listener(self.resume_game)

    def run_game(self, level):
        self.curr_activity = self.play_activity
        self.play_activity.level = level

    def on_mouse(self, x, y):
        self.curr_activity.on_mouse(x, y)

    def on_keydown(self, key):
        if key == pygame.K_ESCAPE:
            self.curr_activity = self.menu_activity
        else:
            self.curr_activity.on_keydown(key)

    def on_keyup(self, key):
        self.curr_activity.on_keyup(key)

    def on_click(self, x, y):
        self.curr_activity.on_click(x, y)

    def render(self, screen):
        self.curr_activity.render(screen)

    def update(self, delta_time):
        self.curr_activity.update(delta_time)

    def get_items(self):
        raise NotImplemented()

    def get_state(self):
        return {
            'play': self.play_activity.get_state()
        }

    def set_state(self, state):
        self.play_activity.set_state(state['play'])

    def resume_game(self):
        self.curr_activity = self.play_activity


class LevelActivity(Activity):

    def __init__(self):
        super().__init__()
        self.button_level1 = None
        self.items = []
        self.event_emitter = EventEmitter()
        self.launched = False

    def prepare(self):
        self.command_label = Label(180, 150, COLOR_BLACK, '* WYBIERZ POZIOM *')
        self.items.append(self.command_label)
        self.button_level1 = ButtonItem(
            100, 200, 'POZIOM 1', GRID_COLOR, COLOR_BLUE)
        self.button_level1.add_click_listener(self.run_level1)
        self.items.append(self.button_level1)

        self.button_level2 = ButtonItem(
            100, 250, 'POZIOM 2', GRID_COLOR, COLOR_BLUE)
        self.button_level2.add_click_listener(self.run_level2)
        self.items.append(self.button_level2)

        self.button_level3 = ButtonItem(
            100, 300, 'POZIOM 3', GRID_COLOR, COLOR_BLUE)
        self.button_level3.add_click_listener(self.run_level3)
        self.items.append(self.button_level3)

    def on_keydown(self, key):
        if pygame.K_1:
            self.run_level1()
        elif pygame.K_2:
            self.run_level2()
        elif pygame.K_3:
            self.run_level3()

    def add_run_level_listener(self, listener):
        self.event_emitter.add_listener('RUN_LEVEL', listener)

    def on_mouse(self, x, y):
        for item in self.items:
            if item.on_mouse(x, y):
                break

    def on_click(self, x, y):
        for item in self.items:
            if item.on_click(x, y):
                break

    def get_items(self):
        return self.items

    def update(self, delta_time):
        pass

    def run_level1(self):
        self.run_level(1)

    def run_level2(self):
        self.run_level(2)

    def run_level3(self):
        self.run_level(3)

    def run_level(self, nr):
        if not self.launched:
            self.launched = True
            self.event_emitter.emit('RUN_LEVEL', nr)


class ButtonItem(Item):

    def __init__(self, x, y, text, color, highlighted_color):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.curr_color = color
        self.highlighted_color = highlighted_color
        self.width = 300
        self.height = 30
        self.event_emitter = EventEmitter()

    def add_click_listener(self, listener):
        self.event_emitter.add_listener('CLICK', listener)

    def contains_pos(self, x, y):
        if self.x <= x <= self.x + self.width:
            if self.y <= y <= self.y + self.height:
                return True
        return False

    def on_mouse(self, x, y):
        if self.contains_pos(x, y):
            self.curr_color = self.highlighted_color
        else:
            self.curr_color = self.color

    def on_click(self, x, y):
        if self.contains_pos(x, y):
            self.event_emitter.emit('CLICK')

    def render(self, painter):
        painter.draw_text(
            self.x + 120, self.y + 5, self.text, self.curr_color)
        painter.draw_rect(
            self.x, self.y, self.width, self.height, self.curr_color)


class PlayActivity(Activity):
    supported_events = ('PAUSE', 'UNPAUSE')

    def __init__(self):
        super().__init__()
        self.items = []
        self.board = None
        self.level_label = None
        self.scores_label = None
        self.event_emitter = EventEmitter()
        self.scores = 0
        self.lines = 0
        self.level = 1

    def prepare(self):
        self.board = create_board(lambda: self.level)
        self.board.add_listener(EVENT_FULL_LINES, self.on_full_lines)
        self.board.add_sound_listener(
            lambda s: self.event_emitter.emit('SOUND', s))
        self.board.add_game_over_listener(self.on_game_over)
        self.items.append(self.board)

        self.level_label = NumberLabel(
            10, 10, COLOR_BLACK, 'POZIOM', lambda: self.level)
        self.items.append(self.level_label)

        self.scores_label = NumberLabel(
            10, 30, COLOR_BLACK, 'PUNKTY', lambda: self.scores)
        self.items.append(self.scores_label)

        self.next_block_label = Label(430, 10, COLOR_BLACK, 'KLOCEK')
        self.items.append(self.next_block_label)

        self.next_block_view = NextBlockView(
            430, 50, lambda: self.board.next_block)
        self.items.append(self.next_block_view)

        self.game_over_label = Label(220, 10, COLOR_RED, '')
        self.items.append(self.game_over_label)

    def add_listener(self, event, listener):
        self.event_emitter.add_listener(event, listener)

    def add_sound_listener(self, listener):
        self.event_emitter.add_listener('SOUND', listener)

    def update(self, delta_time):
        for item in self.items:
            item.update(delta_time)

    def get_items(self):
        return self.items

    def on_keyup(self, key):
        self.board.set_direction(None)

    def on_keydown(self, key):
        if pygame.K_LEFT == key:
            self.board.set_direction('LEFT')
        elif pygame.K_RIGHT == key:
            self.board.set_direction('RIGHT')
        # Po odkomentowaniu zadziała szybsze opadanie
        # elif pygame.K_DOWN == key:
        #     self.board.set_direction('DOWN')
        elif pygame.K_SPACE == key:
            self.board.rotate_curr_block()
        elif pygame.K_p == key:
            self.board.toggle_pause()
            if self.board.paused:
                self.event_emitter.emit('PAUSE')
            else:
                self.event_emitter.emit('UNPAUSE')

    def on_click(self, x, y):
        pass

    def on_full_lines(self, line_count):
        self.lines += line_count
        self.scores += self.level * line_count

    def on_game_over(self):
        self.show_game_over()

    def show_game_over(self):
        self.game_over_label.label = 'GAME OVER'

    def clear_game_over(self):
        self.game_over_label.label = ''

    def get_state(self):
        return {
            'game_over': self.board.game_over,
            'board': self.board.get_state(),
            'scores': self.scores,
            'lines': self.lines,
            'level': self.level
        }

    def set_state(self, state):
        self.board.set_state(state['board'])
        self.scores = state['scores']
        self.lines = state['lines']
        self.level = state['level']
        if state.get('game_over'):
            self.show_game_over()
        else:
            self.clear_game_over()



class MenuActivity(Activity):

    def __init__(self):
        super().__init__()
        self.items = []
        self.launched = False
        self.event_emitter = EventEmitter()

    def add_resume_listener(self, listener):
        self.event_emitter.add_listener('RESUME', listener)

    def add_save_listener(self, listener):
        self.event_emitter.add_listener('SAVE', listener)

    def add_load_listener(self, listener):
        self.event_emitter.add_listener('LOAD', listener)

    def add_toggle_mute_listener(self, listener):
        self.event_emitter.add_listener('TOGGLE_MUTE', listener)

    def add_exit_listener(self, listener):
        self.event_emitter.add_listener('EXIT', listener)

    def prepare(self):
        self.command_label = Label(215, 150, COLOR_BLACK, '* MENU *')
        self.items.append(self.command_label)
        self.button_level1 = ButtonItem(
            100, 200, 'POWRÓT', GRID_COLOR, COLOR_BLUE)
        self.button_level1.add_click_listener(self.resume)
        self.items.append(self.button_level1)

        self.button_level2 = ButtonItem(
            100, 250, 'ZAPISZ', GRID_COLOR, COLOR_BLUE)
        self.button_level2.add_click_listener(self.save)
        self.items.append(self.button_level2)

        self.button_level3 = ButtonItem(
            100, 300, 'WCZYTAJ', GRID_COLOR, COLOR_BLUE)
        self.button_level3.add_click_listener(self.load)
        self.items.append(self.button_level3)

        self.button_level4 = ButtonItem(
            100, 350, 'WYCISZ', GRID_COLOR, COLOR_BLUE)
        self.button_level4.add_click_listener(self.toggle_mute)
        self.items.append(self.button_level4)

        self.button_level5 = ButtonItem(
            100, 400, 'WYJŚCIE', GRID_COLOR, COLOR_BLUE)
        self.button_level5.add_click_listener(self.exit)
        self.items.append(self.button_level5)

    def on_keydown(self, key):
        if pygame.K_1:
            self.resume()
        elif pygame.K_2:
            self.save()
        elif pygame.K_3:
            self.load()
        elif pygame.K_4:
            self.toggle_mute()
        elif pygame.K_5:
            self.exit()

    def on_mouse(self, x, y):
        for item in self.items:
            if item.on_mouse(x, y):
                break

    def on_click(self, x, y):
        for item in self.items:
            if item.on_click(x, y):
                break

    def get_items(self):
        return self.items

    def update(self, delta_time):
        pass

    def resume(self):
        self.event_emitter.emit('RESUME')

    def load(self):
        self.event_emitter.emit('LOAD')

    def save(self):
        self.event_emitter.emit('SAVE')

    def exit(self):
        self.event_emitter.emit('EXIT')

    def toggle_mute(self):
        self.event_emitter.emit('TOGGLE_MUTE')


class Painter:

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.background_color = COLOR_WHITE
        self.screen = None
        self.font = None

    def fill_rect(self, x, y, w, h, color):
        pygame.draw.rect(self.screen, color, [x, y, w, h])

    def draw_rect(self, x, y, w, h, color):
        pygame.draw.rect(self.screen, color, [x, y, w, h], 1)

    def draw_line(self, x1, y1, x2, y2, color):
        pygame.draw.line(self.screen, color, (x1, y1), (x2, y2))

    def draw_text(self, x, y, text, color):
        label = self.font.render(text, 1, color)
        self.screen.blit(label, (x, y))

    def run(self):
        pygame.font.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.font = pygame.font.SysFont("monospace", 15)

    def render_background(self):
        self.screen.fill(self.background_color)


class SoundManager:

    def __init__(self, path):
        self.path = path
        self.mute = False
        self.sounds = {}

    def set_mute(self, value):
        self.mute = value
        if self.mute:
            pygame.mixer.music.stop()
        else:
            pygame.mixer.music.play(-1)

    def prepare(self):
        pygame.mixer.init()
        self.load_sounds()

    def load_bg_music(self, file_name):
        pygame.mixer.music.load(file_name)

    def load_sounds(self):
        for filename in os.listdir(self.path):
            if filename.endswith(".wav"):
                sound = pygame.mixer.Sound(os.path.join(self.path, filename))
                self.sounds[self.make_key(filename)] = sound

    def make_key(self, filename):
        return os.path.splitext(filename)[0]

    def play(self, key):
        if not self.mute:
            sound = self.sounds[key]
            sound.play()


class SettingsManager:

    def __init__(self, settings_file):
        self.settings_file = settings_file
        self.settings = {}

    def get(self, key, default_value):
        return self.settings.get(key, default_value)

    def set(self, key, value):
        self.settings[key] = value
        self.save()

    def prepare(self):
        self.load()

    def load(self):
        try:
            with open(self.settings_file) as document:
                self.settings = json.load(document)
        except IOError as error:
            if os.path.exists(self.settings_file):
                raise error
            else:
                print('NIE WCZYTANO PLIKU USTAWIEŃ (POWÓD: BRAK PLIKU)')
        else:
            print('WCZYTANO PLIK USTAWIEŃ')

    def save(self):
        with open(self.settings_file, 'w') as document:
            json.dump(self.settings, document)


class ActivityContainer:

    def __init__(self, width, height, title):
        self.running = False
        self.painter = Painter(width, height)
        self.sound_manager = SoundManager(SOUNDS_DIR)
        self.settings_manager = SettingsManager(SETTING_FILE)
        self.last_time = None
        self.title = title

    def run_activity(self, activity):
        pygame.init()
        self.painter.run()

        self.settings_manager.prepare()

        self.sound_manager.prepare()
        self.sound_manager.load_bg_music('bg.wav')
        self.sound_manager.set_mute(self.settings_manager.get('mute', False))

        self.set_window_title(self.title)

        activity.prepare()

        activity.add_listener('PAUSE', self.on_paused)
        activity.add_listener('UNPAUSE', self.on_unpaused)

        activity.add_exit_listener(self.on_exit)
        activity.add_load_listener(lambda: self.on_load(activity))
        activity.add_save_listener(lambda: self.on_save(activity))
        activity.add_sound_listener(self.on_sound)
        activity.add_toggle_mute_listener(self.on_toggle_mute)

        self.running = True
        while self.running:
            delta_time = self.calculate_delta_time()
            self.process_activity_events(activity)
            activity.update(delta_time)
            self.painter.render_background()
            activity.render(self.painter)
            pygame.display.update()
            time.sleep(0.05)

        pygame.quit()
        sys.exit(0)

    def calculate_delta_time(self):
        if self.last_time is None:
            self.last_time = time.time()
        current_time = time.time()
        delta_time = current_time - self.last_time
        self.last_time = current_time
        return delta_time

    def process_activity_events(self, activity):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                activity.on_keydown(event.key)
            elif event.type == pygame.KEYUP:
                activity.on_keyup(event.key)
            elif event.type == pygame.MOUSEMOTION:
                x, y = pygame.mouse.get_pos()
                activity.on_mouse(x, y)
            elif event.type == pygame.MOUSEBUTTONUP:
                x, y = pygame.mouse.get_pos()
                activity.on_click(x, y)

    def on_paused(self):
        self.set_window_title('{}:PAUSED!'.format(self.title))

    def on_unpaused(self):
        self.set_window_title('{}'.format(self.title))

    def set_window_title(self, title):
        pygame.display.set_caption(title)

    def on_exit(self):
        self.running = False

    def on_load(self, activity):
        try:
            with open(GAME_STATE_FILE, 'r') as doc:
                activity.set_state(json.load(doc))
        except IOError:
            print('BŁĄD WCZYTYWANIA')
        else:
            print('GRA WCZYTANA')

    def on_save(self, activity):
        with open(GAME_STATE_FILE, 'w') as doc:
            json.dump(activity.get_state(), doc)
        print('GRA ZAPISANA')

    def on_sound(self, sound_name):
        self.sound_manager.play(sound_name)

    def on_toggle_mute(self):
        mute = not self.sound_manager.mute
        self.sound_manager.set_mute(mute)
        self.settings_manager.set('mute', mute)


class Label(Item):

    def __init__(self, x, y, color, label):
        self.x = x
        self.y = y
        self.label = label
        self.color = color

    def render(self, painter):
        painter.draw_text(self.x, self.y, self.label, self.color)

    def update(self, delta_time):
        pass


class NumberLabel:

    def __init__(self, x, y, color, label, value_provider):
        self.x = x
        self.y = y
        self.color = color
        self.label = label
        self.value_provider = value_provider

    def render(self, painter):
        text = '{}: {}'.format(self.label, self.value_provider())
        painter.draw_text(self.x, self.y, text, self.color)

    def update(self, delta_time):
        pass


class NextBlockView:

    def __init__(self, x, y, value_provider):
        self.x = x
        self.y = y
        self.value_provider = value_provider
        self.box_size = 15

    def render(self, painter):
        block = self.value_provider()

        for box in block.boxes:
            rows = block.get_bottom_box().row - box.row
            cols = block.get_right_box().col - box.col
            x = self.box_size * cols
            y = self.box_size * rows
            painter.fill_rect(
                self.x + x, self.y + y, self.box_size, self.box_size, box.color)
            painter.draw_rect(
                self.x + x, self.y + y, self.box_size, self.box_size, COLOR_WHITE)

    def update(self, delta_time):
        pass


class Box:

    def __init__(self, row, col, color, board):
        self.row = row
        self.col = col
        self.color = color
        self.board = board

    @classmethod
    def from_state(cls, board, state):
        row = state['row']
        col = state['col']
        color = state['color']
        return cls(row, col, color, board)

    def get_state(self):
        return {
            'row': self.row,
            'col': self.col,
            'color': self.color
        }

    def __copy__(self):
        return Box(self.row, self.col, self.color, self.board)

    def __eq__(self, other):
        if self is other:
            return True
        return isinstance(other, Box) and self.row == other.row and self.col == other.col

    def render(self, painter):
        x, y, w, h = self.board.calculate_box_geometry(self.row, self.col)
        painter.fill_rect(x, y, w, h, self.color)


class StaticBoxGroup:

    def __init__(self, row_count, col_count):
        self.rows = self.make_rows(row_count, col_count)
        self.boxes = []
        self.row_count = row_count
        self.col_count = col_count

    def make_rows(self, rows_count, col_count):
        rows = []
        for _ in range(rows_count):
            rows.append(self.make_row(col_count))
        return rows

    def make_row(self, row_size):
        return [None] * row_size

    def has_collision(self, block):
        for box in self.boxes:
            if box in block.boxes:
                return True
        return False

    def add_boxes(self, boxes):
        for box in boxes:
            self.rows[box.row][box.col] = box
            self.boxes.append(box)

    def clear_full_rows(self):
        lines = 0
        row_index = self.row_count - 1
        while row_index > -1 and not self.is_empty_row(self.rows[row_index]):
            if self.is_full_row(self.rows[row_index]):
                self.remove_row(row_index)
                lines += 1
                continue
            row_index -= 1
        return lines

    def remove_row(self, row_index):
        for box in self.rows[row_index]:
            self.boxes.remove(box)
        self.rows.pop(row_index)
        for box in self.boxes:
            if row_index > box.row:
                box.row += 1
        self.rows.insert(0, self.make_row(self.col_count))

    def is_empty_row(self, row):
        return row.count(None) == self.col_count

    def is_full_row(self, row):
        return row.count(None) == 0

    def get_state(self):
        return {
            'boxes': [box.get_state() for box in self.boxes]
        }

    def set_state(self, state):
        boxes = []
        for box_state in state['boxes']:
            box = Box.from_state(self, box_state)
            boxes.append(box)
        self.boxes.clear()
        self.add_boxes(boxes)


class Board:

    def __init__(self, block_factories, get_level):
        self.x, self.y, self.w, self.h = BOARD_GEOMETRY
        self.box_size = BOX_SIZE
        self.block_factories = block_factories
        self.grid_color = GRID_COLOR
        self.background_color = COLOR_WHITE
        self.curr_block = None
        self.next_block = None
        self.block_start_row = 0
        self.block_end_row = self.h // self.box_size
        self.block_start_col = 0
        self.block_end_col = self.w // self.box_size
        self.block_mid_col = (self.w // self.box_size) // 2 - 1
        self.static_boxes = StaticBoxGroup(
            self.block_end_row, self.block_end_col)
        self.game_over = False
        self.game_over_bgcolor = COLOR_BG_GAME_OVER
        self.game_over_block_color = COLOR_BLOCK_GAME_OVER
        self.paused = False
        self.get_level = get_level
        self.event_emitter = EventEmitter()

    def add_listener(self, event, listener):
        self.event_emitter.add_listener(event, listener)

    def add_sound_listener(self, listener):
        self.event_emitter.add_listener('SOUND', listener)

    def add_game_over_listener(self, listener):
        self.event_emitter.add_listener('GAME_OVER', listener)

    def get_state(self):
        if self.curr_block:
            return {
                'static_boxes': self.static_boxes.get_state(),
                'curr_block': self.curr_block.get_state(),
                'next_block': self.next_block.get_state()
            }
        else:
            return {
                'static_boxes': self.static_boxes.get_state(),
                'curr_block': None,
                'next_block': self.next_block.get_state()
            }

    def set_state(self, state):
        self.static_boxes.set_state(state['static_boxes'])
        if state['curr_block']:
            self.curr_block = Block.from_state(
                state['curr_block'], self.block_factories, self)
        self.next_block = Block.from_state(
                state['next_block'], self.block_factories, self)

    def set_direction(self, direction):
        if self.curr_block and not self.paused:
            if self.curr_block.direction != direction:
                self.curr_block.direction = direction

    def rotate_curr_block(self):
        if self.curr_block and not self.paused:
            self.curr_block.want_rotate = True

    def render(self, painter):
        if self.game_over:
            bgcolor = self.game_over_bgcolor
        else:
            bgcolor = self.background_color

        painter.fill_rect(self.x, self.y, self.w, self.h, bgcolor)
        self.render_static_boxes(painter)

        if self.curr_block:
            self.render_curr_block(painter)

        # net
        self.render_net_lines(painter)
        painter.draw_rect(self.x, self.y, self.w, self.h, self.grid_color)

    def render_static_boxes(self, painter):
        for box in self.static_boxes.boxes:
            self.render_box(painter, box)

    def render_curr_block(self, painter):
        for box in self.curr_block.boxes:
            self.render_box(painter, box)

    def render_box(self, painter, box):
        box_x = self.x + box.col * self.box_size
        box_y = self.y + box.row * self.box_size
        if self.game_over:
            color = self.game_over_block_color
        else:
            color = box.color
        painter.fill_rect(
            box_x, box_y, self.box_size, self.box_size, color)

    def render_net_lines(self, painter):
        self.render_vertical_net_lines(painter)
        self.render_horizontal_net_lines(painter)

    def render_vertical_net_lines(self, painter):
        for x in range(self.x, self.x + self.w, self.box_size):
            painter.draw_line(
                x, self.y, x, self.y + self.h - 1, self.grid_color)

    def render_horizontal_net_lines(self, painter):
        for y in range(self.y, self.y + self.h, self.box_size):
            painter.draw_line(
                self.x, y, self.x + self.w - 1, y, self.grid_color)

    def take_next_block(self):
        block = self.next_block
        self.next_block = self.create_random_block()
        return block

    def create_random_block(self):
        factory = random.choice(self.block_factories)
        boxes = self.create_boxes(factory.required_boxes, factory.color)
        block = factory.create(boxes)
        return block

    def create_boxes(self, box_count, color):
        boxes = []
        for _ in range(box_count):
            boxes.append(Box(None, None, color, self))
        boxes[0].row = self.block_start_row
        boxes[0].col = self.block_mid_col
        return boxes

    def get_curr_block(self):
        if self.next_block is None:
            self.next_block = self.create_random_block()

        if self.curr_block is None:
            self.curr_block = self.take_next_block()

        return self.curr_block

    def stop_curr_block(self):
        self.curr_block = None

    def toggle_pause(self):
        self.paused = not self.paused

    def update(self, delta_time):
        if self.game_over or self.paused:
            return

        curr_block = self.get_curr_block()

        if curr_block.want_rotate:
            rotated_block = curr_block.make_rotated()
            if not self.has_any_collision(rotated_block):
                curr_block.rotate()
                self.event_emitter.emit('SOUND', 'rotate')
            curr_block.want_rotate = False

        curr_block.horizontal_update(delta_time)

        self.fix_left_border_collision(curr_block)
        self.fix_right_border_collision(curr_block)

        if curr_block.direction == 'LEFT':
            while self.static_boxes.has_collision(curr_block):
                self.curr_block.move_one_right()
        elif curr_block.direction == 'RIGHT':
            while self.static_boxes.has_collision(curr_block):
                self.curr_block.move_one_left()

        curr_block.vertical_update(delta_time, self.get_level())

        stop_curr_block = False

        if self.is_bottom_border_collision(curr_block):
            curr_block.move_one_up()
            while self.is_bottom_border_collision(curr_block):
                curr_block.move_one_up()
            stop_curr_block = True

        if self.static_boxes.has_collision(curr_block):
            curr_block.move_one_up()
            while self.static_boxes.has_collision(curr_block):
                curr_block.move_one_up()
            stop_curr_block = True

        if stop_curr_block:
            self.static_boxes.add_boxes(self.curr_block.boxes)
            self.check_game_over()
            self.stop_curr_block()
            self.event_emitter.emit('SOUND', 'stop')

        lines = self.static_boxes.clear_full_rows()
        if lines > 0:
            self.event_emitter.emit(EVENT_FULL_LINES, lines)
            self.event_emitter.emit('SOUND', 'line')

    def check_game_over(self):
        box = self.curr_block.get_top_box()
        if box.row < 0:
            self.game_over = True
            self.event_emitter.emit('GAME_OVER')

    def has_any_collision(self, block):
        return (
            self.has_left_border_collision(block) or
            self.has_right_border_collision(block) or
            self.has_bottom_border_collision(block) or
            self.static_boxes.has_collision(block)
        )

    def has_left_border_collision(self, block):
        box = block.get_left_box()
        return box.col < self.block_start_col

    def has_right_border_collision(self, block):
        box = block.get_right_box()
        return box.col >= self.block_end_col

    def has_bottom_border_collision(self, block):
        box = block.get_bottom_box()
        return box.row >= self.block_end_row

    def fix_left_border_collision(self, curr_block):
        box = curr_block.get_left_box()
        while box.col < self.block_start_col:
             curr_block.move_one_right()

    def fix_right_border_collision(self, curr_block):
        box = curr_block.get_right_box()
        while box.col >= self.block_end_col:
            curr_block.move_one_left()

    def is_bottom_border_collision(self, curr_block):
        box = curr_block.get_bottom_box()
        return box.row >= self.block_end_row


class BlockFactory:

    def __init__(self, box_class, color, box_size, gravity_speed, player_speed):
        self.box_class = box_class
        self.color = color
        self.box_size = box_size
        self.gravity_speed = gravity_speed
        self.player_speed = player_speed
        self.kind = box_class.kind
        self.required_boxes = box_class.required_boxes

    def create(self, boxes, prepared_boxes=False):
        return self.box_class(boxes, self, prepared_boxes)


class Block:

    def __init__(self, boxes, factory, prepared_boxes=False):
        self.factory = factory
        self.acc_row = UnitAccumulator(factory.box_size)
        self.acc_col = UnitAccumulator(factory.box_size)
        self.direction = None
        if not prepared_boxes:
            self.prepare_boxes(boxes)
        self.boxes = boxes
        self.want_rotate = False
        self.rotate_position = 0

    @classmethod
    def from_state(cls, state, factories, board):
        curr_factory = None
        for factory in factories:
            if factory.kind == state['kind']:
                curr_factory = factory

        boxes = [Box.from_state(board, state) for state in state['boxes']]
        return curr_factory.create(boxes, True)

    def get_state(self):
        return {
            'kind': self.kind,
            'boxes': [box.get_state() for box in self.boxes]
        }

    def prepare_boxes(self, boxes):
        raise NotImplemented()

    def get_top_box(self):
        raise NotImplemented()

    def get_left_box(self):
        raise NotImplemented()

    def get_right_box(self):
        raise NotImplemented()

    def get_bottom_box(self):
        raise NotImplemented()

    def get_bottom_boxes(self):
        raise NotImplemented()

    def copy_boxes(self):
        return [copy.copy(box) for box in self.boxes]

    def vertical_update(self, delta_time, level):
        total_gravity = self.calculate_total_gravity(level)
        self.acc_row.inc(delta_time * total_gravity)
        delta_row = self.acc_row.take_value()
        for box in self.boxes:
            box.row += delta_row

    def horizontal_update(self, delta_time):
        if self.direction in ('RIGHT', 'LEFT'):
            if self.direction == 'LEFT':
                sign = -1
            else:
                sign = 1
            self.acc_col.inc(delta_time * self.factory.player_speed)
            delta_col = self.acc_col.take_value()
            for box in self.boxes:
                box.col += delta_col * sign

    def move_one_left(self):
        for box in self.boxes:
            box.col -= 1

    def move_one_right(self):
        for box in self.boxes:
            box.col += 1

    def move_one_up(self):
        for box in self.boxes:
            box.row -= 1

    def calculate_total_gravity(self, level):
        if self.direction == 'DOWN':
            return self.factory.gravity_speed(level) + self.factory.player_speed
        else:
            return self.factory.gravity_speed(level)


class LongBlock(Block):
    required_boxes = 4
    max_rotate_positions = 2
    kind = '|'

    def prepare_boxes(self, boxes):
        row = boxes[0].row
        col = boxes[0].col
        for box in boxes[1:]:
            row += 1
            box.row = row
            box.col = col

    def is_vertical(self):
        return self.rotate_position == 0

    def get_top_box(self):
        return self.boxes[0]

    def get_bottom_box(self):
        return self.boxes[-1]

    def get_left_box(self):
        return self.boxes[0]

    def get_right_box(self):
        if self.is_vertical():
            return self.boxes[0]
        else:
            return self.boxes[-1]

    def get_bottom_boxes(self):
        if self.is_vertical():
            return [self.boxes[-1]]
        else:
            return self.boxes

    def rotate(self):
        self.rotate_position += 1
        if self.rotate_position == self.max_rotate_positions:
            self.rotate_position = 0

        if self.rotate_position == 0:
            self.use_position_vertical()
        elif self.rotate_position == 1:
            self.use_position_horizontal()

    def make_rotated(self):
        block = LongBlock(self.copy_boxes(), self.factory, prepared_boxes=True)
        block.rotate_position = self.rotate_position
        block.rotate()
        return block

    def use_position_vertical(self):
        row = self.boxes[1].row - 1
        col = self.boxes[1].col
        for box in self.boxes:
            box.row = row
            box.col = col
            row += 1

    def use_position_horizontal(self):
        row = self.boxes[1].row
        col = self.boxes[1].col - 1
        for box in self.boxes:
            box.row = row
            box.col = col
            col += 1


class TBlock(Block):
    required_boxes = 4
    max_rotate_positions = 4
    kind = 'T'

    def prepare_boxes(self, boxes):
        boxes[1].row = boxes[0].row + 1
        boxes[1].col = boxes[0].col
        boxes[2].row = boxes[0].row + 2
        boxes[2].col = boxes[0].col
        boxes[3].row = boxes[0].row + 1
        boxes[3].col = boxes[0].col + 1

    def is_right_position(self):
        return self.rotate_position == 0

    def is_bottom_position(self):
        return self.rotate_position == 1

    def is_left_position(self):
        return self.rotate_position == 2

    def is_top_position(self):
        return self.rotate_position == 3

    def get_top_box(self):
        if self.is_top_position():
            return self.boxes[3]
        else:
            return self.boxes[0]

    def get_bottom_box(self):
        if self.is_bottom_position():
            return self.boxes[3]
        else:
            return self.boxes[2]

    def get_left_box(self):
        if self.is_left_position():
            return self.boxes[3]
        else:
            return self.boxes[0]

    def get_right_box(self):
        if self.is_right_position():
            return self.boxes[3]
        else:
            return self.boxes[2]

    def get_bottom_boxes(self):
        if self.is_bottom_position():
            return [self.boxes[3]]
        elif self.is_top_position():
            return self.boxes[0:3]
        else:
            return [self.boxes[2]]

    def rotate(self):
        self.rotate_position += 1
        if self.rotate_position == self.max_rotate_positions:
            self.rotate_position = 0

        if self.rotate_position == 0:
            self.use_right_position()
        elif self.rotate_position == 1:
            self.use_bottom_position()
        elif self.rotate_position == 2:
            self.use_left_position()
        elif self.rotate_position == 3:
            self.use_top_position()

    def make_rotated(self):
        block = TBlock(self.copy_boxes(), self.factory, prepared_boxes=True)
        block.rotate_position = self.rotate_position
        block.rotate()
        return block

    def use_top_position(self):
        """
        Example:
               [3]
            [0][1][2]
        """
        row = self.boxes[1].row
        col = self.boxes[1].col
        self.boxes[0].row = row
        self.boxes[0].col = col - 1
        self.boxes[2].row = row
        self.boxes[2].col = col + 1
        self.boxes[3].row = row - 1
        self.boxes[3].col = col

    def use_bottom_position(self):
        """
        Example:
            [0][1][2]
               [3]
        """
        row = self.boxes[1].row
        col = self.boxes[1].col
        self.boxes[0].row = row
        self.boxes[0].col = col - 1
        self.boxes[2].row = row
        self.boxes[2].col = col + 1
        self.boxes[3].row = row + 1
        self.boxes[3].col = col

    def use_left_position(self):
        """
        Example:
             [0]
          [3][1]
             [2]
        """
        row = self.boxes[1].row
        col = self.boxes[1].col
        self.boxes[0].row = row - 1
        self.boxes[0].col = col
        self.boxes[2].row = row + 1
        self.boxes[2].col = col
        self.boxes[3].row = row
        self.boxes[3].col = col - 1

    def use_right_position(self):
        """
        Example:
            [0]
            [1][3]
            [2]
        """
        row = self.boxes[1].row
        col = self.boxes[1].col
        self.boxes[0].row = row - 1
        self.boxes[0].col = col
        self.boxes[2].row = row + 1
        self.boxes[2].col = col
        self.boxes[3].row = row
        self.boxes[3].col = col + 1


class ZBlock(Block):
    required_boxes = 4
    max_rotate_positions = 2
    kind = 'Z'

    def prepare_boxes(self, boxes):
        row = boxes[0].row
        col = boxes[0].col
        boxes[1].row = row + 1
        boxes[1].col = col
        boxes[2].row = row + 1
        boxes[2].col = col - 1
        boxes[3].row = row + 2
        boxes[3].col = col - 1

    def is_vertical(self):
        return self.rotate_position == 0

    def get_top_box(self):
        return self.boxes[0]

    def get_bottom_box(self):
        return self.boxes[3]

    def get_left_box(self):
        if self.is_vertical():
            return self.boxes[2]
        else:
            return self.boxes[0]

    def get_right_box(self):
        if self.is_vertical():
            return self.boxes[0]
        else:
            return self.boxes[3]

    def get_bottom_boxes(self):
        if self.is_vertical():
            return [self.boxes[3]]
        else:
            return [self.boxes[2], self.boxes[3]]

    def rotate(self):
        self.rotate_position += 1
        if self.rotate_position == self.max_rotate_positions:
            self.rotate_position = 0

        if self.rotate_position == 0:
            self.use_position_vertical()
        elif self.rotate_position == 1:
            self.use_position_horizontal()

    def make_rotated(self):
        block = ZBlock(self.copy_boxes(), self.factory, prepared_boxes=True)
        block.rotate_position = self.rotate_position
        block.rotate()
        return block

    def use_position_vertical(self):
        row = self.boxes[1].row
        col = self.boxes[1].col
        self.boxes[0].row = row - 1
        self.boxes[0].col = col
        self.boxes[2].row = row
        self.boxes[2].col = col - 1
        self.boxes[3].row = row + 1
        self.boxes[3].col = col - 1

    def use_position_horizontal(self):
        row = self.boxes[1].row
        col = self.boxes[1].col
        self.boxes[0].row = row
        self.boxes[0].col = col - 1
        self.boxes[2].row = row + 1
        self.boxes[2].col = col
        self.boxes[3].row = row + 1
        self.boxes[3].col = col + 1


class SBlock(Block):
    required_boxes = 4
    max_rotate_positions = 2
    kind = 'S'

    def prepare_boxes(self, boxes):
        row = boxes[0].row
        col = boxes[0].col
        boxes[1].row = row + 1
        boxes[1].col = col
        boxes[2].row = row + 1
        boxes[2].col = col + 1
        boxes[3].row = row + 2
        boxes[3].col = col + 1

    def is_vertical(self):
        return self.rotate_position == 0

    def get_top_box(self):
        return self.boxes[0]

    def get_bottom_box(self):
        return self.boxes[3]

    def get_left_box(self):
        if self.is_vertical():
            return self.boxes[1]
        else:
            return self.boxes[3]

    def get_right_box(self):
        if self.is_vertical():
            return self.boxes[3]
        else:
            return self.boxes[0]

    def get_bottom_boxes(self):
        if self.is_vertical():
            return [self.boxes[3]]
        else:
            return [self.boxes[2], self.boxes[3]]

    def rotate(self):
        self.rotate_position += 1
        if self.rotate_position == self.max_rotate_positions:
            self.rotate_position = 0

        if self.rotate_position == 0:
            self.use_position_vertical()
        elif self.rotate_position == 1:
            self.use_position_horizontal()

    def make_rotated(self):
        block = SBlock(self.copy_boxes(), self.factory, prepared_boxes=True)
        block.rotate_position = self.rotate_position
        block.rotate()
        return block

    def use_position_vertical(self):
        row = self.boxes[1].row
        col = self.boxes[1].col
        self.boxes[0].row = row - 1
        self.boxes[0].col = col
        self.boxes[2].row = row
        self.boxes[2].col = col + 1
        self.boxes[3].row = row + 1
        self.boxes[3].col = col + 1

    def use_position_horizontal(self):
        row = self.boxes[1].row
        col = self.boxes[1].col
        self.boxes[0].row = row
        self.boxes[0].col = col + 1
        self.boxes[2].row = row + 1
        self.boxes[2].col = col
        self.boxes[3].row = row + 1
        self.boxes[3].col = col - 1


class LBlock(Block):
    required_boxes = 4
    max_rotate_positions = 4
    kind = 'L'

    def prepare_boxes(self, boxes):
        boxes[1].row = boxes[0].row + 1
        boxes[1].col = boxes[0].col
        boxes[2].row = boxes[0].row + 2
        boxes[2].col = boxes[0].col
        boxes[3].row = boxes[0].row + 2
        boxes[3].col = boxes[0].col + 1

    def is_right_position(self):
        return self.rotate_position == 0

    def is_bottom_position(self):
        return self.rotate_position == 1

    def is_left_position(self):
        return self.rotate_position == 2

    def is_top_position(self):
        return self.rotate_position == 3

    def get_top_box(self):
        if self.is_top_position() or self.is_right_position():
            return self.boxes[0]
        elif self.is_bottom_position() or self.is_left_position():
            return self.boxes[2]

    def get_bottom_box(self):
        return self.get_bottom_boxes()[0]

    def get_left_box(self):
        if self.is_left_position() or self.is_bottom_position():
            return self.boxes[3]
        elif self.is_top_position() or self.is_right_position():
            return self.boxes[0]

    def get_right_box(self):
        if self.is_left_position() or self.is_bottom_position():
            return self.boxes[0]
        elif self.is_top_position() or self.is_right_position():
            return self.boxes[3]

    def get_bottom_boxes(self):
        if self.is_bottom_position():
            return [self.boxes[3]]
        elif self.is_left_position():
            return [self.boxes[0]]
        elif self.is_right_position():
            return [self.boxes[2], self.boxes[3]]
        elif self.is_top_position():
            return self.boxes[:3]

    def rotate(self):
        self.rotate_position += 1
        if self.rotate_position == self.max_rotate_positions:
            self.rotate_position = 0

        if self.rotate_position == 0:
            self.use_right_position()
        elif self.rotate_position == 1:
            self.use_bottom_position()
        elif self.rotate_position == 2:
            self.use_left_position()
        elif self.rotate_position == 3:
            self.use_top_position()

    def make_rotated(self):
        block = LBlock(self.copy_boxes(), self.factory, prepared_boxes=True)
        block.rotate_position = self.rotate_position
        block.rotate()
        return block

    def use_top_position(self):
        """
        Example:
                [3]
          [0][1][2]
        """
        row = self.boxes[1].row
        col = self.boxes[1].col
        self.boxes[0].row = row
        self.boxes[0].col = col - 1
        self.boxes[2].row = row
        self.boxes[2].col = col + 1
        self.boxes[3].row = row - 1
        self.boxes[3].col = col + 1

    def use_bottom_position(self):
        """
        Example:
            [2][1][0]
            [3]
        """
        row = self.boxes[1].row
        col = self.boxes[1].col
        self.boxes[0].row = row
        self.boxes[0].col = col + 1
        self.boxes[2].row = row
        self.boxes[2].col = col - 1
        self.boxes[3].row = row + 1
        self.boxes[3].col = col - 1

    def use_left_position(self):
        """
        Example:
            [3][2]
               [1]
               [0]
        """
        row = self.boxes[1].row
        col = self.boxes[1].col
        self.boxes[0].row = row + 1
        self.boxes[0].col = col
        self.boxes[2].row = row - 1
        self.boxes[2].col = col
        self.boxes[3].row = row - 1
        self.boxes[3].col = col - 1

    def use_right_position(self):
        """
        Example:
           [0]
           [1]
           [2][3]
        """
        row = self.boxes[1].row
        col = self.boxes[1].col
        self.boxes[0].row = row - 1
        self.boxes[0].col = col
        self.boxes[2].row = row + 1
        self.boxes[2].col = col
        self.boxes[3].row = row + 1
        self.boxes[3].col = col + 1


class BigBlock(Block):
    required_boxes = 4
    kind = 'O'

    def prepare_boxes(self, boxes):
        row = boxes[0].row
        col = boxes[0].col
        boxes[1].row = row
        boxes[1].col = col + 1
        boxes[2].row = row + 1
        boxes[2].col = col
        boxes[3].row = row + 1
        boxes[3].col = col + 1

    def get_top_box(self):
        return self.boxes[0]

    def get_bottom_box(self):
        return self.boxes[3]

    def get_left_box(self):
        return self.boxes[2]

    def get_right_box(self):
        return self.boxes[3]

    def get_bottom_boxes(self):
        return [self.boxes[2], self.boxes[3]]

    def rotate(self):
        pass

    def make_rotated(self):
        return self


class UnitAccumulator:

    def __init__(self, unit):
        self.real_value = 0
        self.unit = unit

    def inc(self, delta):
        self.real_value += delta

    def take_value(self):
        value = self.real_value // self.unit
        if value:
            self.real_value -= value * self.unit
        return int(value)


def create_board(get_level):
    return Board(
        block_factories=[
            BlockFactory(
                BigBlock,
                COLOR_BIG_BLOCK,
                BOX_SIZE,
                get_gravity,
                PLAYER_SPEED
            ),
            BlockFactory(
                LongBlock,
                COLOR_LONG_BLOCK,
                BOX_SIZE,
                get_gravity,
                PLAYER_SPEED
            ),
            BlockFactory(
                TBlock,
                COLOR_T_BLOCK,
                BOX_SIZE,
                get_gravity,
                PLAYER_SPEED
            ),
            BlockFactory(
                LBlock,
                COLOR_L_BLOCK,
                BOX_SIZE,
                get_gravity,
                PLAYER_SPEED
            ),
            BlockFactory(
                SBlock,
                COLOR_S_BLOCK,
                BOX_SIZE,
                get_gravity,
                PLAYER_SPEED
            ),
            BlockFactory(
                ZBlock,
                COLOR_Z_BLOCK,
                BOX_SIZE,
                get_gravity,
                PLAYER_SPEED
            ),
        ],
        get_level=get_level
    )


if __name__ == '__main__':
    container = ActivityContainer(WINDOW_WIDTH, WINDOW_HEIGHT, 'Tetris')
    container.run_activity(TetrisActivity())
