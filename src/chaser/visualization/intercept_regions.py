"""Static field plot of successful blue starting regions."""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path

from chaser.atmosphere import ConstantThrustQuadraticDragPath, SphereQuadraticDrag, UniformAtmosphere
from chaser.plane import Vec2
from chaser.scenarios.red_goal import RedGoalSettings


DEFAULT_ACCELERATION_LEVELS = (50.0, 100.0, 150.0, 200.0, 250.0)
LEVEL_COLORS = ("#7c3aed", "#2563eb", "#0891b2", "#16a34a", "#eab308")


@dataclass(frozen=True, slots=True)
class RegionBoundary:
    acceleration_mps2: float
    points: tuple[Vec2, ...]


@dataclass(frozen=True, slots=True)
class InterceptRegionPlot:
    """Compute and render nested successful-start regions for one scenario."""

    settings: RedGoalSettings = RedGoalSettings()
    acceleration_levels_mps2: tuple[float, ...] = DEFAULT_ACCELERATION_LEVELS
    time_samples: int = 2_048
    horizontal_samples: int = 720

    def __post_init__(self) -> None:
        if not self.acceleration_levels_mps2:
            raise ValueError("at least one acceleration level is required")
        if len(self.acceleration_levels_mps2) > len(LEVEL_COLORS):
            raise ValueError(f"at most {len(LEVEL_COLORS)} levels are supported")
        if any(level <= 0.0 for level in self.acceleration_levels_mps2):
            raise ValueError("acceleration levels must be positive")
        if tuple(sorted(self.acceleration_levels_mps2)) != self.acceleration_levels_mps2:
            raise ValueError("acceleration levels must be in ascending order")
        if self.time_samples < 2 or self.horizontal_samples < 2:
            raise ValueError("plot sampling counts must be at least two")

    def boundaries(self) -> tuple[RegionBoundary, ...]:
        circles = {
            level: self._reachable_circles(level)
            for level in self.acceleration_levels_mps2
        }
        largest = circles[self.acceleration_levels_mps2[-1]]
        minimum_x = min(center_x - radius for center_x, radius in largest)
        maximum_x = max(center_x + radius for center_x, radius in largest)
        x_values = tuple(
            minimum_x + (maximum_x - minimum_x) * index / self.horizontal_samples
            for index in range(self.horizontal_samples + 1)
        )

        results: list[RegionBoundary] = []
        for level in self.acceleration_levels_mps2:
            upper: list[Vec2] = []
            for x in x_values:
                half_height = 0.0
                for center_x, radius in circles[level]:
                    horizontal = x - center_x
                    if abs(horizontal) <= radius:
                        half_height = max(
                            half_height,
                            math.sqrt(max(0.0, radius * radius - horizontal * horizontal)),
                        )
                upper.append(Vec2(x, half_height))
            points = (*upper, *(Vec2(point.x, -point.y) for point in reversed(upper)))
            results.append(RegionBoundary(level, tuple(points)))
        return tuple(results)

    def minimum_capability_for(self, start: Vec2) -> float | None:
        """Return the first plotted capability that can contact red in time."""

        for level in self.acceleration_levels_mps2:
            if any(
                math.hypot(start.x - center_x, start.y) <= radius
                for center_x, radius in self._reachable_circles(level)
            ):
                return level
        return None

    def _reachable_circles(self, acceleration: float) -> tuple[tuple[float, float], ...]:
        drag = SphereQuadraticDrag(
            self.settings.blue_body,
            UniformAtmosphere(self.settings.air_density_kg_m3),
            self.settings.sphere_drag_coefficient,
        )
        path = ConstantThrustQuadraticDragPath(
            0.0,
            Vec2(0.0, 0.0),
            Vec2(acceleration, 0.0),
            drag,
        )
        contact_radius = self.settings.blue_radius_m + self.settings.red_radius_m
        deadline = self.settings.uninterrupted_goal_time
        return tuple(
            (
                self.settings.red_start.x + self.settings.red_speed_mps * time,
                path.distance_after(time) + contact_radius,
            )
            for time in (
                deadline * index / self.time_samples
                for index in range(self.time_samples + 1)
            )
        )

    def render_svg(self, *, width: int = 1_200, height: int = 760) -> str:
        if width < 400 or height < 300:
            raise ValueError("plot dimensions are too small")
        boundaries = self.boundaries()
        all_points = tuple(point for boundary in boundaries for point in boundary.points)
        min_x = min(point.x for point in all_points)
        max_x = max(point.x for point in all_points)
        max_abs_y = max(abs(point.y) for point in all_points)
        x_padding = (max_x - min_x) * 0.04
        y_padding = max_abs_y * 0.08
        min_x -= x_padding
        max_x += x_padding
        min_y = -max_abs_y - y_padding
        max_y = max_abs_y + y_padding

        left, right, top, bottom = 86.0, 28.0, 92.0, 68.0
        plot_width = width - left - right
        plot_height = height - top - bottom

        def sx(value: float) -> float:
            return left + (value - min_x) * plot_width / (max_x - min_x)

        def sy(value: float) -> float:
            return top + (max_y - value) * plot_height / (max_y - min_y)

        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<title>Successful blue starting regions by acceleration capability</title>',
            '<desc>Nested colored regions show the minimum low-speed acceleration needed for the blue sphere to contact red before red reaches the goal.</desc>',
            '<rect width="100%" height="100%" fill="#ffffff"/>',
            f'<text x="{left}" y="32" font-family="sans-serif" font-size="22" font-weight="600" fill="#111827">Successful blue starting regions</text>',
            f'<text x="{left}" y="56" font-family="sans-serif" font-size="13" fill="#4b5563">10 cm steel sphere · quadratic drag · red reaches goal at 10 s</text>',
            f'<rect x="{left}" y="{top}" width="{plot_width}" height="{plot_height}" fill="#f8fafc" stroke="#94a3b8"/>',
        ]

        grid_spacing = 1_000.0
        first_grid_x = math.ceil(min_x / grid_spacing) * grid_spacing
        x = first_grid_x
        while x <= max_x:
            screen_x = sx(x)
            parts.append(f'<line x1="{screen_x:.2f}" y1="{top}" x2="{screen_x:.2f}" y2="{top + plot_height}" stroke="#e2e8f0"/>')
            parts.append(f'<text x="{screen_x:.2f}" y="{top + plot_height + 20}" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#475569">{x / 1000:g}</text>')
            x += grid_spacing
        first_grid_y = math.ceil(min_y / grid_spacing) * grid_spacing
        y = first_grid_y
        while y <= max_y:
            screen_y = sy(y)
            parts.append(f'<line x1="{left}" y1="{screen_y:.2f}" x2="{left + plot_width}" y2="{screen_y:.2f}" stroke="#e2e8f0"/>')
            parts.append(f'<text x="{left - 10}" y="{screen_y + 4:.2f}" text-anchor="end" font-family="sans-serif" font-size="11" fill="#475569">{y / 1000:g}</text>')
            y += grid_spacing

        colors = LEVEL_COLORS[: len(self.acceleration_levels_mps2)]
        color_by_level = dict(zip(self.acceleration_levels_mps2, colors, strict=True))
        for boundary in reversed(boundaries):
            points = " ".join(f"{sx(point.x):.2f},{sy(point.y):.2f}" for point in boundary.points)
            parts.append(f'<polygon points="{points}" fill="{color_by_level[boundary.acceleration_mps2]}" stroke="none"/>')

        red_start_x = sx(self.settings.red_start.x)
        red_end_x = sx(self.settings.red_start.x + self.settings.red_speed_mps * self.settings.uninterrupted_goal_time)
        center_y = sy(0.0)
        goal_x = sx(self.settings.goal_position.x)
        parts.extend(
            (
                f'<line x1="{red_start_x:.2f}" y1="{center_y:.2f}" x2="{red_end_x:.2f}" y2="{center_y:.2f}" stroke="#dc2626" stroke-width="3" stroke-dasharray="8 6"/>',
                f'<circle cx="{red_start_x:.2f}" cy="{center_y:.2f}" r="5" fill="#dc2626"/>',
                f'<circle cx="{goal_x:.2f}" cy="{center_y:.2f}" r="7" fill="#111827"/>',
                f'<text x="{red_start_x:.2f}" y="{center_y - 12:.2f}" text-anchor="middle" font-family="sans-serif" font-size="12" fill="#111827">red start</text>',
                f'<text x="{goal_x:.2f}" y="{center_y - 12:.2f}" text-anchor="middle" font-family="sans-serif" font-size="12" fill="#111827">goal</text>',
                f'<text x="{left + plot_width / 2:.2f}" y="{height - 16}" text-anchor="middle" font-family="sans-serif" font-size="13" fill="#111827">Blue initial x position (km)</text>',
                f'<text x="18" y="{top + plot_height / 2:.2f}" text-anchor="middle" transform="rotate(-90 18 {top + plot_height / 2:.2f})" font-family="sans-serif" font-size="13" fill="#111827">Blue initial y position (km)</text>',
            )
        )

        legend_x = left + 10
        legend_y = top + 18
        parts.append(f'<rect x="{legend_x - 7}" y="{legend_y - 15}" width="205" height="{28 + 21 * len(boundaries)}" fill="#ffffff" fill-opacity="0.9" stroke="#cbd5e1"/>')
        parts.append(f'<text x="{legend_x}" y="{legend_y}" font-family="sans-serif" font-size="12" font-weight="600" fill="#111827">Minimum capability required</text>')
        for index, (level, color) in enumerate(zip(self.acceleration_levels_mps2, colors, strict=True)):
            item_y = legend_y + 20 + index * 21
            parts.append(f'<rect x="{legend_x}" y="{item_y - 10}" width="13" height="13" fill="{color}"/>')
            parts.append(f'<text x="{legend_x + 21}" y="{item_y + 1}" font-family="sans-serif" font-size="12" fill="#111827">{level:g} m/s²</text>')

        parts.append('</svg>')
        return "\n".join(parts)

    def write_svg(self, destination: str | Path) -> Path:
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.render_svg(), encoding="utf-8")
        return path
