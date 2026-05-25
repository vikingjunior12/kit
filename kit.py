#!/usr/bin/env python3
"""
KIterminal — Ein schlankes Terminal-KI-Tool für schnelle Aufgaben.

Multi-Provider: Anthropic (Claude) + DeepSeek (V4 Flash/Pro)
Modi: normalchat, codex, mail (-m/-ma/-mp), translate (-t)
Features: Pipe-Support, Clipboard, Chat-History, Config-Editor
"""

import anthropic
import sys
import argparse
import platform
import subprocess
import os
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt
from prompt_toolkit import prompt as pt_prompt
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
import pyperclip

from config import loadconfig, init_config, get_mode_config
from chat_history import save_chat, load_chat, show_chat_selection_menu
import chat_history as ch
from providers import get_client, get_provider_name

AUTHOR = "JLI-Software"
VERSION = "0.9.0"
LICENSE = "MIT"
ANTHROPIC_VERSION = anthropic.__version__
DESCRIPTION = (
    "KIterminal — 🤖 Schlankes KI-CLI-Tool für schnelle Aufgaben. "
    "Multi-Provider: Anthropic + DeepSeek."
)

# ── CLI-Parser ────────────────────────────────────────────────────────────

parser = argparse.ArgumentParser(
    prog="kit",
    description=DESCRIPTION,
    epilog="""
Beispiele:
  kit                     Normaler Chat (default)
  kit -c                  Codex Programmier-Assistent
  kit -c "Frage"          Codex One-Shot
  kit -m                  E-Mail-Korrektur (aus Clipboard)
  kit -m "Text"           E-Mail-Korrektur (direkt)
  kit -ma "Text"          E-Mail-Korrektur + Verbesserung
  kit -mp "Text"          Professioneller E-Mail-Rewrite
  kit -t "Hello World"    Übersetzung DE↔EN
  kit -r                  Chat fortsetzen
  kit -r -c               Codex-Chat fortsetzen
  kit --setup             Config bearbeiten
  kit -e codex            Codex-Instructions bearbeiten
  kit --version           Version anzeigen

Piped Input:
  cat file.txt | kit "Zusammenfassen"
  cat script.py | kit -c "Erklären"
  cat email.txt | kit -m "Korrigieren"
  cat doc.txt | kit -t "Übersetzen"

Konfiguration:
  kit -e normalchat       Chat-Instructions bearbeiten
  kit -e codex            Codex-Instructions bearbeiten
  kit -e email            Mail-Instructions bearbeiten
  kit -e translate        Übersetzungs-Instructions bearbeiten

  Instruction-Dateien: ~/.config/KIterminal/instructions/
  Config-Datei:        ~/.config/KIterminal/config.json

Umgebungsvariablen:
  ANTHROPIC_API_KEY       Anthropic API-Key
  DEEPSEEK_API_KEY        DeepSeek API-Key

Mehr Infos: https://github.com/vikingjunior12/kit
    """,
    formatter_class=argparse.RawDescriptionHelpFormatter,
)

# ── Modi ──────────────────────────────────────────────────────────────────

ai_modes = parser.add_argument_group("KI-Modi")
ai_modes.add_argument(
    "-c", "--codex",
    nargs="?", const=True, metavar="TEXT",
    help="Codex Programmier-Assistent (interaktiv oder One-Shot)",
)

# ── Textverarbeitung ──────────────────────────────────────────────────────

text_proc = parser.add_argument_group("Textverarbeitung")
text_proc.add_argument(
    "-t", "--translate",
    nargs="?", const=True, metavar="TEXT",
    help="Übersetzung DE↔EN (Clipboard oder Text)",
)
text_proc.add_argument(
    "-m", "--mail",
    nargs="?", const=True, metavar="TEXT",
    help="E-Mail-Korrektur (Clipboard oder Text)",
)
text_proc.add_argument(
    "-ma", "--mail-advanced",
    nargs="?", const=True, metavar="TEXT",
    help="E-Mail-Korrektur + inhaltliche Verbesserung",
)
text_proc.add_argument(
    "-mp", "--mail-pro",
    nargs="?", const=True, metavar="TEXT",
    help="Professioneller E-Mail-Rewrite (Business-Ton)",
)

# ── Chat-Management ───────────────────────────────────────────────────────

chat_mgmt = parser.add_argument_group("Chat-Management")
chat_mgmt.add_argument(
    "-r", "--resume",
    action="store_true",
    help="Vorherigen Chat fortsetzen",
)

