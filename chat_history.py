"""
Chat History Management für KIterminal

Dieses Modul verwaltet die persistente Speicherung von Chat-Verläufen.
Es ermöglicht das automatische Speichern und Wiederherstellen von Konversationen
für die Modi: normalchat, websearch und codex.

Funktionalität:
- Automatisches Speichern beim Beenden
- Fortsetzen vorheriger Chats mit interaktivem Menü
- Modusspezifische Trennung (jeder Modus hat eigene Chat-Files)
- Permanente Speicherung ohne automatisches Löschen

Speicherort: ~/.config/KIterminal/chats/
Dateiformat: {mode}_{timestamp}.json
"""

import json
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt
from config import loadconfig
# Globale Variable: Trackt den aktuell geladenen Chat-File
# Wird gesetzt wenn ein Chat fortgesetzt wird, sonst None
current_chat_file = None

# Console-Instanz für Rich-Ausgaben
console = Console()

def get_chat_dir():
    """
    Gibt das Chat-Speicherverzeichnis zurück und erstellt es falls nötig.
    
    Verwendet den benutzerdefinierten Pfad aus der Config falls gesetzt,
    andernfalls den Standard-Pfad ~/.config/KIterminal/chats/

    Returns:
        Path: Pfad zum Chat-Verzeichnis
    """
    config = loadconfig()
    custom_path = config.get("Chatpath", "")
    
    # Prüfe ob custom_path gesetzt und nicht leer ist
    if custom_path and custom_path.strip():
        chat_dir = Path(custom_path) / "KITchats"
    else:
        chat_dir = Path.home() / ".config" / "KIterminal" / "KITchats"
    
    chat_dir.mkdir(parents=True, exist_ok=True)
    return chat_dir


