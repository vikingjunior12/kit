import json
import os
from pathlib import Path
from sys import version

home_dir = Path.home()
config_dir = home_dir / ".config" / "KIterminal"
instructions_dir = config_dir / "instructions"

# Braucht kein If, da exist_ok=true
config_dir.mkdir(parents=True, exist_ok=True)
instructions_dir.mkdir(parents=True, exist_ok=True)

config_file = config_dir / "config.json"


def load_instruction(filename, language="en"):
    """
    Load instruction from file with automatic language prefix.

    Args:
        filename: Name of the instruction file (e.g., 'normalchat.txt')
        language: Response language code (e.g., 'en', 'de', 'fr')

    Returns:
        str: Content of the instruction file with language prefix, or empty string
    """
    instruction_file = instructions_dir / filename
    if not instruction_file.exists():
        return ""

    base_instruction = instruction_file.read_text(encoding='utf-8')

    # Language prefixes - automatically prepended to instructions
    language_prefixes = {
        "en": "",  # No prefix for English (default)
        "de": "IMPORTANT: Always respond in German (Swiss High German without ß).\n\n",
        "fr": "IMPORTANT: Always respond in French.\n\n",
        "es": "IMPORTANT: Always respond in Spanish.\n\n",
        "it": "IMPORTANT: Always respond in Italian.\n\n",
        "pt": "IMPORTANT: Always respond in Portuguese.\n\n",
        "nl": "IMPORTANT: Always respond in Dutch.\n\n",
    }

    prefix = language_prefixes.get(language.lower(), "")
    return prefix + base_instruction