# ── Konfiguration ─────────────────────────────────────────────────────────

config_grp = parser.add_argument_group("Konfiguration")
config_grp.add_argument(
    "-s", "--setup", action="store_true",
    help="Config-Datei mit Editor öffnen",
)
config_grp.add_argument(
    "-i", "--init", action="store_true",
    help="Config auf Werkseinstellungen zurücksetzen",
)
config_grp.add_argument(
    "-e", "--edit-instructions", metavar="MODE",
    help="Instructions für einen Modus bearbeiten "
         "(normalchat, codex, email, email-advanced, email-pro, translate)",
)

# ── Info ──────────────────────────────────────────────────────────────────

info_grp = parser.add_argument_group("Information")
info_grp.add_argument(
    "-v", "--version", action="store_true",
    help="Version & Info anzeigen",
)

# Positionales Argument (für Piped-Input + Frage)
parser.add_argument(
    "question", nargs="?", default=None,
    help="Frage (erforderlich bei Piped-Input)",
)

args = parser.parse_args()


# ── Umgebung ──────────────────────────────────────────────────────────────

console = Console()
currentOS = platform.system()
platforminfo = platform.platform()
config = loadconfig()

# Chat-History (in-memory, global)
chat_history: list[dict] = []


# ── Prompt-Toolkit Setup ──────────────────────────────────────────────────

kb = KeyBindings()

@kb.add("enter")
def _(event):
    event.current_buffer.validate_and_handle()


def get_user_input() -> str:
    """Benutzereingabe mit prompt_toolkit."""
    try:
        return pt_prompt(
            HTML("<ansibrightcyan><b>💬 </b></ansibrightcyan>"),
            multiline=False,
            key_bindings=kb,
        ).strip()
    except KeyboardInterrupt:
        raise
    except EOFError:
        return "exit"


# ── Plattform-Helfer ─────────────────────────────────────────────────────

def is_termux() -> bool:
    return os.path.exists("/data/data/com.termux")


def is_wsl() -> bool:
    try:
        with open("/proc/version") as f:
            content = f.read().lower()
            return "microsoft" in content or "wsl" in content
    except Exception:
        return False


def read_stdin() -> str | None:
    """Liest Piped-Input von stdin, falls vorhanden."""
    if sys.stdin.isatty():
        return None
    return sys.stdin.read().strip()


def reopen_stdin_to_terminal() -> bool:
    """Öffnet stdin neu zum Terminal (nach Piped-Input)."""
    try:
        if currentOS == "Windows" and not is_wsl():
            sys.stdin = open("CON", "r")
        else:
            sys.stdin = open("/dev/tty", "r")
        return True
    except (OSError, FileNotFoundError, PermissionError):
        return False


# ── Clipboard ─────────────────────────────────────────────────────────────

def copyline(text: str) -> None:
    """Text ins Clipboard kopieren."""
    try:
        if is_termux():
            subprocess.run(["termux-clipboard-set"], input=text.encode(), check=True)
        elif is_wsl():
            subprocess.run(["clip.exe"], input=text.encode(), check=True)
        else:
            pyperclip.copy(text)
    except Exception:
        pass  # Silent fail — Clipboard ist optional


def pasteline() -> str:
    """Text aus Clipboard lesen."""
    try:
        if is_termux():
            result = subprocess.run(
                ["termux-clipboard-get"], capture_output=True, text=True, check=True
            )
            return result.stdout
        elif is_wsl():
            result = subprocess.run(
                ["powershell.exe", "-command", "Get-Clipboard"],
                capture_output=True, text=True, check=True,
            )
            return result.stdout.strip()
        else:
            return pyperclip.paste()
    except Exception as e:
        console.print(f"[red]❌ Clipboard-Fehler: {e}[/red]")
        sys.exit(1)


# ── API-Helfer ────────────────────────────────────────────────────────────

def handle_api_error(e: Exception) -> None:
    """Benutzerfreundliche Fehlermeldungen für API-Fehler."""
    if isinstance(e, anthropic.AuthenticationError):
        console.print("[red]❌ Ungültiger API-Key![/red]")
        console.print("Bitte prüfe deine Umgebungsvariable (ANTHROPIC_API_KEY / DEEPSEEK_API_KEY)")
    elif isinstance(e, anthropic.APIConnectionError):
        console.print("[red]❌ Keine Verbindung zur API![/red]")
        console.print("Bitte prüfe deine Internetverbindung.")
    elif isinstance(e, anthropic.RateLimitError):
        console.print("[red]❌ Rate-Limit erreicht![/red]")
        console.print("Bitte warte einen Moment.")
    elif isinstance(e, anthropic.APIStatusError):
        console.print(f"[red]❌ API-Fehler {e.status_code}: {e}[/red]")
    else:
        console.print(f"[red]❌ Unerwarteter Fehler: {e}[/red]")


