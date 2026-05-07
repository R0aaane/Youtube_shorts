from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
import math
import random
from pathlib import Path

import pygame
import pymunk


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "boss_battle_001.json"
FRAMES_DIR = PROJECT_ROOT / "output" / "frames"
METADATA_DIR = PROJECT_ROOT / "output" / "metadata"
RESULT_PATH = METADATA_DIR / "simulation_result.json"
FOOD_SPRITES_DIR = PROJECT_ROOT / "assets" / "food_sprites"
KITCHEN_BACKGROUND_PATH = FOOD_SPRITES_DIR / "kitchen_battle_bg_optimized.png"

WIDTH = 1080
HEIGHT = 1920
FPS = 60
DEFAULT_FRAMES = 600
DEFAULT_BALLS = 10
BALL_RADIUS = 36
WALL_THICKNESS = 8
DISPLAY_SCALE = 0.4
BOSS_MAX_HP = 10000
BALL_DAMAGE = 10
BOSS_RECT = pygame.Rect(260, 240, 560, 180)
HP_BAR_RECT = pygame.Rect(80, 64, 920, 42)
HIT_COOLDOWN_FRAMES = 5
ITEM_RADIUS = 34
ITEM_START_FRAME = 45
EFFECT_FRAMES = 26
POPUP_FRAMES = 42
MAX_ITEMS = 8
MAX_BALL_SPEED = 1800
CLEAR = "CLEAR"
FAILED = "FAILED"


@dataclass
class SimulationConfig:
    video_width: int = WIDTH
    video_height: int = HEIGHT
    fps: int = FPS
    duration_seconds: int = 10
    initial_ball_count: int = DEFAULT_BALLS
    boss_hp: int = BOSS_MAX_HP
    base_damage: int = BALL_DAMAGE
    item_spawn_interval: int = 75
    random_seed: int = 1
    output_name: str = "simulation_001"
    theme: str = "boss_battle"
    fibonacci_count: int = 50
    exponential_count: int = 50
    food_types: list[str] | None = None
    duel_left_food: str = "pizza"
    duel_right_food: str = "burger"
    duel_left_hp: int = 240
    duel_right_hp: int = 260
    duel_ball_radius: int = 118
    duel_speed_scale: float = 1.0
    duel_charge_speed: int = 1220
    duel_burger_charge_hp_cost: int = 40
    duel_ingredient_damage: int = 10
    duel_cheese_damage: int = 6
    duel_cheese_projectile_speed: int = 760
    audio_enabled: bool = True

    @property
    def frame_count(self) -> int:
        return self.fps * self.duration_seconds


DEFAULT_CONFIG = {
    "video_width": WIDTH,
    "video_height": HEIGHT,
    "fps": FPS,
    "duration_seconds": 10,
    "initial_ball_count": DEFAULT_BALLS,
    "boss_hp": BOSS_MAX_HP,
    "base_damage": BALL_DAMAGE,
    "item_spawn_interval": 75,
    "random_seed": 1,
    "output_name": "simulation_001",
    "theme": "boss_battle",
    "fibonacci_count": 50,
    "exponential_count": 50,
    "food_types": None,
    "duel_left_food": "pizza",
    "duel_right_food": "burger",
    "duel_left_hp": 240,
    "duel_right_hp": 260,
    "duel_ball_radius": 118,
    "duel_speed_scale": 1.0,
    "duel_charge_speed": 1220,
    "duel_burger_charge_hp_cost": 40,
    "duel_ingredient_damage": 10,
    "duel_cheese_damage": 6,
    "duel_cheese_projectile_speed": 760,
    "audio_enabled": True,
}


@dataclass
class BallState:
    ball_id: int
    body: pymunk.Body
    damage: int
    team: str = "boss"
    label: str = ""
    skin: str = "plain"
    color: tuple[int, int, int] = (68, 180, 255)
    hit_cooldown: int = 0
    damage_level: int = 0
    speed_level: int = 0
    hits: int = 0
    total_damage_dealt: int = 0
    max_hit_damage: int = 0


@dataclass
class Item:
    kind: str
    position: pygame.Vector2
    radius: int = ITEM_RADIUS


@dataclass
class Effect:
    kind: str
    position: pygame.Vector2
    frames_left: int = EFFECT_FRAMES


@dataclass
class DamagePopup:
    amount: int
    position: pygame.Vector2
    frames_left: int = POPUP_FRAMES
    color: tuple[int, int, int] = (255, 238, 96)
    total_frames: int = POPUP_FRAMES
    scale: float = 1.0
    label: str = ""


@dataclass
class DuelBall:
    name: str
    skin: str
    color: tuple[int, int, int]
    hp: int
    max_hp: int
    position: pygame.Vector2
    velocity: pygame.Vector2
    radius: int
    hit_cooldown: int = 0
    skill_cooldown: int = 0
    charge_frames: int = 0
    burn_frames: int = 0
    burn_tick: int = 0
    total_damage_dealt: int = 0
    hits: int = 0
    trail: list[pygame.Vector2] = field(default_factory=list)
    visual_angle: float = 0.0
    missing_ingredients: list[str] = field(default_factory=list)
    reload_frames: int = 0
    cheese_spent: int = 0


@dataclass
class DuelEffect:
    kind: str
    position: pygame.Vector2
    frames_left: int
    color: tuple[int, int, int]
    label: str = ""


@dataclass
class AudioEvent:
    frame: int
    kind: str


def damage_popup_style(amount: int) -> tuple[int, float, str]:
    if amount >= 50:
        return 86, 1.75, "CRITICAL!"
    if amount >= 25:
        return 66, 1.38, ""
    if amount >= 10:
        return 50, 1.06, ""
    return 30, 0.72, ""


def make_damage_popup(amount: int, position: pygame.Vector2, color: tuple[int, int, int]) -> DamagePopup:
    frames, scale, label = damage_popup_style(amount)
    return DamagePopup(amount=amount, position=position, frames_left=frames, color=color, total_frames=frames, scale=scale, label=label)


def damage_audio_kind(amount: int) -> str:
    if amount >= 50:
        return "big_hit"
    if amount >= 25:
        return "heavy_hit"
    return "soft_hit"


def update_food_reload(ball: DuelBall) -> None:
    if ball.reload_frames <= 0:
        return
    ball.reload_frames -= 1
    step = max(1, round(FPS * 0.75))
    if ball.skin == "burger" and ball.reload_frames % step == 0 and ball.missing_ingredients:
        ball.missing_ingredients.pop()
    elif ball.skin == "pizza" and ball.reload_frames % step == 0 and ball.cheese_spent > 0:
        ball.cheese_spent -= 1


@dataclass
class CheeseProjectile:
    position: pygame.Vector2
    velocity: pygame.Vector2
    radius: int = 18
    frames_left: int = 120


@dataclass
class CheesePatch:
    attached_to: str
    offset: pygame.Vector2
    frames_left: int = 210
    tick_frames: int = 30


@dataclass
class IngredientAlly:
    kind: str
    position: pygame.Vector2
    velocity: pygame.Vector2
    radius: int
    damage: int
    hp: int
    max_hp: int
    hit_cooldown: int = 0
    frames_left: int = 720
    visual_angle: float = 0.0


SPRITE_CACHE: dict[str, pygame.Surface] = {}
BACKGROUND_CACHE: pygame.Surface | None = None
DUEL_BACKGROUND_CACHE: pygame.Surface | None = None


STYLE_FONT_NAMES = (
    "bahnschrift",
    "segoeuiblack",
    "segoeui",
    "centurygothic",
    "trebuchetms",
    "verdana",
)


