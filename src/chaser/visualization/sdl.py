"""SDL 3 renderer for projected simulation records."""

from __future__ import annotations

import ctypes
import math
import os
from pathlib import Path
import time
from typing import Any

from chaser.scenarios.red_goal import PursuitRecord
from chaser.visualization.projection import Color, RedGoalProjection, ViewCircle, ViewLine


REQUIRED_SDL_VERSION = 3_004_014


class SDLUnavailableError(RuntimeError):
    pass


def _load_sdl() -> Any:
    """Load PySDL3 against a system SDL core, without optional extension bundles."""

    os.environ.setdefault("SDL_DISABLE_METADATA", "1")
    os.environ.setdefault("SDL_DOWNLOAD_BINARIES", "0")
    os.environ.setdefault("SDL_FIND_BINARIES", "0")
    os.environ.setdefault("SDL_DOC_GENERATOR", "0")
    os.environ.setdefault("SDL_CHECK_VERSION", "0")
    os.environ.setdefault("SDL_CHECK_BINARY_VERSION", "0")
    os.environ.setdefault("SDL_LOG_LEVEL", "3")

    if "SDL_BINARY_PATH" not in os.environ:
        candidates = (
            Path("/opt/homebrew/opt/sdl3/lib"),
            Path("/usr/local/opt/sdl3/lib"),
        )
        for candidate in candidates:
            if (candidate / "libSDL3.dylib").exists():
                os.environ["SDL_BINARY_PATH"] = str(candidate)
                break

    try:
        import sdl3
    except (ImportError, OSError) as error:
        raise SDLUnavailableError(
            "PySDL3 and SDL 3.4.14 are required for visualization. "
            "Install the visualization extra and set SDL_BINARY_PATH to the "
            "directory containing the SDL 3 library."
        ) from error

    version = int(sdl3.SDL_GetVersion())
    if version < REQUIRED_SDL_VERSION:
        raise SDLUnavailableError(
            f"SDL 3.4.14 or newer is required; loaded encoded version {version}."
        )
    return sdl3


def _error(sdl: Any) -> str:
    raw = sdl.SDL_GetError()
    return raw.decode("utf-8", errors="replace") if raw else "unknown SDL error"


def _set_color(sdl: Any, renderer: Any, color: Color) -> None:
    if not sdl.SDL_SetRenderDrawColor(
        renderer,
        color.red,
        color.green,
        color.blue,
        color.alpha,
    ):
        raise RuntimeError(f"SDL_SetRenderDrawColor failed: {_error(sdl)}")


def _draw_line(sdl: Any, renderer: Any, line: ViewLine) -> None:
    _set_color(sdl, renderer, line.color)
    if not sdl.SDL_RenderLine(
        renderer,
        line.start.x,
        line.start.y,
        line.end.x,
        line.end.y,
    ):
        raise RuntimeError(f"SDL_RenderLine failed: {_error(sdl)}")


def _draw_filled_circle(sdl: Any, renderer: Any, circle: ViewCircle) -> None:
    _set_color(sdl, renderer, circle.color)
    radius = max(1, math.ceil(circle.radius))
    for y_offset in range(-radius, radius + 1):
        half_width = math.sqrt(max(0.0, circle.radius**2 - y_offset**2))
        if not sdl.SDL_RenderLine(
            renderer,
            circle.center.x - half_width,
            circle.center.y + y_offset,
            circle.center.x + half_width,
            circle.center.y + y_offset,
        ):
            raise RuntimeError(f"SDL_RenderLine failed: {_error(sdl)}")


class SDLPlayback:
    """Play a completed record; display timing never changes simulation results."""

    def __init__(self, *, width: int = 1_200, height: int = 720) -> None:
        self.width = width
        self.height = height

    def play(
        self,
        record: PursuitRecord,
        *,
        playback_rate: float = 1.0,
        frames_per_second: float = 60.0,
        final_hold_s: float = 1.5,
        maximum_frames: int | None = None,
    ) -> None:
        if playback_rate <= 0.0 or frames_per_second <= 0.0:
            raise ValueError("playback rate and frame rate must be positive")
        if final_hold_s < 0.0:
            raise ValueError("final hold must be non-negative")

        sdl = _load_sdl()
        projection = RedGoalProjection(record, width=self.width, height=self.height)
        window = ctypes.POINTER(sdl.SDL_Window)()
        renderer = ctypes.POINTER(sdl.SDL_Renderer)()

        if not sdl.SDL_Init(sdl.SDL_INIT_VIDEO):
            raise RuntimeError(f"SDL_Init failed: {_error(sdl)}")
        try:
            if not sdl.SDL_CreateWindowAndRenderer(
                b"Chaser",
                self.width,
                self.height,
                0,
                ctypes.byref(window),
                ctypes.byref(renderer),
            ):
                raise RuntimeError(
                    f"SDL_CreateWindowAndRenderer failed: {_error(sdl)}"
                )

            started = time.monotonic()
            final_reached_at: float | None = None
            rendered_frames = 0
            frame_duration = 1.0 / frames_per_second
            event = sdl.SDL_Event()
            running = True
            while running:
                frame_started = time.monotonic()
                while sdl.SDL_PollEvent(ctypes.byref(event)):
                    if event.type == sdl.SDL_EVENT_QUIT:
                        running = False
                if not running:
                    break

                elapsed = time.monotonic() - started
                simulation_time = min(record.duration_s, elapsed * playback_rate)
                if simulation_time >= record.duration_s and final_reached_at is None:
                    final_reached_at = time.monotonic()

                title = (
                    f"Chaser | t={simulation_time:0.2f}s | "
                    f"{record.outcome.value.replace('_', ' ')}"
                )
                sdl.SDL_SetWindowTitle(window, title.encode("utf-8"))
                self._render_scene(sdl, renderer, projection.scene_at(simulation_time))
                rendered_frames += 1

                if maximum_frames is not None and rendered_frames >= maximum_frames:
                    break
                if (
                    final_reached_at is not None
                    and time.monotonic() - final_reached_at >= final_hold_s
                ):
                    break

                remaining = frame_duration - (time.monotonic() - frame_started)
                if remaining > 0.0:
                    time.sleep(remaining)
        finally:
            if renderer:
                sdl.SDL_DestroyRenderer(renderer)
            if window:
                sdl.SDL_DestroyWindow(window)
            sdl.SDL_Quit()

    @staticmethod
    def _render_scene(sdl: Any, renderer: Any, scene: Any) -> None:
        _set_color(sdl, renderer, scene.background)
        if not sdl.SDL_RenderClear(renderer):
            raise RuntimeError(f"SDL_RenderClear failed: {_error(sdl)}")
        for line in scene.grid:
            _draw_line(sdl, renderer, line)
        for line in scene.trails:
            _draw_line(sdl, renderer, line)
        for circle in scene.circles:
            _draw_filled_circle(sdl, renderer, circle)
        if not sdl.SDL_RenderPresent(renderer):
            raise RuntimeError(f"SDL_RenderPresent failed: {_error(sdl)}")
