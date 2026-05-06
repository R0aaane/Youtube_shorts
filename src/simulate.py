from __future__ import annotations

import argparse
import json
from pathlib import Path

import pygame
import pymunk


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRAMES_DIR = PROJECT_ROOT / "output" / "frames"
METADATA_DIR = PROJECT_ROOT / "output" / "metadata"
RESULT_PATH = METADATA_DIR / "simulation_result.json"

WIDTH = 1080
HEIGHT = 1920
FPS = 60
DEFAULT_FRAMES = 600
BALL_RADIUS = 36
WALL_THICKNESS = 8
DISPLAY_SCALE = 0.4
BOSS_MAX_HP = 10000
BALL_DAMAGE = 10
BOSS_RECT = pygame.Rect(260, 240, 560, 180)
HP_BAR_RECT = pygame.Rect(80, 64, 920, 42)
HIT_COOLDOWN_FRAMES = 5
CLEAR = "CLEAR"
FAILED = "FAILED"


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


def add_ball(space: pymunk.Space) -> pymunk.Body:
    mass = 1.0
    moment = pymunk.moment_for_circle(mass, 0, BALL_RADIUS)
    body = pymunk.Body(mass, moment)
    body.position = WIDTH / 2, HEIGHT / 2
    body.velocity = 520, 780

    shape = pymunk.Circle(body, BALL_RADIUS)
    shape.elasticity = 1.0
    shape.friction = 0.0
    space.add(body, shape)
    return body


def clear_frames_dir() -> None:
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    for frame_path in FRAMES_DIR.glob("*.png"):
        frame_path.unlink(missing_ok=True)


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
    ball: pymunk.Body,
    boss_hp: int,
    damage: int,
    hit_cooldown: int,
) -> tuple[int, int]:
    collided, normal = circle_rect_collision(ball.position, BALL_RADIUS, BOSS_RECT)
    if not collided:
        return boss_hp, max(0, hit_cooldown - 1)

    velocity = pygame.Vector2(ball.velocity.x, ball.velocity.y)
    if velocity.dot(normal) < 0:
        reflected = velocity.reflect(normal)
        ball.velocity = reflected.x, reflected.y

    ball.position = ball.position.x + normal.x * 8, ball.position.y + normal.y * 8
    if hit_cooldown > 0:
        return boss_hp, hit_cooldown - 1

    return max(0, boss_hp - damage), HIT_COOLDOWN_FRAMES


def draw_text(surface: pygame.Surface, font: pygame.font.Font, text: str, center: tuple[int, int], color: tuple[int, int, int]) -> None:
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=center)
    surface.blit(text_surface, text_rect)