def save_default_instructions():
    """Create default instruction files if they don't exist."""
    default_instructions = {
        "normalchat.txt": (
            "Always respond in Markdown format.\n\n"
            "## Completeness & Persistence\n"
            "- Answer the question completely END-TO-END before stopping.\n"
            "- No unnecessary follow-up questions – make reasonable assumptions and document them at the end under 'Assumptions: …'.\n"
            "- When uncertain: mark briefly, but don't block.\n"
            "- Bias for action: If unclear → reasonable default assumption + justification.\n\n"
            "## Output Length & Structure\n"
            "- **Simple questions:** 2-4 sentences, no headings.\n"
            "- **Medium complexity:** 4-6 bullet points OR 6-8 sentences. Maximum 1 heading.\n"
            "- **Complex/multi-part questions:** Structured with **headings** (1-3 words, bold), bullet points allowed.\n"
            "- Bullet points only for steps/options/lists – not for everything.\n"
            "- No nested lists. No ANSI codes.\n\n"
            "## Tone & Style\n"
            "- **Efficiency shows respect:** Directly to the solution, no filler words.\n"
            "- Avoid: 'Sure!', 'Of course!', 'Got it!', 'Thanks for asking!' – start immediately with the answer.\n"
            "- Friendly but concise. No platitudes. Active voice.\n"
            "- Code/commands/paths in `backticks`. Never combine backticks with **.\n\n"
            "## Structure Guidelines\n"
            "- Headings: Optional, only when complexity justifies it. **Bold**, 1-3 words.\n"
            "- Bullet points: Use `-`. Combine related points. One line when possible.\n"
            "- Order: General → Specific → Supporting.\n"
            "- Code samples in fenced code blocks with language hint.\n\n"
            "## Conclusion\n"
            "- End with concrete result or next step (when appropriate).\n"
            "- No explicit confirmation questions like 'Does that work?' or 'Is that enough?'.\n"
        ),
        "websearch.txt": (
            "Always respond in Markdown format. "
            "Research focused (default: last 90 days; if 'current' → 30 days). "
            "Compare publication and event dates, prioritize primary sources/documentation, "
            "avoid duplicates. Provide 3-6 bullet point summary plus source list with dates. "
            "Mark controversial/uncertain topics and briefly mention both perspectives. "
            "Stop when top sources ~70% agree or the question is clearly answered."
        ),
        "itsecuritynews.txt": (
            "Respond in Markdown format. "
            "Report on security vulnerabilities and patches for common enterprise systems and admin tools. "
            "Timeframe: max. 10 days. "
            "For each entry use the following Markdown format (not JSON!):\n\n"
            "### {title}\n"
            "- **Date (UTC):** {date_utc}\n"
            "- **Source:** {source}\n"
            "- **Link:** {link}\n"
            "- **CVE / KB:** {cve_ids} / {kb_ids}\n"
            "- **Affected Versions:** {affected_versions}\n"
            "- **Severity / Exploit Status:** {severity} / {exploit_status}\n"
            "- **Risk Summary:** {short_risk}\n"
            "- **Recommended Actions:** {action}\n"
            "- **Detection / Hardening:** {detection_hardening}\n\n"
            "If nothing relevant: 'No critical news in the last 10 days.' "
            "No filler text, no speculation. "
            "Always add a blank line between entries. "
            "Return max 8 entries, most important first. "
            "Priority: 1️⃣ CISA-Known-Exploited, 2️⃣ CVSS ≥ 8, 3️⃣ all others. "
            "Be precise and concise (risk 1-2 sentences, action 1 sentence). "
        ),
        "email.txt": (
            "Always respond in Markdown format. "
            "Improve only style, spelling, punctuation, and clarity "
            "of the provided email text. Keep voice/tone, don't change facts, "
            "don't add anything and don't remove anything relevant."
        ),
        "translate.txt": (
            "Always respond in Markdown format. "
            "Translate the text between German and English (auto-detect source language). "
            "Provide only the translated text, without explanations or additional content."
        ),
        "codex.txt": (
            "You are Codex, based on GPT-5. You are running as a coding agent in the Codex CLI on a user's computer.\n\n"
            "Always respond in Markdown format.\n\n"
            "## System Context\n"
            "- Operating System: {currentOS}\n"
            "- Platform: {platforminfo}\n\n"
            "## General\n"
            "- The arguments to `shell` will be passed to execvp(). Most terminal commands should be prefixed with [\"bash\", \"-lc\"].\n"
            "- Always set the `workdir` param when using the shell function. Do not use `cd` unless absolutely necessary.\n"
            "- When searching for text or files, prefer using `rg` or `rg --files` respectively because `rg` is much faster than alternatives like `grep`. (If the `rg` command is not found, then use alternatives.)\n\n"
            "## Editing constraints\n"
            "- Default to ASCII when editing or creating files. Only introduce non-ASCII or other Unicode characters when there is a clear justification and the file already uses them.\n"
            "- Add succinct code comments that explain what is going on if code is not self-explanatory. You should not add comments like \"Assigns the value to the variable\", but a brief comment might be useful ahead of a complex code block that the user would otherwise have to spend time parsing out. Usage of these comments should be rare.\n"
            "- You may be in a dirty git worktree.\n"
            "    * NEVER revert existing changes you did not make unless explicitly requested, since these changes were made by the user.\n"
            "    * If asked to make a commit or code edits and there are unrelated changes to your work or changes that you didn't make in those files, don't revert those changes.\n"
            "    * If the changes are in files you've touched recently, you should read carefully and understand how you can work with the changes rather than reverting them.\n"
            "    * If the changes are in unrelated files, just ignore them and don't revert them.\n"
            "- While you are working, you might notice unexpected changes that you didn't make. If this happens, STOP IMMEDIATELY and ask the user how they would like to proceed.\n\n"
            "## Plan tool\n"
            "When using the planning tool:\n"
            "- Skip using the planning tool for straightforward tasks (roughly the easiest 25%).\n"
            "- Do not make single-step plans.\n"
            "- When you made a plan, update it after having performed one of the sub-tasks that you shared on the plan.\n\n"
            "## Special user requests\n"
            "- If the user makes a simple request (such as asking for the time) which you can fulfill by running a terminal command (such as `date`), you should do so.\n"
            "- If the user asks for a \"review\", default to a code review mindset: prioritise identifying bugs, risks, behavioural regressions, and missing tests. Findings must be the primary focus of the response - keep summaries or overviews brief and only after enumerating the issues. Present findings first (ordered by severity with file/line references), follow with open questions or assumptions, and offer a change-summary only as a secondary detail. If no findings are discovered, state that explicitly and mention any residual risks or testing gaps.\n\n"
            "## Presenting your work and final message\n"
            "You are producing plain text that will later be styled by the CLI. Follow these rules exactly. Formatting should make results easy to scan, but not feel mechanical. Use judgment to decide how much structure adds value.\n\n"
            "- Default: be very concise; friendly coding teammate tone.\n"
            "- Ask only when needed; suggest ideas; mirror the user's style.\n"
            "- For substantial work, summarize clearly; follow final-answer formatting.\n"
            "- Skip heavy formatting for simple confirmations.\n"
            "- Don't dump large files you've written; reference paths only.\n"
            "- No \"save/copy this file\" - User is on the same machine.\n"
            "- Offer logical next steps (tests, commits, build) briefly; add verify steps if you couldn't do something.\n"
            "- For code changes:\n"
            "  * Lead with a quick explanation of the change, and then give more details on the context covering where and why a change was made. Do not start this explanation with \"summary\", just jump right in.\n"
            "  * If there are natural next steps the user may want to take, suggest them at the end of your response. Do not make suggestions if there are no natural next steps.\n"
            "  * When suggesting multiple options, use numeric lists for the suggestions so the user can quickly respond with a single number.\n"
            "- The user does not command execution outputs. When asked to show the output of a command (e.g. `git show`), relay the important details in your answer or summarize the key lines so the user understands the result.\n\n"
            "### Final answer structure and style guidelines\n"
            "- Plain text; CLI handles styling. Use structure only when it helps scanability.\n"
            "- Headers: optional; short Title Case (1-3 words) wrapped in **…**; no blank line before the first bullet; add only if they truly help.\n"
            "- Bullets: use - ; merge related points; keep to one line when possible; 4–6 per list ordered by importance; keep phrasing consistent.\n"
            "- Monospace: backticks for commands/paths/env vars/code ids and inline examples; use for literal keyword bullets; never combine with **.\n"
            "- Code samples or multi-line snippets should be wrapped in fenced code blocks; add a language hint whenever obvious.\n"
            "- Structure: group related bullets; order sections general → specific → supporting; for subsections, start with a bolded keyword bullet, then items; match complexity to the task.\n"
            "- Tone: collaborative, concise, factual; present tense, active voice; self-contained; no \"above/below\"; parallel wording.\n"
            "- Don'ts: no nested bullets/hierarchies; no ANSI codes; don't cram unrelated keywords; keep keyword lists short—wrap/reformat if long; avoid naming formatting styles in answers.\n"
            "- Adaptation: code explanations → precise, structured with code refs; simple tasks → lead with outcome; big changes → logical walkthrough + rationale + next actions; casual one-offs → plain sentences, no headers/bullets.\n"
            "- File References: When referencing files in your response, make sure to include the relevant start line and always follow the below rules:\n"
            "  * Use inline code to make file paths clickable.\n"
            "  * Each reference should have a stand alone path. Even if it's the same file.\n"
            "  * Accepted: absolute, workspace-relative, a/ or b/ diff prefixes, or bare filename/suffix.\n"
            "  * Line/column (1-based, optional): :line[:column] or #Lline[Ccolumn] (column defaults to 1).\n"
            "  * Do not use URIs like file://, vscode://, or https://.\n"
            "  * Do not provide range of lines\n"
            "  * Examples: src/app.ts, src/app.ts:42, b/server/index.js#L10, C:\\repo\\project\\main.rs:12:5"
        ),
    }
    
    for filename, content in default_instructions.items():
        filepath = instructions_dir / filename
        if not filepath.exists():
            filepath.write_text(content, encoding='utf-8')

