from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import random

import pygame
import psycopg2

from db import SnakeDatabase
from ui import (
    Button,
    TextInput,
    draw_label,
    draw_multiline_label,
    draw_panel,
    draw_progress_bar,
    draw_title,
)


BASE_DIR = Path(__file__).resolve().parent
SETTINGS_PATH = BASE_DIR / "settings.json"

SCREEN_WIDTH = 980
SCREEN_HEIGHT = 720
BOARD_SIZE = 576
CELL_SIZE = 24
GRID_COLS = BOARD_SIZE // CELL_SIZE
GRID_ROWS = BOARD_SIZE // CELL_SIZE
BOARD_RECT = pygame.Rect(32, 88, BOARD_SIZE, BOARD_SIZE)
SIDEBAR_RECT = pygame.Rect(640, 88, 308, 576)

BACKGROUND = (24, 28, 38)
BOARD_BACKGROUND = (31, 35, 46)
GRID_COLOR = (48, 54, 69)
OUTLINE = (89, 98, 114)
TEXT_DARK = (24, 28, 36)
SNAKE_HEAD = (240, 248, 255)
FOOD_COLORS = {
    1: (255, 192, 72),
    2: (98, 215, 124),
    3: (90, 184, 255),
}
POISON_COLOR = (136, 33, 44)
OBSTACLE_COLOR = (92, 98, 115)
POWERUP_COLORS = {
    "speed": (255, 173, 75),
    "slow": (112, 196, 255),
    "shield": (146, 225, 220),
}

DEFAULT_SETTINGS = {
    "snake_color": [78, 204, 122],
    "grid_on": True,
    "sound_on": False,
}

DIRECTION_VECTORS = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
}
OPPOSITE_DIRECTIONS = {
    "up": "down",
    "down": "up",
    "left": "right",
    "right": "left",
}


@dataclass
class FoodItem:
    position: tuple[int, int]
    points: int
    color: tuple[int, int, int]
    expires_at: int


@dataclass
class FieldPowerup:
    kind: str
    position: tuple[int, int]
    expires_at: int


