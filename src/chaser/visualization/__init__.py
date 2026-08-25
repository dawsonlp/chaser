"""Projection and presentation of completed simulation records."""

from chaser.visualization.intercept_regions import InterceptRegionPlot
from chaser.visualization.projection import (
    BACKGROUND,
    BLUE,
    BLUE_TRAIL,
    GOAL,
    GRID,
    RED,
    RED_TRAIL,
    Color,
    RedGoalProjection,
    UniversalProjection2D,
    ViewCircle,
    ViewLine,
    ViewScene,
)
from chaser.visualization.sdl import SDLPlayback

__all__ = [
    "BACKGROUND",
    "BLUE",
    "BLUE_TRAIL",
    "GOAL",
    "GRID",
    "InterceptRegionPlot",
    "RED",
    "RED_TRAIL",
    "RedGoalProjection",
    "SDLPlayback",
    "UniversalProjection2D",
    "ViewCircle",
    "ViewLine",
    "ViewScene",
]
