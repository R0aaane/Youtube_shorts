from __future__ import annotations

import json
from pathlib import Path
import sys

import pymunk

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from generate_config import load_config  # noqa: E402
from render import draw_frame, init_surface, save_frame  # noqa: E402


OUTPUT_METADATA = PROJECT_ROOT / "output" / "metadata" / "simulation_result.json"
PREVIEW_FRAME = PROJECT_ROOT / "output" / "frames" / "preview.png"


def add_ball(space: pymunk.Space, x: float, y: float, radius: float, velocity: tuple[float, float]) -> pymunk.Body:
    mass = 1.0
    moment = pymunk.moment_for_circle(mass, 0, radius)
    body = pymunk.Body(mass, moment)
    body.position = x, y
    body.velocity = velocity

    shape = pymunk.Circle(body, radius)
    shape.elasticity = 0.95
    shape.friction = 0.2
    space.add(body, shape)
    return body


def add_walls(space: pymunk.Space, width: int, height: int) -> None:
    static = space.static_body
    walls = [
        pymunk.Segment(static, (0, 0), (width, 0), 1),
        pymunk.Segment(static, (0, height), (width, height), 1),
        pymunk.Segment(static, (0, 0), (0, height), 1),
        pymunk.Segment(static, (width, 0), (width, height), 1),
    ]
    for wall in walls:
        wall.elasticity = 0.95
        wall.friction = 0.2
    space.add(*walls)


def run_simulation(config: dict, seconds: float = 3.0) -> dict:
    video = config["video"]
    sim = config["simulation"]
    width = int(video["width"])
    height = int(video["height"])
    fps = int(video["fps"])
    radius = float(sim["ball_radius"])

    space = pymunk.Space()
    space.gravity = tuple(sim["gravity"])
    add_walls(space, width, height)

    balls = []
    for index in range(int(sim["ball_count"])):
        body = add_ball(
            space,
            x=width * (0.3 + index * 0.2),
            y=height * 0.55,
            radius=radius,
            velocity=(260 - index * 90, -420 - index * 60),
        )
        balls.append(body)

    boss_hp = int(sim["boss_hp"])
    boss_max_hp = boss_hp
    steps = int(seconds * fps)
    boss_y = 210

    for _ in range(steps):
        space.step(1 / fps)
        for body in balls:
            if body.position.y - radius <= boss_y and boss_hp > 0:
                boss_hp -= int(sim["ball_damage"])
                body.velocity = (body.velocity.x, abs(body.velocity.y) + 120)

    rendered_balls = [
        {"x": body.position.x, "y": body.position.y, "radius": radius}
        for body in balls
    ]
    surface = init_surface(width, height)
    draw_frame(surface, rendered_balls, boss_hp, boss_max_hp)
    save_frame(surface, PREVIEW_FRAME)

    result = {
        "status": "ok",
        "frames_simulated": steps,
        "boss_hp_start": boss_max_hp,
        "boss_hp_end": max(0, boss_hp),
        "preview_frame": str(PREVIEW_FRAME.relative_to(PROJECT_ROOT)),
    }
    OUTPUT_METADATA.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_METADATA.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    simulation_result = run_simulation(load_config())
    print(json.dumps(simulation_result, indent=2))