class SnakeSession:
    def __init__(self, settings, username, personal_best, start_ticks):
        self.settings = settings
        self.username = username
        self.personal_best = personal_best
        self.reset(start_ticks)

    def reset(self, start_ticks):
        center = (GRID_COLS // 2, GRID_ROWS // 2)
        self.snake = [center, (center[0] - 1, center[1]), (center[0] - 2, center[1])]
        self.direction = "right"
        self.pending_direction = "right"
        self.score = 0
        self.level = 1
        self.foods_eaten = 0
        self.obstacles = set()
        self.food = None
        self.poison_food = None
        self.field_powerup = None
        self.active_powerup = None
        self.next_powerup_spawn_at = start_ticks + 7000
        self.last_move_at = start_ticks
        self.status_message = "Eat food, avoid walls, and climb the leaderboard."
        self.status_until = start_ticks + 2200

    def set_status(self, message, now, duration=2200):
        self.status_message = message
        self.status_until = now + duration

    def current_status(self, now):
        return self.status_message if now <= self.status_until else ""

    def snake_color(self):
        raw = self.settings.get("snake_color", DEFAULT_SETTINGS["snake_color"])
        return tuple(int(max(0, min(255, value))) for value in raw)

    def current_power_name(self):
        if not self.active_powerup:
            return "None"
        return self.active_powerup["kind"].title()

    def current_power_timer(self, now):
        if not self.active_powerup:
            return "-"
        if self.active_powerup["ends_at"] is None:
            return "Until hit"
        remaining = max(0, self.active_powerup["ends_at"] - now)
        return f"{remaining / 1000:.1f}s"

    def current_step_delay(self):
        delay = max(70, 170 - (self.level - 1) * 10)
        if self.active_powerup:
            if self.active_powerup["kind"] == "speed":
                delay = max(45, delay - 55)
            elif self.active_powerup["kind"] == "slow":
                delay += 70
        return delay

    def progress_ratio(self):
        return (self.foods_eaten % 5) / 5

    def queue_direction(self, direction):
        if direction not in DIRECTION_VECTORS:
            return
        if OPPOSITE_DIRECTIONS[direction] == self.direction and len(self.snake) > 1:
            return
        self.pending_direction = direction

    def in_bounds(self, cell):
        x, y = cell
        return 0 <= x < GRID_COLS and 0 <= y < GRID_ROWS

    def random_free_cell(self, blocked=None):
        used = set(self.snake) | set(self.obstacles)
        if self.food is not None:
            used.add(self.food.position)
        if self.poison_food is not None:
            used.add(self.poison_food)
        if self.field_powerup is not None:
            used.add(self.field_powerup.position)
        if blocked:
            used |= set(blocked)

        free_cells = [
            (x, y)
            for y in range(GRID_ROWS)
            for x in range(GRID_COLS)
            if (x, y) not in used
        ]
        return random.choice(free_cells) if free_cells else None

    def spawn_food(self, now):
        points = random.choices([1, 2, 3], weights=[0.6, 0.28, 0.12], k=1)[0]
        position = self.random_free_cell()
        if position is None:
            return
        self.food = FoodItem(
            position=position,
            points=points,
            color=FOOD_COLORS[points],
            expires_at=now + random.randint(5000, 8500),
        )

    def spawn_poison(self):
        position = self.random_free_cell()
        if position is not None:
            self.poison_food = position

    def spawn_powerup(self, now):
        position = self.random_free_cell()
        if position is None:
            return
        kind = random.choice(["speed", "slow", "shield"])
        self.field_powerup = FieldPowerup(
            kind=kind,
            position=position,
            expires_at=now + 8000,
        )

    def build_obstacles(self):
        self.obstacles = set()
        if self.level < 3:
            return

        head_x, head_y = self.snake[0]
        reserved = set(self.snake)
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                reserved.add((head_x + dx, head_y + dy))

        target_blocks = min(8 + self.level * 2, 28)
        attempts = 0
        while len(self.obstacles) < target_blocks and attempts < target_blocks * 30:
            attempts += 1
            orientation = random.choice(["single", "horizontal", "vertical"])
            length = 1 if orientation == "single" else random.randint(2, 3)
            start = (
                random.randint(1, GRID_COLS - 2),
                random.randint(1, GRID_ROWS - 2),
            )

            cells = []
            for index in range(length):
                x, y = start
                if orientation == "horizontal":
                    x += index
                elif orientation == "vertical":
                    y += index
                cell = (x, y)
                if not self.in_bounds(cell):
                    cells = []
                    break
                cells.append(cell)

            if not cells:
                continue
            if any(cell in reserved or cell in self.obstacles for cell in cells):
                continue
            self.obstacles.update(cells)

    def ensure_spawns(self, now):
        if self.food is None or now >= self.food.expires_at:
            self.spawn_food(now)
        if self.poison_food is None:
            self.spawn_poison()
        if self.field_powerup is not None and now >= self.field_powerup.expires_at:
            self.field_powerup = None
            self.next_powerup_spawn_at = now + 4500
        if self.field_powerup is None and now >= self.next_powerup_spawn_at:
            self.spawn_powerup(now)
            self.next_powerup_spawn_at = now + random.randint(9000, 13000)

    def update_active_powerup(self, now):
        if self.active_powerup and self.active_powerup["ends_at"] is not None:
            if now >= self.active_powerup["ends_at"]:
                expired = self.active_powerup["kind"].title()
                self.active_powerup = None
                self.set_status(f"{expired} expired.", now, 1500)

    def trigger_shield(self, now):
        if self.active_powerup and self.active_powerup["kind"] == "shield":
            self.active_powerup = None
            self.set_status("Shield blocked the collision.", now, 1800)
            return True
        return False

    def activate_powerup(self, kind, now):
        if kind == "shield":
            self.active_powerup = {"kind": kind, "ends_at": None}
            self.set_status("Shield ready. One crash can be ignored.", now)
        else:
            self.active_powerup = {"kind": kind, "ends_at": now + 5000}
            if kind == "speed":
                self.set_status("Speed boost for 5 seconds.", now)
            else:
                self.set_status("Slow motion for 5 seconds.", now)

    def game_over_payload(self):
        return {
            "username": self.username,
            "score": self.score,
            "level": self.level,
            "personal_best": max(self.personal_best, self.score),
        }

    def handle_level_up(self, now):
        if self.foods_eaten and self.foods_eaten % 5 == 0:
            self.level += 1
            self.build_obstacles()
            self.food = None
            self.poison_food = None
            self.field_powerup = None
            self.next_powerup_spawn_at = now + 3000
            self.set_status(f"Level {self.level}. Obstacles changed.", now, 2200)

    def update(self, now):
        self.ensure_spawns(now)
        self.update_active_powerup(now)

        if now - self.last_move_at < self.current_step_delay():
            return None

        self.last_move_at = now
        self.direction = self.pending_direction
        vector = DIRECTION_VECTORS[self.direction]
        next_head = (self.snake[0][0] + vector[0], self.snake[0][1] + vector[1])

        collision = (
            not self.in_bounds(next_head)
            or next_head in self.obstacles
            or next_head in self.snake[:-1]
        )
        if collision:
            if self.trigger_shield(now):
                return None
            return self.game_over_payload()

        self.snake.insert(0, next_head)

        if self.food and next_head == self.food.position:
            gained_score = self.food.points * 10
            self.score += gained_score
            self.foods_eaten += 1
            self.food = None
            self.personal_best = max(self.personal_best, self.score)
            self.set_status(f"Food eaten. +{gained_score} score.", now, 1300)
            self.handle_level_up(now)
            return None

        if self.poison_food and next_head == self.poison_food:
            self.poison_food = None
            for _ in range(3):
                if self.snake:
                    self.snake.pop()
            self.score = max(0, self.score - 15)
            if len(self.snake) <= 1:
                return self.game_over_payload()
            self.set_status("Poison food! Snake lost 2 segments.", now, 1800)
            return None

        if self.field_powerup and next_head == self.field_powerup.position:
            powerup_kind = self.field_powerup.kind
            self.field_powerup = None
            self.next_powerup_spawn_at = now + 10000
            self.activate_powerup(powerup_kind, now)

        self.snake.pop()
        self.personal_best = max(self.personal_best, self.score)
        return None

    def draw_board(self, screen):
        pygame.draw.rect(screen, BOARD_BACKGROUND, BOARD_RECT, border_radius=18)
        pygame.draw.rect(screen, OUTLINE, BOARD_RECT, 2, border_radius=18)

        if self.settings.get("grid_on", True):
            for row in range(GRID_ROWS + 1):
                y = BOARD_RECT.top + row * CELL_SIZE
                pygame.draw.line(screen, GRID_COLOR, (BOARD_RECT.left, y), (BOARD_RECT.right, y), 1)
            for col in range(GRID_COLS + 1):
                x = BOARD_RECT.left + col * CELL_SIZE
                pygame.draw.line(screen, GRID_COLOR, (x, BOARD_RECT.top), (x, BOARD_RECT.bottom), 1)

        for cell in self.obstacles:
            self.draw_cell(screen, cell, OBSTACLE_COLOR, inset=2, border_radius=0)

        if self.food is not None:
            self.draw_cell(screen, self.food.position, self.food.color, inset=4, border_radius=0)
            self.draw_food_value(screen, self.food)

        if self.poison_food is not None:
            self.draw_cell(screen, self.poison_food, POISON_COLOR, inset=4, border_radius=0)

        if self.field_powerup is not None:
            self.draw_cell(screen, self.field_powerup.position, POWERUP_COLORS[self.field_powerup.kind], inset=4, border_radius=0)
            self.draw_powerup_mark(screen, self.field_powerup)

        body_color = self.snake_color()
        for index, cell in enumerate(self.snake):
            color = SNAKE_HEAD if index == 0 else body_color
            self.draw_cell(screen, cell, color, inset=3 if index == 0 else 4, border_radius=0)

    def draw_cell(self, screen, cell, color, inset=4, border_radius=6):
        x = BOARD_RECT.left + cell[0] * CELL_SIZE + inset
        y = BOARD_RECT.top + cell[1] * CELL_SIZE + inset
        size = CELL_SIZE - inset * 2
        rect = pygame.Rect(x, y, size, size)
        pygame.draw.rect(screen, color, rect, border_radius=border_radius)

    def draw_food_value(self, screen, food):
        font = pygame.font.SysFont("Verdana", 12, bold=True)
        label = font.render(str(food.points), True, (20, 20, 20))
        center_x = BOARD_RECT.left + food.position[0] * CELL_SIZE + CELL_SIZE // 2
        center_y = BOARD_RECT.top + food.position[1] * CELL_SIZE + CELL_SIZE // 2
        screen.blit(label, label.get_rect(center=(center_x, center_y)))

    def draw_powerup_mark(self, screen, powerup):
        font = pygame.font.SysFont("Verdana", 12, bold=True)
        mark = {
            "speed": "S",
            "slow": "M",
            "shield": "H",
        }[powerup.kind]
        label = font.render(mark, True, (20, 20, 20))
        center_x = BOARD_RECT.left + powerup.position[0] * CELL_SIZE + CELL_SIZE // 2
        center_y = BOARD_RECT.top + powerup.position[1] * CELL_SIZE + CELL_SIZE // 2
        screen.blit(label, label.get_rect(center=(center_x, center_y)))

    def draw_sidebar(self, screen, fonts, now):
        draw_panel(screen, SIDEBAR_RECT, alpha=220)
        left = SIDEBAR_RECT.left + 18
        right = SIDEBAR_RECT.right - 18

        draw_label(screen, fonts["subtitle"], self.username[:18], (left, SIDEBAR_RECT.top + 18), TEXT_DARK)
        draw_label(screen, fonts["body"], f"Score: {self.score}", (left, SIDEBAR_RECT.top + 56), TEXT_DARK)
        draw_label(screen, fonts["body"], f"Level: {self.level}", (left, SIDEBAR_RECT.top + 82), TEXT_DARK)
        draw_label(screen, fonts["body"], f"Best: {self.personal_best}", (left, SIDEBAR_RECT.top + 108), TEXT_DARK)
        draw_label(screen, fonts["body"], f"Power: {self.current_power_name()}", (left, SIDEBAR_RECT.top + 134), TEXT_DARK)
        draw_label(screen, fonts["body"], f"Timer: {self.current_power_timer(now)}", (left, SIDEBAR_RECT.top + 160), TEXT_DARK)

        draw_label(screen, fonts["subtitle"], "Level Progress", (left, SIDEBAR_RECT.top + 212), TEXT_DARK)
        progress_rect = pygame.Rect(left, SIDEBAR_RECT.top + 244, right - left, 16)
        draw_progress_bar(screen, progress_rect, self.progress_ratio(), (99, 204, 147))
        draw_label(screen, fonts["small"], f"Food eaten: {self.foods_eaten}", (left, SIDEBAR_RECT.top + 268), TEXT_DARK)

        draw_label(screen, fonts["subtitle"], "Status", (left, SIDEBAR_RECT.top + 320), TEXT_DARK)
        status = self.current_status(now) or "Stay alive and keep moving."
        draw_multiline_label(screen, fonts["body"], status, (left, SIDEBAR_RECT.top + 352), right - left, TEXT_DARK, line_gap=0)

        draw_label(screen, fonts["subtitle"], "Legend", (left, SIDEBAR_RECT.top + 434), TEXT_DARK)
        legend = [
            ("Food", "1 / 2 / 3 points, disappears on timer."),
            ("Poison", "Shortens snake by 2."),
            ("Speed", "Moves faster for 5 seconds."),
            ("Slow", "Moves slower for 5 seconds."),
            ("Shield", "Ignores one crash."),
        ]
        y = SIDEBAR_RECT.top + 468
        for title, description in legend:
            draw_label(screen, fonts["body"], title, (left, y), TEXT_DARK)
            draw_multiline_label(screen, fonts["small"], description, (left + 70, y + 2), right - left - 74, TEXT_DARK, line_gap=0)
            y += 36

    def draw(self, screen, fonts, now):
        self.draw_board(screen)
        self.draw_sidebar(screen, fonts, now)


class SnakeApp:
    def __init__(self):
        pygame.init()
        self.base_dir = BASE_DIR
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("TSIS4 Snake")
        self.clock = pygame.time.Clock()
        self.fonts = {
            "title": pygame.font.SysFont("Verdana", 34, bold=True),
            "subtitle": pygame.font.SysFont("Verdana", 20, bold=True),
            "body": pygame.font.SysFont("Verdana", 16),
            "small": pygame.font.SysFont("Verdana", 12),
        }

        self.settings = self.load_settings()
        self.db = SnakeDatabase()
        self.db_available = True
        self.db_message = "Database ready."
        try:
            self.db.init_db()
        except (OSError, psycopg2.Error) as error:
            self.db_available = False
            self.db_message = f"Database unavailable: {error.__class__.__name__}"

        self.state = "menu"
        self.running = True
        self.session = None
        self.last_result = None
        self.leaderboard = []
        self.info_message = ""
        self.info_until = 0
        self.username_input = TextInput(
            self.centered_rect(190, 320, 46),
            text="Player",
            placeholder="Enter username",
            max_length=16,
        )

    def centered_rect(self, y, width, height):
        return pygame.Rect((SCREEN_WIDTH - width) // 2, y, width, height)

    def load_settings(self):
        if not SETTINGS_PATH.exists():
            return DEFAULT_SETTINGS.copy()
        try:
            payload = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return DEFAULT_SETTINGS.copy()

        settings = DEFAULT_SETTINGS.copy()
        if isinstance(payload, dict):
            color = payload.get("snake_color", settings["snake_color"])
            if isinstance(color, list) and len(color) == 3:
                settings["snake_color"] = [int(max(0, min(255, value))) for value in color]
            settings["grid_on"] = bool(payload.get("grid_on", settings["grid_on"]))
            settings["sound_on"] = bool(payload.get("sound_on", settings["sound_on"]))
        return settings

    def save_settings(self):
        SETTINGS_PATH.write_text(json.dumps(self.settings, indent=2), encoding="utf-8")

    def set_info(self, message, duration=2200):
        self.info_message = message
        self.info_until = pygame.time.get_ticks() + duration

    def menu_buttons(self):
        center_x = SCREEN_WIDTH // 2 - 110
        return {
            "play": Button(pygame.Rect(center_x, 302, 220, 44), "Play"),
            "leaderboard": Button(pygame.Rect(center_x, 356, 220, 44), "Leaderboard"),
            "settings": Button(pygame.Rect(center_x, 410, 220, 44), "Settings"),
            "quit": Button(pygame.Rect(center_x, 464, 220, 44), "Quit"),
        }

    def settings_buttons(self):
        panel = self.centered_rect(130, 420, 434)
        buttons = {
            "grid": Button(pygame.Rect(panel.left + 182, 172, 160, 38), f"Grid: {'On' if self.settings['grid_on'] else 'Off'}"),
            "sound": Button(pygame.Rect(panel.left + 182, 220, 160, 38), f"Sound: {'On' if self.settings['sound_on'] else 'Off'}"),
            "save": Button(pygame.Rect(panel.left + 112, 510, 196, 40), "Save & Back"),
        }

        y_positions = {"r": 326, "g": 370, "b": 414}
        for channel, y in y_positions.items():
            buttons[f"{channel}_minus"] = Button(pygame.Rect(panel.left + 182, y, 48, 36), "-")
            buttons[f"{channel}_plus"] = Button(pygame.Rect(panel.left + 294, y, 48, 36), "+")
        return buttons

    def leaderboard_buttons(self):
        return {"back": Button(self.centered_rect(624, 200, 40), "Back")}

    def game_over_buttons(self):
        left = SCREEN_WIDTH // 2 - 150
        return {
            "retry": Button(pygame.Rect(left, 516, 136, 40), "Retry"),
            "menu": Button(pygame.Rect(left + 164, 516, 136, 40), "Main Menu"),
        }

    def start_game(self):
        username = self.username_input.text.strip()[:16] or "Player"
        personal_best = 0
        start_ticks = pygame.time.get_ticks()
        if self.db_available:
            try:
                personal_best = self.db.fetch_personal_best(username)
            except psycopg2.Error as error:
                self.db_available = False
                self.db_message = f"Database unavailable: {error.__class__.__name__}"
        self.session = SnakeSession(self.settings.copy(), username, personal_best, start_ticks)
        self.last_result = None
        self.state = "game"

    def finish_game(self, result):
        if self.db_available:
            try:
                self.db.save_session(result["username"], result["score"], result["level"])
                result["personal_best"] = self.db.fetch_personal_best(result["username"])
            except psycopg2.Error as error:
                self.db_available = False
                self.db_message = f"Database unavailable: {error.__class__.__name__}"
                self.set_info("Result saved only locally this run.", 2600)
        self.last_result = result
        self.session = None
        self.state = "game_over"

    def open_leaderboard(self):
        if self.db_available:
            try:
                self.leaderboard = self.db.fetch_top_scores(10)
            except psycopg2.Error as error:
                self.db_available = False
                self.db_message = f"Database unavailable: {error.__class__.__name__}"
                self.leaderboard = []
        else:
            self.leaderboard = []
        self.state = "leaderboard"

    def change_color_channel(self, channel_index, delta):
        self.settings["snake_color"][channel_index] = max(
            0,
            min(255, self.settings["snake_color"][channel_index] + delta),
        )

    def handle_menu_event(self, event):
        result = self.username_input.handle_event(event)
        if result == "submit":
            self.start_game()
            return

        buttons = self.menu_buttons()
        if buttons["play"].is_clicked(event):
            self.start_game()
        elif buttons["leaderboard"].is_clicked(event):
            self.open_leaderboard()
        elif buttons["settings"].is_clicked(event):
            self.state = "settings"
        elif buttons["quit"].is_clicked(event):
            self.running = False

    def handle_settings_event(self, event):
        buttons = self.settings_buttons()
        if buttons["grid"].is_clicked(event):
            self.settings["grid_on"] = not self.settings["grid_on"]
        elif buttons["sound"].is_clicked(event):
            self.settings["sound_on"] = not self.settings["sound_on"]
        elif buttons["r_minus"].is_clicked(event):
            self.change_color_channel(0, -15)
        elif buttons["r_plus"].is_clicked(event):
            self.change_color_channel(0, 15)
        elif buttons["g_minus"].is_clicked(event):
            self.change_color_channel(1, -15)
        elif buttons["g_plus"].is_clicked(event):
            self.change_color_channel(1, 15)
        elif buttons["b_minus"].is_clicked(event):
            self.change_color_channel(2, -15)
        elif buttons["b_plus"].is_clicked(event):
            self.change_color_channel(2, 15)
        elif buttons["save"].is_clicked(event):
            self.save_settings()
            self.set_info("Settings saved.", 1800)
            self.state = "menu"

    def handle_leaderboard_event(self, event):
        if self.leaderboard_buttons()["back"].is_clicked(event):
            self.state = "menu"

    def handle_game_over_event(self, event):
        buttons = self.game_over_buttons()
        if buttons["retry"].is_clicked(event):
            self.start_game()
        elif buttons["menu"].is_clicked(event):
            self.state = "menu"

    def handle_game_event(self, event):
        if event.type != pygame.KEYDOWN or self.session is None:
            return
        if event.key in (pygame.K_UP, pygame.K_w):
            self.session.queue_direction("up")
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.session.queue_direction("down")
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            self.session.queue_direction("left")
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self.session.queue_direction("right")

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.state == "game":
                self.state = "menu"
                self.session = None
            elif self.state != "menu":
                self.state = "menu"
            return

        if self.state == "menu":
            self.handle_menu_event(event)
        elif self.state == "settings":
            self.handle_settings_event(event)
        elif self.state == "leaderboard":
            self.handle_leaderboard_event(event)
        elif self.state == "game_over":
            self.handle_game_over_event(event)
        elif self.state == "game":
            self.handle_game_event(event)

    def draw_background(self):
        self.screen.fill(BACKGROUND)
        for stripe in range(0, SCREEN_WIDTH, 120):
            rect = pygame.Rect(stripe, 0, 60, SCREEN_HEIGHT)
            overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 6))
            self.screen.blit(overlay, rect.topleft)

    def draw_info_message(self):
        if pygame.time.get_ticks() > self.info_until or not self.info_message:
            return
        rect = pygame.Rect(32, 24, 916, 42)
        draw_panel(self.screen, rect, alpha=205)
        draw_label(self.screen, self.fonts["body"], self.info_message, (48, 37), TEXT_DARK)

    def draw_menu(self):
        self.draw_background()
        draw_title(self.screen, self.fonts["title"], "TSIS4 Snake", 76)
        panel = self.centered_rect(146, 420, 402)
        draw_panel(self.screen, panel, alpha=220)

        draw_label(self.screen, self.fonts["subtitle"], "Username", (panel.left + 34, 160), TEXT_DARK)
        draw_multiline_label(
            self.screen,
            self.fonts["body"],
            "Enter a username before playing. Your best score is loaded from PostgreSQL.",
            (panel.left + 34, 248),
            352,
            TEXT_DARK,
            line_gap=1,
        )
        self.username_input.draw(self.screen, self.fonts["body"])

        draw_label(self.screen, self.fonts["small"], self.db_message, (panel.left + 34, 530), TEXT_DARK)

        mouse_pos = pygame.mouse.get_pos()
        for button in self.menu_buttons().values():
            button.draw(self.screen, self.fonts["body"], mouse_pos)

    def draw_settings(self):
        self.draw_background()
        draw_title(self.screen, self.fonts["title"], "Settings", 76)
        panel = self.centered_rect(130, 420, 434)
        draw_panel(self.screen, panel, alpha=222)

        draw_label(self.screen, self.fonts["subtitle"], "Preferences", (panel.left + 20, 140), TEXT_DARK)
        draw_label(self.screen, self.fonts["body"], "Grid overlay", (panel.left + 20, 180), TEXT_DARK)
        draw_label(self.screen, self.fonts["body"], "Sound", (panel.left + 20, 228), TEXT_DARK)
        draw_label(self.screen, self.fonts["subtitle"], "Snake Color (RGB)", (panel.left + 20, 280), TEXT_DARK)

        labels = [("R", 326, self.settings["snake_color"][0]), ("G", 370, self.settings["snake_color"][1]), ("B", 414, self.settings["snake_color"][2])]
        for letter, y, value in labels:
            draw_label(self.screen, self.fonts["body"], f"{letter}: {value}", (panel.left + 20, y + 8), TEXT_DARK)

        preview_rect = pygame.Rect(panel.left + 20, 465, 76, 36)
        pygame.draw.rect(self.screen, tuple(self.settings["snake_color"]), preview_rect, border_radius=10)
        pygame.draw.rect(self.screen, OUTLINE, preview_rect, 2, border_radius=10)
        draw_label(self.screen, self.fonts["small"], "Preview", (panel.left + 112, 475), TEXT_DARK)

        mouse_pos = pygame.mouse.get_pos()
        buttons = self.settings_buttons()
        buttons["grid"].draw(self.screen, self.fonts["body"], mouse_pos, active=self.settings["grid_on"])
        buttons["sound"].draw(self.screen, self.fonts["body"], mouse_pos, active=self.settings["sound_on"])
        buttons["save"].draw(self.screen, self.fonts["body"], mouse_pos)

        for key in ("r_minus", "r_plus", "g_minus", "g_plus", "b_minus", "b_plus"):
            buttons[key].draw(self.screen, self.fonts["body"], mouse_pos)

    def draw_leaderboard(self):
        self.draw_background()
        draw_title(self.screen, self.fonts["title"], "Top 10 Scores", 76)
        panel = self.centered_rect(126, 760, 510)
        draw_panel(self.screen, panel, alpha=224)

        headers = [("#", 26), ("Player", 82), ("Score", 300), ("Level", 412), ("Date", 510)]
        for label, offset in headers:
            draw_label(self.screen, self.fonts["subtitle"], label, (panel.left + offset, 156), TEXT_DARK)

        if not self.db_available:
            draw_multiline_label(
                self.screen,
                self.fonts["body"],
                self.db_message,
                (panel.left + 36, 246),
                680,
                TEXT_DARK,
                line_gap=1,
            )
        elif not self.leaderboard:
            draw_label(self.screen, self.fonts["body"], "No scores saved yet.", (panel.left + 36, 246), TEXT_DARK)
        else:
            y = 196
            for index, entry in enumerate(self.leaderboard, start=1):
                username, score, level_reached, played_at = entry
                date_text = played_at.strftime("%Y-%m-%d %H:%M") if isinstance(played_at, datetime) else str(played_at)
                draw_label(self.screen, self.fonts["body"], str(index), (panel.left + 26, y), TEXT_DARK)
                draw_label(self.screen, self.fonts["body"], str(username)[:16], (panel.left + 82, y), TEXT_DARK)
                draw_label(self.screen, self.fonts["body"], str(score), (panel.left + 300, y), TEXT_DARK)
                draw_label(self.screen, self.fonts["body"], str(level_reached), (panel.left + 420, y), TEXT_DARK)
                draw_label(self.screen, self.fonts["small"], date_text, (panel.left + 510, y + 2), TEXT_DARK)
                y += 30

        mouse_pos = pygame.mouse.get_pos()
        self.leaderboard_buttons()["back"].draw(self.screen, self.fonts["body"], mouse_pos)

    def draw_game_over(self):
        self.draw_background()
        draw_title(self.screen, self.fonts["title"], "Game Over", 76)
        panel = self.centered_rect(160, 420, 322)
        draw_panel(self.screen, panel, alpha=222)

        result = self.last_result or {
            "username": self.username_input.text.strip() or "Player",
            "score": 0,
            "level": 1,
            "personal_best": 0,
        }
        draw_label(self.screen, self.fonts["subtitle"], f"Player: {result['username']}", (panel.left + 30, 198), TEXT_DARK)
        draw_label(self.screen, self.fonts["body"], f"Score: {result['score']}", (panel.left + 30, 238), TEXT_DARK)
        draw_label(self.screen, self.fonts["body"], f"Level reached: {result['level']}", (panel.left + 30, 266), TEXT_DARK)
        draw_label(self.screen, self.fonts["body"], f"Personal best: {result['personal_best']}", (panel.left + 30, 294), TEXT_DARK)
        draw_multiline_label(
            self.screen,
            self.fonts["body"],
            "Results are saved automatically after each run when the database is available.",
            (panel.left + 30, 340),
            340,
            TEXT_DARK,
            line_gap=1,
        )

        mouse_pos = pygame.mouse.get_pos()
        for button in self.game_over_buttons().values():
            button.draw(self.screen, self.fonts["body"], mouse_pos)

    def draw_game(self):
        self.draw_background()
        draw_title(self.screen, self.fonts["title"], "Snake Run", 44)
        if self.session is not None:
            self.session.draw(self.screen, self.fonts, pygame.time.get_ticks())
        hint = "Arrow keys or WASD to move. Esc returns to menu."
        draw_label(self.screen, self.fonts["small"], hint, (32, 676), (216, 222, 232))

    def draw(self):
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "settings":
            self.draw_settings()
        elif self.state == "leaderboard":
            self.draw_leaderboard()
        elif self.state == "game_over":
            self.draw_game_over()
        elif self.state == "game":
            self.draw_game()

        self.draw_info_message()
        pygame.display.flip()

    def run(self):
        while self.running:
            self.clock.tick(60)
            for event in pygame.event.get():
                self.handle_event(event)

            if self.state == "game" and self.session is not None:
                result = self.session.update(pygame.time.get_ticks())
                if result is not None:
                    self.finish_game(result)

            self.draw()

        pygame.quit()
