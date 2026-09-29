"""
Rich Terminal UI, Formatting, and Live Streaming Renderer.
Provides clean terminal aesthetics, Markdown rendering, diagnostics, and banners.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from rich.box import DOUBLE, HEAVY, ROUNDED, SIMPLE
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

# Custom modern terminal theme
CUSTOM_THEME = Theme(
    {
        "info": "cyan",
        "warning": "bright_yellow",
        "error": "bright_red bold",
        "success": "bright_green bold",
        "highlight": "bright_magenta bold",
        "muted": "dim white",
        "accent": "bold deep_sky_blue1",
        "user_tag": "bold deep_sky_blue1",
        "assistant_tag": "bold medium_spring_green",
        "system_tag": "bold dark_violet",
    }
)

# Shared Rich console
console = Console(theme=CUSTOM_THEME)


def format_bytes(size_bytes: int) -> str:
    """Format bytes to human readable string (MB/GB)."""
    if not size_bytes or size_bytes <= 0:
        return "Unknown"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"


def print_banner(host: str, model: str, healthy: bool = True) -> None:
    """Print the startup header banner and connection status."""
    title_text = Text()
    title_text.append("⚡ OLLAMA CLI CHATBOT ", style="bold bright_cyan")
    title_text.append("v1.0.0", style="dim white")

    status_tag = (
        Text("● ONLINE", style="bold bright_green")
        if healthy
        else Text("○ OFFLINE", style="bold bright_red")
    )

    info_table = Table.grid(padding=(0, 2))
    info_table.add_column(style="bold white", justify="left")
    info_table.add_column(style="bright_cyan", justify="left")
    info_table.add_column(style="bold white", justify="left")
    info_table.add_column(style="bright_magenta", justify="left")
    info_table.add_column(style="bold white", justify="right")
    info_table.add_column(justify="right")

    info_table.add_row(
        "Host:",
        host,
        "Model:",
        model,
        "Status:",
        status_tag,
    )

    quick_cmds = (
        "[dim]Slash Commands: [/dim]"
        "[bold cyan]/help[/bold cyan] [dim]•[/dim] "
        "[bold cyan]/clear[/bold cyan] [dim]•[/dim] "
        "[bold cyan]/system[/bold cyan] [dim]•[/dim] "
        "[bold cyan]/model[/bold cyan] [dim]•[/dim] "
        "[bold cyan]/history[/bold cyan] [dim]•[/dim] "
        "[bold cyan]/save[/bold cyan] [dim]•[/dim] "
        "[bold cyan]/exit[/bold cyan]"
    )

    content = Table.grid(padding=(0, 0))
    content.add_row(info_table)
    content.add_row(Rule(style="dim blue", end="\n"))
    content.add_row(Text.from_markup(quick_cmds))

    panel = Panel(
        content,
        title=title_text,
        title_align="center",
        border_style="bright_blue",
        box=ROUNDED,
        padding=(1, 2),
    )
    console.print(panel)


def print_troubleshooting(
    host: str,
    error_message: Optional[str] = None,
    advice: Optional[str] = None,
) -> None:
    """Display an intuitive diagnostic troubleshooting card when backend is unreachable."""
    trouble_table = Table(
        box=ROUNDED,
        border_style="bright_red",
        show_header=False,
        padding=(0, 1),
        expand=True,
    )
    trouble_table.add_column("Category", style="bold bright_yellow", width=22)
    trouble_table.add_column("Details / Action Items", style="white")

    trouble_table.add_row(
        "Target Endpoint",
        f"[bold bright_red]{host}[/bold bright_red] (Unreachable)",
    )
    if error_message:
        trouble_table.add_row("Detected Error", f"[coral]{error_message}[/coral]")

    trouble_table.add_section()
    trouble_table.add_row(
        "1. Network / VPN",
        "Ensure your workstation is on the same subnet (e.g. [cyan]10.100.11.0/24[/cyan]) "
        "or connected to the corporate/lab VPN.\n"
        "Test basic connectivity: [bold]ping 10.100.11.38[/bold]",
    )
    trouble_table.add_row(
        "2. Ubuntu Service",
        "Verify that Ollama daemon is active on the Ubuntu VM:\n"
        "[bold green]systemctl status ollama[/bold green] (or check [bold green]docker ps[/bold green] if containerized)",
    )
    trouble_table.add_row(
        "3. Network Binding",
        "By default, Ollama binds strictly to [yellow]127.0.0.1:11434[/yellow] (localhost only).\n"
        "To allow remote LAN access, configure systemd environment on the Ubuntu VM:\n"
        "  1. Run: [bold]sudo systemctl edit ollama.service[/bold]\n"
        "  2. Add under [yellow][Service][/yellow]:\n"
        "     [bold bright_green]Environment=\"OLLAMA_HOST=0.0.0.0:11434\"[/bold bright_green]\n"
        "  3. Save and reload: [bold]sudo systemctl daemon-reload && sudo systemctl restart ollama[/bold]",
    )
    trouble_table.add_row(
        "4. Ubuntu Firewall",
        "Ensure UFW allows TCP port 11434 on the Ubuntu VM:\n"
        "[bold green]sudo ufw allow 11434/tcp[/bold green] && [bold green]sudo ufw reload[/bold green]",
    )

    panel = Panel(
        trouble_table,
        title="[bold bright_red]⚠️  Ollama Backend Connection Failed[/bold bright_red]",
        title_align="center",
        border_style="bright_red",
        box=HEAVY,
        padding=(1, 1),
    )
    console.print(panel)


def print_help_table() -> None:
    """Display interactive commands help table."""
    table = Table(
        title="Command Reference & Keyboard Shortcuts",
        box=ROUNDED,
        border_style="cyan",
        header_style="bold bright_cyan",
        expand=True,
    )
    table.add_column("Command / Key", style="bold bright_magenta", width=22)
    table.add_column("Action & Description", style="white")

    table.add_row("/help, /?", "Show this command cheat sheet.")
    table.add_row("/clear, /c", "Reset conversation context/memory (preserves persona).")
    table.add_row("/system <prompt>", "Change the system prompt / persona dynamically.")
    table.add_row("/model [name|#]", "Switch active model by name or index #. Lists models if empty.")
    table.add_row("/pull <name>", "Download/pull a new model to the remote Ollama server.")
    table.add_row("/delete <name>", "Delete a model from the remote Ollama server.")
    table.add_row("/detach, /unload", "Unload active model from server RAM to free memory.")
    table.add_row("/history", "View questions & turns in the current session.")
    table.add_row("/save [path]", "Export session transcript as a formatted Markdown (.md) file.")
    table.add_row("/json [path]", "Export session transcript as a raw JSON (.json) file.")
    table.add_row("/status", "Display current session stats, active model, and host URL.")
    table.add_row("/exit, /quit", "Gracefully terminate the CLI chatbot session.")
    table.add_section()
    table.add_row("Up / Down Arrow", "Navigate previously entered command history.")
    table.add_row("Ctrl + C", "Interrupt ongoing LLM stream response without exiting.")
    table.add_row("Ctrl + D", "Exit application (EOF).")
    table.add_row("Alt + Enter / Esc+Enter", "Insert a newline for multi-line inputs.")

    console.print(table)


def print_model_table(models: List[Dict[str, Any]], active_model: str) -> None:
    """Render a table of models available on the remote Ollama server."""
    table = Table(
        title="Available Models on Ollama Host",
        box=ROUNDED,
        border_style="bright_blue",
        header_style="bold bright_cyan",
        expand=True,
    )
    table.add_column("#", justify="center", width=4, style="bold bright_yellow")
    table.add_column("Status", justify="center", width=10)
    table.add_column("Model Name", style="bold white")
    table.add_column("Parameters", justify="center", style="bright_yellow")
    table.add_column("Quantization", justify="center", style="cyan")
    table.add_column("File Size", justify="right", style="green")
    table.add_column("Modified", justify="right", style="dim")

    for idx, m in enumerate(models, 1):
        name = m.get("name", "unknown")
        details = m.get("details", {})
        param_size = details.get("parameter_size", "N/A")
        quant = details.get("quantization_level", "N/A")
        size_bytes = m.get("size", 0)
        size_str = format_bytes(size_bytes)
        modified = m.get("modified_at", "")[:10]

        is_active = (name == active_model) or (name.split(":")[0] == active_model.split(":")[0])
        status = "[bold green]▶ ACTIVE[/bold green]" if is_active else "[dim]AVAILABLE[/dim]"
        name_styled = f"[bold bright_cyan]{name}[/bold bright_cyan]" if is_active else name

        table.add_row(str(idx), status, name_styled, param_size, quant, size_str, modified)

    console.print(table)


def print_history_table(history: List[Dict[str, Any]]) -> None:
    """Render conversation history table."""
    if not history:
        console.print("[dim yellow]No conversation history yet. Ask a question to begin![/dim yellow]")
        return

    table = Table(
        title="Current Session History",
        box=ROUNDED,
        border_style="purple",
        header_style="bold bright_magenta",
        expand=True,
    )
    table.add_column("Turn #", justify="center", width=8, style="bold cyan")
    table.add_column("Time", justify="center", width=12, style="dim white")
    table.add_column("User Query Preview", style="white")
    table.add_column("Length", justify="right", width=10, style="dim green")

    for item in history:
        table.add_row(
            str(item["turn"]),
            item["time"],
            item["preview"],
            f"{item['full_length']} chars",
        )

    console.print(table)


def print_status_card(
    host: str,
    model: str,
    turn_count: int,
    user_turn_count: int,
    system_prompt: str,
    timeout: float,
) -> None:
    """Print current session status card."""
    table = Table.grid(padding=(0, 2))
    table.add_column(style="bold cyan", width=18)
    table.add_column(style="white")

    table.add_row("Remote Host:", host)
    table.add_row("Active Model:", f"[bold bright_magenta]{model}[/bold bright_magenta]")
    table.add_row("Inference Timeout:", f"{timeout:.0f} seconds")
    table.add_row("Session Memory:", f"{user_turn_count} user turns ({turn_count} total messages)")
    table.add_row(
        "System Persona:",
        f"[italic]{system_prompt[:120]}...[/italic]" if len(system_prompt) > 120 else f"[italic]{system_prompt}[/italic]",
    )

    panel = Panel(
        table,
        title="[bold bright_cyan]Session Information[/bold bright_cyan]",
        border_style="bright_blue",
        box=ROUNDED,
        padding=(1, 2),
    )
    console.print(panel)


def print_metrics_footer(metrics: Any) -> None:
    """Print streaming inference execution statistics."""
    if not metrics:
        return

    tokens_sec = metrics.tokens_per_second
    eval_count = metrics.eval_count
    total_sec = metrics.total_duration_sec
    prompt_tokens = metrics.prompt_eval_count

    stats_text = Text()
    stats_text.append("  ⚡ ", style="bright_yellow")
    stats_text.append(f"{tokens_sec:.1f} tokens/s", style="bold bright_green")
    stats_text.append("  │  ", style="dim white")
    stats_text.append(f"{eval_count} tokens generated", style="cyan")
    if prompt_tokens:
        stats_text.append(f" ({prompt_tokens} prompt tokens)", style="dim cyan")
    stats_text.append("  │  ", style="dim white")
    stats_text.append(f"{total_sec:.2f}s latency", style="bright_magenta")

    console.print(stats_text)
    console.print()


def render_markdown(text: str) -> Markdown:
    """Create a Markdown object with code syntax highlighting and consistent styling."""
    return Markdown(
        text,
        code_theme="monokai",
        justify="left",
    )