def get_response_text(response) -> str:
    """Extrahiert Text aus einer Anthropic-Response."""
    if response.stop_reason == "refusal":
        console.print("[yellow]⚠ Die KI hat die Anfrage abgelehnt.[/yellow]")
        return ""
    text_blocks = [block.text for block in response.content if block.type == "text"]
    return "\n\n".join(text_blocks) if text_blocks else ""


def build_effort_params(reasoning_effort: str) -> dict:
    """Erstellt thinking/output_config-Parameter für Adaptive Thinking."""
    if reasoning_effort in ("low", "medium", "high"):
        return {
            "thinking": {"type": "adaptive"},
            "output_config": {"effort": reasoning_effort},
        }
    return {}


def build_piped_message(question: str, stdin_content: str) -> str:
    """Kombiniert Frage mit Piped-Input."""
    return f"{question}\n\n```\n{stdin_content}\n```"


# ── Chat-Funktionen ───────────────────────────────────────────────────────

def _call_api(mode: str, messages: list[dict], system: str) -> str:
    """
    Führt einen API-Call für den angegebenen Modus aus.

    Nutzt den in der Config eingestellten Provider + Modell.
    """
    mode_cfg = get_mode_config(config, mode)
    provider = mode_cfg.get("provider", "anthropic")
    model = mode_cfg.get("model", "claude-sonnet-4-6")
    max_tokens = mode_cfg.get("max_tokens", 4096)
    reasoning_effort = mode_cfg.get("reasoning_effort", "none")

    client = get_client(provider)

    params = dict(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=messages,
        **build_effort_params(reasoning_effort),
    )

    status_text = f"[bold green]{get_provider_name(provider)}/{model} denkt nach..."
    with console.status(status_text):
        response = client.messages.create(**params)

    return get_response_text(response)


def normalchat(userfrage: str) -> None:
    """Normaler Chat-Modus (interaktiv)."""
    chat_history.append({"role": "user", "content": userfrage})

    try:
        response_text = _call_api(
            "normalchat",
            messages=chat_history,
            system=config["instructions"]["normalchat"],
        )
        chat_history.append({"role": "assistant", "content": response_text})
        copyline(response_text)
        console.print(Markdown(response_text))
    except (anthropic.APIConnectionError, anthropic.AuthenticationError,
            anthropic.RateLimitError, anthropic.APIStatusError) as e:
        handle_api_error(e)
        chat_history.pop()


def codex(userfrage: str) -> None:
    """Codex Programmier-Assistent (interaktiv)."""
    instruction = config["instructions"]["codex"].format(
        currentOS=currentOS, platforminfo=platforminfo
    )
    chat_history.append({"role": "user", "content": userfrage})

    try:
        response_text = _call_api(
            "codex",
            messages=chat_history,
            system=instruction,
        )
        chat_history.append({"role": "assistant", "content": response_text})
        copyline(response_text)
        console.print(Markdown(response_text))
    except (anthropic.APIConnectionError, anthropic.AuthenticationError,
            anthropic.RateLimitError, anthropic.APIStatusError) as e:
        handle_api_error(e)
        chat_history.pop()


def mail_correct(userfrage: str, mode: str = "email") -> None:
    """E-Mail-Korrektur (One-Shot)."""
    try:
        response_text = _call_api(
            mode,
            messages=[{"role": "user", "content": f"Proofread and correct this email:\n\n{userfrage}"}],
            system=config["instructions"][mode],
        )
        copyline(response_text)
        print(response_text)
    except (anthropic.APIConnectionError, anthropic.AuthenticationError,
            anthropic.RateLimitError, anthropic.APIStatusError) as e:
        handle_api_error(e)


def _run_mail(mode: str, args_flag, stdin_content: str | None, question: str | None) -> None:
    """Gemeinsame Routing-Logik für alle Mail-Modi (-m, -ma, -mp)."""
    if isinstance(args_flag, str):
        mail_correct(args_flag, mode=mode)
    elif stdin_content:
        content = build_piped_message(question, stdin_content) if question else stdin_content
        console.print("[green]✓ Piped-Input wird verarbeitet[/green]")
        mail_correct(content, mode=mode)
    else:
        text = pasteline()
        console.print("[green]✓ Aus Clipboard gelesen[/green]")
        mail_correct(text, mode=mode)


