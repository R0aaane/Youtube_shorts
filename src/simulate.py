from __future__ import annotations

import argparse
from pathlib import Path

import pygame
import pymunk


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRAMES_DIR = PROJECT_ROOT / "output" / "frames"

WIDTH = 1080
HEIGHT = 1920
FPS = 60
DEFAULT_FRAMES = 600
BALL_RADIUS = 36
WALL_THICKNESS = 8
DISPLAY_SCALE = 0.4


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
        frame_path.unlink()


def draw(surface: pygame.Surface, ball: pymunk.Body) -> None:
    surface.fill((15, 18, 24))
    pygame.draw.rect(surface, (230, 236, 242), surface.get_rect(), width=WALL_THICKNESS)
    pygame.draw.circle(
        surface,
        (68, 180, 255),
        (round(ball.position.x), round(ball.position.y)),
        BALL_RADIUS,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a minimal 2D ball simulation.")
    parser.add_argument("--frames", type=int, default=DEFAULT_FRAMES, help="Number of frames to simulate and save.")
    window_group = parser.add_mutually_exclusive_group()
    window_group.add_argument("--window", action="store_true", help="Show a scaled preview window while generating.")
    window_group.add_argument("--no-window", action="store_true", help="Generate frames without opening a window.")
    return parser.parse_args()


def run(frame_count: int, show_window: bool) -> None:
    if frame_count < 1:
        raise ValueError("--frames must be 1 or greater.")

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

    for frame_index in range(1, frame_count + 1):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        draw(render_surface, ball)
        frame_path = FRAMES_DIR / f"frame_{frame_index:06d}.png"
        pygame.image.save(render_surface, str(frame_path))

        if preview_screen is not None:
            scaled_surface = pygame.transform.smoothscale(render_surface, preview_screen.get_size())
            preview_screen.blit(scaled_surface, (0, 0))
            pygame.display.flip()
            clock.tick(FPS)

        space.step(1 / FPS)

    pygame.quit()


def main() -> None:
    args = parse_args()
    show_window = args.window and not args.no_window
    run(frame_count=args.frames, show_window=show_window)


if __name__ == "__main__":
    main()
