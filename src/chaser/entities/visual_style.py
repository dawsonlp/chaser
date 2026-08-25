"""Visual styling and shapes for simulation entities."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Color:
    red: int
    green: int
    blue: int
    alpha: int = 255


# Standard simulation color themes
BACKGROUND_COLOR = Color(248, 250, 252)
GRID_COLOR = Color(218, 224, 230)
RED_COLOR = Color(220, 55, 55)
RED_TRAIL_COLOR = Color(235, 150, 150)
BLUE_COLOR = Color(45, 100, 220)
BLUE_TRAIL_COLOR = Color(145, 175, 235)
CYAN_COLOR = Color(8, 145, 178)
CYAN_TRAIL_COLOR = Color(103, 232, 249)
GREEN_COLOR = Color(22, 163, 74)
GREEN_TRAIL_COLOR = Color(134, 239, 172)
YELLOW_COLOR = Color(234, 179, 8)
YELLOW_TRAIL_COLOR = Color(254, 240, 138)
PURPLE_COLOR = Color(124, 58, 237)
PURPLE_TRAIL_COLOR = Color(216, 180, 254)
GOAL_COLOR = Color(65, 70, 80)
GOAL_TRAIL_COLOR = Color(140, 145, 155)
OBSTACLE_COLOR = Color(100, 116, 139)


@dataclass(frozen=True, slots=True)
class CircleShape:
    radius_m: float

    def __post_init__(self) -> None:
        if self.radius_m < 0.0:
            raise ValueError("circle radius must be non-negative")


@dataclass(frozen=True, slots=True)
class VisualStyle:
    color: Color
    trail_color: Color | None = None
    show_trail: bool = True
    show_label: bool = True
    min_screen_radius_px: float = 3.0