def save_chat(chat_history, mode, filepath=None):
    """
    Speichert die Chat-Historie in einer JSON-Datei.

    Verhaltensweise:
    - Wenn filepath übergeben wird (Chat wird fortgesetzt):
      → Überschreibt die bestehende Datei mit dem gleichen Timestamp
    - Wenn filepath=None (neuer Chat):
      → Erstellt eine neue Datei mit aktuellem Timestamp

    Args:
        chat_history (list): Liste von Nachrichten [{"role": "user/assistant", "content": "..."}]
        mode (str): Chat-Modus (normalchat, websearch, codex)
        filepath (Path, optional): Pfad zum bestehenden Chat-File. Defaults to None.

    Returns:
        Path: Pfad zur gespeicherten Datei, oder None wenn chat_history leer ist

    Beispiel JSON-Struktur:
        {
            "mode": "normalchat",
            "timestamp": "2025-11-16_14-30-15",
            "history": [
                {"role": "user", "content": "Hallo"},
                {"role": "assistant", "content": "Hallo! Wie kann ich helfen?"}
            ]
        }
    """
    # Leere Chat-Historie wird nicht gespeichert
    if not chat_history:
        return None

    chat_dir = get_chat_dir()

    # Fall 1: Bestehenden Chat fortsetzen
    if filepath:
        filepath = Path(filepath)
        # Versuche den ursprünglichen Timestamp aus der Datei zu lesen
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                # Behalte den originalen Timestamp bei
                timestamp = existing_data.get("timestamp", datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        except:
            # Fallback: Falls die Datei nicht lesbar ist, nutze aktuellen Timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Fall 2: Neuen Chat erstellen
    else:
        # Erstelle Timestamp im Format: YYYY-MM-DD_HH-MM-SS
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # Dateiname: {mode}_{timestamp}.json (z.B. normalchat_2025-11-16_14-30-15.json)
        filename = f"{mode}_{timestamp}.json"
        filepath = chat_dir / filename

    # Erstelle die JSON-Struktur
    chat_data = {
        "mode": mode,
        "timestamp": timestamp,
        "history": chat_history
    }

    # Speichere in Datei mit UTF-8 Encoding (wichtig für Umlaute/Emojis)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(chat_data, f, ensure_ascii=False, indent=2)

    return filepath


def load_chat(filepath):
    """
    Lädt einen gespeicherten Chat aus einer JSON-Datei.

    Args:
        filepath (str/Path): Pfad zur Chat-Datei

    Returns:
        list: Chat-Historie als Liste von Message-Dictionaries

    Raises:
        FileNotFoundError: Wenn die Datei nicht existiert
        json.JSONDecodeError: Wenn die JSON-Struktur ungültig ist
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        chat_data = json.load(f)
    return chat_data["history"]


def list_saved_chats(mode=None):
    """
    Listet alle gespeicherten Chats auf, optional gefiltert nach Modus.

    Args:
        mode (str, optional): Filter für spezifischen Modus (normalchat, websearch, codex).
                             Wenn None, werden alle Chats aufgelistet.

    Returns:
        list: Liste von Chat-Informationen, sortiert nach Änderungsdatum (neueste zuerst)
              Jeder Eintrag enthält:
              - filepath: Pfad zur Chat-Datei
              - mode: Chat-Modus
              - timestamp: Original-Timestamp
              - preview: Vorschau der ersten User-Nachricht (max 60 Zeichen)
              - message_count: Anzahl der Nachrichten im Chat

    Beispiel Rückgabe:
        [
            {
                "filepath": Path("~/.config/KIterminal/chats/normalchat_2025-11-16_14-30-15.json"),
                "mode": "normalchat",
                "timestamp": "2025-11-16_14-30-15",
                "preview": "Hallo wie gehts?",
                "message_count": 8
            },
            ...
        ]
    """
    chat_dir = get_chat_dir()

    # Glob-Pattern: Suche nach "{mode}_*.json" oder allen "*.json" wenn kein Modus angegeben
    pattern = f"{mode}_*.json" if mode else "*.json"

    # Finde alle passenden Dateien, sortiert nach Änderungsdatum (neueste zuerst)
    chat_files = sorted(
        chat_dir.glob(pattern),
        key=lambda p: p.stat().st_mtime,  # Sortierung nach Modifikationszeit
        reverse=True  # Neueste zuerst
    )

    chats = []
    for filepath in chat_files:
        try:
            # Lade die Chat-Datei
            with open(filepath, 'r', encoding='utf-8') as f:
                chat_data = json.load(f)

                # Extrahiere die erste User-Nachricht für die Vorschau
                first_user_msg = next(
                    (m["content"] for m in chat_data["history"] if m["role"] == "user"),
                    ""  # Fallback: Leerer String falls keine User-Nachricht gefunden
                )

                # Kürze die Vorschau auf 60 Zeichen
                preview = first_user_msg[:60] + "..." if len(first_user_msg) > 60 else first_user_msg

                # Füge Chat-Info zur Liste hinzu
                chats.append({
                    "filepath": filepath,
                    "mode": chat_data["mode"],
                    "timestamp": chat_data["timestamp"],
                    "preview": preview,
                    "message_count": len(chat_data["history"])
                })
        except (json.JSONDecodeError, KeyError):
            # Überspringe fehlerhafte/unvollständige Dateien
            continue

    return chats


def show_chat_selection_menu(mode):
    """
    Zeigt ein interaktives Auswahlmenü für gespeicherte Chats.

    Der User kann:
    - Einen vorherigen Chat auswählen (1, 2, 3, ...)
    - "0" wählen um einen neuen Chat zu starten

    Args:
        mode (str): Chat-Modus für den Chats angezeigt werden sollen

    Returns:
        Path or None:
            - Path-Objekt zur ausgewählten Chat-Datei
            - None wenn User "0" wählt (neuer Chat) oder keine Chats vorhanden

    Ausgabe-Format:
        Gespeicherte normalchat-Chats:

        1. 2025:11:16 14:30:15 - Hallo wie gehts? (8 Nachrichten)
        2. 2025:11:16 13:20:10 - Kannst du mir helfen? (12 Nachrichten)
        0. Neuen Chat starten

        Wähle einen Chat (0):
    """
    # Hole alle gespeicherten Chats für diesen Modus
    chats = list_saved_chats(mode)

    # Falls keine Chats vorhanden sind
    if not chats:
        console.print(f"[yellow]Keine gespeicherten {mode}-Chats gefunden.[/yellow]")
        return None

    # Zeige Überschrift
    console.print(f"\n[bold cyan]Gespeicherte {mode}-Chats:[/bold cyan]\n")

    # Zeige jeden Chat als nummerierte Option
    for idx, chat in enumerate(chats, 1):  # Start bei 1 (nicht 0)
        # Formatiere Timestamp für Anzeige: "2025:11:16 14:30:15"
        timestamp_display = chat["timestamp"].replace("_", " ").replace("-", ":")

        # Zeige: Nummer, Timestamp, Vorschau, Anzahl Nachrichten
        console.print(
            f"[cyan]{idx}[/cyan]. {timestamp_display} - {chat['preview']} "
            f"[dim]({chat['message_count']} Nachrichten)[/dim]"
        )

    # Option 0: Neuer Chat
    console.print(f"[cyan]0[/cyan]. Neuen Chat starten\n")

    # Eingabeschleife bis gültige Auswahl
    while True:
        try:
            choice = Prompt.ask("[bold cyan]Wähle einen Chat[/bold cyan]", default="0")

            try:
                choice_idx = int(choice)

                # Option 0: Neuer Chat
                if choice_idx == 0:
                    return None

                # Gültige Chat-Nummer (1 bis Anzahl Chats)
                if 1 <= choice_idx <= len(chats):
                    return chats[choice_idx - 1]["filepath"]  # -1 weil Liste bei 0 startet

                # Ungültige Nummer
                console.print("[red]Ungültige Auswahl, bitte versuche es erneut.[/red]")

            except ValueError:
                # User hat keine Zahl eingegeben
                console.print("[red]Bitte gib eine Zahl ein.[/red]")

        except KeyboardInterrupt:
            # Ctrl+C im Auswahlmenü → Gib None zurück, globaler Handler übernimmt
            raise
