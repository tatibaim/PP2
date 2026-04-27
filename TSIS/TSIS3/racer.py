from dataclasses import dataclass, field
from pathlib import Path
import random

import pygame

from persistence import (
    add_leaderboard_entry,
    load_leaderboard,
    load_settings,
    save_settings,
)
from ui import (
    Button,
    TextInput,
    draw_label,
    draw_multiline_label,
    draw_panel,
    draw_progress_bar,
    draw_title,
)


SCREEN_WIDTH = 760
SCREEN_HEIGHT = 600
ROAD_WIDTH = 400
ROAD_RECT = pygame.Rect((SCREEN_WIDTH - ROAD_WIDTH) // 2, 0, ROAD_WIDTH, SCREEN_HEIGHT)
LANE_COUNT = 3
LANE_WIDTH = ROAD_RECT.width / LANE_COUNT
PLAYER_Y = SCREEN_HEIGHT - 40

ROAD_EDGE = (35, 35, 40)
ROAD_LINE = (245, 245, 245)
BACKGROUND_COLOR = (22, 26, 34)
SIDEBAR_COLOR = (28, 33, 43)
ACCENT = (112, 196, 255)

CAR_COLORS = {
    "blue": (70, 130, 255),
    "red": (230, 80, 80),
    "green": (60, 190, 95),
    "yellow": (245, 195, 72),
    "white": (245, 245, 245),
}

DIFFICULTY_PROFILES = {
    "easy": {
        "base_speed": 260,
        "finish_distance": 1800,
        "traffic_interval": 1.45,
        "hazard_interval": 2.1,
        "event_interval": 3.3,
        "powerup_interval": 6.0,
        "coin_interval": 0.85,
    },
    "normal": {
        "base_speed": 300,
        "finish_distance": 2400,
        "traffic_interval": 1.2,
        "hazard_interval": 1.8,
        "event_interval": 3.0,
        "powerup_interval": 5.4,
        "coin_interval": 0.75,
    },
    "hard": {
        "base_speed": 340,
        "finish_distance": 3000,
        "traffic_interval": 1.0,
        "hazard_interval": 1.55,
        "event_interval": 2.7,
        "powerup_interval": 4.8,
        "coin_interval": 0.65,
    },
}


@dataclass
class RoadEntity:
    kind: str
    surface: pygame.Surface
    x: float
    y: float
    lane: int | None = None
    speed_offset: float = 0.0
    ttl: float = 0.0
    value: int = 0
    vx: float = 0.0
    data: dict = field(default_factory=dict)
    rect: pygame.Rect = field(init=False)

    def __post_init__(self):
        self.rect = self.surface.get_rect(topleft=(int(self.x), int(self.y)))

    def sync_rect(self):
        self.rect.topleft = (int(self.x), int(self.y))


def load_image(path, size, alpha=True):
    file_path = Path(path)
    if file_path.exists():
        image = pygame.image.load(str(file_path))
        image = image.convert_alpha() if alpha else image.convert()
        return pygame.transform.smoothscale(image, size)

    flags = pygame.SRCALPHA if alpha else 0
    surface = pygame.Surface(size, flags)
    surface.fill((180, 180, 180))
    pygame.draw.rect(surface, (80, 80, 80), surface.get_rect(), 3)
    return surface


def tint_surface(base_surface, tint_color):
    tinted = pygame.Surface(base_surface.get_size(), pygame.SRCALPHA)
    tint_r, tint_g, tint_b = tint_color

    for x in range(base_surface.get_width()):
        for y in range(base_surface.get_height()):
            red, green, blue, alpha = base_surface.get_at((x, y))
            if alpha == 0:
                continue

            brightness = max(red, green, blue)
            if brightness < 55:
                tinted.set_at((x, y), (red, green, blue, alpha))
                continue

            shade = brightness / 255
            tinted.set_at(
                (x, y),
                (
                    int(tint_r * shade),
                    int(tint_g * shade),
                    int(tint_b * shade),
                    alpha,
                ),
            )

    return tinted


def make_barrier_surface(size):
    surface = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.rect(surface, (232, 133, 42), surface.get_rect(), border_radius=6)
    pygame.draw.rect(surface, (255, 240, 120), surface.get_rect(), 3, border_radius=6)
    for index in range(0, size[0], 18):
        pygame.draw.line(surface, (255, 235, 180), (index, size[1]), (index + 16, 0), 4)
    return surface


def make_oil_surface(size):
    surface = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.ellipse(surface, (20, 20, 24, 220), pygame.Rect(0, 6, size[0], size[1] - 12))
    pygame.draw.ellipse(surface, (45, 45, 52, 180), pygame.Rect(10, 0, size[0] - 20, size[1]))
    return surface


def make_pothole_surface(size):
    surface = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.circle(surface, (25, 25, 25), (size[0] // 2, size[1] // 2), size[0] // 2)
    pygame.draw.circle(surface, (55, 55, 55), (size[0] // 2, size[1] // 2), size[0] // 2, 3)
    return surface


def make_speed_bump_surface(size):
    surface = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.rect(surface, (242, 193, 76), surface.get_rect(), border_radius=8)
    pygame.draw.rect(surface, (60, 60, 60), surface.get_rect(), 2, border_radius=8)
    for x in range(8, size[0] - 6, 18):
        pygame.draw.line(surface, (50, 50, 50), (x, 4), (x + 8, size[1] - 4), 3)
    return surface


def make_nitro_strip_surface(size):
    surface = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.rect(surface, (55, 165, 255), surface.get_rect(), border_radius=8)
    for x in range(6, size[0] - 8, 16):
        pygame.draw.line(surface, (220, 245, 255), (x, 5), (x, size[1] - 5), 3)
    return surface


def make_powerup_surface(label, fill):
    surface = pygame.Surface((40, 40), pygame.SRCALPHA)
    pygame.draw.circle(surface, fill, (20, 20), 18)
    pygame.draw.circle(surface, (255, 255, 255), (20, 20), 18, 2)
    font = pygame.font.SysFont("Verdana", 20, bold=True)
    text = font.render(label, True, (255, 255, 255))
    text_rect = text.get_rect(center=(20, 20))
    surface.blit(text, text_rect)
    return surface


def load_sound(path):
    try:
        return pygame.mixer.Sound(str(path))
    except pygame.error:
        return None


class GameSession:
    def __init__(self, assets, settings, username, play_sound_callback):
        self.assets = assets
        self.settings = settings
        self.username = username
        self.play_sound = play_sound_callback
        self.profile = DIFFICULTY_PROFILES[settings["difficulty"]]
        self.reset()

    def reset(self):
        self.player_surface = self.assets["player_variants"][self.settings["car_color"]]
        self.player_rect = self.player_surface.get_rect(midbottom=(ROAD_RECT.centerx, PLAYER_Y))
        self.player_x = float(self.player_rect.x)
        self.horizontal_speed = 280.0
        self.distance = 0.0
        self.finish_distance = self.profile["finish_distance"]
        self.coins = 0
        self.score = 0
        self.bonus_score = 0
        self.next_speed_threshold = 10
        self.coin_speed_bonus = 0
        self.road_scroll = 0.0
        self.traffic = []
        self.coins_on_road = []
        self.hazards = []
        self.powerups = []
        self.traffic_timer = self.profile["traffic_interval"]
        self.hazard_timer = self.profile["hazard_interval"]
        self.event_timer = self.profile["event_interval"]
        self.powerup_timer = self.profile["powerup_interval"]
        self.coin_timer = self.profile["coin_interval"]
        self.active_powerup = None
        self.event_boost_timer = 0.0
        self.slow_timer = 0.0
        self.skid_timer = 0.0
        self.skid_direction = 1
        self.status_message = "Collect coins, watch lanes, and reach the finish line."
        self.status_timer = 3.0

    def lane_x(self, lane, surface_width):
        lane_center = ROAD_RECT.left + lane * LANE_WIDTH + LANE_WIDTH / 2
        return lane_center - surface_width / 2

    def current_lane(self):
        relative_x = self.player_rect.centerx - ROAD_RECT.left
        lane = int(relative_x // LANE_WIDTH)
        return max(0, min(LANE_COUNT - 1, lane))

    def progress_ratio(self):
        return min(1.0, self.distance / self.finish_distance) if self.finish_distance else 0.0

    def set_status(self, message, duration=2.0):
        self.status_message = message
        self.status_timer = duration

    def get_spawnable_lanes(self, include_player_lane=True):
        lanes = []
        occupied = self.traffic + self.hazards + self.powerups

        for lane in range(LANE_COUNT):
            if not include_player_lane and lane == self.current_lane():
                continue

            blocked = False
            for entity in occupied:
                if entity.lane == lane and entity.y < 150:
                    blocked = True
                    break
            if not blocked:
                lanes.append(lane)
        return lanes

    def create_lane_entity(self, kind, lane, surface, y, **kwargs):
        return RoadEntity(
            kind=kind,
            surface=surface,
            x=self.lane_x(lane, surface.get_width()),
            y=y,
            lane=lane,
            **kwargs,
        )

    def spawn_coin_group(self):
        lanes = self.get_spawnable_lanes(include_player_lane=True)
        if not lanes:
            return

        chosen_lanes = random.sample(lanes, k=min(len(lanes), random.randint(1, 2)))
        coin_pool = [
            ("bronze", self.assets["coins"]["bronze"], 1),
            ("silver", self.assets["coins"]["silver"], 2),
            ("gold", self.assets["coins"]["gold"], 3),
        ]

        for lane in chosen_lanes:
            steps = random.randint(1, 3)
            for index in range(steps):
                name, surface, value = random.choices(
                    coin_pool,
                    weights=[0.55, 0.3, 0.15],
                    k=1,
                )[0]
                entity = self.create_lane_entity(
                    kind=f"coin_{name}",
                    lane=lane,
                    surface=surface,
                    y=-60 - index * 75,
                    value=value,
                )
                self.coins_on_road.append(entity)

    def spawn_traffic(self):
        lanes = self.get_spawnable_lanes(include_player_lane=self.distance > 200)
        if not lanes:
            return

        spawn_count = 1
        if self.progress_ratio() > 0.55 and len(lanes) > 1 and random.random() < 0.35:
            spawn_count = 2

        for lane in random.sample(lanes, k=min(spawn_count, len(lanes))):
            surface = random.choice(self.assets["traffic_variants"])
            speed_offset = random.randint(35, 90)
            entity = self.create_lane_entity(
                kind="traffic",
                lane=lane,
                surface=surface,
                y=-surface.get_height() - random.randint(0, 120),
                speed_offset=speed_offset,
            )
            self.traffic.append(entity)

    def spawn_hazard_wave(self):
        safe_lane = random.randrange(LANE_COUNT)
        hazard_lanes = [lane for lane in range(LANE_COUNT) if lane != safe_lane]
        random.shuffle(hazard_lanes)

        count = 1 if self.progress_ratio() < 0.3 else 2
        options = [
            ("oil", self.assets["hazards"]["oil"]),
            ("barrier", self.assets["hazards"]["barrier"]),
            ("pothole", self.assets["hazards"]["pothole"]),
        ]
        if self.progress_ratio() > 0.25:
            options.append(("slow_zone", self.assets["hazards"]["speed_bump"]))

        for lane in hazard_lanes[:count]:
            kind, surface = random.choice(options)
            entity = self.create_lane_entity(
                kind=kind,
                lane=lane,
                surface=surface,
                y=-surface.get_height() - random.randint(0, 80),
            )
            self.hazards.append(entity)

    def spawn_road_event(self):
        event_roll = random.choice(["moving_barrier", "speed_bump", "nitro_strip"])

        if event_roll == "moving_barrier":
            surface = self.assets["hazards"]["moving_barrier"]
            x = ROAD_RECT.left + 15
            entity = RoadEntity(
                kind="moving_barrier",
                surface=surface,
                x=x,
                y=-surface.get_height(),
                speed_offset=55,
                vx=150,
            )
            self.hazards.append(entity)
            return

        lanes = self.get_spawnable_lanes(include_player_lane=True)
        if not lanes:
            return

        lane = random.choice(lanes)
        if event_roll == "speed_bump":
            surface = self.assets["hazards"]["speed_bump"]
            kind = "slow_zone"
        else:
            surface = self.assets["hazards"]["nitro_strip"]
            kind = "nitro_strip"

        entity = self.create_lane_entity(
            kind=kind,
            lane=lane,
            surface=surface,
            y=-surface.get_height(),
        )
        self.hazards.append(entity)

    def spawn_powerup(self):
        lanes = self.get_spawnable_lanes(include_player_lane=True)
        if not lanes:
            return

        lane = random.choice(lanes)
        powerup_type = random.choice(["nitro", "shield", "repair"])
        surface = self.assets["powerups"][powerup_type]
        entity = self.create_lane_entity(
            kind=f"powerup_{powerup_type}",
            lane=lane,
            surface=surface,
            y=-surface.get_height(),
            ttl=7.0,
        )
        self.powerups.append(entity)

    def collect_coin(self, entity):
        self.play_sound("coin")
        self.coins += entity.value
        self.bonus_score += entity.value * 6
        if self.coins >= self.next_speed_threshold:
            self.coin_speed_bonus += 26
            self.next_speed_threshold += 10
            self.set_status("Traffic speed increased. Stay sharp!", 2.2)

    def activate_powerup(self, powerup_type):
        self.bonus_score += 35
        if powerup_type == "repair":
            cleared = self.apply_repair()
            if cleared:
                self.set_status("Repair cleared danger ahead.", 2.0)
            else:
                self.set_status("Repair tuned the car and removed slow effects.", 2.0)
            return

        if powerup_type == "nitro":
            self.active_powerup = {"type": "nitro", "remaining": 4.2}
            self.set_status("Nitro online for a few seconds.", 2.0)
            return

        if powerup_type == "shield":
            self.active_powerup = {"type": "shield", "remaining": None}
            self.set_status("Shield armed. One crash can be absorbed.", 2.0)

    def apply_repair(self):
        lane = self.current_lane()
        candidates = []
        for entity in self.traffic + self.hazards:
            if entity.lane == lane or entity.rect.colliderect(self.player_rect.inflate(90, 120)):
                distance = abs(entity.rect.centery - self.player_rect.centery)
                candidates.append((distance, entity))

        if candidates:
            _, entity = min(candidates, key=lambda item: item[0])
            if entity in self.traffic:
                self.traffic.remove(entity)
            elif entity in self.hazards:
                self.hazards.remove(entity)
            self.bonus_score += 80
            return True

        self.slow_timer = 0.0
        self.skid_timer = 0.0
        self.event_boost_timer = max(0.6, self.event_boost_timer)
        return False

    def absorb_collision(self, entity):
        if self.active_powerup and self.active_powerup["type"] == "shield":
            self.active_powerup = None
            self.bonus_score += 60
            if entity in self.traffic:
                self.traffic.remove(entity)
            elif entity in self.hazards:
                self.hazards.remove(entity)
            self.set_status("Shield absorbed the impact.", 2.0)
            return True
        return False

    def finish_result(self, won):
        if won:
            self.bonus_score += 250
            result_text = "Finished"
        else:
            result_text = "Crash"

        self.update_score()
        return {
            "name": self.username,
            "score": int(self.score),
            "distance": int(self.distance),
            "coins": self.coins,
            "difficulty": self.settings["difficulty"],
            "result": result_text,
            "won": won,
        }

    def update_player(self, dt, pressed_keys):
        control_multiplier = 0.45 if self.skid_timer > 0 else 1.0
        move_amount = self.horizontal_speed * control_multiplier * dt

        if pressed_keys[pygame.K_LEFT] or pressed_keys[pygame.K_a]:
            self.player_x -= move_amount
        if pressed_keys[pygame.K_RIGHT] or pressed_keys[pygame.K_d]:
            self.player_x += move_amount

        if self.skid_timer > 0:
            self.player_x += self.skid_direction * 110 * dt

        min_x = ROAD_RECT.left + 10
        max_x = ROAD_RECT.right - self.player_rect.width - 10
        self.player_rect.x = int(self.player_x)

        if self.player_x < min_x or self.player_x > max_x:
            return self.finish_result(False)

        return None

    def current_speed(self):
        profile_bonus = self.progress_ratio() * 110
        speed = self.profile["base_speed"] + self.coin_speed_bonus + profile_bonus

        if self.slow_timer > 0:
            speed *= 0.72

        if self.active_powerup and self.active_powerup["type"] == "nitro":
            speed += 165

        if self.event_boost_timer > 0:
            speed += 85

        return speed

    def update_entities(self, dt):
        speed = self.current_speed()
        self.road_scroll = (self.road_scroll + speed * dt) % SCREEN_HEIGHT
        self.distance += speed * dt * 0.11

        for entity in self.coins_on_road + self.powerups + self.hazards + self.traffic:
            entity.y += (speed + entity.speed_offset) * dt
            entity.x += entity.vx * dt

            if entity.kind == "moving_barrier":
                if entity.x <= ROAD_RECT.left + 10 or entity.x + entity.rect.width >= ROAD_RECT.right - 10:
                    entity.vx *= -1
                    entity.x = max(ROAD_RECT.left + 10, min(ROAD_RECT.right - entity.rect.width - 10, entity.x))

            if entity.ttl:
                entity.ttl -= dt

            entity.sync_rect()

        self.coins_on_road = [entity for entity in self.coins_on_road if entity.y < SCREEN_HEIGHT + 40]
        self.traffic = [entity for entity in self.traffic if entity.y < SCREEN_HEIGHT + 80]
        self.hazards = [
            entity
            for entity in self.hazards
            if entity.y < SCREEN_HEIGHT + 80 and (entity.ttl == 0 or entity.ttl > 0)
        ]
        self.powerups = [
            entity
            for entity in self.powerups
            if entity.y < SCREEN_HEIGHT + 40 and entity.ttl > 0
        ]

    def handle_collectibles(self):
        for entity in self.coins_on_road[:]:
            if self.player_rect.colliderect(entity.rect):
                self.collect_coin(entity)
                self.coins_on_road.remove(entity)

        for entity in self.powerups[:]:
            if self.player_rect.colliderect(entity.rect):
                self.play_sound("coin")
                powerup_type = entity.kind.split("_", 1)[1]
                self.activate_powerup(powerup_type)
                self.powerups.remove(entity)

    def handle_hazards(self):
        for entity in self.hazards[:]:
            if not self.player_rect.colliderect(entity.rect):
                continue

            if entity.kind in {"barrier", "pothole", "moving_barrier"}:
                if self.absorb_collision(entity):
                    continue
                return self.finish_result(False)

            if entity.kind == "oil":
                self.skid_timer = 1.4
                self.skid_direction = random.choice([-1, 1])
                self.hazards.remove(entity)
                self.set_status("Oil spill. Steering is sliding!", 1.7)
                continue

            if entity.kind == "slow_zone":
                self.slow_timer = 1.5
                self.hazards.remove(entity)
                self.set_status("Speed bump ahead. Pace dropped.", 1.7)
                continue

            if entity.kind == "nitro_strip":
                self.event_boost_timer = 1.8
                self.bonus_score += 20
                self.hazards.remove(entity)
                self.set_status("Nitro strip launched a short boost.", 1.7)

        for entity in self.traffic[:]:
            if self.player_rect.colliderect(entity.rect):
                if self.absorb_collision(entity):
                    continue
                return self.finish_result(False)

        return None

    def update_timers(self, dt):
        if self.status_timer > 0:
            self.status_timer = max(0.0, self.status_timer - dt)
        if self.slow_timer > 0:
            self.slow_timer = max(0.0, self.slow_timer - dt)
        if self.skid_timer > 0:
            self.skid_timer = max(0.0, self.skid_timer - dt)
        if self.event_boost_timer > 0:
            self.event_boost_timer = max(0.0, self.event_boost_timer - dt)

        if self.active_powerup and self.active_powerup["remaining"] is not None:
            self.active_powerup["remaining"] = max(0.0, self.active_powerup["remaining"] - dt)
            if self.active_powerup["remaining"] == 0:
                self.active_powerup = None
                self.set_status("Nitro expired. Back to base pace.", 1.5)

    def update_spawns(self, dt):
        scale = 1.0 - self.progress_ratio() * 0.35

        self.traffic_timer -= dt
        self.hazard_timer -= dt
        self.event_timer -= dt
        self.powerup_timer -= dt
        self.coin_timer -= dt

        if self.traffic_timer <= 0:
            self.spawn_traffic()
            self.traffic_timer = max(0.55, self.profile["traffic_interval"] * scale)

        if self.hazard_timer <= 0:
            self.spawn_hazard_wave()
            self.hazard_timer = max(0.9, self.profile["hazard_interval"] * scale)

        if self.event_timer <= 0:
            self.spawn_road_event()
            self.event_timer = max(1.7, self.profile["event_interval"] * scale)

        if self.powerup_timer <= 0:
            self.spawn_powerup()
            self.powerup_timer = max(3.5, self.profile["powerup_interval"] * (0.85 + random.random() * 0.25))

        if self.coin_timer <= 0:
            self.spawn_coin_group()
            self.coin_timer = max(0.45, self.profile["coin_interval"] * (0.8 + random.random() * 0.4))

    def update_score(self):
        self.score = int(self.coins * 30 + self.distance * 0.85 + self.bonus_score)

    def update(self, dt, pressed_keys):
        self.update_timers(dt)
        boundary_result = self.update_player(dt, pressed_keys)
        if boundary_result:
            return boundary_result
        self.update_spawns(dt)
        self.update_entities(dt)
        self.handle_collectibles()

        hazard_result = self.handle_hazards()
        if hazard_result:
            return hazard_result

        self.update_score()
        if self.distance >= self.finish_distance:
            return self.finish_result(True)
        return None

    def draw_road(self, screen):
        screen.fill(BACKGROUND_COLOR)

        background = self.assets["road_background"]
        y_offset = int(self.road_scroll)
        screen.blit(background, (ROAD_RECT.left, y_offset - SCREEN_HEIGHT))
        screen.blit(background, (ROAD_RECT.left, y_offset))

        pygame.draw.rect(screen, ROAD_EDGE, ROAD_RECT, 4)

    def draw_entity_list(self, screen, entities):
        for entity in entities:
            screen.blit(entity.surface, entity.rect)

    def draw(self, screen, fonts):
        self.draw_road(screen)
        self.draw_entity_list(screen, self.hazards)
        self.draw_entity_list(screen, self.traffic)
        self.draw_entity_list(screen, self.coins_on_road)
        self.draw_entity_list(screen, self.powerups)

        screen.blit(self.player_surface, self.player_rect)
        if self.active_powerup and self.active_powerup["type"] == "shield":
            pygame.draw.ellipse(screen, (100, 210, 255), self.player_rect.inflate(20, 14), 3)

        left_x = 12
        right_x = ROAD_RECT.right + 12
        sidebar_width = ROAD_RECT.left - 24
        top_y = 14
        bottom_y = SCREEN_HEIGHT - 186

        left_top_panel = pygame.Rect(left_x, top_y, sidebar_width, 124)
        right_top_panel = pygame.Rect(right_x, top_y, sidebar_width, 124)
        left_bottom_panel = pygame.Rect(left_x, bottom_y, sidebar_width, 172)
        right_bottom_panel = pygame.Rect(right_x, 148, sidebar_width, 438)

        draw_panel(screen, left_top_panel, alpha=212)
        draw_panel(screen, right_top_panel, alpha=212)
        draw_panel(screen, left_bottom_panel, alpha=212)
        draw_panel(screen, right_bottom_panel, alpha=212)

        header_font = fonts["subtitle"]
        body_font = fonts["body"]
        small_font = fonts["small"]

        left_text_x = left_top_panel.left + 12
        right_text_x = right_top_panel.left + 12

        draw_label(screen, header_font, self.username[:12], (left_text_x, left_top_panel.top + 10), (20, 24, 31))
        draw_label(screen, small_font, f"Score {self.score}", (left_text_x, left_top_panel.top + 42), (20, 24, 31))
        draw_label(screen, small_font, f"Coins {self.coins}", (left_text_x, left_top_panel.top + 64), (20, 24, 31))
        draw_label(screen, small_font, f"Speed {int(self.current_speed())}", (left_text_x, left_top_panel.top + 86), (20, 24, 31))

        power_name = "None"
        power_info = "-"
        if self.active_powerup:
            power_name = self.active_powerup["type"].title()
            if self.active_powerup["remaining"] is None:
                power_info = "Until hit"
            else:
                power_info = f"{self.active_powerup['remaining']:.1f}s"

        draw_label(screen, header_font, f"{int(self.distance)} m", (right_text_x, right_top_panel.top + 10), (20, 24, 31))
        draw_label(
            screen,
            small_font,
            f"Remain {max(0, int(self.finish_distance - self.distance))} m",
            (right_text_x, right_top_panel.top + 42),
            (20, 24, 31),
        )
        draw_label(screen, small_font, f"Power {power_name}", (right_text_x, right_top_panel.top + 64), (20, 24, 31))
        draw_label(screen, small_font, f"Timer {power_info}", (right_text_x, right_top_panel.top + 86), (20, 24, 31))

        draw_label(screen, body_font, "Status", (left_bottom_panel.left + 12, left_bottom_panel.top + 10), (20, 24, 31))
        draw_multiline_label(
            screen,
            small_font,
            self.status_message,
            (left_bottom_panel.left + 12, left_bottom_panel.top + 40),
            sidebar_width - 24,
            (20, 24, 31),
            line_gap=0,
        )

        draw_label(screen, body_font, "Run", (left_bottom_panel.left + 12, left_bottom_panel.top + 86), (20, 24, 31))
        draw_label(
            screen,
            small_font,
            f"Mode {self.settings['difficulty'].title()}",
            (left_bottom_panel.left + 12, left_bottom_panel.top + 108),
            (20, 24, 31),
        )
        draw_label(
            screen,
            small_font,
            f"Bonus {self.bonus_score}",
            (left_bottom_panel.left + 12, left_bottom_panel.top + 126),
            (20, 24, 31),
        )

        draw_label(screen, small_font, "Finish", (left_bottom_panel.left + 12, left_bottom_panel.top + 144), (20, 24, 31))
        progress_rect = pygame.Rect(left_bottom_panel.left + 12, left_bottom_panel.top + 158, sidebar_width - 24, 14)
        draw_progress_bar(screen, progress_rect, self.progress_ratio(), ACCENT)

        draw_label(screen, body_font, "Legend", (right_bottom_panel.left + 12, right_bottom_panel.top + 10), (20, 24, 31))
        legend_entries = [
            (self.assets["coins"]["gold"], "Coin", "Coins help score and speed."),
            (self.assets["hazards"]["barrier"], "Barrier", "Crash if you hit it."),
            (self.assets["hazards"]["oil"], "Oil", "Makes steering slide."),
            (self.assets["hazards"]["speed_bump"], "Bump", "Slows the car briefly."),
            (self.assets["hazards"]["nitro_strip"], "Nitro Strip", "Gives a short boost."),
            (self.assets["powerups"]["shield"], "Shield", "Blocks one crash."),
            (self.assets["powerups"]["nitro"], "Nitro", "Adds extra speed."),
            (self.assets["powerups"]["repair"], "Repair", "Clears nearby danger."),
        ]

        legend_y = right_bottom_panel.top + 38
        for surface, title, description in legend_entries:
            icon = pygame.transform.smoothscale(surface, (24, 24))
            icon_rect = icon.get_rect(topleft=(right_bottom_panel.left + 12, legend_y + 4))
            screen.blit(icon, icon_rect)
            draw_label(screen, small_font, title, (right_bottom_panel.left + 44, legend_y), (20, 24, 31))
            draw_multiline_label(
                screen,
                fonts["small"],
                description,
                (right_bottom_panel.left + 44, legend_y + 14),
                sidebar_width - 56,
                (20, 24, 31),
                line_gap=0,
            )
            legend_y += 48


class RacerApp:
    def __init__(self):
        pygame.init()
        self.base_dir = Path(__file__).resolve().parent
        self._setup_audio()
        self.settings = load_settings(self.base_dir)
        if not self.audio_available:
            self.settings["sound_on"] = False

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("TSIS3 Racer")
        self.clock = pygame.time.Clock()
        self.assets = self.load_assets()
        self.fonts = {
            "title": pygame.font.SysFont("Verdana", 30, bold=True),
            "subtitle": pygame.font.SysFont("Verdana", 18, bold=True),
            "body": pygame.font.SysFont("Verdana", 15),
            "small": pygame.font.SysFont("Verdana", 12),
        }
        if self.assets.get("icon") is not None:
            pygame.display.set_icon(self.assets["icon"])

        self.leaderboard = load_leaderboard(self.base_dir)
        self.state = "menu"
        self.running = True
        self.menu_scroll = 0.0
        self.name_input = TextInput(
            self.centered_rect(248, 290, 46),
            text=self.settings.get("last_username", "Player"),
            placeholder="Enter driver name",
        )
        self.current_game = None
        self.last_result = None
        self.sync_music()

    def centered_rect(self, y, width, height):
        return pygame.Rect((SCREEN_WIDTH - width) // 2, y, width, height)

    def _setup_audio(self):
        try:
            pygame.mixer.init()
            self.audio_available = True
        except pygame.error:
            self.audio_available = False

    def load_assets(self):
        image_dir = self.base_dir / "image"
        sound_dir = self.base_dir / "sound"

        road_background = load_image(image_dir / "AnimatedStreet.png", ROAD_RECT.size, alpha=False)
        player_base = load_image(image_dir / "Player.png", (56, 96))
        enemy_base = load_image(image_dir / "Enemy.png", (56, 96))
        icon = load_image(image_dir / "icon.png", (64, 64)) if (image_dir / "icon.png").exists() else None

        player_variants = {
            color_name: tint_surface(player_base, tint)
            for color_name, tint in CAR_COLORS.items()
        }

        traffic_variants = [
            tint_surface(enemy_base, tint)
            for tint in ((200, 90, 90), (100, 140, 255), (95, 200, 120), (220, 210, 90))
        ]

        assets = {
            "road_background": road_background,
            "player_variants": player_variants,
            "traffic_variants": traffic_variants,
            "coins": {
                "bronze": load_image(image_dir / "bronze_coin.png", (28, 28)),
                "silver": load_image(image_dir / "silver_coin.png", (28, 28)),
                "gold": load_image(image_dir / "golden_coin.png", (28, 28)),
            },
            "hazards": {
                "barrier": make_barrier_surface((82, 26)),
                "moving_barrier": make_barrier_surface((126, 24)),
                "oil": make_oil_surface((74, 38)),
                "pothole": make_pothole_surface((40, 40)),
                "speed_bump": make_speed_bump_surface((90, 22)),
                "nitro_strip": make_nitro_strip_surface((96, 22)),
            },
            "powerups": {
                "nitro": make_powerup_surface("N", (72, 149, 255)),
                "shield": make_powerup_surface("S", (80, 205, 210)),
                "repair": make_powerup_surface("R", (255, 172, 82)),
            },
            "sounds": {
                "background": load_sound(sound_dir / "background.wav") if self.audio_available else None,
                "coin": load_sound(sound_dir / "lost_money.wav") if self.audio_available else None,
                "crash": load_sound(sound_dir / "crash.wav") if self.audio_available else None,
            },
            "icon": icon,
        }
        return assets

    def play_sound(self, sound_name):
        if not self.settings.get("sound_on") or not self.audio_available:
            return
        sound = self.assets["sounds"].get(sound_name)
        if sound is not None:
            sound.play()

    def sync_music(self):
        if not self.audio_available:
            return

        background = self.assets["sounds"].get("background") if hasattr(self, "assets") else None
        if background is None:
            return

        if self.settings.get("sound_on"):
            if background.get_num_channels() == 0:
                background.play(loops=-1)
            background.set_volume(0.25)
        else:
            background.stop()

    def save_current_settings(self):
        save_settings(self.base_dir, self.settings)
        self.sync_music()

    def start_game(self):
        username = self.name_input.text.strip() or "Player"
        self.settings["last_username"] = username
        self.save_current_settings()
        self.current_game = GameSession(self.assets, self.settings, username, self.play_sound)
        self.last_result = None
        self.state = "game"

    def finish_game(self, result):
        self.play_sound("crash" if not result["won"] else "coin")
        self.last_result = result
        self.leaderboard = add_leaderboard_entry(self.base_dir, result)
        self.state = "game_over"
        self.current_game = None

    def menu_buttons(self):
        center_x = SCREEN_WIDTH // 2 - 110
        return {
            "play": Button(pygame.Rect(center_x, 282, 220, 42), "Play"),
            "leaderboard": Button(pygame.Rect(center_x, 334, 220, 42), "Leaderboard"),
            "settings": Button(pygame.Rect(center_x, 386, 220, 42), "Settings"),
            "quit": Button(pygame.Rect(center_x, 438, 220, 42), "Quit"),
        }

    def name_entry_buttons(self):
        left = SCREEN_WIDTH // 2 - 145
        return {
            "start": Button(pygame.Rect(left, 316, 130, 40), "Start Race"),
            "back": Button(pygame.Rect(left + 160, 316, 130, 40), "Back"),
        }

    def settings_buttons(self):
        panel = self.centered_rect(116, 360, 460)
        buttons = {
            "sound": Button(pygame.Rect(panel.left + 85, 155, 190, 40), f"Sound: {'On' if self.settings['sound_on'] else 'Off'}"),
            "back": Button(pygame.Rect(panel.left + 65, 522, 230, 40), "Back to Menu"),
        }

        x = panel.left + 20
        for difficulty in ("easy", "normal", "hard"):
            buttons[f"difficulty_{difficulty}"] = Button(
                pygame.Rect(x, 240, 100, 38),
                difficulty.title(),
            )
            x += 110

        for index, color_name in enumerate(CAR_COLORS):
            row = index // 3
            column = index % 3
            buttons[f"color_{color_name}"] = Button(
                pygame.Rect(panel.left + 20 + column * 110, 330 + row * 46, 100, 38),
                color_name.title(),
            )
        return buttons

    def leaderboard_buttons(self):
        return {"back": Button(self.centered_rect(546, 220, 40), "Back to Menu")}

    def game_over_buttons(self):
        left = SCREEN_WIDTH // 2 - 150
        return {
            "retry": Button(pygame.Rect(left, 438, 135, 40), "Retry"),
            "menu": Button(pygame.Rect(left + 165, 438, 135, 40), "Main Menu"),
        }

    def handle_menu_event(self, event):
        buttons = self.menu_buttons()
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_p):
                self.state = "name_entry"
                return
            if event.key == pygame.K_l:
                self.leaderboard = load_leaderboard(self.base_dir)
                self.state = "leaderboard"
                return
            if event.key == pygame.K_s:
                self.state = "settings"
                return
            if event.key == pygame.K_q:
                self.running = False
                return

        if buttons["play"].is_clicked(event):
            self.state = "name_entry"
        elif buttons["leaderboard"].is_clicked(event):
            self.leaderboard = load_leaderboard(self.base_dir)
            self.state = "leaderboard"
        elif buttons["settings"].is_clicked(event):
            self.state = "settings"
        elif buttons["quit"].is_clicked(event):
            self.running = False

    def handle_name_entry_event(self, event):
        result = self.name_input.handle_event(event)
        if result == "submit":
            self.start_game()
            return

        buttons = self.name_entry_buttons()
        if buttons["start"].is_clicked(event):
            self.start_game()
        elif buttons["back"].is_clicked(event):
            self.state = "menu"

    def handle_settings_event(self, event):
        buttons = self.settings_buttons()
        if buttons["sound"].is_clicked(event):
            self.settings["sound_on"] = not self.settings["sound_on"]
            self.save_current_settings()
            return

        for difficulty in ("easy", "normal", "hard"):
            if buttons[f"difficulty_{difficulty}"].is_clicked(event):
                self.settings["difficulty"] = difficulty
                self.save_current_settings()
                return

        for color_name in CAR_COLORS:
            if buttons[f"color_{color_name}"].is_clicked(event):
                self.settings["car_color"] = color_name
                self.save_current_settings()
                return

        if buttons["back"].is_clicked(event):
            self.state = "menu"

    def handle_leaderboard_event(self, event):
        buttons = self.leaderboard_buttons()
        if buttons["back"].is_clicked(event):
            self.state = "menu"

    def handle_game_over_event(self, event):
        buttons = self.game_over_buttons()
        if buttons["retry"].is_clicked(event):
            self.start_game()
        elif buttons["menu"].is_clicked(event):
            self.state = "menu"

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.state == "game":
                self.state = "menu"
                self.current_game = None
            elif self.state != "menu":
                self.state = "menu"
            return

        if self.state == "menu":
            self.handle_menu_event(event)
        elif self.state == "name_entry":
            self.handle_name_entry_event(event)
        elif self.state == "settings":
            self.handle_settings_event(event)
        elif self.state == "leaderboard":
            self.handle_leaderboard_event(event)
        elif self.state == "game_over":
            self.handle_game_over_event(event)

    def draw_scene_background(self):
        self.menu_scroll = (self.menu_scroll + 2.8) % SCREEN_HEIGHT
        self.screen.fill(BACKGROUND_COLOR)
        pygame.draw.rect(self.screen, (26, 29, 35), ROAD_RECT)
        bg = self.assets["road_background"]
        offset = int(self.menu_scroll)
        self.screen.blit(bg, (ROAD_RECT.left, offset - SCREEN_HEIGHT))
        self.screen.blit(bg, (ROAD_RECT.left, offset))

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((12, 16, 24, 110))
        self.screen.blit(overlay, (0, 0))

    def draw_menu(self):
        self.draw_scene_background()
        info_panel = self.centered_rect(88, 360, 120)
        buttons_panel = self.centered_rect(250, 300, 250)

        draw_panel(self.screen, info_panel, alpha=214)
        draw_panel(self.screen, buttons_panel, alpha=214)
        divider_x = info_panel.left + 180
        pygame.draw.line(self.screen, (124, 132, 144), (divider_x, 102), (divider_x, 188), 1)

        mouse_pos = pygame.mouse.get_pos()
        for button in self.menu_buttons().values():
            button.draw(self.screen, self.fonts["body"], mouse_pos)

        player_preview = pygame.transform.smoothscale(
            self.assets["player_variants"][self.settings["car_color"]],
            (40, 68),
        )
        player_preview_rect = player_preview.get_rect(center=(info_panel.left + 32, 140))
        self.screen.blit(player_preview, player_preview_rect)

        best_entry = self.leaderboard[0] if self.leaderboard else None

        left_col = info_panel.left + 64
        right_col = info_panel.left + 196
        draw_label(self.screen, self.fonts["subtitle"], "Driver", (left_col, 106), (20, 24, 31))
        draw_label(
            self.screen,
            self.fonts["body"],
            self.settings.get("last_username", "Player"),
            (left_col, 132),
            (20, 24, 31),
        )
        draw_label(
            self.screen,
            self.fonts["small"],
            f"Difficulty: {self.settings['difficulty'].title()}",
            (left_col, 152),
            (20, 24, 31),
        )
        draw_label(
            self.screen,
            self.fonts["small"],
            f"Car color: {self.settings['car_color'].title()}",
            (left_col, 168),
            (20, 24, 31),
        )
        draw_label(
            self.screen,
            self.fonts["small"],
            f"Sound: {'On' if self.settings['sound_on'] else 'Off'}",
            (left_col, 182),
            (20, 24, 31),
        )

        draw_label(self.screen, self.fonts["subtitle"], "Best Run", (right_col, 106), (20, 24, 31))
        if best_entry:
            draw_label(
                self.screen,
                self.fonts["body"],
                best_entry["name"][:12],
                (right_col, 132),
                (20, 24, 31),
            )
            draw_label(
                self.screen,
                self.fonts["small"],
                f"Score: {best_entry['score']}",
                (right_col, 152),
                (20, 24, 31),
            )
            draw_label(
                self.screen,
                self.fonts["small"],
                f"Distance: {best_entry['distance']} m",
                (right_col, 168),
                (20, 24, 31),
            )
        else:
            draw_label(
                self.screen,
                self.fonts["small"],
                "No runs saved yet.",
                (right_col, 142),
                (20, 24, 31),
            )
            draw_label(
                self.screen,
                self.fonts["small"],
                "Finish one to create a record.",
                (right_col, 158),
                (20, 24, 31),
            )


    def draw_name_entry(self):
        self.draw_scene_background()
        draw_title(self.screen, self.fonts["title"], "Driver Name", 86)
        panel = self.centered_rect(168, 350, 220)
        draw_panel(self.screen, panel, alpha=214)
        draw_multiline_label(
            self.screen,
            self.fonts["body"],
            "Enter the name that should appear in the top 10 leaderboard.",
            (panel.left + 13, 180),
            320,
            (20, 24, 31),
            line_gap=1,
        )
        draw_label(
            self.screen,
            self.fonts["small"],
            "Press Enter to start right away.",
            (panel.left + 13, 230),
            (20, 24, 31),
        )
        self.name_input.draw(self.screen, self.fonts["body"])

        mouse_pos = pygame.mouse.get_pos()
        for button in self.name_entry_buttons().values():
            button.draw(self.screen, self.fonts["body"], mouse_pos)

    def draw_settings(self):
        self.draw_scene_background()
        draw_title(self.screen, self.fonts["title"], "Settings", 76)
        panel = self.centered_rect(116, 360, 460)
        draw_panel(self.screen, panel, alpha=220)

        draw_label(self.screen, self.fonts["subtitle"], "Sound", (panel.left + 16, 125), (20, 24, 31))
        draw_label(self.screen, self.fonts["subtitle"], "Difficulty", (panel.left + 16, 210), (20, 24, 31))
        draw_label(self.screen, self.fonts["subtitle"], "Car Color", (panel.left + 16, 300), (20, 24, 31))

        preview = pygame.transform.smoothscale(
            self.assets["player_variants"][self.settings["car_color"]],
            (40, 70),
        )
        self.screen.blit(preview, preview.get_rect(center=(panel.centerx, 480)))
        draw_label(self.screen, self.fonts["small"], "Preview", (panel.centerx - 24, 420), (20, 24, 31))

        mouse_pos = pygame.mouse.get_pos()
        buttons = self.settings_buttons()
        buttons["sound"].draw(self.screen, self.fonts["body"], mouse_pos, active=self.settings["sound_on"])

        for difficulty in ("easy", "normal", "hard"):
            buttons[f"difficulty_{difficulty}"].draw(
                self.screen,
                self.fonts["body"],
                mouse_pos,
                active=self.settings["difficulty"] == difficulty,
            )

        for color_name in CAR_COLORS:
            buttons[f"color_{color_name}"].draw(
                self.screen,
                self.fonts["body"],
                mouse_pos,
                active=self.settings["car_color"] == color_name,
            )

        buttons["back"].draw(self.screen, self.fonts["body"], mouse_pos)

    def draw_leaderboard(self):
        self.draw_scene_background()
        draw_title(self.screen, self.fonts["title"], "Top 10 Drivers", 76)
        panel = self.centered_rect(118, 372, 414)
        draw_panel(self.screen, panel, alpha=222)

        draw_label(self.screen, self.fonts["subtitle"], "#", (panel.left + 14, 148), (20, 24, 31))
        draw_label(self.screen, self.fonts["subtitle"], "Name", (panel.left + 44, 148), (20, 24, 31))
        draw_label(self.screen, self.fonts["subtitle"], "Score", (panel.left + 192, 148), (20, 24, 31))
        draw_label(self.screen, self.fonts["subtitle"], "Dist", (panel.left + 290, 148), (20, 24, 31))

        if not self.leaderboard:
            draw_multiline_label(
                self.screen,
                self.fonts["body"],
                "No runs saved yet. Finish a race and your score will appear here.",
                (panel.left + 20, 250),
                320,
                (20, 24, 31),
                line_gap=1,
            )
        else:
            y = 186
            for index, entry in enumerate(self.leaderboard, start=1):
                draw_label(self.screen, self.fonts["body"], str(index), (panel.left + 14, y), (20, 24, 31))
                draw_label(self.screen, self.fonts["body"], entry["name"][:11], (panel.left + 44, y), (20, 24, 31))
                draw_label(self.screen, self.fonts["body"], str(entry["score"]), (panel.left + 192, y), (20, 24, 31))
                draw_label(self.screen, self.fonts["body"], f"{entry['distance']}m", (panel.left + 290, y), (20, 24, 31))
                y += 30

        mouse_pos = pygame.mouse.get_pos()
        self.leaderboard_buttons()["back"].draw(self.screen, self.fonts["body"], mouse_pos)

    def draw_game_over(self):
        self.draw_scene_background()
        title = "Finish Line" if self.last_result and self.last_result["won"] else "Game Over"
        draw_title(self.screen, self.fonts["title"], title, 88)
        panel = self.centered_rect(170, 324, 232)
        draw_panel(self.screen, panel, alpha=222)

        result = self.last_result or {
            "score": 0,
            "distance": 0,
            "coins": 0,
            "difficulty": self.settings["difficulty"],
            "name": self.settings.get("last_username", "Player"),
        }
        draw_label(self.screen, self.fonts["subtitle"], f"Driver: {result['name']}", (panel.left + 32, 180), (20, 24, 31))
        draw_label(self.screen, self.fonts["body"], f"Score: {result['score']}", (panel.left + 32, 220), (20, 24, 31))
        draw_label(self.screen, self.fonts["body"], f"Distance: {result['distance']} m", (panel.left + 32, 240), (20, 24, 31))
        draw_label(self.screen, self.fonts["body"], f"Coins: {result['coins']}", (panel.left + 32, 260), (20, 24, 31))
        draw_label(
            self.screen,
            self.fonts["body"],
            f"Difficulty: {result['difficulty'].title()}",
            (panel.left + 32, 280),
            (20, 24, 31),
        )
        draw_multiline_label(
            self.screen,
            self.fonts["small"],
            "Score combines distance, coins, and power-up bonuses.",
            (panel.left + 32, 330),
            240,
            (20, 24, 31),
            line_gap=0,
        )

        mouse_pos = pygame.mouse.get_pos()
        for button in self.game_over_buttons().values():
            button.draw(self.screen, self.fonts["body"], mouse_pos)

    def draw(self):
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "name_entry":
            self.draw_name_entry()
        elif self.state == "settings":
            self.draw_settings()
        elif self.state == "leaderboard":
            self.draw_leaderboard()
        elif self.state == "game_over":
            self.draw_game_over()
        elif self.state == "game" and self.current_game is not None:
            self.current_game.draw(self.screen, self.fonts)

        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0

            for event in pygame.event.get():
                self.handle_event(event)

            if self.state == "game" and self.current_game is not None:
                result = self.current_game.update(dt, pygame.key.get_pressed())
                if result is not None:
                    self.finish_game(result)

            self.draw()

        pygame.quit()