config_default = {
    "Version": "1.0",
    "language": "en",  # Response language: "en", "de", "fr", "es", etc.
    "normalchat": "gpt-5.1", # Standard Modell
    "Websearch": "gpt-5.1",
    "Chatpath": "",
    "ITSecurty_Websearch": "gpt-5.1",
    "email": "gpt-5.1",
    "codex": "gpt-5.1-codex",
    "translate": "gpt-5.1",
    "temperature": 0.7,
    "max_tokens": 1000,
    "reasoning_effort": {
        "default": "none",
        "normalchat": "none",
        "Websearch": "low",
        "ITSecurty_Websearch": "medium",
        "email": "none",
        "codex": "low",
        "translate": "none",
    },
    "securityNewsPromt": (
        "Research the following topics:"
        "Exchange OnPrem Zero Day etc"
        "Windows 11 from 23H2"
        "Office 365"
        "EntraID, Intune, Teams, Sharepoint"
        "Always security"
    ),
    "security_domains": [
        "msrc.microsoft.com",
        "learn.microsoft.com",
        "support.microsoft.com",
        "techcommunity.microsoft.com",
        "cloudblogs.microsoft.com",
        # CVE / Scoring / Known Exploited
        "nvd.nist.gov",
        "cisa.gov",
        # Sekundär / News / Analysen
        "bleepingcomputer.com",
        "qualys.com",
        "threatprotect.qualys.com",
    ],
}


# Ensure instruction files exist on import
save_default_instructions()


if not config_file.exists():
    with open(config_file, "w") as f:
        json.dump(config_default, f, indent=4)


def loadconfig():
    """
    Load configuration from JSON file and instructions from text files.
    Automatically applies language prefix to all instructions.

    Returns:
        dict: Configuration with instructions loaded from files
    """
    with open(config_file, "r") as f:
        config = json.load(f)

    # Get language setting (default to "en" if not set)
    language = config.get("language", "en")

    # Load instructions from separate files (backwards compatible)
    if "instructions" not in config:
        config["instructions"] = {}

    # Load instructions from separate files with language prefix
    config["instructions"]["normalchat"] = load_instruction("normalchat.txt", language)
    config["instructions"]["Websearch"] = load_instruction("websearch.txt", language)
    config["instructions"]["ITSecurityNews"] = load_instruction("itsecuritynews.txt", language)
    config["instructions"]["email"] = load_instruction("email.txt", language)
    config["instructions"]["translate"] = load_instruction("translate.txt", language)
    config["instructions"]["codex"] = load_instruction("codex.txt", language)

    return config


def init_config():
    """Reset configuration file to defaults and ensure instruction files exist."""
    with open(config_file, "w") as f:
        json.dump(config_default, f, indent=4)
    save_default_instructions()