def update_layout(width: int, height: int) -> None:
    global WIDTH, HEIGHT, BOSS_RECT, HP_BAR_RECT, BACKGROUND_CACHE, DUEL_BACKGROUND_CACHE
    WIDTH = width
    HEIGHT = height
    BACKGROUND_CACHE = None
    DUEL_BACKGROUND_CACHE = None
    boss_width = round(width * 0.52)
    boss_height = round(height * 0.094)
    BOSS_RECT = pygame.Rect((width - boss_width) // 2, round(height * 0.125), boss_width, boss_height)
    HP_BAR_RECT = pygame.Rect(round(width * 0.055), round(height * 0.03), round(width * 0.89), round(height * 0.04))


def ensure_default_config(path: Path = DEFAULT_CONFIG_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8")
    return path


def load_config(path: Path | None) -> SimulationConfig:
    config_data = DEFAULT_CONFIG.copy()
    if path is not None:
        config_path = path if path.is_absolute() else PROJECT_ROOT / path
        loaded = json.loads(config_path.read_text(encoding="utf-8"))
        config_data.update(loaded)
    return SimulationConfig(**config_data)


def add_walls(space: pymunk.Space) -> None:
    static_body = space.static_body
    inset = WALL_THICKNESS / 2
    walls = [
        pymunk.Segment(static_body, (inset, inset), (WIDTH - inset, inset), WALL_THICKNESS),
        pymunk.Segment(static_body, (WIDTH - inset, inset), (WIDTH - inset, HEIGHT - inset), WALL_THICKNESS),
        pymunk.Segment(static_body, (WIDTH - inset, HEIGHT - inset), (inset, HEIGHT - inset), WALL_THICKNESS),
        pymunk.Segment(static_body, (inset, HEIGHT - inset), (inset, inset), WALL_THICKNESS),
    ]

    for wall in walls:
        wall.elasticity = 1.0
        wall.friction = 0.0

    space.add(*walls)


def add_ball(
    space: pymunk.Space,
    rng: random.Random,
    damage: int,
    ball_id: int,
    *,
    team: str = "boss",
    label: str = "",
    color: tuple[int, int, int] = (68, 180, 255),
    x_range: tuple[int, int] | None = None,
) -> BallState:
    mass = 1.0
    moment = pymunk.moment_for_circle(mass, 0, BALL_RADIUS)
    body = pymunk.Body(mass, moment)
    min_x, max_x = x_range if x_range is not None else (BALL_RADIUS + 40, WIDTH - BALL_RADIUS - 40)
    body.position = rng.randint(min_x, max_x), rng.randint(620, HEIGHT - BALL_RADIUS - 80)

    speed = rng.randint(520, 920)
    direction = pygame.Vector2(rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0))
    if direction.length_squared() == 0:
        direction = pygame.Vector2(1, 0)
    direction = direction.normalize()
    body.velocity = direction.x * speed, direction.y * speed

    shape = pymunk.Circle(body, BALL_RADIUS)
    shape.elasticity = 1.0
    shape.friction = 0.0
    space.add(body, shape)
    return BallState(ball_id=ball_id, body=body, damage=damage, team=team, label=label, skin=team, color=color)


def compact_number(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(value)


def fibonacci_values(count: int, base_damage: int) -> list[int]:
    values = []
    a, b = 1, 1
    for _ in range(count):
        values.append(max(1, a * base_damage))
        a, b = b, min(a + b, 999)
    return values


def exponential_values(count: int, base_damage: int) -> list[int]:
    return [max(1, min(base_damage * (2 ** index), base_damage * 999)) for index in range(count)]


FOOD_BALL_STYLES = {
    "pizza": {"label": "PIZ", "color": (255, 202, 77)},
    "burger": {"label": "BRG", "color": (188, 118, 60)},
    "sushi": {"label": "SUS", "color": (246, 246, 238)},
    "taco": {"label": "TAC", "color": (244, 187, 66)},
    "donut": {"label": "DON", "color": (229, 133, 181)},
    "fries": {"label": "FRY", "color": (247, 205, 75)},
}


def food_ball_types(config: SimulationConfig) -> list[str]:
    requested = config.food_types or ["pizza", "burger", "sushi", "taco", "donut", "fries"]
    valid = [food for food in requested if food in FOOD_BALL_STYLES]
    return valid or ["pizza", "burger"]


def create_balls(space: pymunk.Space, rng: random.Random, config: SimulationConfig, damage: int) -> list[BallState]:
    if config.theme == "food_boss":
        foods = food_ball_types(config)
        balls: list[BallState] = []
        for index in range(config.initial_ball_count):
            food = foods[index % len(foods)]
            style = FOOD_BALL_STYLES[food]
            ball = add_ball(
                space,
                rng,
                damage,
                ball_id=index + 1,
                team=food,
                label=style["label"],
                color=style["color"],
            )
            ball.skin = food
            balls.append(ball)
        return balls

    if config.theme != "fibonacci_vs_exponential":
        return [add_ball(space, rng, damage, ball_id=index + 1) for index in range(config.initial_ball_count)]

    balls: list[BallState] = []
    left_range = (BALL_RADIUS + 46, WIDTH // 2 - BALL_RADIUS - 24)
    right_range = (WIDTH // 2 + BALL_RADIUS + 24, WIDTH - BALL_RADIUS - 46)

    for index, value in enumerate(fibonacci_values(config.fibonacci_count, damage), start=1):
        balls.append(
            add_ball(
                space,
                rng,
                value,
                ball_id=index,
                team="fibonacci",
                label=compact_number(value),
                color=(255, 213, 83),
                x_range=left_range,
            )
        )

    offset = len(balls)
    for index, value in enumerate(exponential_values(config.exponential_count, damage), start=1):
        balls.append(
            add_ball(
                space,
                rng,
                value,
                ball_id=offset + index,
                team="exponential",
                label=compact_number(value),
                color=(89, 211, 255),
                x_range=right_range,
            )
        )

    return balls


def clear_frames_dir() -> None:
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    for frame_path in FRAMES_DIR.glob("*.png"):
        frame_path.unlink(missing_ok=True)
    for frame_path in FRAMES_DIR.glob("*.jpg"):
        frame_path.unlink(missing_ok=True)


def create_background() -> pygame.Surface:
    background = pygame.Surface((WIDTH, HEIGHT))
    top = pygame.Color(8, 12, 24)
    bottom = pygame.Color(24, 31, 48)
    band_height = 12

    for y in range(0, HEIGHT, band_height):
        ratio = y / max(1, HEIGHT - band_height)
        color = top.lerp(bottom, ratio)
        pygame.draw.rect(background, color, pygame.Rect(0, y, WIDTH, band_height))

    minor_color = (42, 54, 78)
    major_color = (64, 84, 116)
    for x in range(0, WIDTH, 90):
        color = major_color if x % 270 == 0 else minor_color
        pygame.draw.line(background, color, (x, 0), (x, HEIGHT), 1)
    for y in range(0, HEIGHT, 90):
        color = major_color if y % 270 == 0 else minor_color
        pygame.draw.line(background, color, (0, y), (WIDTH, y), 1)

    pygame.draw.circle(background, (34, 48, 74), (WIDTH // 2, round(HEIGHT * 0.55)), round(WIDTH * 0.56), width=3)
    return background


def circle_rect_collision(position: pymunk.Vec2d, radius: int, rect: pygame.Rect) -> tuple[bool, pygame.Vector2]:
    closest_x = max(rect.left, min(position.x, rect.right))
    closest_y = max(rect.top, min(position.y, rect.bottom))
    delta = pygame.Vector2(position.x - closest_x, position.y - closest_y)

    if delta.length_squared() > radius * radius:
        return False, pygame.Vector2()

    if delta.length_squared() == 0:
        rect_center = pygame.Vector2(rect.center)
        delta = pygame.Vector2(position.x, position.y) - rect_center
        if delta.length_squared() == 0:
            delta = pygame.Vector2(0, 1)

    return True, delta.normalize()


def handle_boss_collision(
    ball: BallState,
    boss_hp: int,
    total_damage: int,
) -> tuple[int, int, int]:
    collided, normal = circle_rect_collision(ball.body.position, BALL_RADIUS, BOSS_RECT)
    if not collided:
        ball.hit_cooldown = max(0, ball.hit_cooldown - 1)
        return boss_hp, total_damage, 0

    velocity = pygame.Vector2(ball.body.velocity.x, ball.body.velocity.y)
    if velocity.dot(normal) < 0:
        reflected = velocity.reflect(normal)
        ball.body.velocity = reflected.x, reflected.y

    ball.body.position = ball.body.position.x + normal.x * 8, ball.body.position.y + normal.y * 8
    if ball.hit_cooldown > 0:
        ball.hit_cooldown -= 1
        return boss_hp, total_damage, 0

    ball.hit_cooldown = HIT_COOLDOWN_FRAMES
    dealt = min(boss_hp, ball.damage)
    ball.hits += 1
    ball.total_damage_dealt += dealt
    ball.max_hit_damage = max(ball.max_hit_damage, dealt)
    return max(0, boss_hp - dealt), total_damage + dealt, dealt


def clamp_to_arena(position: pygame.Vector2) -> pygame.Vector2:
    return pygame.Vector2(
        max(BALL_RADIUS + 60, min(WIDTH - BALL_RADIUS - 60, position.x)),
        max(BOSS_RECT.bottom + 80, min(HEIGHT - BALL_RADIUS - 80, position.y)),
    )


def spawn_item(rng: random.Random, balls: list[BallState], item_index: int) -> Item:
    source_ball = rng.choice(balls)
    source_position = pygame.Vector2(source_ball.body.position.x, source_ball.body.position.y)
    offset = pygame.Vector2(rng.randint(-24, 24), rng.randint(-24, 24))
    kind = "damage_up" if item_index % 2 == 0 else "speed_up"
    return Item(kind=kind, position=clamp_to_arena(source_position + offset))


def limit_ball_speed(ball: BallState) -> None:
    velocity = pygame.Vector2(ball.body.velocity.x, ball.body.velocity.y)
    if velocity.length() > MAX_BALL_SPEED:
        velocity.scale_to_length(MAX_BALL_SPEED)
        ball.body.velocity = velocity.x, velocity.y


def apply_item(ball: BallState, item: Item) -> None:
    if item.kind == "damage_up":
        ball.damage += 5
        ball.damage_level += 1
        return

    velocity = pygame.Vector2(ball.body.velocity.x, ball.body.velocity.y)
    if velocity.length_squared() == 0:
        velocity = pygame.Vector2(600, 0)
    velocity *= 1.14
    if velocity.length() > MAX_BALL_SPEED:
        velocity.scale_to_length(MAX_BALL_SPEED)
    ball.body.velocity = velocity.x, velocity.y
    ball.speed_level += 1


def handle_item_collisions(
    balls: list[BallState],
    items: list[Item],
    effects: list[Effect],
) -> tuple[int, int]:
    damage_up_count = 0
    speed_up_count = 0
    remaining_items = []

    for item in items:
        collected = False
        for ball in balls:
            ball_position = pygame.Vector2(ball.body.position.x, ball.body.position.y)
            if ball_position.distance_to(item.position) > BALL_RADIUS + item.radius:
                continue

            apply_item(ball, item)
            effects.append(Effect(kind=item.kind, position=item.position.copy()))
            damage_up_count += int(item.kind == "damage_up")
            speed_up_count += int(item.kind == "speed_up")
            collected = True
            break

        if not collected:
            remaining_items.append(item)

    items[:] = remaining_items
    return damage_up_count, speed_up_count


def draw_text(surface: pygame.Surface, font: pygame.font.Font, text: str, center: tuple[int, int], color: tuple[int, int, int]) -> None:
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=center)
    surface.blit(text_surface, text_rect)


def make_font(size: int, bold: bool = True, italic: bool = False) -> pygame.font.Font:
    for name in STYLE_FONT_NAMES:
        font_path = pygame.font.match_font(name, bold=bold, italic=italic)
        if font_path:
            return pygame.font.Font(font_path, size)
    return pygame.font.SysFont("arial", size, bold=bold, italic=italic)


def draw_text_with_shadow(
    surface: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    center: tuple[int, int],
    color: tuple[int, int, int],
    shadow: tuple[int, int, int] = (0, 0, 0),
) -> None:
    draw_text(surface, font, text, (center[0] + 3, center[1] + 3), shadow)
    draw_text(surface, font, text, center, color)


def item_color(kind: str) -> tuple[int, int, int]:
    if kind == "damage_up":
        return (255, 108, 95)
    return (99, 220, 156)


def draw_food_skin(surface: pygame.Surface, ball: BallState, position: tuple[int, int], radius: int, font: pygame.font.Font) -> None:
    x, y = position
    if ball.skin == "pizza":
        points = [(x - 22, y - 16), (x + 24, y - 7), (x - 8, y + 27)]
        pygame.draw.polygon(surface, (248, 180, 58), points)
        pygame.draw.polygon(surface, (176, 95, 38), points, width=4)
        pygame.draw.circle(surface, (206, 52, 48), (x - 6, y - 4), 5)
        pygame.draw.circle(surface, (206, 52, 48), (x + 6, y + 7), 5)
        pygame.draw.circle(surface, (242, 235, 150), (x - 12, y + 10), 4)
        return

    if ball.skin == "burger":
        pygame.draw.ellipse(surface, (230, 164, 82), pygame.Rect(x - 24, y - 23, 48, 19))
        pygame.draw.rect(surface, (82, 132, 54), pygame.Rect(x - 24, y - 7, 48, 7), border_radius=3)
        pygame.draw.rect(surface, (109, 61, 37), pygame.Rect(x - 25, y, 50, 12), border_radius=5)
        pygame.draw.ellipse(surface, (238, 190, 102), pygame.Rect(x - 23, y + 9, 46, 16))
        return

    if ball.skin == "sushi":
        pygame.draw.ellipse(surface, (246, 246, 238), pygame.Rect(x - 26, y - 18, 52, 36))
        pygame.draw.ellipse(surface, (235, 93, 86), pygame.Rect(x - 23, y - 13, 46, 26))
        pygame.draw.line(surface, (255, 214, 204), (x - 10, y - 11), (x + 7, y + 11), 5)
        return

    if ball.skin == "taco":
        pygame.draw.arc(surface, (238, 175, 54), pygame.Rect(x - 28, y - 15, 56, 45), 3.14, 6.28, 12)
        pygame.draw.rect(surface, (96, 145, 58), pygame.Rect(x - 22, y - 4, 44, 10), border_radius=4)
        pygame.draw.circle(surface, (198, 63, 50), (x - 8, y - 3), 5)
        pygame.draw.circle(surface, (198, 63, 50), (x + 10, y - 2), 5)
        return

    if ball.skin == "donut":
        pygame.draw.circle(surface, (197, 119, 67), position, radius - 7)
        pygame.draw.circle(surface, (235, 132, 184), position, radius - 13)
        pygame.draw.circle(surface, (255, 238, 210), position, 11)
        for dx, dy, color in [(-12, -8, (255, 245, 102)), (10, -7, (92, 206, 255)), (-4, 12, (255, 255, 255))]:
            pygame.draw.rect(surface, color, pygame.Rect(x + dx, y + dy, 10, 4), border_radius=2)
        return

    if ball.skin == "fries":
        pygame.draw.rect(surface, (204, 39, 46), pygame.Rect(x - 20, y - 1, 40, 27), border_radius=5)
        for dx in [-14, -6, 2, 10]:
            pygame.draw.rect(surface, (250, 213, 85), pygame.Rect(x + dx, y - 24, 8, 28), border_radius=3)
        return

    draw_text(surface, font, ball.label or str(ball.damage), position, (7, 20, 32))


def draw(
    surface: pygame.Surface,
    background: pygame.Surface,
    balls: list[BallState],
    items: list[Item],
    effects: list[Effect],
    popups: list[DamagePopup],
    boss_hp: int,
    boss_max_hp: int,
    status: str | None,
) -> None:
    title_font = pygame.font.SysFont("arial", 54, bold=True)
    hp_font = pygame.font.SysFont("arial", 42, bold=True)
    item_font = pygame.font.SysFont("arial", 26, bold=True)
    popup_font = pygame.font.SysFont("arial", 42, bold=True)
    status_font = pygame.font.SysFont("arial", 86, bold=True)
    team_font = pygame.font.SysFont("arial", 48, bold=True)

    surface.blit(background, (0, 0))
    pygame.draw.rect(surface, (230, 236, 242), surface.get_rect(), width=WALL_THICKNESS)

    if any(ball.team in {"fibonacci", "exponential"} for ball in balls):
        pygame.draw.line(surface, (238, 244, 250), (WIDTH // 2, BOSS_RECT.bottom + 40), (WIDTH // 2, HEIGHT - 70), 3)
        draw_text_with_shadow(surface, team_font, "FIBONACCI", (WIDTH // 4, BOSS_RECT.bottom + 58), (255, 213, 83))
        draw_text_with_shadow(surface, team_font, "EXPONENTIAL", (WIDTH * 3 // 4, BOSS_RECT.bottom + 58), (89, 211, 255))

    boss_shadow = BOSS_RECT.move(0, 10)
    pygame.draw.rect(surface, (52, 20, 34), boss_shadow, border_radius=18)
    pygame.draw.rect(surface, (165, 48, 62), BOSS_RECT, border_radius=14)
    boss_inner = BOSS_RECT.inflate(-28, -28)
    pygame.draw.rect(surface, (214, 72, 88), boss_inner, border_radius=10)
    pygame.draw.rect(surface, (230, 236, 242), BOSS_RECT, width=5, border_radius=14)
    has_number_theme = any(ball.team in {"fibonacci", "exponential"} for ball in balls)
    has_food_theme = any(ball.skin in FOOD_BALL_STYLES for ball in balls)
    if has_number_theme:
        boss_title = "NUMBER HP WALL"
    elif has_food_theme:
        boss_title = "HUNGER HP BOSS"
    else:
        boss_title = "HP BOSS"
    draw_text_with_shadow(surface, title_font, boss_title, BOSS_RECT.center, (255, 245, 230))

    hp_ratio = boss_hp / boss_max_hp if boss_max_hp > 0 else 0
    hp_ratio = max(0.0, min(1.0, hp_ratio))
    pygame.draw.rect(surface, (12, 15, 22), HP_BAR_RECT.inflate(14, 14), border_radius=18)
    pygame.draw.rect(surface, (46, 52, 64), HP_BAR_RECT, border_radius=14)
    hp_fill = pygame.Rect(HP_BAR_RECT.left, HP_BAR_RECT.top, round(HP_BAR_RECT.width * hp_ratio), HP_BAR_RECT.height)
    fill_color = (93, 230, 126) if hp_ratio > 0.5 else (242, 190, 76) if hp_ratio > 0.2 else (255, 92, 92)
    pygame.draw.rect(surface, fill_color, hp_fill, border_radius=14)
    pygame.draw.rect(surface, (250, 252, 255), HP_BAR_RECT, width=5, border_radius=14)
    draw_text_with_shadow(surface, hp_font, f"HP {boss_hp:,}/{boss_max_hp:,}", HP_BAR_RECT.center, (255, 255, 255))

    for item in items:
        color = item_color(item.kind)
        center = (round(item.position.x), round(item.position.y))
        pygame.draw.circle(surface, (255, 255, 255), center, item.radius + 11, width=4)
        pygame.draw.circle(surface, (16, 20, 28), center, item.radius + 6)
        pygame.draw.circle(surface, color, center, item.radius + 1)
        pygame.draw.circle(surface, (255, 255, 255), center, item.radius, width=3)
        label = "DMG" if item.kind == "damage_up" else "SPD"
        draw_text(surface, item_font, label, center, (20, 24, 30))

    for ball in balls:
        position = (round(ball.body.position.x), round(ball.body.position.y))
        pygame.draw.circle(surface, (8, 16, 28), (position[0] + 5, position[1] + 7), BALL_RADIUS + 3)
        pygame.draw.circle(surface, (245, 250, 255), position, BALL_RADIUS + 5)
        pygame.draw.circle(surface, ball.color, position, BALL_RADIUS)
        highlight = pygame.Color(ball.color).lerp(pygame.Color(255, 255, 255), 0.35)
        pygame.draw.circle(surface, highlight, (position[0] - 9, position[1] - 10), max(8, BALL_RADIUS // 3))
        pygame.draw.circle(surface, (7, 20, 32), position, BALL_RADIUS, width=3)
        if ball.skin in FOOD_BALL_STYLES:
            draw_food_skin(surface, ball, position, BALL_RADIUS, item_font)
        else:
            draw_text(surface, item_font, ball.label or str(ball.damage), position, (7, 20, 32))

    for effect in effects:
        progress = 1 - (effect.frames_left / EFFECT_FRAMES)
        radius = round(34 + progress * 48)
        color = item_color(effect.kind)
        pygame.draw.circle(surface, color, (round(effect.position.x), round(effect.position.y)), radius, width=5)

    for popup in popups:
        progress = 1 - (popup.frames_left / max(1, popup.total_frames))
        y_offset = round(progress * 62 * popup.scale)
        center = (round(popup.position.x), round(popup.position.y) - y_offset)
        draw_text_with_shadow(surface, popup_font, f"-{popup.amount}", center, popup.color)

    if status is not None:
        color = (104, 232, 143) if status == CLEAR else (255, 105, 105)
        draw_text_with_shadow(surface, status_font, status, (WIDTH // 2, HEIGHT // 2), color)


def find_top_damage_ball(balls: list[BallState]) -> BallState:
    return max(balls, key=lambda ball: (ball.max_hit_damage, ball.total_damage_dealt, ball.damage, -ball.ball_id))


def draw_result_screen(
    surface: pygame.Surface,
    status: str,
    boss_hp: int,
    boss_max_hp: int,
    total_damage: int,
    top_ball: BallState,
    clear_frame: int | None,
    fps: int,
) -> None:
    headline_font = pygame.font.SysFont("arial", 138, bold=True)
    label_font = pygame.font.SysFont("arial", 56, bold=True)
    value_font = pygame.font.SysFont("arial", 46, bold=True)
    small_font = pygame.font.SysFont("arial", 36, bold=True)

    top = pygame.Color(8, 12, 24)
    bottom = pygame.Color(24, 32, 50)
    for y in range(0, HEIGHT, 18):
        pygame.draw.rect(surface, top.lerp(bottom, y / max(1, HEIGHT)), pygame.Rect(0, y, WIDTH, 18))

    color = (104, 232, 143) if status == CLEAR else (255, 105, 105)
    pygame.draw.rect(surface, color, pygame.Rect(0, 0, WIDTH, 26))
    pygame.draw.rect(surface, color, pygame.Rect(0, HEIGHT - 26, WIDTH, 26))

    badge_rect = pygame.Rect(round(WIDTH * 0.12), round(HEIGHT * 0.13), round(WIDTH * 0.76), round(HEIGHT * 0.22))
    pygame.draw.rect(surface, (12, 15, 22), badge_rect, border_radius=26)
    pygame.draw.rect(surface, color, badge_rect, width=7, border_radius=26)
    draw_text_with_shadow(surface, headline_font, status, badge_rect.center, color)

    if status == CLEAR and clear_frame is not None:
        clear_seconds = clear_frame / fps
        result_line = f"Clear Time  {clear_seconds:.2f}s"
    else:
        result_line = f"Remaining HP  {boss_hp}/{boss_max_hp}"

    rows = [
        result_line,
        f"Total Damage  {total_damage}",
        f"Top Ball  #{top_ball.ball_id:02d}",
        f"Max Hit  {top_ball.max_hit_damage}",
        f"Hits / Damage  {top_ball.hits} / {top_ball.total_damage_dealt}",
    ]

    panel_rect = pygame.Rect(round(WIDTH * 0.1), round(HEIGHT * 0.42), round(WIDTH * 0.8), round(HEIGHT * 0.32))
    pygame.draw.rect(surface, (20, 26, 38), panel_rect, border_radius=22)
    pygame.draw.rect(surface, (82, 104, 138), panel_rect, width=3, border_radius=22)

    start_y = panel_rect.top + round(panel_rect.height * 0.16)
    row_gap = round(panel_rect.height * 0.18)
    for index, row in enumerate(rows):
        font = label_font if index == 0 else value_font
        row_color = color if index == 0 else (238, 244, 250)
        draw_text_with_shadow(surface, font, row, (WIDTH // 2, start_y + index * row_gap), row_color)

    if top_ball.team in {"fibonacci", "exponential"}:
        subtitle = "100 Fibonacci VS Exponential"
    elif top_ball.skin in FOOD_BALL_STYLES:
        subtitle = "Food Balls vs Hunger HP Boss"
    else:
        subtitle = "Evolving Balls vs HP Boss"
    draw_text_with_shadow(surface, small_font, subtitle, (WIDTH // 2, round(HEIGHT * 0.86)), (190, 204, 224))


def food_label(food: str) -> str:
    labels = {
        "pizza": "PIZZA",
        "burger": "BURGER",
        "sushi": "SUSHI",
        "taco": "TACO",
        "donut": "DONUT",
        "fries": "FRIES",
    }
    return labels.get(food, food.upper())


def duel_skill_name(food: str) -> str:
    names = {
        "pizza": "CHEESE",
        "burger": "CHARGE+ALLY",
        "sushi": "HEAL",
        "taco": "CRIT",
        "donut": "SHIELD",
        "fries": "COMBO",
    }
    return names.get(food, "HIT")


def duel_ball_by_side(side: str, left: DuelBall, right: DuelBall) -> DuelBall:
    return left if side == "left" else right


def duel_attack_color(skin: str) -> tuple[int, int, int]:
    return (255, 215, 70) if skin == "pizza" else (255, 76, 70)


def duel_arena_rect() -> pygame.Rect:
    size = round(min(WIDTH * 0.88, HEIGHT * 0.50))
    return pygame.Rect((WIDTH - size) // 2, round(HEIGHT * 0.215), size, size)


def draw_scaled_food_skin(surface: pygame.Surface, skin: str, position: tuple[int, int], radius: int) -> None:
    x, y = position
    scale = radius / 118

    def rect(dx: int, dy: int, width: int, height: int) -> pygame.Rect:
        return pygame.Rect(
            round(x + dx * scale),
            round(y + dy * scale),
            round(width * scale),
            round(height * scale),
        )

    def point(px: int, py: int) -> tuple[int, int]:
        return round(x + px * scale), round(y + py * scale)

    if skin == "pizza":
        points = [point(-70, -48), point(74, -22), point(-18, 82)]
        pygame.draw.polygon(surface, (250, 184, 54), points)
        pygame.draw.polygon(surface, (160, 86, 37), points, width=max(5, round(9 * scale)))
        for px, py in [(-20, -18), (24, 6), (-36, 34)]:
            pygame.draw.circle(surface, (204, 43, 41), point(px, py), round(11 * scale))
        for px, py in [(-2, 28), (31, -18)]:
            pygame.draw.circle(surface, (252, 235, 151), point(px, py), round(8 * scale))
        return

    if skin == "burger":
        pygame.draw.ellipse(surface, (232, 166, 80), rect(-72, -62, 144, 48))
        pygame.draw.rect(surface, (84, 137, 58), rect(-72, -22, 144, 20), border_radius=round(8 * scale))
        pygame.draw.rect(surface, (105, 58, 36), rect(-76, 0, 152, 34), border_radius=round(14 * scale))
        pygame.draw.ellipse(surface, (240, 192, 104), rect(-70, 30, 140, 42))
        return

    if skin == "sushi":
        pygame.draw.ellipse(surface, (246, 246, 238), rect(-76, -48, 152, 96))
        pygame.draw.ellipse(surface, (235, 92, 84), rect(-66, -34, 132, 68))
        pygame.draw.line(surface, (255, 214, 204), point(-28, -32), point(20, 33), max(7, round(13 * scale)))
        return

    if skin == "taco":
        pygame.draw.arc(surface, (238, 175, 54), rect(-82, -42, 164, 128), 3.14, 6.28, max(10, round(22 * scale)))
        pygame.draw.rect(surface, (96, 145, 58), rect(-62, -12, 124, 24), border_radius=round(10 * scale))
        for px, py in [(-26, -9), (20, -6), (0, 12)]:
            pygame.draw.circle(surface, (198, 63, 50), point(px, py), round(11 * scale))
        return

    if skin == "donut":
        pygame.draw.circle(surface, (197, 119, 67), position, round(radius * 0.72))
        pygame.draw.circle(surface, (235, 132, 184), position, round(radius * 0.54))
        pygame.draw.circle(surface, (255, 238, 210), position, round(radius * 0.22))
        for px, py, color in [(-34, -22, (255, 245, 102)), (22, -24, (92, 206, 255)), (-8, 36, (255, 255, 255))]:
            pygame.draw.rect(surface, color, rect(px, py, 28, 9), border_radius=round(4 * scale))
        return

    if skin == "fries":
        pygame.draw.rect(surface, (204, 39, 46), rect(-54, -2, 108, 76), border_radius=round(10 * scale))
        for px in [-42, -20, 2, 24]:
            pygame.draw.rect(surface, (250, 213, 85), rect(px, -72, 18, 82), border_radius=round(6 * scale))
        return


def chroma_key_magenta(surface: pygame.Surface) -> pygame.Surface:
    keyed = surface.copy()
    key_color = surface.get_at((0, 0))
    keyed.set_colorkey((key_color.r, key_color.g, key_color.b), pygame.RLEACCEL)
    return keyed


def scale_cover(source: pygame.Surface, target_size: tuple[int, int]) -> pygame.Surface:
    target_width, target_height = target_size
    source_width, source_height = source.get_size()
    scale = max(target_width / source_width, target_height / source_height)
    scaled_size = (round(source_width * scale), round(source_height * scale))
    scaled = pygame.transform.smoothscale(source, scaled_size)
    crop_rect = pygame.Rect(0, 0, target_width, target_height)
    crop_rect.center = scaled.get_rect().center
    result = pygame.Surface(target_size, pygame.SRCALPHA)
    result.blit(scaled, (0, 0), crop_rect)
    return result


def load_kitchen_background() -> pygame.Surface | None:
    global BACKGROUND_CACHE
    if BACKGROUND_CACHE is not None:
        return BACKGROUND_CACHE
    if not KITCHEN_BACKGROUND_PATH.exists():
        return None
    source = pygame.image.load(str(KITCHEN_BACKGROUND_PATH))
    BACKGROUND_CACHE = scale_cover(source, (WIDTH, HEIGHT))
    return BACKGROUND_CACHE


def load_food_sprite(skin: str, radius: int, missing_stage: int = 0, cheese_stage: int = 0) -> pygame.Surface | None:
    missing_stage = min(4, max(0, missing_stage if skin == "burger" else 0))
    cheese_stage = min(4, max(0, cheese_stage if skin == "pizza" else 0))
    cache_key = f"{skin}:{radius}:{missing_stage}:{cheese_stage}"
    if cache_key in SPRITE_CACHE:
        return SPRITE_CACHE[cache_key]

    burger_variants = {
        1: FOOD_SPRITES_DIR / "burger_missing_lettuce_alpha.png",
        2: FOOD_SPRITES_DIR / "burger_missing_lettuce_cheese_alpha.png",
        3: FOOD_SPRITES_DIR / "burger_missing_lettuce_cheese_tomato_alpha.png",
        4: FOOD_SPRITES_DIR / "burger_missing_lettuce_cheese_tomato_meat_alpha.png",
    }
    pizza_variants = {
        1: FOOD_SPRITES_DIR / "pizza_cheese_1_alpha.png",
        2: FOOD_SPRITES_DIR / "pizza_cheese_2_alpha.png",
        3: FOOD_SPRITES_DIR / "pizza_cheese_3_alpha.png",
        4: FOOD_SPRITES_DIR / "pizza_cheese_4_alpha.png",
    }
    if skin == "burger" and missing_stage > 0:
        sprite_path = burger_variants.get(missing_stage)
        if sprite_path is not None and not sprite_path.exists():
            sprite_path = FOOD_SPRITES_DIR / "burger_alpha.png"
    elif skin == "pizza" and cheese_stage > 0:
        sprite_path = pizza_variants.get(cheese_stage)
        if sprite_path is not None and not sprite_path.exists():
            sprite_path = FOOD_SPRITES_DIR / "pizza_alpha.png"
    else:
        sprite_paths = {
            "pizza": FOOD_SPRITES_DIR / "pizza_alpha.png",
            "burger": FOOD_SPRITES_DIR / "burger_alpha.png",
        }
        sprite_path = sprite_paths.get(skin)
    if sprite_path is None or not sprite_path.exists():
        return None

    keyed = load_alpha_surface(sprite_path)
    sprite_size = round(radius * (2.95 if skin == "pizza" else 2.7))
    scaled = pygame.transform.smoothscale(keyed, (sprite_size, sprite_size))
    SPRITE_CACHE[cache_key] = scaled
    return scaled


def load_alpha_surface(path: Path) -> pygame.Surface:
    surface = pygame.image.load(str(path))
    try:
        return surface.convert_alpha()
    except pygame.error:
        return surface


def load_ingredient_sprite(kind: str, radius: int) -> pygame.Surface | None:
    cache_key = f"ingredient:{kind}:{radius}"
    if cache_key in SPRITE_CACHE:
        return SPRITE_CACHE[cache_key]

    sprite_path = FOOD_SPRITES_DIR / f"ingredient_{kind}_alpha.png"
    if not sprite_path.exists():
        return None

    keyed = load_alpha_surface(sprite_path)
    sprite_size = round(radius * 2.45)
    scaled = pygame.transform.smoothscale(keyed, (sprite_size, sprite_size))
    SPRITE_CACHE[cache_key] = scaled
    return scaled


def draw_food_sprite(surface: pygame.Surface, ball: DuelBall, position: tuple[int, int]) -> bool:
    missing_stage = len(ball.missing_ingredients) if ball.skin == "burger" else 0
    sprite = load_food_sprite(ball.skin, ball.radius, missing_stage, ball.cheese_spent)
    if sprite is None:
        return False

    glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    glow_color = (*duel_attack_color(ball.skin), 54)
    pygame.draw.circle(glow, glow_color, position, round(ball.radius * 1.55))
    pygame.draw.circle(glow, (*duel_attack_color(ball.skin), 98), position, round(ball.radius * 1.12), width=6)
    pygame.draw.circle(glow, (255, 246, 216, 36), (position[0] - round(ball.radius * 0.18), position[1] - round(ball.radius * 0.22)), round(ball.radius * 0.72))
    surface.blit(glow, (0, 0))
    rotated = pygame.transform.rotozoom(sprite, -ball.visual_angle, 1.0)
    rect = rotated.get_rect(center=position)
    shadow = rotated.copy()
    shadow.fill((0, 0, 0, 165), special_flags=pygame.BLEND_RGBA_MULT)
    surface.blit(shadow, rect.move(12, 18))
    surface.blit(rotated, rect)
    return True


def draw_duel_ball(surface: pygame.Surface, ball: DuelBall, font: pygame.font.Font) -> None:
    position = (round(ball.position.x), round(ball.position.y))
    if ball.charge_frames > 0 and len(ball.trail) > 1:
        for index, trail_position in enumerate(ball.trail[-8:]):
            ratio = (index + 1) / min(8, len(ball.trail))
            trail_radius = round(ball.radius * (0.34 + ratio * 0.2))
            trail_color = pygame.Color(255, 76, 70).lerp(pygame.Color(255, 230, 210), ratio * 0.35)
            pygame.draw.circle(
                surface,
                trail_color,
                (round(trail_position.x), round(trail_position.y)),
                trail_radius,
                width=max(4, round(10 * ratio)),
            )

    if ball.burn_frames > 0:
        pulse = 1 + ((ball.burn_frames % 18) / 18) * 0.16
        flame_radius = round(ball.radius * pulse)
        pygame.draw.circle(surface, (255, 88, 32), position, flame_radius + 18, width=10)
        pygame.draw.circle(surface, (255, 211, 72), position, flame_radius + 4, width=7)
        for angle in range(0, 360, 45):
            offset = pygame.Vector2(1, 0).rotate(angle) * (ball.radius + 24)
            tip = pygame.Vector2(position) + offset
            left = pygame.Vector2(position) + offset.rotate(9) * 0.86
            right = pygame.Vector2(position) + offset.rotate(-9) * 0.86
            pygame.draw.polygon(surface, (255, 115, 36), [tip, left, right])

    sprite_drawn = draw_food_sprite(surface, ball, position)
    if not sprite_drawn:
        pygame.draw.circle(surface, (3, 8, 18), (position[0] + 11, position[1] + 14), ball.radius + 8)
        pygame.draw.circle(surface, (242, 248, 255), position, ball.radius + 10)
        pygame.draw.circle(surface, ball.color, position, ball.radius)
        glow = pygame.Color(ball.color).lerp(pygame.Color(255, 255, 255), 0.22)
        pygame.draw.circle(surface, glow, (position[0] - round(ball.radius * 0.25), position[1] - round(ball.radius * 0.28)), round(ball.radius * 0.32))
        draw_scaled_food_skin(surface, ball.skin, position, ball.radius)
    draw_text_with_shadow(surface, font, str(max(0, ball.hp)), position, (255, 255, 255))
    if ball.charge_frames > 0:
        pulse = 1 + math.sin(ball.charge_frames * 0.42) * 0.12
        label_font = make_font(round(37 * pulse), bold=True, italic=True)
        draw_text_with_shadow(surface, label_font, "CHARGE", (position[0], position[1] - ball.radius - 48), duel_attack_color("burger"))
    elif ball.burn_frames > 0:
        pulse = 1 + math.sin(ball.burn_frames * 0.38) * 0.1
        label_font = make_font(round(36 * pulse), bold=True, italic=True)
        draw_text_with_shadow(surface, label_font, "BURN", (position[0], position[1] - ball.radius - 48), (255, 172, 58))
    elif ball.reload_frames > 0:
        pulse = 1 + math.sin(ball.reload_frames * 0.22) * 0.08
        label_font = make_font(round(34 * pulse), bold=True, italic=True)
        draw_text_with_shadow(surface, label_font, "Reloading...", (position[0], position[1] - ball.radius - 48), (255, 236, 190))


def draw_duel_particles(surface: pygame.Surface, center: tuple[int, int], color: tuple[int, int, int], progress: float, count: int, spread: float) -> None:
    for index in range(count):
        angle = index * (360 / count) + math.sin(index * 1.7) * 16
        distance = spread * (0.25 + progress * (0.72 + (index % 3) * 0.12))
        particle = pygame.Vector2(center) + pygame.Vector2(1, 0).rotate(angle) * distance
        radius = max(3, round((1 - progress) * (7 + index % 4)))
        particle_color = pygame.Color(color).lerp(pygame.Color(255, 239, 196), 0.25 + (index % 2) * 0.18)
        pygame.draw.circle(surface, particle_color, (round(particle.x), round(particle.y)), radius)


def draw_skill_label(
    surface: pygame.Surface,
    text: str,
    center: tuple[int, int],
    color: tuple[int, int, int],
    progress: float,
    base_size: int = 42,
) -> None:
    alpha = max(0, min(255, round(255 * (1 - progress))))
    scale = 1 + progress * 0.45
    font = make_font(round(base_size * scale), bold=True, italic=True)
    text_surface = font.render(text, True, color)
    shadow_surface = font.render(text, True, (0, 0, 0))
    text_surface.set_alpha(alpha)
    shadow_surface.set_alpha(round(alpha * 0.7))
    y = center[1] - round(progress * 34)
    rect = text_surface.get_rect(center=(center[0], y))
    surface.blit(shadow_surface, rect.move(4, 4))
    surface.blit(text_surface, rect)


def should_draw_skill_label(label: str) -> bool:
    return label in {"CHEESE SHOT", "CHARGE HIT", "LETTUCE", "CHEESE", "TOMATO", "MEAT"}


def draw_duel_effects(surface: pygame.Surface, effects: list[DuelEffect]) -> None:
    for effect in effects:
        progress = 1 - effect.frames_left / max(1, 36)
        center = (round(effect.position.x), round(effect.position.y))
        if effect.kind == "impact":
            alpha = max(0, min(210, round(210 * (1 - progress))))
            flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            if effect.label:
                flash.fill((255, 242, 210, round(34 * (1 - progress))))
            radius = round(70 + progress * (260 if effect.label else 190))
            pygame.draw.circle(flash, (*effect.color, alpha), center, radius, width=14)
            pygame.draw.circle(flash, (255, 244, 214, round(alpha * 0.82)), center, max(20, round(radius * 0.58)), width=7)
            pygame.draw.circle(flash, (255, 255, 255, round(alpha * 0.72)), center, max(18, radius // 3), width=4)
            for angle in range(0, 360, 30):
                start = pygame.Vector2(center) + pygame.Vector2(1, 0).rotate(angle) * (radius * 0.42)
                end = pygame.Vector2(center) + pygame.Vector2(1, 0).rotate(angle) * (radius * 0.86)
                pygame.draw.line(flash, (255, 255, 255, round(alpha * 0.72)), start, end, 4)
            surface.blit(flash, (0, 0))
            draw_duel_particles(surface, center, effect.color, progress, 12 if effect.label else 8, radius * 0.55)
            if effect.label:
                draw_skill_label(surface, effect.label, (center[0], center[1] - radius - 18), effect.color, progress, 46)
        elif effect.kind == "burn":
            radius = round(60 + progress * 70)
            pygame.draw.circle(surface, (255, 78, 28), center, radius, width=8)
            pygame.draw.circle(surface, (255, 220, 78), center, radius - 18, width=5)
            if effect.label and should_draw_skill_label(effect.label):
                draw_skill_label(surface, effect.label, (center[0], center[1] - radius - 24), effect.color, progress)
        elif effect.kind == "charge":
            radius = round(44 + progress * 118)
            pygame.draw.circle(surface, (255, 232, 205), center, radius + 14, width=3)
            pygame.draw.circle(surface, duel_attack_color("burger"), center, radius, width=8)
            draw_duel_particles(surface, center, duel_attack_color("burger"), progress, 7, radius * 0.55)
            if effect.label and should_draw_skill_label(effect.label):
                draw_skill_label(surface, effect.label, (center[0], center[1] - radius - 22), effect.color, progress)
        elif effect.kind == "cheese":
            radius = round(34 + progress * 65)
            pygame.draw.circle(surface, (255, 220, 64), center, radius, width=8)
            pygame.draw.circle(surface, (255, 250, 180), center, max(12, radius // 2), width=4)
            draw_duel_particles(surface, center, (255, 220, 64), progress, 6, radius * 0.6)
            if effect.label and should_draw_skill_label(effect.label):
                draw_skill_label(surface, effect.label, (center[0], center[1] - radius - 20), effect.color, progress, 38)
        elif effect.kind == "ingredient":
            radius = round(28 + progress * 52)
            pygame.draw.circle(surface, effect.color, center, radius, width=7)
            draw_duel_particles(surface, center, effect.color, progress, 6, radius * 0.72)
            if effect.label and should_draw_skill_label(effect.label):
                draw_skill_label(surface, effect.label, (center[0], center[1] - radius - 18), effect.color, progress, 36)


def draw_cheese_projectiles(surface: pygame.Surface, projectiles: list[CheeseProjectile]) -> None:
    for projectile in projectiles:
        center = (round(projectile.position.x), round(projectile.position.y))
        pygame.draw.circle(surface, (148, 98, 18), (center[0] + 5, center[1] + 7), projectile.radius + 3)
        pygame.draw.circle(surface, (255, 217, 61), center, projectile.radius)
        pygame.draw.circle(surface, (255, 250, 186), (center[0] - 5, center[1] - 5), max(5, projectile.radius // 3))
        pygame.draw.circle(surface, (177, 114, 20), center, projectile.radius, width=3)


def draw_cheese_patches(surface: pygame.Surface, patches: list[CheesePatch], left: DuelBall, right: DuelBall) -> None:
    for patch in patches:
        target = duel_ball_by_side(patch.attached_to, left, right)
        position = target.position + patch.offset.rotate(target.visual_angle)
        center = (round(position.x), round(position.y))
        age = 1 - patch.frames_left / 210
        base_radius = round(target.radius * (0.28 + min(0.18, age * 0.18)))
        cheese = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        points = []
        for angle, scale in [(0, 1.0), (45, 0.78), (95, 1.12), (150, 0.82), (210, 1.05), (285, 0.72)]:
            offset = pygame.Vector2(1, 0).rotate(angle + target.visual_angle) * (base_radius * scale)
            points.append((round(center[0] + offset.x), round(center[1] + offset.y)))
        pygame.draw.polygon(cheese, (255, 211, 54, 232), points)
        pygame.draw.polygon(cheese, (167, 105, 18, 190), points, width=max(3, base_radius // 9))
        pygame.draw.circle(cheese, (255, 232, 98, 238), center, round(base_radius * 0.72))
        pygame.draw.circle(cheese, (255, 248, 177, 215), (center[0] - round(base_radius * 0.28), center[1] - round(base_radius * 0.24)), max(6, round(base_radius * 0.22)))
        for angle, length_scale in [(75, 0.72), (130, 0.56), (250, 0.64)]:
            start = pygame.Vector2(center) + pygame.Vector2(1, 0).rotate(angle + target.visual_angle) * (base_radius * 0.4)
            end = pygame.Vector2(center) + pygame.Vector2(1, 0).rotate(angle + target.visual_angle) * (base_radius * (1.0 + length_scale))
            pygame.draw.line(cheese, (255, 210, 50, 222), start, end, max(8, base_radius // 5))
            pygame.draw.circle(cheese, (255, 210, 50, 230), (round(end.x), round(end.y)), max(6, base_radius // 7))
        surface.blit(cheese, (0, 0))


def ingredient_color(kind: str) -> tuple[int, int, int]:
    colors = {
        "lettuce": (116, 215, 70),
        "cheese": (255, 211, 62),
        "tomato": (229, 58, 48),
        "meat": (105, 61, 38),
    }
    return colors.get(kind, (240, 240, 240))


def draw_ingredient_allies(surface: pygame.Surface, allies: list[IngredientAlly]) -> None:
    hp_font = make_font(28, bold=True)
    for ally in allies:
        center = (round(ally.position.x), round(ally.position.y))
        color = duel_attack_color("burger")
        glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*color, 52), center, ally.radius + 18)
        pygame.draw.circle(glow, (*color, 110), center, ally.radius + 8, width=4)
        surface.blit(glow, (0, 0))
        sprite = load_ingredient_sprite(ally.kind, ally.radius)
        if sprite is not None:
            rotated = pygame.transform.rotozoom(sprite, -ally.visual_angle, 1.0)
            rect = rotated.get_rect(center=center)
            shadow = rotated.copy()
            shadow.fill((0, 0, 0, 105), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(shadow, rect.move(8, 12))
            surface.blit(rotated, rect)
        else:
            pygame.draw.circle(surface, (8, 12, 18), (center[0] + 4, center[1] + 6), ally.radius + 3)
            pygame.draw.circle(surface, ingredient_color(ally.kind), center, ally.radius)
        pygame.draw.circle(surface, color, center, ally.radius + 8, width=4)
        draw_text_with_shadow(surface, hp_font, str(max(0, ally.hp)), center, (255, 245, 235))


def draw_duel_background(surface: pygame.Surface) -> pygame.Rect:
    global DUEL_BACKGROUND_CACHE
    arena_rect = duel_arena_rect()
    if DUEL_BACKGROUND_CACHE is not None:
        surface.blit(DUEL_BACKGROUND_CACHE, (0, 0))
        return arena_rect

    cached = pygame.Surface((WIDTH, HEIGHT))
    cached.fill((24, 16, 12))
    vs_font = make_font(88, bold=True, italic=True)

    board_rect = pygame.Rect(round(WIDTH * 0.035), round(HEIGHT * 0.035), round(WIDTH * 0.93), round(HEIGHT * 0.86))
    pygame.draw.rect(cached, (18, 11, 8), board_rect.move(0, 18), border_radius=30)
    pygame.draw.rect(cached, (43, 27, 18), board_rect, border_radius=28)
    pygame.draw.rect(cached, (66, 42, 27), board_rect.inflate(-18, -18), border_radius=22)
    pygame.draw.rect(cached, (91, 59, 36), board_rect.inflate(-34, -34), width=3, border_radius=18)
    for x in range(board_rect.left + 38, board_rect.right, 86):
        pygame.draw.line(cached, (79, 51, 32), (x, board_rect.top + 24), (x, board_rect.bottom - 24), 2)
    for x in range(board_rect.left + 78, board_rect.right, 172):
        pygame.draw.line(cached, (32, 20, 14), (x, board_rect.top + 28), (x, board_rect.bottom - 28), 1)

    arena_shadow = arena_rect.move(0, 10)
    outer_glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(outer_glow, (255, 225, 160, 34), arena_rect.inflate(30, 30), border_radius=18)
    pygame.draw.rect(outer_glow, (0, 0, 0, 92), arena_shadow.inflate(18, 14), border_radius=16)
    cached.blit(outer_glow, (0, 0))
    pygame.draw.rect(cached, (13, 9, 8), arena_shadow, border_radius=10)
    pygame.draw.rect(cached, (101, 66, 39), arena_rect, border_radius=8)
    pygame.draw.rect(cached, (139, 93, 55), arena_rect.inflate(-14, -14), border_radius=6)
    pygame.draw.rect(cached, (164, 111, 67), pygame.Rect(arena_rect.left + 18, arena_rect.top + 18, arena_rect.width - 36, round(arena_rect.height * 0.42)), border_radius=6)
    for y in range(arena_rect.top + 44, arena_rect.bottom - 28, 72):
        pygame.draw.line(cached, (160, 108, 66), (arena_rect.left + 22, y), (arena_rect.right - 22, y), 2)
        pygame.draw.line(cached, (94, 59, 34), (arena_rect.left + 26, y + 3), (arena_rect.right - 26, y + 3), 1)
    for x in range(arena_rect.left + 70, arena_rect.right - 30, 150):
        pygame.draw.line(cached, (157, 103, 61), (x, arena_rect.top + 28), (x, arena_rect.bottom - 28), 1)
    pygame.draw.rect(cached, (237, 219, 178), arena_rect, width=5, border_radius=8)
    pygame.draw.rect(cached, (177, 134, 86), arena_rect.inflate(-12, -12), width=2, border_radius=6)
    vignette = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.circle(vignette, (255, 224, 154, 22), arena_rect.center, round(arena_rect.width * 0.62))
    for inset, alpha in [(0, 90), (34, 54), (76, 32)]:
        pygame.draw.rect(vignette, (0, 0, 0, alpha), pygame.Rect(inset, inset, WIDTH - inset * 2, HEIGHT - inset * 2), width=34, border_radius=24)
    cached.blit(vignette, (0, 0))
    draw_text_with_shadow(cached, vs_font, "VS", (WIDTH // 2, round(HEIGHT * 0.138)), (238, 229, 206), (34, 20, 14))
    DUEL_BACKGROUND_CACHE = cached
    surface.blit(DUEL_BACKGROUND_CACHE, (0, 0))
    return arena_rect


def draw_duel_hud(surface: pygame.Surface, left: DuelBall, right: DuelBall, frame_index: int, total_frames: int) -> None:
    hud_font = make_font(39, bold=True)
    small_font = make_font(25, bold=True)
    panel_y = round(HEIGHT * 0.047)
    panel_width = round(WIDTH * 0.42)
    panel_height = 112
    left_panel = pygame.Rect(round(WIDTH * 0.045), panel_y, panel_width, panel_height)
    right_panel = pygame.Rect(WIDTH - round(WIDTH * 0.045) - panel_width, panel_y, panel_width, panel_height)

    def draw_panel(rect: pygame.Rect, ball: DuelBall, color: tuple[int, int, int], align_right: bool = False) -> None:
        pygame.draw.rect(surface, (11, 8, 7), rect.inflate(10, 10), border_radius=12)
        pygame.draw.rect(surface, (31, 22, 18), rect, border_radius=10)
        pygame.draw.rect(surface, color, rect, width=4, border_radius=10)
        label_x = rect.right - 24 if align_right else rect.left + 24
        label_center = (label_x, rect.top + 30)
        label_text = f"{ball.name} {max(0, ball.hp)} HP"
        text_surface = hud_font.render(label_text, True, (255, 245, 230))
        text_rect = text_surface.get_rect(midright=label_center) if align_right else text_surface.get_rect(midleft=label_center)
        shadow_rect = text_rect.move(3, 3)
        surface.blit(hud_font.render(label_text, True, (0, 0, 0)), shadow_rect)
        surface.blit(text_surface, text_rect)

        bar_rect = pygame.Rect(rect.left + 22, rect.top + 61, rect.width - 44, 31)
        ratio = max(0.0, min(1.0, ball.hp / max(1, ball.max_hp)))
        pygame.draw.rect(surface, (61, 54, 48), bar_rect, border_radius=7)
        fill_rect = bar_rect.copy()
        fill_rect.width = round(bar_rect.width * ratio)
        pygame.draw.rect(surface, color, fill_rect, border_radius=7)
        block_count = 10
        block_gap = 4
        block_width = (bar_rect.width - block_gap * (block_count - 1)) // block_count
        for index in range(block_count):
            block = pygame.Rect(bar_rect.left + index * (block_width + block_gap), bar_rect.top, block_width, bar_rect.height)
            pygame.draw.rect(surface, (235, 226, 205), block, width=2, border_radius=4)
        pygame.draw.rect(surface, (235, 226, 205), bar_rect, width=3, border_radius=7)

    left_cd = max(0, left.skill_cooldown // 60)
    right_cd = max(0, right.skill_cooldown // 60)
    draw_panel(left_panel, left, duel_attack_color(left.skin))
    draw_panel(right_panel, right, duel_attack_color(right.skin), align_right=True)
    draw_text_with_shadow(surface, small_font, f"{duel_skill_name(left.skin)} {left_cd}", (left_panel.centerx, left_panel.bottom + 18), (235, 226, 205))
    draw_text_with_shadow(surface, small_font, f"{duel_skill_name(right.skin)} {right_cd}", (right_panel.centerx, right_panel.bottom + 18), (235, 226, 205))

    progress = min(1.0, frame_index / max(1, total_frames))
    progress_rect = pygame.Rect(68, HEIGHT - 126, WIDTH - 136, 8)
    pygame.draw.rect(surface, (58, 48, 41), progress_rect)
    pygame.draw.rect(surface, (235, 226, 205), pygame.Rect(progress_rect.left, progress_rect.top, round(progress_rect.width * progress), progress_rect.height))


def draw_duel_intro(surface: pygame.Surface, frame_index: int, ready_frames: int, intro_frames: int) -> None:
    if frame_index > intro_frames:
        return
    intro_font = make_font(122, bold=True, italic=True)
    title_font = make_font(62, bold=True)
    small_font = make_font(46, bold=True)
    if frame_index <= ready_frames:
        text = "READY"
        color = (255, 238, 128)
    else:
        text = "FIGHT!"
        color = (255, 245, 230)
    draw_text_with_shadow(surface, intro_font, text, (WIDTH // 2, round(HEIGHT * 0.47)), color)
    draw_text_with_shadow(surface, title_font, "PIZZA vs BURGER", (WIDTH // 2, round(HEIGHT * 0.36)), (255, 245, 230))
    draw_text_with_shadow(surface, small_font, "WHO WINS?", (WIDTH // 2, round(HEIGHT * 0.56)), (255, 226, 93))


def apply_duel_skill(
    attacker: DuelBall,
    defender: DuelBall,
    base_damage: int,
    rng: random.Random,
    effects: list[DuelEffect],
    audio_events: list[AudioEvent],
    frame_index: int,
) -> int:
    damage = base_damage
    if attacker.skin == "pizza":
        damage += 6
        effects.append(DuelEffect("cheese", defender.position.copy(), 30, duel_attack_color("pizza"), "CHEESE HIT"))
        audio_events.append(AudioEvent(frame_index, "cheese_stick"))
    elif attacker.skin == "burger" and attacker.charge_frames > 0:
        damage += 35
        effects.append(DuelEffect("charge", defender.position.copy(), 30, duel_attack_color("burger"), "CHARGE HIT"))
        audio_events.append(AudioEvent(frame_index, "charge_hit"))
    elif attacker.skin == "sushi":
        attacker.hp = min(attacker.max_hp, attacker.hp + 14)
    elif attacker.skin == "taco" and rng.random() < 0.35:
        damage *= 2
    elif attacker.skin == "donut":
        damage = max(1, damage - 6)
    elif attacker.skin == "fries":
        damage += 8
    return damage


def update_duel_ball(
    ball: DuelBall,
    target: DuelBall,
    arena_rect: pygame.Rect,
    rng: random.Random,
    audio_events: list[AudioEvent],
    frame_index: int,
    charge_speed: int,
    burger_hp_cost: int,
    ingredient_damage: int,
    allies: list[IngredientAlly],
    effects: list[DuelEffect],
) -> None:
    if ball.skill_cooldown > 0:
        ball.skill_cooldown -= 1
    if ball.hit_cooldown > 0:
        ball.hit_cooldown -= 1
    if ball.charge_frames > 0:
        ball.charge_frames -= 1
    update_food_reload(ball)

    ball.trail.append(ball.position.copy())
    if len(ball.trail) > 10:
        ball.trail.pop(0)

    if ball.skin == "burger" and ball.skill_cooldown == 0:
        direction = target.position - ball.position
        if direction.length_squared() > 0:
            if ball.reload_frames > 0:
                ball.skill_cooldown = 18
            elif len(ball.missing_ingredients) >= 4:
                ball.reload_frames = FPS * 3
                ball.skill_cooldown = 18
            else:
                paid_cost = min(max(0, ball.hp - 1), burger_hp_cost)
                if paid_cost > 0:
                    ball.hp -= paid_cost
                    ingredient_kinds = ["lettuce", "cheese", "tomato", "meat"]
                    ingredient_kind = ingredient_kinds[len(ball.missing_ingredients) % len(ingredient_kinds)]
                    ball.missing_ingredients.append(ingredient_kind)
                    if len(ball.missing_ingredients) >= 4:
                        ball.reload_frames = FPS * 3
                    spawn_direction = -direction.normalize()
                    spawn_offset = spawn_direction.rotate(rng.uniform(-18, 18)) * (ball.radius + round(ball.radius * 0.58))
                    spawn_position = ball.position + spawn_offset
                    target_direction = target.position - spawn_position
                    if target_direction.length_squared() == 0:
                        target_direction = -spawn_direction
                    velocity = target_direction.normalize().rotate(rng.uniform(-16, 16)) * 500
                    allies.append(
                        IngredientAlly(
                            kind=ingredient_kind,
                            position=spawn_position,
                            velocity=velocity,
                            radius=max(46, round(ball.radius * 0.72)),
                            damage=paid_cost,
                            hp=paid_cost,
                            max_hp=paid_cost,
                        )
                    )
                    effects.append(DuelEffect("ingredient", spawn_position, 36, duel_attack_color("burger"), ingredient_kind.upper()))
                    audio_events.append(AudioEvent(frame_index, "ingredient_spawn"))
                ball.velocity = direction.normalize() * charge_speed
                ball.charge_frames = 36
                ball.skill_cooldown = 132
                audio_events.append(AudioEvent(frame_index, "charge_start"))
    elif ball.skill_cooldown == 0 and ball.skin != "pizza":
        ball.velocity.rotate_ip(rng.uniform(-22, 22))
        ball.skill_cooldown = 120

    ball.position += ball.velocity / FPS
    if ball.velocity.length_squared() > 0:
        ball.visual_angle = ball.velocity.as_polar()[1] + 90

    if ball.position.x - ball.radius < arena_rect.left:
        ball.position.x = arena_rect.left + ball.radius
        ball.velocity.x = abs(ball.velocity.x)
    elif ball.position.x + ball.radius > arena_rect.right:
        ball.position.x = arena_rect.right - ball.radius
        ball.velocity.x = -abs(ball.velocity.x)

    if ball.position.y - ball.radius < arena_rect.top:
        ball.position.y = arena_rect.top + ball.radius
        ball.velocity.y = abs(ball.velocity.y)
    elif ball.position.y + ball.radius > arena_rect.bottom:
        ball.position.y = arena_rect.bottom - ball.radius
        ball.velocity.y = -abs(ball.velocity.y)


def apply_burn(ball: DuelBall, popups: list[DamagePopup], effects: list[DuelEffect], audio_events: list[AudioEvent], frame_index: int) -> int:
    if ball.burn_frames <= 0:
        return 0
    ball.burn_frames -= 1
    ball.burn_tick -= 1
    if ball.burn_tick > 0:
        return 0
    ball.burn_tick = 15
    damage = min(ball.hp, 4)
    ball.hp -= damage
    popups.append(DamagePopup(amount=damage, position=ball.position.copy()))
    effects.append(DuelEffect("burn", ball.position.copy(), 18, (255, 172, 58), "FIRE"))
    audio_events.append(AudioEvent(frame_index, "fire_tick"))
    return damage


def fire_cheese_projectile(
    attacker: DuelBall,
    target: DuelBall,
    projectiles: list[CheeseProjectile],
    effects: list[DuelEffect],
    audio_events: list[AudioEvent],
    frame_index: int,
    speed: int,
) -> None:
    if attacker.reload_frames > 0:
        attacker.skill_cooldown = 18
        return
    if attacker.cheese_spent >= 4:
        attacker.reload_frames = FPS * 3
        attacker.skill_cooldown = 18
        return
    direction = target.position - attacker.position
    if direction.length_squared() == 0:
        direction = pygame.Vector2(1, 0)
    direction = direction.normalize()
    start = attacker.position + direction * (attacker.radius + 24)
    projectiles.append(CheeseProjectile(position=start, velocity=direction * speed))
    attacker.cheese_spent += 1
    if attacker.cheese_spent >= 4:
        attacker.reload_frames = FPS * 3
    attacker.skill_cooldown = 96
    effects.append(DuelEffect("cheese", start.copy(), 24, (255, 228, 82), "CHEESE SHOT"))
    audio_events.append(AudioEvent(frame_index, "cheese_shot"))


def update_cheese_projectiles(
    projectiles: list[CheeseProjectile],
    patches: list[CheesePatch],
    target_side: str,
    target: DuelBall,
    effects: list[DuelEffect],
    audio_events: list[AudioEvent],
    frame_index: int,
) -> None:
    remaining: list[CheeseProjectile] = []
    for projectile in projectiles:
        projectile.position += projectile.velocity / FPS
        projectile.frames_left -= 1
        if projectile.position.distance_to(target.position) <= target.radius + projectile.radius:
            offset = projectile.position - target.position
            if offset.length_squared() == 0:
                offset = pygame.Vector2(0, -target.radius * 0.5)
            offset = offset.rotate(-target.visual_angle)
            patches.append(CheesePatch(attached_to=target_side, offset=offset))
            effects.append(DuelEffect("cheese", projectile.position.copy(), 36, (255, 228, 82), "STICKY"))
            audio_events.append(AudioEvent(frame_index, "cheese_stick"))
            continue
        if projectile.frames_left > 0:
            remaining.append(projectile)
    projectiles[:] = remaining


def update_cheese_patches(
    patches: list[CheesePatch],
    left: DuelBall,
    right: DuelBall,
    damage: int,
    popups: list[DamagePopup],
    effects: list[DuelEffect],
    audio_events: list[AudioEvent],
    frame_index: int,
) -> int:
    total_damage = 0
    remaining: list[CheesePatch] = []
    for patch in patches:
        target = duel_ball_by_side(patch.attached_to, left, right)
        patch.frames_left -= 1
        patch.tick_frames -= 1
        if patch.tick_frames <= 0 and target.hp > 0:
            patch.tick_frames = 30
            dealt = min(target.hp, damage)
            target.hp -= dealt
            total_damage += dealt
            position = target.position + patch.offset.rotate(target.visual_angle)
            popups.append(make_damage_popup(dealt, position, duel_attack_color("pizza")))
            effects.append(DuelEffect("cheese", position, 18, duel_attack_color("pizza"), "MELT"))
            audio_events.append(AudioEvent(frame_index, "cheese_tick"))
        if patch.frames_left > 0 and target.hp > 0:
            remaining.append(patch)
    patches[:] = remaining
    return total_damage


def update_ingredient_allies(
    allies: list[IngredientAlly],
    target: DuelBall,
    arena_rect: pygame.Rect,
    popups: list[DamagePopup],
    effects: list[DuelEffect],
    audio_events: list[AudioEvent],
    frame_index: int,
) -> int:
    total_damage = 0
    remaining: list[IngredientAlly] = []
    for ally in allies:
        if ally.hit_cooldown > 0:
            ally.hit_cooldown -= 1
        ally.frames_left -= 1
        ally.position += ally.velocity / FPS
        if ally.velocity.length_squared() > 0:
            ally.visual_angle = ally.velocity.as_polar()[1] + 90

        if ally.position.x - ally.radius < arena_rect.left or ally.position.x + ally.radius > arena_rect.right:
            ally.velocity.x *= -1
        if ally.position.y - ally.radius < arena_rect.top or ally.position.y + ally.radius > arena_rect.bottom:
            ally.velocity.y *= -1
        ally.position.x = max(arena_rect.left + ally.radius, min(arena_rect.right - ally.radius, ally.position.x))
        ally.position.y = max(arena_rect.top + ally.radius, min(arena_rect.bottom - ally.radius, ally.position.y))

        if ally.hit_cooldown == 0 and ally.position.distance_to(target.position) <= target.radius + ally.radius:
            dealt = min(target.hp, ally.hp)
            target.hp -= dealt
            ally.hp = 0
            popups.append(make_damage_popup(dealt, target.position.copy(), duel_attack_color("burger")))
            effects.append(DuelEffect("ingredient", ally.position.copy(), 24, duel_attack_color("burger"), ally.kind.upper()))
            if dealt >= 25:
                effect_frames = 34 if dealt >= 50 else 28
                effects.append(DuelEffect("impact", target.position.copy(), effect_frames, duel_attack_color("burger"), "CRITICAL!" if dealt >= 50 else ""))
            audio_events.append(AudioEvent(frame_index, "ingredient_hit"))
            audio_events.append(AudioEvent(frame_index, damage_audio_kind(dealt)))
            ally.hit_cooldown = 42
            total_damage += dealt

        if ally.frames_left > 0 and ally.hp > 0 and target.hp > 0:
            remaining.append(ally)
    allies[:] = remaining
    return total_damage


def handle_duel_collision(
    left: DuelBall,
    right: DuelBall,
    base_damage: int,
    popups: list[DamagePopup],
    effects: list[DuelEffect],
    audio_events: list[AudioEvent],
    frame_index: int,
    rng: random.Random,
) -> tuple[bool, bool, int]:
    delta = right.position - left.position
    distance = delta.length()
    min_distance = left.radius + right.radius
    if distance <= 0 or distance >= min_distance:
        return False, False, 0

    normal = delta.normalize()
    overlap = min_distance - distance
    left.position -= normal * (overlap / 2)
    right.position += normal * (overlap / 2)
    left.velocity = left.velocity.reflect(normal)
    right.velocity = right.velocity.reflect(-normal)
    audio_events.append(AudioEvent(frame_index, "impact"))
    hit_landed = False
    burger_charge_hit = False
    max_damage = 0

    if left.hit_cooldown == 0:
        was_burger_charge = left.skin == "burger" and left.charge_frames > 0
        damage = min(right.hp, apply_duel_skill(left, right, base_damage, rng, effects, audio_events, frame_index))
        right.hp -= damage
        left.total_damage_dealt += damage
        left.hits += 1
        left.hit_cooldown = 28
        popups.append(make_damage_popup(damage, right.position.copy(), duel_attack_color(left.skin)))
        if damage >= 25:
            effect_frames = 34 if damage >= 50 else 28
            effects.append(DuelEffect("impact", right.position.copy(), effect_frames, duel_attack_color(left.skin), "CRITICAL!" if damage >= 50 else ""))
        audio_events.append(AudioEvent(frame_index, damage_audio_kind(damage)))
        hit_landed = True
        burger_charge_hit = burger_charge_hit or was_burger_charge
        max_damage = max(max_damage, damage)

    if right.hit_cooldown == 0:
        was_burger_charge = right.skin == "burger" and right.charge_frames > 0
        damage = min(left.hp, apply_duel_skill(right, left, base_damage, rng, effects, audio_events, frame_index))
        left.hp -= damage
        right.total_damage_dealt += damage
        right.hits += 1
        right.hit_cooldown = 28
        popups.append(make_damage_popup(damage, left.position.copy(), duel_attack_color(right.skin)))
        if damage >= 25:
            effect_frames = 34 if damage >= 50 else 28
            effects.append(DuelEffect("impact", left.position.copy(), effect_frames, duel_attack_color(right.skin), "CRITICAL!" if damage >= 50 else ""))
        audio_events.append(AudioEvent(frame_index, damage_audio_kind(damage)))
        hit_landed = True
        burger_charge_hit = burger_charge_hit or was_burger_charge
        max_damage = max(max_damage, damage)
    return hit_landed, burger_charge_hit, max_damage


def draw_duel_result(
    surface: pygame.Surface,
    winner: DuelBall,
    loser: DuelBall,
    frame_index: int,
    fps: int,
    result_started_frame: int | None = None,
) -> None:
    draw_duel_background(surface)
    progress = 1.0
    if result_started_frame is not None:
        progress = max(0.0, min(1.0, (frame_index - result_started_frame) / max(1, fps * 1.2)))
    ease = 1 - (1 - progress) * (1 - progress)

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, round(92 + ease * 74)))
    surface.blit(overlay, (0, 0))

    focus = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    focus_center = (WIDTH // 2, round(HEIGHT * 0.48))
    spotlight_radius = round(winner.radius * (2.4 + ease * 1.4))
    pygame.draw.circle(focus, (*duel_attack_color(winner.skin), 54), focus_center, spotlight_radius)
    pygame.draw.circle(focus, (255, 255, 255, 210), focus_center, round(spotlight_radius * 0.72), width=6)
    surface.blit(focus, (0, 0))

    focus_ball = DuelBall(
        name=winner.name,
        skin=winner.skin,
        color=winner.color,
        hp=winner.hp,
        max_hp=winner.max_hp,
        position=pygame.Vector2(focus_center),
        velocity=pygame.Vector2(0, 0),
        radius=round(winner.radius * (1.3 + ease * 0.62)),
        total_damage_dealt=winner.total_damage_dealt,
        hits=winner.hits,
        visual_angle=winner.visual_angle + progress * 10,
    )
    draw_duel_ball(surface, focus_ball, make_font(max(58, round(focus_ball.radius * 0.38)), bold=True))

    headline_font = make_font(118, bold=True, italic=True)
    result_font = make_font(50, bold=True)
    draw_text_with_shadow(surface, headline_font, f"{winner.name} WINS", (WIDTH // 2, round(HEIGHT * 0.24)), duel_attack_color(winner.skin))
    draw_text_with_shadow(surface, result_font, "THIS FOOD WINS", (WIDTH // 2, round(HEIGHT * 0.68)), (255, 245, 230))
    draw_text_with_shadow(surface, result_font, f"Damage {winner.total_damage_dealt}  Hits {winner.hits}", (WIDTH // 2, round(HEIGHT * 0.74)), (220, 232, 255))
    draw_text_with_shadow(
        surface,
        make_font(40, bold=True),
        f"{loser.name} HP {max(0, loser.hp)}",
        (WIDTH // 2, round(HEIGHT * 0.80)),
        duel_attack_color(loser.skin),
    )


def run_food_duel(
    frame_count: int,
    show_window: bool,
    damage: int,
    seed: int,
    fps: int,
    output_name: str,
    config: SimulationConfig,
) -> dict:
    pygame.init()
    render_surface = pygame.Surface((WIDTH, HEIGHT))
    preview_screen = None
    clock = pygame.time.Clock()
    if show_window:
        preview_size = (round(WIDTH * DISPLAY_SCALE), round(HEIGHT * DISPLAY_SCALE))
        preview_screen = pygame.display.set_mode(preview_size)
        pygame.display.set_caption("Food Skill Battle")

    clear_frames_dir()
    rng = random.Random(seed)
    radius = config.duel_ball_radius
    speed_scale = max(0.2, config.duel_speed_scale)
    charge_speed = max(240, config.duel_charge_speed)
    burger_hp_cost = max(0, config.duel_burger_charge_hp_cost)
    ingredient_damage = max(1, config.duel_ingredient_damage)
    cheese_damage = max(1, config.duel_cheese_damage)
    cheese_projectile_speed = max(200, config.duel_cheese_projectile_speed)
    arena_rect = duel_arena_rect()
    center = pygame.Vector2(arena_rect.center)
    left_style = FOOD_BALL_STYLES.get(config.duel_left_food, FOOD_BALL_STYLES["pizza"])
    right_style = FOOD_BALL_STYLES.get(config.duel_right_food, FOOD_BALL_STYLES["burger"])
    left = DuelBall(
        name=food_label(config.duel_left_food),
        skin=config.duel_left_food,
        color=left_style["color"],
        hp=config.duel_left_hp,
        max_hp=config.duel_left_hp,
        position=center + pygame.Vector2(-radius * 1.65, -radius * 0.38),
        velocity=pygame.Vector2(760, 220) * speed_scale,
        radius=radius,
    )
    right = DuelBall(
        name=food_label(config.duel_right_food),
        skin=config.duel_right_food,
        color=right_style["color"],
        hp=config.duel_right_hp,
        max_hp=config.duel_right_hp,
        position=center + pygame.Vector2(radius * 1.65, radius * 0.38),
        velocity=pygame.Vector2(-820, -180) * speed_scale,
        radius=radius,
    )
    popups: list[DamagePopup] = []
    duel_effects: list[DuelEffect] = []
    cheese_projectiles: list[CheeseProjectile] = []
    cheese_patches: list[CheesePatch] = []
    ingredient_allies: list[IngredientAlly] = []
    ready_frames = max(18, round(fps * 0.38))
    intro_frames = max(36, round(fps * 0.72))
    audio_events: list[AudioEvent] = [AudioEvent(1, "ready"), AudioEvent(ready_frames + 1, "fight")]
    result_frame_count = fps * 3
    winner: DuelBall | None = None
    loser: DuelBall | None = None
    result_started_frame: int | None = None
    frames_rendered = 0
    hit_stop_frames = 0
    shake_frames = 0
    shake_strength = 0

    frame_index = 0
    while True:
        frame_index += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                result = {"status": "STOPPED", "frames_rendered": frames_rendered, "theme": config.theme}
                write_result(result)
                return result

        if winner is None:
            arena_rect = draw_duel_background(render_surface)
            if winner is None and frame_index > intro_frames:
                if hit_stop_frames <= 0:
                    update_duel_ball(
                        left,
                        right,
                        arena_rect,
                        rng,
                        audio_events,
                        frame_index,
                        charge_speed,
                        burger_hp_cost,
                        ingredient_damage,
                        ingredient_allies,
                        duel_effects,
                    )
                    update_duel_ball(
                        right,
                        left,
                        arena_rect,
                        rng,
                        audio_events,
                        frame_index,
                        charge_speed,
                        burger_hp_cost,
                        ingredient_damage,
                        ingredient_allies,
                        duel_effects,
                    )
                    if left.skin == "pizza" and left.skill_cooldown == 0:
                        fire_cheese_projectile(
                            left,
                            right,
                            cheese_projectiles,
                            duel_effects,
                            audio_events,
                            frame_index,
                            cheese_projectile_speed,
                        )
                    update_cheese_projectiles(cheese_projectiles, cheese_patches, "right", right, duel_effects, audio_events, frame_index)
                    cheese_damage_done = update_cheese_patches(
                        cheese_patches,
                        left,
                        right,
                        cheese_damage,
                        popups,
                        duel_effects,
                        audio_events,
                        frame_index,
                    )
                    if cheese_damage_done > 0:
                        left.total_damage_dealt += cheese_damage_done
                    ally_damage = update_ingredient_allies(
                        ingredient_allies,
                        left,
                        arena_rect,
                        popups,
                        duel_effects,
                        audio_events,
                        frame_index,
                    )
                    hit_landed, burger_charge_hit, hit_damage = handle_duel_collision(left, right, damage, popups, duel_effects, audio_events, frame_index, rng)
                    if ally_damage > 0:
                        right.total_damage_dealt += ally_damage
                    if burger_charge_hit:
                        hit_stop_frames = 7
                        shake_frames = 16
                        shake_strength = 22
                    elif hit_damage >= 50 or ally_damage >= 50:
                        shake_frames = max(shake_frames, 18)
                        shake_strength = max(shake_strength, 24)
                    elif hit_damage >= 25 or ally_damage >= 25:
                        shake_frames = max(shake_frames, 10)
                        shake_strength = max(shake_strength, 13)
                    elif hit_landed:
                        shake_frames = max(shake_frames, 3)
                        shake_strength = max(shake_strength, 3)
                else:
                    hit_stop_frames -= 1

            if winner is None and (left.hp <= 0 or right.hp <= 0):
                winner, loser = (left, right) if left.hp > right.hp else (right, left)
                result_started_frame = frame_index + 1
                audio_events.append(AudioEvent(frame_index + 1, "victory"))

            ball_font = make_font(max(48, round(radius * 0.43)), bold=True)
            if winner is None:
                draw_duel_effects(render_surface, duel_effects)
                draw_cheese_projectiles(render_surface, cheese_projectiles)
                draw_ingredient_allies(render_surface, ingredient_allies)
                draw_duel_ball(render_surface, left, ball_font)
                draw_duel_ball(render_surface, right, ball_font)
                draw_cheese_patches(render_surface, cheese_patches, left, right)
                draw_duel_intro(render_surface, frame_index, ready_frames, intro_frames)

                for popup in popups:
                    progress = 1 - (popup.frames_left / max(1, popup.total_frames))
                    lift = 42 + 54 * popup.scale
                    wobble = math.sin(progress * math.pi * 3) * 6 * popup.scale
                    center = (round(popup.position.x + wobble), round(popup.position.y - progress * lift))
                    dynamic_popup_font = make_font(max(28, round(50 * popup.scale)), bold=True, italic=True)
                    draw_text_with_shadow(render_surface, dynamic_popup_font, f"-{popup.amount}", center, popup.color)
                    if popup.label:
                        label_font = make_font(round(28 * popup.scale), bold=True, italic=True)
                        draw_text_with_shadow(render_surface, label_font, popup.label, (center[0], center[1] - round(42 * popup.scale)), popup.color)
                    popup.frames_left -= 1
                popups = [popup for popup in popups if popup.frames_left > 0]
                for effect in duel_effects:
                    effect.frames_left -= 1
                duel_effects = [effect for effect in duel_effects if effect.frames_left > 0]
                draw_duel_hud(render_surface, left, right, frame_index, max(frame_count, frame_index + result_frame_count))
            else:
                draw_duel_result(render_surface, winner, loser or left, frame_index, fps, result_started_frame)
        else:
            if result_started_frame is None:
                result_started_frame = frame_index
            draw_duel_result(render_surface, winner, loser or left, frame_index, fps, result_started_frame)

        if shake_frames > 0 and winner is None:
            frame_copy = render_surface.copy()
            render_surface.fill((0, 0, 0))
            offset_x = rng.randint(-shake_strength, shake_strength)
            offset_y = rng.randint(-shake_strength, shake_strength)
            render_surface.blit(frame_copy, (offset_x, offset_y))
            shake_frames -= 1
            shake_strength = max(4, round(shake_strength * 0.84))

        frame_path = FRAMES_DIR / f"frame_{frame_index:06d}.jpg"
        pygame.image.save(render_surface, str(frame_path))
        frames_rendered = frame_index

        if preview_screen is not None:
            scaled_surface = pygame.transform.smoothscale(render_surface, preview_screen.get_size())
            preview_screen.blit(scaled_surface, (0, 0))
            pygame.display.flip()
            clock.tick(fps)

        if winner is not None and result_started_frame is not None:
            if frame_index - result_started_frame + 1 >= result_frame_count:
                break

    if winner is None:
        winner, loser = (left, right) if left.hp >= right.hp else (right, left)
        result_started_frame = frames_rendered
        audio_events.append(AudioEvent(frames_rendered, "victory"))

    pygame.quit()
    result = {
        "status": "CLEAR",
        "theme": config.theme,
        "winner": winner.name,
        "loser": loser.name if loser is not None else None,
        "left": {
            "name": left.name,
            "food": left.skin,
            "hp_start": left.max_hp,
            "hp_end": max(0, left.hp),
            "skill": duel_skill_name(left.skin),
            "hits": left.hits,
            "total_damage_dealt": left.total_damage_dealt,
        },
        "right": {
            "name": right.name,
            "food": right.skin,
            "hp_start": right.max_hp,
            "hp_end": max(0, right.hp),
            "skill": duel_skill_name(right.skin),
            "hits": right.hits,
            "total_damage_dealt": right.total_damage_dealt,
        },
        "base_damage": damage,
        "ball_radius": radius,
        "speed_scale": speed_scale,
        "charge_speed": charge_speed,
        "burger_charge_hp_cost": burger_hp_cost,
        "ingredient_damage": ingredient_damage,
        "cheese_damage": cheese_damage,
        "cheese_projectile_speed": cheese_projectile_speed,
        "ingredient_ally_count": len(ingredient_allies),
        "cheese_patch_count": len(cheese_patches),
        "frames_rendered": frames_rendered,
        "result_started_frame": result_started_frame,
        "fps": fps,
        "video_width": WIDTH,
        "video_height": HEIGHT,
        "random_seed": seed,
        "output_name": output_name,
        "audio_events": [{"frame": event.frame, "kind": event.kind} for event in audio_events],
    }
    write_result(result)
    print(json.dumps(result, indent=2))
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a minimal 2D ball simulation.")
    parser.add_argument("--config", type=Path, help="Path to a simulation JSON config.")
    parser.add_argument("--frames", type=int, help="Number of frames to simulate and save.")
    parser.add_argument("--balls", type=int, help="Initial number of balls.")
    parser.add_argument("--boss-hp", type=int, help="Initial boss HP.")
    parser.add_argument("--damage", type=int, help="Damage dealt when the ball hits the boss.")
    parser.add_argument("--seed", type=int, help="Random seed for reproducible simulations.")
    window_group = parser.add_mutually_exclusive_group()
    window_group.add_argument("--window", action="store_true", help="Show a scaled preview window while generating.")
    window_group.add_argument("--no-window", action="store_true", help="Generate frames without opening a window.")
    return parser.parse_args()


def write_result(result: dict) -> None:
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")


def run(
    frame_count: int,
    show_window: bool,
    ball_count: int,
    boss_max_hp: int,
    damage: int,
    seed: int,
    fps: int,
    item_spawn_interval: int,
    output_name: str,
    config: SimulationConfig | None = None,
) -> dict:
    if frame_count < 1:
        raise ValueError("--frames must be 1 or greater.")
    if ball_count < 1:
        raise ValueError("--balls must be 1 or greater.")
    if boss_max_hp < 1:
        raise ValueError("--boss-hp must be 1 or greater.")
    if damage < 1:
        raise ValueError("--damage must be 1 or greater.")
    if fps < 1:
        raise ValueError("fps must be 1 or greater.")
    if item_spawn_interval < 1:
        raise ValueError("item_spawn_interval must be 1 or greater.")

    run_config = config or SimulationConfig(
        video_width=WIDTH,
        video_height=HEIGHT,
        fps=fps,
        duration_seconds=max(1, frame_count // fps),
        initial_ball_count=ball_count,
        boss_hp=boss_max_hp,
        base_damage=damage,
        item_spawn_interval=item_spawn_interval,
        random_seed=seed,
        output_name=output_name,
    )
    if run_config.theme == "food_duel":
        return run_food_duel(
            frame_count=frame_count,
            show_window=show_window,
            damage=damage,
            seed=seed,
            fps=fps,
            output_name=output_name,
            config=run_config,
        )

    pygame.init()
    render_surface = pygame.Surface((WIDTH, HEIGHT))
    background = create_background()
    preview_screen = None
    clock = pygame.time.Clock()

    if show_window:
        preview_size = (round(WIDTH * DISPLAY_SCALE), round(HEIGHT * DISPLAY_SCALE))
        preview_screen = pygame.display.set_mode(preview_size)
        pygame.display.set_caption("Minimal 2D Physics Simulation")

    clear_frames_dir()

    rng = random.Random(seed)
    space = pymunk.Space()
    space.gravity = 0, 0
    add_walls(space)
    balls = create_balls(space, rng, run_config, damage)
    items: list[Item] = []
    effects: list[Effect] = []
    popups: list[DamagePopup] = []
    boss_hp = boss_max_hp
    status = None
    frames_rendered = 0
    total_damage = 0
    damage_up_count = 0
    speed_up_count = 0
    item_spawn_count = 0
    result_frame_count = min(fps * 3, max(1, frame_count // 2))
    simulation_frame_limit = frame_count - result_frame_count
    clear_frame = None
    result_started_frame = None

    for frame_index in range(1, frame_count + 1):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                result = {
                    "status": "STOPPED",
                    "boss_hp_start": boss_max_hp,
                    "boss_hp_end": boss_hp,
                    "ball_count": ball_count,
                    "frames_rendered": frames_rendered,
                }
                write_result(result)
                return result

        if status is None and frame_index > simulation_frame_limit:
            status = FAILED

        if status is None:
            if frame_index >= ITEM_START_FRAME and (frame_index - ITEM_START_FRAME) % item_spawn_interval == 0:
                if len(items) < MAX_ITEMS:
                    items.append(spawn_item(rng, balls, item_spawn_count))
                    item_spawn_count += 1

            for ball in balls:
                boss_hp, total_damage, dealt = handle_boss_collision(ball, boss_hp, total_damage)
                if dealt > 0:
                    popup_position = pygame.Vector2(ball.body.position.x, max(HP_BAR_RECT.bottom + 70, BOSS_RECT.top - 20))
                    popups.append(make_damage_popup(dealt, popup_position, (255, 230, 95)))
                limit_ball_speed(ball)

            if boss_hp <= 0:
                status = CLEAR
                clear_frame = frame_index

            draw(render_surface, background, balls, items, effects, popups, boss_hp, boss_max_hp, status)

            for effect in effects:
                effect.frames_left -= 1
            effects = [effect for effect in effects if effect.frames_left > 0]
            for popup in popups:
                popup.frames_left -= 1
            popups = [popup for popup in popups if popup.frames_left > 0]

            gained_damage_up, gained_speed_up = handle_item_collisions(balls, items, effects)
            damage_up_count += gained_damage_up
            speed_up_count += gained_speed_up

            if status is None:
                space.step(1 / fps)
        else:
            if result_started_frame is None:
                result_started_frame = frame_index
            draw_result_screen(
                render_surface,
                status,
                boss_hp,
                boss_max_hp,
                total_damage,
                find_top_damage_ball(balls),
                clear_frame,
                fps,
            )

        frame_path = FRAMES_DIR / f"frame_{frame_index:06d}.png"
        pygame.image.save(render_surface, str(frame_path))
        frames_rendered = frame_index

        if preview_screen is not None:
            scaled_surface = pygame.transform.smoothscale(render_surface, preview_screen.get_size())
            preview_screen.blit(scaled_surface, (0, 0))
            pygame.display.flip()
            clock.tick(fps)

        if status == CLEAR and result_started_frame is not None:
            if frame_index - result_started_frame + 1 >= result_frame_count:
                break

    if status is None:
        status = FAILED
        result_started_frame = frames_rendered
        draw_result_screen(
            render_surface,
            status,
            boss_hp,
            boss_max_hp,
            total_damage,
            find_top_damage_ball(balls),
            clear_frame,
            fps,
        )
        frame_path = FRAMES_DIR / f"frame_{frames_rendered:06d}.png"
        pygame.image.save(render_surface, str(frame_path))

    pygame.quit()
    top_ball = find_top_damage_ball(balls)
    result = {
        "status": status,
        "boss_hp_start": boss_max_hp,
        "boss_hp_end": boss_hp,
        "base_damage": damage,
        "ball_count": ball_count,
        "actual_ball_count": len(balls),
        "theme": run_config.theme,
        "fibonacci_count": run_config.fibonacci_count if run_config.theme == "fibonacci_vs_exponential" else 0,
        "exponential_count": run_config.exponential_count if run_config.theme == "fibonacci_vs_exponential" else 0,
        "total_damage": total_damage,
        "damage_up_collected": damage_up_count,
        "speed_up_collected": speed_up_count,
        "max_ball_damage": top_ball.max_hit_damage,
        "top_ball": {
            "id": top_ball.ball_id,
            "damage": top_ball.damage,
            "max_hit_damage": top_ball.max_hit_damage,
            "hits": top_ball.hits,
            "total_damage_dealt": top_ball.total_damage_dealt,
            "damage_level": top_ball.damage_level,
            "speed_level": top_ball.speed_level,
        },
        "max_speed_level": max(ball.speed_level for ball in balls),
        "frames_rendered": frames_rendered,
        "result_started_frame": result_started_frame,
        "result_frames": frames_rendered - result_started_frame + 1 if result_started_frame is not None else 0,
        "clear_frame": clear_frame,
        "clear_time_seconds": round(clear_frame / fps, 3) if clear_frame is not None else None,
        "fps": fps,
        "video_width": WIDTH,
        "video_height": HEIGHT,
        "item_spawn_interval": item_spawn_interval,
        "random_seed": seed,
        "output_name": output_name,
    }
    write_result(result)
    print(json.dumps(result, indent=2))
    return result


def main() -> None:
    args = parse_args()
    ensure_default_config()
    config = load_config(args.config)
    if args.frames is not None:
        frame_count = args.frames
    else:
        frame_count = config.frame_count

    ball_count = args.balls if args.balls is not None else config.initial_ball_count
    boss_hp = args.boss_hp if args.boss_hp is not None else config.boss_hp
    damage = args.damage if args.damage is not None else config.base_damage
    seed = args.seed if args.seed is not None else config.random_seed
    update_layout(config.video_width, config.video_height)

    show_window = args.window and not args.no_window
    run(
        frame_count=frame_count,
        show_window=show_window,
        ball_count=ball_count,
        boss_max_hp=boss_hp,
        damage=damage,
        seed=seed,
        fps=config.fps,
        item_spawn_interval=config.item_spawn_interval,
        output_name=config.output_name,
        config=config,
    )


if __name__ == "__main__":
    main()
