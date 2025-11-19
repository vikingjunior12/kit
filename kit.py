from openai import OpenAI, APIError, APIConnectionError, AuthenticationError, RateLimitError
import sys
import argparse
import platform
import subprocess
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt
from prompt_toolkit import prompt
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
import pyperclip
import os
from config import loadconfig, init_config
from chat_history import save_chat, load_chat, show_chat_selection_menu
import chat_history as ch  # For accessing current_chat_file
import openai

AUTHOR = "JLI-Software"
VERSION = "0.6.1"
LICENSE = "MIT"
OPENAI_VERSION = openai.__version__
DESCRIPTION = "KIterminal - 🤖 AI-powered CLI assistant with multiple modes for chat, coding, translation, and more."

parser = argparse.ArgumentParser(
    prog="kit",
    description=f"{DESCRIPTION}",
    epilog="""
Examples:
  kit                      Start normal chat mode
  kit -c                   Start Codex programming assistant
  kit -c "explain this"    Ask Codex a quick question
  kit -w                   Start web search mode
  kit -m                   Proofread email from clipboard
  kit -t "Hello World"     Translate text
  kit -r -w                Resume previous web search chat
  kit --setup              Open configuration file
  kit -e codex             Edit instructions for codex mode
  kit --version            Show version information


Customization:
  Edit AI behavior by customizing instruction files:
    kit -e normalchat        Edit normal chat instructions
    kit -e websearch         Edit web search instructions
    kit -e codex             Edit codex instructions
    kit -e email             Edit email proofreading instructions
    kit -e translate         Edit translation instructions
    kit -e itsecurity        Edit IT security news instructions

  Instruction files are stored in:
    ~/.config/KIterminal/instructions/

Environment:
  OPENAI_API_KEY must be set to use this tool.
  
For more info: https://github.com/JLI-Software
    """,
    formatter_class=argparse.RawDescriptionHelpFormatter,
)

# AI Modes
ai_modes = parser.add_argument_group("AI Modes")
ai_modes.add_argument(
    "-c",
    "--codex",
    nargs="?",
    const=True,
    metavar="TEXT",
    help="Start interactive Codex programming assistant or ask a quick coding question",
)
ai_modes.add_argument(
    "-w",
    "--Websearch",
    action="store_true",
    help="Search the internet using GPT with web search capabilities",
)
ai_modes.add_argument(
    "-it",
    "--ITSecurityNews",
    action="store_true",
    help="Get latest IT security news (Setup in Config required)",
)

# Text Processing
text_proc = parser.add_argument_group("Text Processing")
text_proc.add_argument(
    "-t",
    "--Translate",
    nargs="?",
    const=True,
    metavar="TEXT",
    help="Translate(from clipboard or provided text)",
)   
text_proc.add_argument(
    "-m",
    "--Mail",
    nargs="?",
    const=True,
    metavar="TEXT",
    help="Proofread and correct email text (from clipboard or provided text)",
)

# Chat Management
chat_mgmt = parser.add_argument_group("Chat Management")
chat_mgmt.add_argument(
    "-r",
    "--resume",
    action="store_true",
    help="Resume a previous chat (works with normal chat, websearch, and codex modes)",
)

# Configuration
config_grp = parser.add_argument_group("Configuration")
config_grp.add_argument(
    "-s",
    "--setup",
    action="store_true",
    help="Open configuration file with default editor",
)
config_grp.add_argument(
    "-i",
    "--init",
    action="store_true",
    help="Reset configuration file to default settings",
)
config_grp.add_argument(
    "-e",
    "--edit-instructions",
    metavar="MODE",
    help="Edit instruction file for a specific mode (normalchat, websearch, codex, email, translate, itsecurity)",
)

# Information
info_grp = parser.add_argument_group("Information")
info_grp.add_argument(
    "-v",
    "--version",
    action="store_true",
    help="Show version, author, license, and OpenAI library version",
)

args = parser.parse_args()


api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("Error: OPENAI_API_KEY environment variable not set!")
    print("Set it with: export OPENAI_API_KEY='your-key'")
    sys.exit(1)

client = OpenAI()
console = Console()
currentOS = platform.system()
platforminfo = platform.platform()


def show_setup_file():
    """Open the setup configuration file with the default editor."""
    config_file_path = os.path.join(os.path.expanduser("~"), ".config", "KIterminal", "config.json")
    try:
        if currentOS == "Windows":
            os.startfile(config_file_path)
        elif currentOS == "Darwin":  # macOS
            subprocess.run(["open", config_file_path])
        else:  # Linux and others
            if nvim_installed := subprocess.run(["which", "nvim"], capture_output=True).returncode == 0:
                subprocess.run(["nvim", config_file_path])
            else:
                subprocess.run(["xdg-open", config_file_path])

    except Exception as e:
        console.print(f"[red]❌ Error opening configuration file: {str(e)}[/red]")


