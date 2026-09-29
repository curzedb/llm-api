"""
Main Entrypoint and Interactive Command Loop for Ollama CLI Chatbot.
Provides interactive CLI with prompt_toolkit, slash commands, and streaming inference.
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from rich.live import Live
from rich.panel import Panel

from cli_chat.client import (
    InferenceMetrics,
    OllamaClient,
    OllamaConnectionError,
    OllamaModelNotFoundError,
    OllamaTimeoutError,
)
from cli_chat.config import Config
from cli_chat.session import ChatSession
from cli_chat.ui import (
    console,
    print_banner,
    print_help_table,
    print_history_table,
    print_metrics_footer,
    print_model_table,
    print_status_card,
    print_troubleshooting,
    render_markdown,
)

# Slash command autocomplete keywords
SLASH_COMMANDS = [
    "/help",
    "/clear",
    "/system",
    "/model",
    "/pull",
    "/delete",
    "/detach",
    "/unload",
    "/history",
    "/save",
    "/json",
    "/status",
    "/multiline",
    "/exit",
    "/quit",
]

# Custom prompt_toolkit styling
PROMPT_STYLE = Style.from_dict(
    {
        "prompt-model": "#00d7ff bold",
        "prompt-arrow": "#00ffaf bold",
        "prompt-tag": "#af87ff",
    }
)


def handle_stream_response(
    client: OllamaClient,
    session: ChatSession,
) -> None:
    """Stream response from Ollama API with live Markdown typewriter rendering."""
    console.print()
    console.print(f"[bold medium_spring_green]🤖 Assistant[/bold medium_spring_green] [dim]({session.model})[/dim]:")

    accumulated_text = ""
    final_metrics: Optional[InferenceMetrics] = None
    interrupted = False

    try:
        with Live(
            render_markdown("▌"),
            console=console,
            refresh_per_second=15,
            vertical_overflow="visible",
        ) as live:
            try:
                for chunk in client.stream_chat(session.get_api_messages(), model=session.model):
                    accumulated_text += chunk.content
                    if chunk.metrics:
                        final_metrics = chunk.metrics

                    cursor = "" if chunk.is_done else " ▌"
                    display_content = (accumulated_text + cursor) if accumulated_text else "▌"
                    live.update(render_markdown(display_content))

                # Final update without cursor
                if accumulated_text:
                    live.update(render_markdown(accumulated_text))

            except KeyboardInterrupt:
                interrupted = True
                if accumulated_text:
                    live.update(render_markdown(accumulated_text))

    except OllamaModelNotFoundError as e:
        session.remove_last_user_message()
        console.print(
            Panel(
                f"[bold bright_red]Model Error:[/bold bright_red] {e}",
                border_style="bright_red",
                title="Model Not Found",
            )
        )
        return
    except OllamaTimeoutError as e:
        session.remove_last_user_message()
        console.print(
            Panel(
                f"[bold bright_red]Timeout Error:[/bold bright_red] {e}",
                border_style="bright_yellow",
                title="Inference Timeout",
            )
        )
        return
    except OllamaConnectionError as e:
        session.remove_last_user_message()
        console.print(
            Panel(
                f"[bold bright_red]Network Error:[/bold bright_red] {e}",
                border_style="bright_red",
                title="Connection Error",
            )
        )
        return
    except Exception as e:
        session.remove_last_user_message()
        console.print(
            Panel(
                f"[bold bright_red]Unexpected Error:[/bold bright_red] {e}",
                border_style="bright_red",
                title="Runtime Error",
            )
        )
        return

    if interrupted:
        console.print("\n[bright_yellow]⚠️  Generation interrupted by user (Ctrl+C)[/bright_yellow]\n")
        if accumulated_text.strip():
            session.add_assistant_message(accumulated_text + " *(Generation interrupted)*")
        else:
            session.remove_last_user_message()
    else:
        if accumulated_text.strip():
            session.add_assistant_message(accumulated_text)
            print_metrics_footer(final_metrics)
        else:
            session.remove_last_user_message()
            console.print("[dim yellow](Empty response received from model)[/dim yellow]\n")


def execute_slash_command(
    command_line: str,
    session: ChatSession,
    client: OllamaClient,
    config: Config,
    multiline_state: dict,
) -> bool:
    """
    Process slash commands.
    Returns True if application should continue running, False if should exit.
    """
    parts = command_line.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    if cmd in ("/exit", "/quit"):
        console.print("[bold bright_cyan]👋 Goodbye! Session ended.[/bold bright_cyan]")
        return False

    elif cmd in ("/help", "/?"):
        print_help_table()

    elif cmd in ("/clear", "/c"):
        session.clear()
        console.print("[bold bright_green]✨ Conversation context reset.[/bold bright_green] System persona preserved.")

    elif cmd == "/system":
        if not arg:
            console.print(
                Panel(
                    session.system_prompt or "*(No system prompt set)*",
                    title="[bold purple]Current System Persona[/bold purple]",
                    border_style="purple",
                )
            )
            console.print("[dim]Usage to update: /system <your custom persona prompt>[/dim]")
        else:
            session.set_system_prompt(arg)
            console.print(
                Panel(
                    f"[bold bright_green]System Persona Updated:[/bold bright_green]\n{arg}",
                    border_style="bright_green",
                )
            )

    elif cmd in ("/model", "/models"):
        if not arg:
            try:
                models = client.list_models()
                print_model_table(models, session.model)
                console.print(
                    "[dim]Switch model: [bold cyan]/model <#>[/bold cyan] or [bold cyan]/model <name>[/bold cyan] "
                    "| Pull model: [bold cyan]/pull <name>[/bold cyan][/dim]"
                )
            except Exception as exc:
                console.print(f"[bold bright_red]Failed to retrieve models:[/bold bright_red] {exc}")
        else:
            try:
                # Check if user entered a number (index from list)
                if arg.isdigit():
                    models = client.list_models()
                    idx = int(arg)
                    if 1 <= idx <= len(models):
                        new_model_name = models[idx - 1].get("name", "")
                        old_model = session.model
                        session.set_model(new_model_name)
                        console.print(
                            f"[bold bright_green]Switched active model:[/bold bright_green] "
                            f"[dim]{old_model}[/dim] ➔ [bold bright_cyan]{session.model}[/bold bright_cyan]"
                        )
                    else:
                        console.print(
                            f"[bright_yellow]Invalid model number '{arg}'. Choose between 1 and {len(models)}.[/bright_yellow]"
                        )
                else:
                    # Switch by name
                    old_model = session.model
                    session.set_model(arg)
                    console.print(
                        f"[bold bright_green]Switched active model:[/bold bright_green] "
                        f"[dim]{old_model}[/dim] ➔ [bold bright_cyan]{session.model}[/bold bright_cyan]"
                    )
            except Exception as exc:
                console.print(f"[bold bright_red]Model switch error:[/bold bright_red] {exc}")

    elif cmd == "/pull":
        if not arg:
            console.print("[bright_yellow]Usage: /pull <model_name>[/bright_yellow] (e.g. [cyan]/pull llama3.2:3b[/cyan])")
        else:
            console.print(f"[dim]Initiating download for '[bold cyan]{arg}[/bold cyan]' on remote Ollama server...[/dim]")
            try:
                with Live(console=console, refresh_per_second=4) as live:
                    last_status = ""
                    for progress in client.pull_model(arg):
                        status = progress.get("status", "")
                        total = progress.get("total", 0)
                        completed = progress.get("completed", 0)
                        if total > 0:
                            pct = (completed / total) * 100
                            comp_mb = completed / (1024 * 1024)
                            total_mb = total / (1024 * 1024)
                            msg = f"[cyan]{status}[/cyan]: [bold green]{pct:.1f}%[/bold green] ({comp_mb:.1f} MB / {total_mb:.1f} MB)"
                        else:
                            msg = f"[cyan]{status}[/cyan]"
                        if msg != last_status:
                            live.update(Panel(msg, title=f"Downloading {arg}", border_style="bright_blue"))
                            last_status = msg
                console.print(f"[bold bright_green]✔ Model '{arg}' successfully pulled to Ollama server![/bold bright_green]")
                # Switch to it automatically
                old_model = session.model
                session.set_model(arg)
                console.print(f"[dim]Active model switched to:[/dim] [bold bright_cyan]{session.model}[/bold bright_cyan]")
            except Exception as exc:
                console.print(f"[bold bright_red]Pull failed:[/bold bright_red] {exc}")

    elif cmd in ("/delete", "/rm"):
        if not arg:
            console.print("[bright_yellow]Usage: /delete <model_name>[/bright_yellow] (e.g. [cyan]/delete mistral:7b[/cyan])")
        else:
            confirm = console.input(f"[bold bright_red]Are you sure you want to delete '{arg}' from the server? [y/N]: [/bold bright_red]").strip().lower()
            if confirm in ("y", "yes"):
                try:
                    success = client.delete_model(arg)
                    if success:
                        console.print(f"[bold bright_green]✔ Model '{arg}' deleted from Ollama server.[/bold bright_green]")
                        # If active model was deleted, switch back to config default
                        if session.model == arg:
                            session.set_model(config.model)
                            console.print(f"[dim]Active model reverted to:[/dim] [cyan]{session.model}[/cyan]")
                except Exception as exc:
                    console.print(f"[bold bright_red]Delete failed:[/bold bright_red] {exc}")
            else:
                console.print("[dim]Deletion cancelled.[/dim]")

    elif cmd in ("/detach", "/unload"):
        target_model = arg if arg else session.model
        console.print(f"[dim]Unloading model '[bold cyan]{target_model}[/bold cyan]' from server RAM...[/dim]")
        success = client.unload_model(target_model)
        if success:
            console.print(f"[bold bright_green]✔ Model '{target_model}' successfully unloaded from RAM.[/bold bright_green] Server memory freed.")
        else:
            console.print(f"[bright_yellow]Notice: Model '{target_model}' was not actively loaded in RAM or host did not respond.[/bright_yellow]")

    elif cmd == "/history":
        history = session.get_history_summary()
        print_history_table(history)

    elif cmd == "/save":
        try:
            saved_path = session.export_markdown(arg if arg else None)
            console.print(
                Panel(
                    f"Transcript exported successfully to:\n[bold bright_green]{saved_path}[/bold bright_green]",
                    title="Markdown Export",
                    border_style="bright_green",
                )
            )
        except Exception as exc:
            console.print(f"[bold bright_red]Failed to export Markdown:[/bold bright_red] {exc}")

    elif cmd == "/json":
        try:
            saved_path = session.export_json(arg if arg else None)
            console.print(
                Panel(
                    f"Session state saved to:\n[bold bright_green]{saved_path}[/bold bright_green]",
                    title="JSON Export",
                    border_style="bright_green",
                )
            )
        except Exception as exc:
            console.print(f"[bold bright_red]Failed to export JSON:[/bold bright_red] {exc}")

    elif cmd == "/status":
        print_status_card(
            host=session.host,
            model=session.model,
            turn_count=session.turn_count,
            user_turn_count=session.user_turn_count,
            system_prompt=session.system_prompt,
            timeout=config.timeout,
        )

    elif cmd == "/multiline":
        multiline_state["enabled"] = not multiline_state.get("enabled", False)
        status = "ENABLED" if multiline_state["enabled"] else "DISABLED"
        style = "bright_green" if multiline_state["enabled"] else "bright_yellow"
        shortcut_info = (
            " (Press [bold]Esc+Enter[/bold] or [bold]Alt+Enter[/bold] to submit)"
            if multiline_state["enabled"]
            else ""
        )
        console.print(f"[{style}]Multi-line mode {status}[/{style}]{shortcut_info}")

    else:
        console.print(
            f"[bold bright_yellow]Unknown command '{cmd}'.[/bold bright_yellow] "
            "Type [bold cyan]/help[/bold cyan] for available commands."
        )

    return True


def interactive_select_model(client: OllamaClient, current_model: str) -> str:
    """Interactively prompt user to select a model from the remote server."""
    try:
        models = client.list_models()
        if not models:
            console.print("[dim yellow]No models found on server. Using default.[/dim yellow]")
            return current_model

        print_model_table(models, current_model)
        console.print("[dim]Select a model to use for this session:[/dim]")

        while True:
            choice = console.input(
                f"[bold cyan]Enter model # (1-{len(models)}) or name [Enter for '{current_model}']: [/bold cyan]"
            ).strip()

            if not choice:
                return current_model

            if choice.isdigit():
                idx = int(choice)
                if 1 <= idx <= len(models):
                    chosen = models[idx - 1].get("name", "")
                    if chosen:
                        console.print(f"[bold bright_green]Active model set to:[/bold bright_green] [cyan]{chosen}[/cyan]\n")
                        return chosen
                console.print(f"[bright_yellow]Invalid number. Choose between 1 and {len(models)}.[/bright_yellow]")
            else:
                match = next((m.get("name") for m in models if m.get("name", "").lower() == choice.lower()), None)
                if match:
                    console.print(f"[bold bright_green]Active model set to:[/bold bright_green] [cyan]{match}[/cyan]\n")
                    return match
                return choice
    except Exception as exc:
        console.print(f"[dim yellow]Could not fetch model list: {exc}[/dim yellow]")
        return current_model


def run_interactive_loop(config: Config, prompt_selection: bool = False) -> None:
    """Run interactive terminal REPL session."""
    client = OllamaClient(config)
    session = ChatSession(
        model=config.model,
        system_prompt=config.system_prompt,
        host=config.host,
        sessions_dir=config.sessions_dir,
    )

    # Health check
    console.print(f"[dim]Performing pre-flight health check on {config.host}...[/dim]")
    health = client.check_health()

    if not health.is_healthy:
        print_banner(config.host, config.model, healthy=False)
        print_troubleshooting(
            host=config.host,
            error_message=health.error_message,
            advice=health.troubleshooting_advice,
        )
        console.print(
            "[dim yellow]Warning: Remote host is currently unreachable. "
            "You may still explore CLI commands, or resolve connection and retry.[/dim yellow]\n"
        )
    else:
        # If user passed --select or if model not in list, prompt selection
        if prompt_selection:
            selected = interactive_select_model(client, session.model)
            session.set_model(selected)

        print_banner(config.host, session.model, healthy=True)

        if not prompt_selection and health.available_models:
            if session.model not in health.available_models and not any(
                m.startswith(session.model.split(":")[0]) for m in health.available_models
            ):
                console.print(
                    f"[bright_yellow]⚠️  Notice: Model '[bold]{session.model}[/bold]' was not detected in remote tags.[/bright_yellow]\n"
                    f"[dim]Available on host: {', '.join(health.available_models)}[/dim]\n"
                    f"[dim]Use [bold cyan]/model[/bold cyan] to select an available model or [bold cyan]/pull <model>[/bold cyan] to download it.[/dim]\n"
                )

    # Initialize prompt_toolkit session
    completer = WordCompleter(SLASH_COMMANDS, ignore_case=True, sentence=True)
    prompt_history = FileHistory(str(config.history_file))
    prompt_session: PromptSession = PromptSession(
        history=prompt_history,
        completer=completer,
        style=PROMPT_STYLE,
    )

    multiline_state = {"enabled": False}

    while True:
        try:
            # Dynamic prompt prefix
            safe_model_tag = session.model.split(":")[0]
            multiline_flag = " [ML]" if multiline_state["enabled"] else ""
            prompt_html = HTML(
                f"<prompt-model>[{safe_model_tag}{multiline_flag}]</prompt-model> <prompt-arrow>❯</prompt-arrow> "
            )

            user_input = prompt_session.prompt(
                prompt_html,
                multiline=multiline_state["enabled"],
            )

            # Strip whitespace
            user_input_clean = user_input.strip()
            if not user_input_clean:
                continue

            # Check for slash commands
            if user_input_clean.startswith("/"):
                should_continue = execute_slash_command(
                    command_line=user_input_clean,
                    session=session,
                    client=client,
                    config=config,
                    multiline_state=multiline_state,
                )
                if not should_continue:
                    break
                continue

            # Standard chat interaction
            session.add_user_message(user_input_clean)
            handle_stream_response(client, session)

        except KeyboardInterrupt:
            # Handle Ctrl+C at prompt: just clear line and keep running
            console.print("\n[dim]Input cancelled. (Type /exit or Ctrl+D to quit)[/dim]")
            continue

        except EOFError:
            # Handle Ctrl+D
            console.print("\n[bold bright_cyan]👋 Goodbye! Session closed.[/bold bright_cyan]")
            break


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Production-grade Interactive CLI Chatbot Client for Ollama LLM.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Ollama API base URL (e.g. http://<server-ip>:11434)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Default model name (e.g. qwen2.5:14b)",
    )
    parser.add_argument(
        "-s",
        "--select",
        action="store_true",
        help="Interactively select a model from the remote server on startup",
    )
    parser.add_argument(
        "-l",
        "--list-models",
        action="store_true",
        help="List all models currently installed on the remote Ollama server and exit",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Inference read timeout in seconds (default: 120.0s for 14B model)",
    )
    parser.add_argument(
        "--system",
        type=str,
        default=None,
        help="Custom system prompt persona override",
    )
    parser.add_argument(
        "-p",
        "--prompt",
        type=str,
        default=None,
        help="Single-shot prompt execution without entering interactive loop",
    )
    return parser.parse_args()


def run_single_shot(config: Config, prompt_text: str) -> None:
    """Execute a single query against Ollama and stream the output to terminal."""
    client = OllamaClient(config)
    session = ChatSession(
        model=config.model,
        system_prompt=config.system_prompt,
        host=config.host,
        sessions_dir=config.sessions_dir,
    )
    session.add_user_message(prompt_text)
    handle_stream_response(client, session)


def main() -> None:
    """Application entrypoint."""
    args = parse_arguments()
    config = Config.load(
        host=args.host,
        model=args.model,
        timeout=args.timeout,
        system_prompt=args.system,
    )

    if args.list_models:
        client = OllamaClient(config)
        try:
            models = client.list_models()
            print_model_table(models, config.model)
        except Exception as exc:
            console.print(f"[bold bright_red]Error fetching models:[/bold bright_red] {exc}")
        return

    if args.prompt:
        run_single_shot(config, args.prompt)
    else:
        run_interactive_loop(config, prompt_selection=args.select)


if __name__ == "__main__":
    main()

