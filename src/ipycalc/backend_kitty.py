from __future__ import annotations

import os
import shutil
import subprocess
import sys
from io import BytesIO

from matplotlib import interactive, is_interactive
from matplotlib._pylab_helpers import Gcf
from matplotlib.backend_bases import FigureManagerBase, _Backend
from matplotlib.backends.backend_agg import FigureCanvasAgg

if hasattr(sys, "ps1") or sys.flags.interactive:
    interactive(True)


def _icat_command() -> list[str]:
    if kitten := os.environ.get("IPYCALC_KITTEN"):
        return [kitten, "icat"]
    if kitty := os.environ.get("IPYCALC_KITTY"):
        return [kitty, "+kitten", "icat"]
    if kitten := shutil.which("kitten"):
        return [kitten, "icat"]
    if kitty := shutil.which("kitty"):
        return [kitty, "+kitten", "icat"]
    raise RuntimeError("IPyCalc cannot find kitten or kitty; start plotting from the IPyCalc AppImage")


def _query(command: list[str], *arguments: str) -> str:
    completed = subprocess.run(
        [*command, *arguments],
        capture_output=True,
        check=True,
    )
    return completed.stdout.decode("utf-8", errors="replace").strip()


def _display(command: list[str], png: bytes) -> None:
    subprocess.run(
        [*command, "--align", "left"],
        input=png,
        check=True,
    )


class FigureManagerICat(FigureManagerBase):
    def show(self) -> None:
        command = _icat_command()
        if os.environ.get("MPLBACKEND_KITTY_SIZING", "automatic") != "manual":
            try:
                rows = max(shutil.get_terminal_size(fallback=(80, 24)).lines, 1)
                width, height = (int(value) for value in _query(command, "--print-window-size").split("x", 1))
                height -= int(3 * (height / rows))
                dpi = self.canvas.figure.dpi
                self.canvas.figure.set_size_inches(width / dpi, height / dpi)
            except (OSError, ValueError, subprocess.SubprocessError):
                pass
        with BytesIO() as buffer:
            self.canvas.figure.savefig(buffer, format="png", facecolor="#001e26")
            _display(command, buffer.getvalue())


class FigureCanvasICat(FigureCanvasAgg):
    manager_class = FigureManagerICat


@_Backend.export
class _BackendICatAgg(_Backend):
    FigureCanvas = FigureCanvasICat
    FigureManager = FigureManagerICat
    mainloop = lambda: None

    @classmethod
    def draw_if_interactive(cls):
        manager = Gcf.get_active()
        if manager is not None and is_interactive() and manager.canvas.figure.get_axes():
            cls.show()

    @classmethod
    def show(cls, *args, **kwargs):
        super().show(*args, **kwargs)
        Gcf.destroy_all()
