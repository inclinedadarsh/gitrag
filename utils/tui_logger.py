"""
Rich-powered logging helpers for the terminal UI.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Optional, Sequence, Tuple

from rich import box
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table
from rich.text import Text

ASCII_LOGO = r"""
 ██████╗ ██╗████████╗██████╗  █████╗  ██████╗ 
██╔════╝ ██║╚══██╔══╝██╔══██╗██╔══██╗██╔════╝ 
██║  ███╗██║   ██║   ██████╔╝███████║██║  ███╗
██║   ██║██║   ██║   ██╔══██╗██╔══██║██║   ██║
╚██████╔╝██║   ██║   ██║  ██║██║  ██║╚██████╔╝
 ╚═════╝ ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ 
                                              
""".strip("\n")


class TUILogger:
    """Centralized helper for rendering Rich-powered output."""

    def __init__(self, mode: Optional[str] = None, console: Optional[Console] = None):
        self.mode = (mode or os.getenv("MODE", "production")).strip().lower()
        self.console = console or Console(highlight=False, soft_wrap=True)
        self.is_dev = self.mode == "dev"
        self._logo_printed = False

    # --------------------------------------------------------------------- basics
    def show_logo(self) -> None:
        """Render the ASCII logo exactly once per session."""
        if self._logo_printed:
            return
        logo_panel = Panel(
            Align.center(Text(ASCII_LOGO, style="bold cyan")),
            border_style="cyan",
            padding=(1, 4),
        )
        self.console.print(logo_panel)
        self._logo_printed = True

    def rule(self, title: str, icon: Optional[str] = None, style: str = "cyan") -> None:
        label = f"{icon} {title}" if icon else title
        self.console.rule(f"[bold {style}]{label}[/bold {style}]")

    def info(self, message: str, icon: str = "-", style: str = "cyan", indent: int = 0):
        self._line(message, icon=icon, style=style, indent=indent)

    def success(
        self, message: str, icon: str = "[OK]", style: str = "green", indent: int = 0
    ):
        self._line(message, icon=icon, style=style, indent=indent)

    def warning(
        self, message: str, icon: str = "[!]", style: str = "yellow", indent: int = 0
    ):
        self._line(message, icon=icon, style=style, indent=indent)

    def error(
        self, message: str, icon: str = "[X]", style: str = "red", indent: int = 0
    ):
        self._line(message, icon=icon, style=style, indent=indent)

    def bullet(
        self, message: str, icon: str = "->", style: str = "dim", indent: int = 1
    ):
        self._line(message, icon=icon, style=style, indent=indent)

    def panel(self, title: str, body: str, style: str = "cyan"):
        # Convert body to Text to enable proper wrapping within the panel
        # Text objects automatically wrap based on the console width
        text_body = Text(str(body)) if body else Text("")
        self.console.print(
            Panel(text_body, title=title, border_style=style, padding=(1, 2))
        )

    def table(
        self,
        title: str,
        rows: Sequence[Tuple[str, str]],
        header: Tuple[str, str] = ("Metric", "Value"),
    ):
        table = Table(*header, box=box.SIMPLE, header_style="bold white")
        for key, value in rows:
            table.add_row(str(key), str(value))
        panel = Panel(table, title=title, border_style="cyan", padding=(1, 2))
        self.console.print(panel)

    def help(self, commands: Sequence[Tuple[str, str]]) -> None:
        table = Table("Command", "Description", box=box.MINIMAL_DOUBLE_HEAD)
        for command, description in commands:
            table.add_row(f"[bold]{command}[/bold]", description)
        self.console.print(
            Panel(
                table,
                title="Command Palette",
                subtitle="Use /exit to quit",
                border_style="cyan",
                padding=(1, 2),
            )
        )

    # --------------------------------------------------------------- dev helpers
    def dev(self, title: str, payload: Any = None, footer: Optional[str] = None):
        if not self.is_dev:
            return
        body = ""
        if payload is not None:
            body = Pretty(payload, max_length=120, expand_all=False)
        panel = Panel(
            body if body else "",
            title=f"[magenta]{title}[/magenta]",
            subtitle=footer,
            border_style="magenta",
            padding=(1, 2),
        )
        self.console.print(panel)

    def tool_event(
        self,
        action: str,
        status: str,
        params: Optional[Any] = None,
        result_preview: Optional[str] = None,
        error: Optional[str] = None,
    ):
        if not self.is_dev:
            return
        body_lines = [f"[bold]Status:[/bold] {status}"]
        if params:
            body_lines.append(f"[bold]Params:[/bold] {self._truncate(params)}")
        if result_preview:
            body_lines.append(f"[bold]Result:[/bold] {self._truncate(result_preview)}")
        if error:
            body_lines.append(f"[bold red]Error:[/bold red] {error}")
        self.console.print(
            Panel(
                "\n".join(body_lines),
                title=f"Tool - {action}",
                border_style="magenta",
                padding=(1, 2),
            )
        )

    @contextmanager
    def status(self, message: str):
        with self.console.status(f"[cyan]{message}[/cyan]", spinner="dots"):
            yield

    # ---------------------------------------------------------------- utilities
    def _line(self, message: str, icon: str, style: str, indent: int) -> None:
        prefix = " " * (indent * 2)
        self.console.print(
            f"{prefix}[{style}]{icon}[/] {message}", highlight=False, soft_wrap=True
        )

    def _truncate(self, value: Any, limit: int = 120) -> str:
        text = str(value)
        return text if len(text) <= limit else text[: limit - 3] + "..."


def get_tui_logger(mode: Optional[str] = None) -> TUILogger:
    """Factory helper for modules that need a quick logger."""
    return TUILogger(mode=mode)
