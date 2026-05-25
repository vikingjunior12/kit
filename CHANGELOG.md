# Changelog

Alle nennenswerten Änderungen an KIterminal (kit) werden in dieser Datei dokumentiert.

## [0.9.1] — 2026-05-25

### Hinzugefügt
- **Streaming-Output:** Antworten erscheinen jetzt live Wort-für-Wort im Terminal (statt auf einmal nach Fertigstellung)
- **Startup-Banner:** Beim Start wird Provider, Modell und Version angezeigt (`kit v0.9.1 · DeepSeek · deepseek-v4-flash · Modus: Chat`)
- **Dynamischer Prompt:** Der Prompt zeigt jetzt den aktiven Provider und das Modell (`deep/v4-flash 💬` oder `anth/sonnet-4-6 💬`)

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