def edit_instructions(mode):
    """Open an instruction file for a specific mode with the default editor."""
    instructions_dir = os.path.join(os.path.expanduser("~"), ".config", "KIterminal", "instructions")

    # Map mode names to instruction files
    mode_files = {
        "normalchat": "normalchat.txt",
        "websearch": "websearch.txt",
        "codex": "codex.txt",
        "email": "email.txt",
        "translate": "translate.txt",
        "itsecurity": "itsecuritynews.txt"
    }

    if mode.lower() not in mode_files:
        console.print(f"[red]❌ Unknown mode: {mode}[/red]")
        console.print(f"[yellow]Available modes: {', '.join(mode_files.keys())}[/yellow]")
        return

    instruction_file = os.path.join(instructions_dir, mode_files[mode.lower()])

    if not os.path.exists(instruction_file):
        console.print(f"[red]❌ Instruction file not found: {instruction_file}[/red]")
        return

    try:
        if currentOS == "Windows":
            os.startfile(instruction_file)
        elif currentOS == "Darwin":  # macOS
            subprocess.run(["open", instruction_file])
        else:  # Linux and others
            if subprocess.run(["which", "nvim"], capture_output=True).returncode == 0:
                subprocess.run(["nvim", instruction_file])
            else:
                subprocess.run(["xdg-open", instruction_file])

        console.print(f"[green]✓ Instruction file opened: {mode}[/green]")
    except Exception as e:
        console.print(f"[red]❌ Error opening instruction file: {str(e)}[/red]")

def is_termux():
    """Check if running in Termux environment."""
    return os.path.exists('/data/data/com.termux')


def is_wsl():
    """Check if running in WSL (Windows Subsystem for Linux)."""
    try:
        with open('/proc/version', 'r') as f:
            return 'microsoft' in f.read().lower() or 'wsl' in f.read().lower()
    except:
        return False


def handle_api_error(e):
    """Handle OpenAI API errors with user-friendly messages."""
    if isinstance(e, AuthenticationError):
        console.print("[red]❌ Error: Invalid API key![/red]")
        console.print("Please check your OPENAI_API_KEY")
    elif isinstance(e, APIConnectionError):
        console.print("[red]❌ Error: No connection to OpenAI API![/red]")
        console.print("Please check your internet connection")
    elif isinstance(e, RateLimitError):
        console.print("[red]❌ Error: Rate limit reached![/red]")
        console.print("Please wait a moment and try again")
    elif isinstance(e, APIError):
        console.print(f"[red]❌ API error: {str(e)}[/red]")
    else:
        console.print(f"[red]❌ Unexpected error: {str(e)}[/red]")


config = loadconfig()
# Chat History
chat_history = []

# Setup prompt_toolkit keybindings
kb = KeyBindings()

@kb.add('enter')
def _(event):
    """Submit on Enter (single line mode)"""
    event.current_buffer.validate_and_handle()

@kb.add('escape', 'enter')
def _(event):
    """Submit on Esc+Enter (alternative)"""
    event.current_buffer.validate_and_handle()


def get_user_input():
    """
    Get user input with prompt_toolkit.
    Features:
    - Enter: Submit
    - Esc+Enter: Also submit (alternative)
    - Ctrl+C: Exit
    - Multi-line paste support
    """
    try:
        user_input = prompt(
            HTML('<ansibrightcyan><b>💬 </b></ansibrightcyan>'),
            multiline=False,
            key_bindings=kb,
        )
        return user_input.strip()
    except KeyboardInterrupt:
        raise
    except EOFError:
        return "exit"


def copyline(text: str):
    """Copy text to clipboard with error handling."""
    try:
        if is_termux():
            subprocess.run(["termux-clipboard-set"], input=text.encode(), check=True)
        elif is_wsl():
            # WSL: Use Windows clip.exe
            subprocess.run(["clip.exe"], input=text.encode('utf-16le'), check=True)
        else:
            pyperclip.copy(text)
    except subprocess.CalledProcessError:
        console.print("[yellow]⚠️  Warning: Could not copy to clipboard[/yellow]")
    except Exception as e:
        console.print(f"[yellow]⚠️  Warning: Clipboard error: {str(e)}[/yellow]")


