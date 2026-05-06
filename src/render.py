from __future__ import annotations

from pathlib import Path

import pygame


def init_surface(width: int, height: int) -> pygame.Surface:
    pygame.init()
    return pygame.Surface((width, height))


def draw_frame(surface: pygame.Surface, balls: list[dict], boss_hp: int, boss_max_hp: int) -> pygame.Surface:
    surface.fill((14, 18, 24))
    width, height = surface.get_size()

    boss_rect = pygame.Rect(width // 2 - 220, 120, 440, 90)
    pygame.draw.rect(surface, (185, 52, 52), boss_rect, border_radius=8)

    hp_ratio = max(0.0, min(1.0, boss_hp / boss_max_hp))
    hp_rect = pygame.Rect(boss_rect.left, boss_rect.bottom + 16, int(boss_rect.width * hp_ratio), 18)
    pygame.draw.rect(surface, (246, 196, 83), hp_rect, border_radius=4)

    for ball in balls:
        pygame.draw.circle(
            surface,
            (74, 179, 255),
            (int(ball["x"]), int(ball["y"])),
            int(ball["radius"]),
        )

    pygame.draw.rect(surface, (235, 241, 245), surface.get_rect(), width=6)
    return surface


def save_frame(surface: pygame.Surface, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(surface, str(path))