def translate(userfrage: str) -> None:
    """Übersetzung DE↔EN (One-Shot)."""
    try:
        response_text = _call_api(
            "translate",
            messages=[{"role": "user", "content": f"Translate this text:\n\n{userfrage}"}],
            system=config["instructions"]["translate"],
        )
        copyline(response_text)
        print(response_text)
    except (anthropic.APIConnectionError, anthropic.AuthenticationError,
            anthropic.RateLimitError, anthropic.APIStatusError) as e:
        handle_api_error(e)


# ── Interaktiver Chat-Loop ────────────────────────────────────────────────

def interactive_chat(turn_handler, mode: str = None, resume_chat: bool = False,
                     initial_message: str = None) -> None:
    """
    Interaktiver Chat mit Resume- und Auto-Save-Funktionalität.

    Args:
        turn_handler: Funktion für jeden Chat-Turn (normalchat/codex)
        mode: Chat-Modus für Speicherung (normalchat, codex)
        resume_chat: Vorherigen Chat fortsetzen?
        initial_message: Optionale erste Nachricht (Piped-Input / One-Shot-Argument)
    """
    global chat_history

    if resume_chat and mode:
        selected = show_chat_selection_menu(mode)
        if selected:
            try:
                chat_history.clear()
                loaded = load_chat(selected)
                chat_history.extend(loaded)
                ch.current_chat_file = selected
                console.print(f"[green]✓ Chat geladen ({len(chat_history)} Nachrichten)[/green]\n")
            except Exception as e:
                console.print(f"[red]❌ Fehler beim Laden: {e}[/red]")
                return
        else:
            ch.current_chat_file = None
            chat_history.clear()
    else:
        ch.current_chat_file = None
        chat_history.clear()

    try:
        if initial_message:
            if not sys.stdin.isatty():
                console.print("[dim]📎 Piped-Input wird verarbeitet...[/dim]")
                turn_handler(initial_message)
                if not reopen_stdin_to_terminal():
                    console.print("[dim]💡 Tipp: Mit -r kannst du diesen Chat später fortsetzen[/dim]")
                    return
                console.print("[dim]💬 Interaktiver Modus — du kannst Folgefragen stellen[/dim]")
            else:
                turn_handler(initial_message)

        while True:
            userfrage = get_user_input()
            if not userfrage:
                continue
            if userfrage.lower() == "exit":
                break
            turn_handler(userfrage)

    except KeyboardInterrupt:
        if mode and chat_history:
            save_chat(chat_history, mode, filepath=ch.current_chat_file)
            console.print("\n[green]✓ Chat gespeichert[/green]")
        raise
    finally:
        if mode and chat_history:
            save_chat(chat_history, mode, filepath=ch.current_chat_file)
            console.print("[green]✓ Chat gespeichert[/green]")
        ch.current_chat_file = None


# ── Config-Editor ─────────────────────────────────────────────────────────

def show_setup_file() -> None:
    """Öffnet die Config-Datei mit dem Standard-Editor."""
    config_path = os.path.join(os.path.expanduser("~"), ".config", "KIterminal", "config.json")
    try:
        if currentOS == "Windows":
            os.startfile(config_path)
        elif currentOS == "Darwin":
            subprocess.run(["open", config_path])
        else:
            if subprocess.run(["which", "nvim"], capture_output=True).returncode == 0:
                subprocess.run(["nvim", config_path])
            else:
                subprocess.run(["xdg-open", config_path])
    except Exception as e:
        console.print(f"[red]❌ Fehler beim Öffnen: {e}[/red]")


