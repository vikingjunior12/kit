# Kit — KIterminal

**Ein schlankes Terminal-KI-Tool für schnelle Aufgaben.**

Multi-Provider-Support: **Anthropic Claude** + **DeepSeek V4 (Flash & Pro)**. Entwickelt als Ergänzung zu vollwertigen Coding-Agents (Claude Code, Codex CLI) — für die kleinen, schnellen Dinge zwischendurch.

## Features

- 🤖 **Multi-Provider** — Anthropic Claude + DeepSeek V4, pro Modus konfigurierbar
- 💬 **Chat-Modi**
  - Normaler Chat (default)
  - Codex — Programmier-Assistent
- ✉️ **E-Mail** — Korrektur (`-m`), Verbesserung (`-ma`), Professioneller Rewrite (`-mp`)
- 🌐 **Übersetzung** — DE↔EN aus Clipboard oder direkt (`-t`)
- 📋 **Clipboard-Integration** — Input aus Clipboard lesen, Antwort automatisch kopieren
- 🔄 **Pipe-Support** — `cat file.txt | kit "Zusammenfassen"` + interaktiver Follow-up
- 💾 **Chat-History** — Automatisches Speichern, Fortsetzen mit `-r`

## Installation

### Voraussetzungen

- Python 3.13+
- Anthropic API-Key ([console.anthropic.com](https://console.anthropic.com))
- DeepSeek API-Key ([platform.deepseek.com](https://platform.deepseek.com/api_keys)) — optional

### Aus dem Repository

```bash
git clone git@github.com:vikingjunior12/kit.git
cd kit
pip install anthropic rich prompt_toolkit pyperclip
```

### API-Keys einrichten

```bash
export ANTHROPIC_API_KEY='dein-anthropic-key'
export DEEPSEEK_API_KEY='dein-deepseek-key'   # optional

# Permanent:
echo "export ANTHROPIC_API_KEY='dein-key'" >> ~/.zshrc
echo "export DEEPSEEK_API_KEY='dein-key'" >> ~/.zshrc
source ~/.zshrc
```

## Verwendung

### Normaler Chat

```bash
kit                     # Interaktiver Chat
kit -r                  # Vorherigen Chat fortsetzen
```

### Codex (Programmier-Assistent)

```bash
kit -c                  # Interaktiv
kit -c "Wie sortiere ich eine Liste in Python?"
kit -c -r               # Codex-Chat fortsetzen
```

### E-Mail-Korrektur

```bash
kit -m                  # Aus Clipboard lesen + korrigieren
kit -m "Hallo, ich wollte fragen ob..."
kit -ma                 # Korrektur + inhaltliche Verbesserung
kit -mp                 # Professioneller Business-Rewrite
```

### Übersetzung

```bash
kit -t                  # Aus Clipboard
kit -t "Hello World"
```

### Pipe-Support

```bash
# Code Review
cat script.py | kit -c "Review diesen Code"

# Log-Analyse
tail -100 app.log | kit "Fasse die Fehler zusammen"

# E-Mail aus Datei
cat email.txt | kit -m

# Übersetzung aus Datei
cat dokument.txt | kit -t
```

Nach der Pipe-Verarbeitung wechselt kit automatisch in den interaktiven Modus für Folgefragen.

## Konfiguration

### Provider & Modell pro Modus

Bearbeite `~/.config/KIterminal/config.json`:

```json
{
  "version": "2.0",
  "language": "de",
  "modes": {
    "normalchat": {
      "provider": "deepseek",
      "model": "deepseek-v4-flash",
      "max_tokens": 4096,
      "reasoning_effort": "none"
    },
    "codex": {
      "provider": "anthropic",
      "model": "claude-sonnet-4-6",
      "max_tokens": 4096,
      "reasoning_effort": "low"
    }
  }
}
```

**Provider-Optionen:** `anthropic`, `deepseek`  
**DeepSeek-Modelle:** `deepseek-v4-flash` (schnell), `deepseek-v4-pro` (stark)  
**Reasoning Effort:** `none`, `low`, `medium`, `high`

### Config-Editor

```bash
kit --setup             # Config mit Editor öffnen
kit -e codex            # Codex-Instructions bearbeiten
kit -e normalchat       # Chat-Instructions bearbeiten
kit -i                  # Auf Werkseinstellungen zurücksetzen
```

### Sprache

Setze `"language": "de"` in der Config für deutsche Antworten.  
Unterstützt: `en`, `de`, `chde`, `fr`, `es`, `it`, `pt`, `nl`

## Architektur

```
kit.py          — Main: CLI, Modi, Chat-Loop
config.py       — Config v2.0 + Instruction-Dateien
providers.py    — Provider-Abstraktion (Anthropic + DeepSeek)
chat_history.py — Persistente Chat-Speicherung
```

Alle Provider nutzen das gleiche API-Format (`client.messages.create()`). DeepSeek wird über den Anthropic-kompatiblen Endpoint (`https://api.deepseek.com/anthropic`) angesprochen — keine Message-Format-Konvertierung nötig.

## Plattform-Support

- **Linux** — vollständig
- **macOS** — vollständig
- **WSL (Windows)** — vollständig
- **Termux (Android)** — Clipboard-Integration angepasst

## Tipps

1. **Pipe + Follow-up** — `cat file | kit -c "Erklären"` und dann direkt Folgefragen stellen
2. **Chat fortsetzen** — `-r` lädt den letzten Chat mit allen Kontext
3. **Clipboard-Workflow** — Text kopieren → `kit -m` oder `kit -t` → Antwort ist schon im Clipboard
4. **Reasoning steuern** — `reasoning_effort: "high"` für komplexe Fragen, `"none"` für schnelle Antworten
5. **Provider pro Aufgabe** — DeepSeek Flash für einfache Sachen, Anthropic/DeepSeek Pro für Code

## License

MIT — [JLI-Software](https://github.com/vikingjunior12)