def pasteline():
    """Paste text from clipboard with error handling."""
    try:
        if is_termux():
            result = subprocess.run(
                ["termux-clipboard-get"], capture_output=True, text=True, check=True
            )
            return result.stdout
        elif is_wsl():
            # WSL: Use PowerShell Get-Clipboard
            result = subprocess.run(
                ["powershell.exe", "-command", "Get-Clipboard"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        else:
            result = pyperclip.paste()
            return result
    except subprocess.CalledProcessError:
        console.print("[red]❌ Error: Could not read from clipboard[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Clipboard error: {str(e)}[/red]")
        sys.exit(1)


def convert_to_responses_format(chat_history):
    """Convert chat history to OpenAI Responses API format."""
    input_messages = []
    for m in chat_history:
        role = m["role"]
        text = m["content"]
        if role == "assistant":
            parts = [{"type": "output_text", "text": text}]
        else:  # user
            parts = [{"type": "input_text", "text": text}]
        input_messages.append({"role": role, "content": parts})
    return input_messages


def interactive_chat(turn_handler, mode=None, resume_chat=False):
    """Interactive chat with optional resume and auto-save functionality."""
    global chat_history

    # Handle resume functionality
    if resume_chat and mode:
        selected_chat = show_chat_selection_menu(mode)
        if selected_chat:
            try:
                chat_history.clear()
                loaded_history = load_chat(selected_chat)
                chat_history.extend(loaded_history)
                ch.current_chat_file = selected_chat  # Track the loaded file
                console.print(f"[green]✓ Chat restored ({len(chat_history)} messages)[/green]\n")
            except Exception as e:
                console.print(f"[red]❌ Error loading chat: {str(e)}[/red]")
                return
        else:
            # User chose to start a new chat
            ch.current_chat_file = None
            chat_history.clear()
    else:
        # Starting fresh without resume
        ch.current_chat_file = None
        chat_history.clear()

    try:
        while True:
            userfrage = get_user_input()
            if userfrage.lower() == "exit":
                break

            turn_handler(userfrage)
    except KeyboardInterrupt:
        # Save before exiting on Ctrl+C
        if mode and chat_history:
            save_chat(chat_history, mode, filepath=ch.current_chat_file)
            console.print("\n[green]✓ Chat saved[/green]")
        # Re-raise for global handler
        raise
    finally:
        # Auto-save when exiting normally
        if mode and chat_history:
            save_chat(chat_history, mode, filepath=ch.current_chat_file)
            console.print("[green]✓ Chat saved[/green]")
        ch.current_chat_file = None  # Reset for next session


def Websearch(userfrage):
    model = config["Websearch"]
    reasoning_effort = config["reasoning_effort"]["Websearch"]
    chat_history.append({"role": "user", "content": userfrage})
    input_messages = convert_to_responses_format(chat_history)

    try:
        with console.status(f"[bold green]{model} is Thinking...") as status:
            response = client.responses.create(
                model=model,
                reasoning={"effort": reasoning_effort},
                tools=[{"type": "web_search"}],
                instructions=config["instructions"]["Websearch"],
                input=input_messages,
            )
        chat_history.append({"role": "assistant", "content": response.output_text})
        markdown_text = response.output_text
        markdown = Markdown(markdown_text)
        copyline(response.output_text)
        console.print(markdown)
    except (APIError, APIConnectionError, AuthenticationError, RateLimitError) as e:
        handle_api_error(e)
        # Remove user message from history if API call failed
        chat_history.pop()


def ITSecurty_Websearch():
    model = config["ITSecurty_Websearch"]
    securityNewsPromt = config["securityNewsPromt"]

    try:
        with console.status(f"[bold green]{model} is Thinking...") as status:
            response = client.responses.create(
                model=model,
                reasoning={"effort": "low"},
                instructions=config["instructions"]["ITSecurityNews"],
                tools=[
                    {
                        "type": "web_search",
                        "filters": {"allowed_domains": config["security_domains"]},
                    }
                ],
                tool_choice="auto",
                include=["web_search_call.action.sources"],
                input=f"{securityNewsPromt}",
            )
        message = response.output[-1]
        markdown_text = message.content[0].text
        markdown = Markdown(markdown_text)
        console.print(markdown)
    except (APIError, APIConnectionError, AuthenticationError, RateLimitError) as e:
        handle_api_error(e)


def normalchat(userfrage):
    model = config["normalchat"]
    reasoning_effort = config["reasoning_effort"]["normalchat"]
    chat_history.append({"role": "user", "content": userfrage})
    input_messages = convert_to_responses_format(chat_history)

    try:
        with console.status(f"[bold green]{model} is Thinking... ") as status:
            response = client.responses.create(
                model=model,
                reasoning={"effort": reasoning_effort},
                instructions=config["instructions"]["normalchat"],
                input=input_messages,
            )
        chat_history.append({"role": "assistant", "content": response.output_text})
        markdown_text = response.output_text
        markdown = Markdown(markdown_text)
        copyline(response.output_text)
        console.print(markdown)
    except (APIError, APIConnectionError, AuthenticationError, RateLimitError) as e:
        handle_api_error(e)
        # Remove user message from history if API call failed
        chat_history.pop()


def mailkoregierer(userfrage):
    model = config["email"]
    reasoning_effort = config["reasoning_effort"]["email"]
    try:
        with console.status(f"[bold green]{model} is Thinking...") as status:
            response = client.responses.create(
                model=model,
                reasoning={"effort": reasoning_effort},
                instructions=config["instructions"]["email"],
                input=f"{userfrage}",
            )
        copyline(response.output_text)
        print(response.output_text)
    except (APIError, APIConnectionError, AuthenticationError, RateLimitError) as e:
        handle_api_error(e)


def translate(userfrage):
    model = config["translate"]
    reasoning_effort = config["reasoning_effort"]["translate"]
    try:
        with console.status(f"[bold green]{model} is Thinking...") as status:
            response = client.responses.create(
                model=model,
                reasoning={"effort": reasoning_effort},
                instructions=config["instructions"]["translate"],
                input=f"{userfrage}",
            )
        copyline(response.output_text)
        print(response.output_text)
    except (APIError, APIConnectionError, AuthenticationError, RateLimitError) as e:
        handle_api_error(e)


def codex(userfrage):
    instruction_template = config["instructions"]["codex"]
    final_instruction = instruction_template.format(
        currentOS=currentOS, platforminfo=platforminfo
    )
    model = config["codex"]
    reasoning_effort = config["reasoning_effort"]["codex"]

    chat_history.append({"role": "user", "content": userfrage})
    input_messages = convert_to_responses_format(chat_history)

    try:
        with console.status(f"[bold green]{model} is Thinking... ") as status:
            response = client.responses.create(
                model=model,
                reasoning={"effort": reasoning_effort},
                instructions=final_instruction,
                input=input_messages,
            )
        chat_history.append({"role": "assistant", "content": response.output_text})
        markdown_text = response.output_text
        markdown = Markdown(markdown_text)
        copyline(response.output_text)
        console.print(markdown)
    except (APIError, APIConnectionError, AuthenticationError, RateLimitError) as e:
        handle_api_error(e)
        # Remove user message from history if API call failed
        chat_history.pop()


def main():
    if args.init:
        control = input("Reset configuration file to defaults? (y/n): ").lower()
        if control == "y":
            init_config()
            console.print("[green]✓ Configuration reset to defaults[/green]")
            sys.exit(0)
        else:
            console.print("[yellow]Configuration reset cancelled[/yellow]")
            sys.exit(0)

    elif args.edit_instructions:
        edit_instructions(args.edit_instructions)
        sys.exit(0)

    elif args.Websearch:
        interactive_chat(Websearch, mode="Websearch", resume_chat=args.resume)



    elif args.Mail:
        if isinstance(args.Mail, str):
            # User provided text
            mailkoregierer(args.Mail)
        else:
            # args.Mail is True → Use clipboard
            userfrage = pasteline()
            console.print("[green]✓ Clipboard read successfully[/green]")
            mailkoregierer(userfrage)

    elif args.Translate:
        if isinstance(args.Translate, str):
            # User provided text
            translate(args.Translate)
        else:
            # args.Translate is True → Use clipboard
            userfrage = pasteline()
            console.print("[green]✓ Clipboard read successfully[/green]")
            translate(userfrage)

    elif args.setup:
        show_setup_file()
        console.print("[bold green]✅ Configuration file opened[/bold green]")

    elif args.ITSecurityNews:
        ITSecurty_Websearch()

    elif args.version:
        console.print(f"[bold cyan]🚀 Version:[/bold cyan] [green]{VERSION}[/green]")
        console.print(f"[bold cyan]👨 Author:[/bold cyan] [yellow]{AUTHOR}[/yellow]")
        console.print(f"[bold cyan]📜 License:[/bold cyan] [blue]{LICENSE}[/blue]")
        console.print(f"[bold cyan]💻 OpenAI Library:[/bold cyan] [magenta]{OPENAI_VERSION}[/magenta]")
        console.print(f"[bold cyan]🖥️ Description:[/bold cyan] [magenta]{DESCRIPTION}[/magenta]")
    elif args.codex:
        if isinstance(args.codex, str):
            codex(args.codex)
        else:
            interactive_chat(codex, mode="codex", resume_chat=args.resume)

    # If user doesn't provide arguments
    else:
        interactive_chat(normalchat, mode="normalchat", resume_chat=args.resume)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Global Ctrl+C handler → Clean exit
        # PyInstaller issue: Even print() can be interrupted
        # Therefore: Exit only, no output
        try:
            console.print("\n[yellow]Program terminated[/yellow]")
        except:
            pass
        finally:
            os._exit(0)  # Force immediate exit without cleanup
