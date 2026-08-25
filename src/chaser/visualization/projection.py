"""Pure projection from simulation records to view-space primitives."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping

from chaser.entities.visual_style import (
    BACKGROUND_COLOR,
    BLUE_COLOR,
    BLUE_TRAIL_COLOR,
    Color,
    GOAL_COLOR,
    GRID_COLOR,
    RED_COLOR,
    RED_TRAIL_COLOR,
)
from chaser.math.vec2 import Vec2


@dataclass(frozen=True, slots=True)
class ViewLine:
    start: Vec2
    end: Vec2
    color: Color


@dataclass(frozen=True, slots=True)
class ViewCircle:
    object_id: str
    center: Vec2
    radius: float
    color: Color


@dataclass(frozen=True, slots=True)
class ViewScene:
    time_s: float
    width: int
    height: int
    background: Color
    grid: tuple[ViewLine, ...]
    trails: tuple[ViewLine, ...]
    circles: tuple[ViewCircle, ...]


BACKGROUND = BACKGROUND_COLOR
GRID = GRID_COLOR
RED = RED_COLOR
RED_TRAIL = RED_TRAIL_COLOR
BLUE = BLUE_COLOR
BLUE_TRAIL = BLUE_TRAIL_COLOR
GOAL = GOAL_COLOR


class UniversalProjection2D:
    """Project any 2D simulation record into a fixed screen view."""

    def __init__(
        self,
        record: any,
        *,
        width: int = 1_200,
        height: int = 720,
        padding_px: float = 50.0,
        grid_spacing_m: float = 1_000.0,
    ) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("projection dimensions must be positive")
        if padding_px < 0.0 or grid_spacing_m <= 0.0:
            raise ValueError("padding must be non-negative and grid spacing positive")

        self.record = record
        self.width = width
        self.height = height
        self.padding_px = padding_px
        self.grid_spacing_m = grid_spacing_m

        positions = [
            record.state_at(object_id, time).position
            for object_id in record.tracks
            for time in (0.0, record.duration_s)
        ]
        largest_radius = max(track.radius_m for track in record.tracks.values())
        margin = max(grid_spacing_m * 0.5, largest_radius * 2.0)
        min_x = min(position.x for position in positions) - margin
        max_x = max(position.x for position in positions) + margin
        min_y = min(position.y for position in positions) - margin
        max_y = max(position.y for position in positions) + margin
        if math.isclose(min_y, max_y):
            min_y -= grid_spacing_m
            max_y += grid_spacing_m

        drawable_width = width - 2.0 * padding_px
        drawable_height = height - 2.0 * padding_px
        if drawable_width <= 0.0 or drawable_height <= 0.0:
            raise ValueError("padding leaves no drawable area")

        self._scale = min(
            drawable_width / (max_x - min_x),
            drawable_height / (max_y - min_y),
        )
        visible_world_width = drawable_width / self._scale
        visible_world_height = drawable_height / self._scale
        center_x = (min_x + max_x) * 0.5
        center_y = (min_y + max_y) * 0.5
        self._min_x = center_x - visible_world_width * 0.5
        self._max_x = center_x + visible_world_width * 0.5
        self._min_y = center_y - visible_world_height * 0.5
        self._max_y = center_y + visible_world_height * 0.5

    def to_view(self, position: Vec2) -> Vec2:
        return Vec2(
            self.padding_px + (position.x - self._min_x) * self._scale,
            self.height
            - self.padding_px
            - (position.y - self._min_y) * self._scale,
        )

    def scene_at(self, time_s: float) -> ViewScene:
        time_s = min(self.record.duration_s, max(0.0, time_s))
        circles: list[ViewCircle] = []
        for object_id, track in self.record.tracks.items():
            color = getattr(track, "style", None)
            circle_color = color.color if color else {
                "red": RED,
                "blue": BLUE,
                "goal": GOAL,
            }.get(object_id, BLUE)

            min_rad = color.min_screen_radius_px if color else 3.0
            screen_rad = max(min_rad, track.radius_m * self._scale)

            circles.append(
                ViewCircle(
                    object_id=object_id,
                    center=self.to_view(self.record.state_at(object_id, time_s).position),
                    radius=screen_rad,
                    color=circle_color,
                )
            )

        return ViewScene(
            time_s=time_s,
            width=self.width,
            height=self.height,
            background=BACKGROUND,
            grid=self._grid_lines(),
            trails=self._trail_lines(time_s),
            circles=tuple(circles),
        )

    def _grid_lines(self) -> tuple[ViewLine, ...]:
        lines: list[ViewLine] = []
        first_x = math.ceil(self._min_x / self.grid_spacing_m) * self.grid_spacing_m
        x = first_x
        while x <= self._max_x:
            lines.append(
                ViewLine(
                    self.to_view(Vec2(x, self._min_y)),
                    self.to_view(Vec2(x, self._max_y)),
                    GRID,
                )
            )
            x += self.grid_spacing_m

        first_y = math.ceil(self._min_y / self.grid_spacing_m) * self.grid_spacing_m
        y = first_y
        while y <= self._max_y:
            lines.append(
                ViewLine(
                    self.to_view(Vec2(self._min_x, y)),
                    self.to_view(Vec2(self._max_x, y)),
                    GRID,
                )
            )
            y += self.grid_spacing_m
        return tuple(lines)

    def _trail_lines(self, time_s: float) -> tuple[ViewLine, ...]:
        if time_s <= 0.0:
            return ()
        segment_count = max(1, min(120, math.ceil(time_s * 20.0)))
        times = [time_s * index / segment_count for index in range(segment_count + 1)]
        lines: list[ViewLine] = []

        for object_id, track in self.record.tracks.items():
            style = getattr(track, "style", None)
            if style and not style.show_trail:
                continue

            trail_col = style.trail_color if (style and style.trail_color) else {
                "red": RED_TRAIL,
                "blue": BLUE_TRAIL,
            }.get(object_id)

            if trail_col is None:
                continue

            points = [
                self.to_view(self.record.state_at(object_id, time).position)
                for time in times
            ]
            lines.extend(
                ViewLine(start, end, trail_col)
                for start, end in zip(points, points[1:])
            )
        return tuple(lines)


class RedGoalProjection(UniversalProjection2D):
    """Backward-compatible projection alias for the first scenario."""
    pass
