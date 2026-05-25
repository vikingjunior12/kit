"""
Multi-Provider Client für KIterminal.

Unterstützt Anthropic (nativ) und DeepSeek (via Anthropic-kompatiblem Endpoint).
DeepSeek: https://api-docs.deepseek.com/guides/anthropic_api
"""

import os
import anthropic

# Provider-Konfiguration
PROVIDERS = {
    "anthropic": {
        "name": "Anthropic",
        "env": "ANTHROPIC_API_KEY",
        "base_url": None,  # Standard-URL von anthropic SDK
    },
    "deepseek": {
        "name": "DeepSeek",
        "env": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com/anthropic",
    },
}


def get_client(provider_name: str) -> anthropic.Anthropic:
    """
    Erstellt einen Anthropic-Client für den angegebenen Provider.

    Args:
        provider_name: "anthropic" oder "deepseek"

    Returns:
        anthropic.Anthropic Client-Instanz

    Raises:
        ValueError: Wenn der Provider unbekannt ist oder der API-Key fehlt
    """
    if provider_name not in PROVIDERS:
        raise ValueError(
            f"Unbekannter Provider '{provider_name}'. "
            f"Verfügbar: {', '.join(PROVIDERS.keys())}"
        )

    cfg = PROVIDERS[provider_name]
    api_key = os.environ.get(cfg["env"])

    if not api_key:
        raise ValueError(
            f"❌ {cfg['name']} API-Key nicht gesetzt!\n"
            f"Bitte setze die Umgebungsvariable: export {cfg['env']}='dein-key'"
        )

    kwargs = {"api_key": api_key}
    if cfg["base_url"]:
        kwargs["base_url"] = cfg["base_url"]

    return anthropic.Anthropic(**kwargs)


def get_provider_name(provider_name: str) -> str:
    """Gibt den lesbaren Namen eines Providers zurück."""
    return PROVIDERS.get(provider_name, {}).get("name", provider_name)


def list_providers() -> list[str]:
    """Gibt alle verfügbaren Provider-Namen zurück."""
    return list(PROVIDERS.keys())