def edit_instructions(mode: str) -> None:
    """Öffnet die Instruction-Datei eines Modus."""
    instructions_dir = os.path.join(os.path.expanduser("~"), ".config", "KIterminal", "instructions")

    mode_files = {
        "normalchat": "normalchat.txt",
        "codex": "codex.txt",
        "email": "email.txt",
        "email-advanced": "email_advanced.txt",
        "email-pro": "email_pro.txt",
        "translate": "translate.txt",
    }

    if mode.lower() not in mode_files:
        console.print(f"[red]❌ Unbekannter Modus: {mode}[/red]")
        console.print(f"[yellow]Verfügbar: {', '.join(sorted(mode_files.keys()))}[/yellow]")
        return

    instruction_file = os.path.join(instructions_dir, mode_files[mode.lower()])

    if not os.path.exists(instruction_file):
        console.print(f"[red]❌ Datei nicht gefunden: {instruction_file}[/red]")
        return

    try:
        if currentOS == "Windows":
            os.startfile(instruction_file)
        elif currentOS == "Darwin":
            subprocess.run(["open", instruction_file])
        else:
            if subprocess.run(["which", "nvim"], capture_output=True).returncode == 0:
                subprocess.run(["nvim", instruction_file])
            else:
                subprocess.run(["xdg-open", instruction_file])
        console.print(f"[green]✓ Instructions geöffnet: {mode}[/green]")
    except Exception as e:
        console.print(f"[red]❌ Fehler: {e}[/red]")


# ── Main ──────────────────────────────────────────────────────────────────

def main() -> None:
    stdin_content = read_stdin()

    # Frage ermitteln
    question = args.question
    for flag in (args.codex, args.mail, args.mail_advanced, args.mail_pro, args.translate):
        if not question and isinstance(flag, str):
            question = flag

    # Validierung: Piped-Input ohne Frage? Nur Mail/Translate erlauben das
    if stdin_content and not question:
        if not (args.mail or args.mail_advanced or args.mail_pro or args.translate):
            console.print("[red]❌ Bei Piped-Input ist eine Frage erforderlich![/red]")
            console.print("[yellow]Beispiel: cat file.txt | kit \"Zusammenfassen\"[/yellow]")
            console.print("[yellow]Mail/Translate-Modi funktionieren auch ohne Frage.[/yellow]")
            sys.exit(1)

    # Initiale Nachricht (Piped-Input + Frage)
    initial_message = None
    if stdin_content and question:
        initial_message = build_piped_message(question, stdin_content)

    # ── Routing ────────────────────────────────────────────────────────

    if args.init:
        control = input("Config auf Werkseinstellungen zurücksetzen? (j/n): ").lower()
        if control in ("j", "y", "ja"):
            init_config()
            console.print("[green]✓ Config zurückgesetzt[/green]")
        else:
            console.print("[yellow]Abgebrochen[/yellow]")
        sys.exit(0)

    elif args.edit_instructions:
        edit_instructions(args.edit_instructions)
        sys.exit(0)

    elif args.setup:
        show_setup_file()
        console.print("[bold green]✅ Config-Datei geöffnet[/bold green]")

    elif args.version:
        console.print(f"[bold cyan]🚀 Version:[/bold cyan] [green]{VERSION}[/green]")
        console.print(f"[bold cyan]👨 Autor:[/bold cyan] [yellow]{AUTHOR}[/yellow]")
        console.print(f"[bold cyan]📜 Lizenz:[/bold cyan] [blue]{LICENSE}[/blue]")
        console.print(f"[bold cyan]💻 Anthropic SDK:[/bold cyan] [magenta]{ANTHROPIC_VERSION}[/magenta]")
        console.print(f"[bold cyan]🖥️ Beschreibung:[/bold cyan] [magenta]{DESCRIPTION}[/magenta]")

    elif args.mail:
        _run_mail("email", args.mail, stdin_content, question)

    elif args.mail_advanced:
        _run_mail("email_advanced", args.mail_advanced, stdin_content, question)

    elif args.mail_pro:
        _run_mail("email_pro", args.mail_pro, stdin_content, question)

    elif args.translate:
        if isinstance(args.translate, str):
            translate(args.translate)
        elif stdin_content:
            console.print("[green]✓ Piped-Input wird verarbeitet[/green]")
            content = build_piped_message(question, stdin_content) if question else stdin_content
            translate(content)
        else:
            text = pasteline()
            console.print("[green]✓ Aus Clipboard gelesen[/green]")
            translate(text)

    elif args.codex:
        if isinstance(args.codex, str) and not stdin_content:
            codex(args.codex)
        else:
            interactive_chat(codex, mode="codex", resume_chat=args.resume,
                             initial_message=initial_message)

    else:
        # Default: normalchat
        msg = initial_message if initial_message else question
        interactive_chat(normalchat, mode="normalchat", resume_chat=args.resume,
                         initial_message=msg)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        try:
            console.print("\n[yellow]Programm beendet[/yellow]")
        except Exception:
            pass
        finally:
            os._exit(0)