def draw(surface: pygame.Surface, ball: pymunk.Body, boss_hp: int, boss_max_hp: int, status: str | None) -> None:
    title_font = pygame.font.SysFont("arial", 48, bold=True)
    hp_font = pygame.font.SysFont("arial", 36, bold=True)
    status_font = pygame.font.SysFont("arial", 86, bold=True)

    surface.fill((15, 18, 24))
    pygame.draw.rect(surface, (230, 236, 242), surface.get_rect(), width=WALL_THICKNESS)

    pygame.draw.rect(surface, (165, 48, 62), BOSS_RECT, border_radius=14)
    pygame.draw.rect(surface, (230, 236, 242), BOSS_RECT, width=5, border_radius=14)
    draw_text(surface, title_font, "HP BOSS", BOSS_RECT.center, (255, 245, 230))

    hp_ratio = boss_hp / boss_max_hp if boss_max_hp > 0 else 0
    hp_ratio = max(0.0, min(1.0, hp_ratio))
    pygame.draw.rect(surface, (46, 52, 64), HP_BAR_RECT, border_radius=10)
    hp_fill = pygame.Rect(HP_BAR_RECT.left, HP_BAR_RECT.top, round(HP_BAR_RECT.width * hp_ratio), HP_BAR_RECT.height)
    pygame.draw.rect(surface, (242, 190, 76), hp_fill, border_radius=10)
    pygame.draw.rect(surface, (230, 236, 242), HP_BAR_RECT, width=4, border_radius=10)
    draw_text(surface, hp_font, f"HP {boss_hp}/{boss_max_hp}", HP_BAR_RECT.center, (255, 255, 255))

    pygame.draw.circle(
        surface,
        (68, 180, 255),
        (round(ball.position.x), round(ball.position.y)),
        BALL_RADIUS,
    )

    if status is not None:
        color = (104, 232, 143) if status == CLEAR else (255, 105, 105)
        draw_text(surface, status_font, status, (WIDTH // 2, HEIGHT // 2), color)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a minimal 2D ball simulation.")
    parser.add_argument("--frames", type=int, default=DEFAULT_FRAMES, help="Number of frames to simulate and save.")
    parser.add_argument("--boss-hp", type=int, default=BOSS_MAX_HP, help="Initial boss HP.")
    parser.add_argument("--damage", type=int, default=BALL_DAMAGE, help="Damage dealt when the ball hits the boss.")
    window_group = parser.add_mutually_exclusive_group()
    window_group.add_argument("--window", action="store_true", help="Show a scaled preview window while generating.")
    window_group.add_argument("--no-window", action="store_true", help="Generate frames without opening a window.")
    return parser.parse_args()


def write_result(result: dict) -> None:
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")


def run(frame_count: int, show_window: bool, boss_max_hp: int, damage: int) -> dict:
    if frame_count < 1:
        raise ValueError("--frames must be 1 or greater.")
    if boss_max_hp < 1:
        raise ValueError("--boss-hp must be 1 or greater.")
    if damage < 1:
        raise ValueError("--damage must be 1 or greater.")

    pygame.init()
    render_surface = pygame.Surface((WIDTH, HEIGHT))
    preview_screen = None
    clock = pygame.time.Clock()

    if show_window:
        preview_size = (round(WIDTH * DISPLAY_SCALE), round(HEIGHT * DISPLAY_SCALE))
        preview_screen = pygame.display.set_mode(preview_size)
        pygame.display.set_caption("Minimal 2D Physics Simulation")

    clear_frames_dir()

    space = pymunk.Space()
    space.gravity = 0, 0
    add_walls(space)
    ball = add_ball(space)
    boss_hp = boss_max_hp
    status = None
    hit_cooldown = 0
    frames_rendered = 0

    for frame_index in range(1, frame_count + 1):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                result = {
                    "status": "STOPPED",
                    "boss_hp_start": boss_max_hp,
                    "boss_hp_end": boss_hp,
                    "frames_rendered": frames_rendered,
                }
                write_result(result)
                return result

        boss_hp, hit_cooldown = handle_boss_collision(ball, boss_hp, damage, hit_cooldown)
        if boss_hp <= 0:
            status = CLEAR

        draw(render_surface, ball, boss_hp, boss_max_hp, status)
        frame_path = FRAMES_DIR / f"frame_{frame_index:06d}.png"
        pygame.image.save(render_surface, str(frame_path))
        frames_rendered = frame_index

        if preview_screen is not None:
            scaled_surface = pygame.transform.smoothscale(render_surface, preview_screen.get_size())
            preview_screen.blit(scaled_surface, (0, 0))
            pygame.display.flip()
            clock.tick(FPS)

        if status == CLEAR:
            break

        space.step(1 / FPS)

    if status is None:
        status = FAILED
        draw(render_surface, ball, boss_hp, boss_max_hp, status)
        frame_path = FRAMES_DIR / f"frame_{frames_rendered:06d}.png"
        pygame.image.save(render_surface, str(frame_path))

    pygame.quit()
    result = {
        "status": status,
        "boss_hp_start": boss_max_hp,
        "boss_hp_end": boss_hp,
        "damage": damage,
        "frames_rendered": frames_rendered,
    }
    write_result(result)
    print(json.dumps(result, indent=2))
    return result


def main() -> None:
    args = parse_args()
    show_window = args.window and not args.no_window
    run(frame_count=args.frames, show_window=show_window, boss_max_hp=args.boss_hp, damage=args.damage)


if __name__ == "__main__":
    main()
