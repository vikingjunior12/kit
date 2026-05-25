# Changelog

Alle nennenswerten Änderungen an KIterminal (kit) werden in dieser Datei dokumentiert.

## [0.9.1] — 2026-05-25

### Hinzugefügt
- **Streaming-Output:** Antworten erscheinen live im Terminal mit Rich `Live`+`Markdown`-Rendering
- **Startup-Banner:** Beim Start wird Provider, Modell und Version angezeigt
- **Dynamischer Prompt:** Prompt zeigt aktiven Provider + Modell (`deep/v4-flash 💬`)
- **`[project.scripts]`:** `kit = "kit:main"` → `pipx install .` macht `kit` global

### Gefixt
- **Markdown-Rendering:** Streaming nutzt jetzt `rich.live.Live` mit `rich.markdown.Markdown` — Tabellen, Code-Blocks, Listen werden live gerendert
- **Runtime-Deps:** `rich`, `pyperclip`, `prompt-toolkit` nach `[project].dependencies` verschoben (waren fälschlich in `[dependency-groups].dev` → `pipx` hat sie nicht installiert)
- **Paket-Struktur:** Flache `.py`-Dateien → `kit/`-Paket mit `__init__.py` (pipx braucht Packages, nicht lose Module)
- **Python-Version:** `requires-python` auf `<4.0` gelockert (CachyOS hat 3.14)

### Lessons Learned
- **`pipx` installiert nur `[project].dependencies`** — Runtime-Deps gehören NICHT in `[dependency-groups].dev`
- **`pipx` braucht Python-Packages** (Verzeichnis mit `__init__.py`), keine losen `.py`-Module
- **`[project.scripts]` Entry-Point** muss auf `paket:funktion` zeigen, nicht auf lockere Datei
- **Streaming + Markdown** kombinierbar via `rich.live.Live(Markdown(text))` — kein Trade-off nötig

### Geändert
- Chat-Modi (normalchat, codex) streamen jetzt live; Mail/Translate bleiben bei One-Shot ohne Stream
- Verbesserte Fehlerbehandlung: `_call_api()` fängt `ValueError` von `get_client()` sauber ab

## [0.9.0] — 2026-05-25

### Hinzugefügt
- **Multi-Provider-Support:** Anthropic Claude + DeepSeek V4 (Flash & Pro)
- `providers.py` — Provider-Abstraktion, DeepSeek via Anthropic-kompatiblen Endpoint
- API-Keys aus Umgebungsvariablen: `ANTHROPIC_API_KEY`, `DEEPSEEK_API_KEY`
- Config v2.0 mit pro-Modus Provider/Modell/max_tokens/reasoning_effort
- Automatische Migration von v1.x Configs

### Entfernt
- Websearch-Modus (`-w`) — durch vollwertige Agents (Claude Code, Codex CLI) abgedeckt
- IT-Security-News-Modus (`-it`) — gleicher Grund

### Geändert
- CLI-Texte auf Deutsch
- Code-Struktur bereinigt, `_call_api()` als zentrale API-Schnittstelle
- README komplett neu, auf Deutsch, mit Multi-Provider-Dokumentation

## [0.8.2] und früher

Siehe Git-History für Details zu älteren Versionen.
