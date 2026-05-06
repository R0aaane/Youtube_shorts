from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import random
from pathlib import Path

import pygame
import pymunk


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "boss_battle_001.json"
FRAMES_DIR = PROJECT_ROOT / "output" / "frames"
METADATA_DIR = PROJECT_ROOT / "output" / "metadata"
RESULT_PATH = METADATA_DIR / "simulation_result.json"

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
ITEM_RADIUS = 28
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
}


@dataclass
class BallState:
    ball_id: int
    body: pymunk.Body
    damage: int
    team: str = "boss"
    label: str = ""
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


def update_layout(width: int, height: int) -> None:
    global WIDTH, HEIGHT, BOSS_RECT, HP_BAR_RECT
    WIDTH = width
    HEIGHT = height
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
    return BallState(ball_id=ball_id, body=body, damage=damage, team=team, label=label, color=color)


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


def create_balls(space: pymunk.Space, rng: random.Random, config: SimulationConfig, damage: int) -> list[BallState]:
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
    boss_title = "NUMBER HP WALL" if any(ball.team in {"fibonacci", "exponential"} for ball in balls) else "HP BOSS"
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
        draw_text(surface, item_font, ball.label or str(ball.damage), position, (7, 20, 32))

    for effect in effects:
        progress = 1 - (effect.frames_left / EFFECT_FRAMES)
        radius = round(34 + progress * 48)
        color = item_color(effect.kind)
        pygame.draw.circle(surface, color, (round(effect.position.x), round(effect.position.y)), radius, width=5)

    for popup in popups:
        progress = 1 - (popup.frames_left / POPUP_FRAMES)
        y_offset = round(progress * 62)
        center = (round(popup.position.x), round(popup.position.y) - y_offset)
        draw_text_with_shadow(surface, popup_font, f"-{popup.amount}", center, (255, 230, 95))

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

    subtitle = "100 Fibonacci VS Exponential" if top_ball.team in {"fibonacci", "exponential"} else "Evolving Balls vs HP Boss"
    draw_text_with_shadow(surface, small_font, subtitle, (WIDTH // 2, round(HEIGHT * 0.86)), (190, 204, 224))


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
                    popups.append(DamagePopup(amount=dealt, position=popup_position))
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
