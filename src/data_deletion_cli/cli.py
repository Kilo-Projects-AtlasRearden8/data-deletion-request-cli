"""Draft GDPR/CCPA data-deletion and opt-out letters locally from templates.

Prints only; never sends automatically. Optional LLM polishing via a
configurable OpenAI-compatible endpoint (default Ollama).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import sys
from email.utils import formatdate
from typing import Optional

import httpx
from jinja2 import Environment, PackageLoader, select_autoescape

# Default OpenAI-compatible chat endpoint (Ollama).
DEFAULT_LLM_ENDPOINT = "http://localhost:11434/v1/chat/completions"
DEFAULT_LLM_MODEL = "llama3.2"

REGULATIONS = ("gdpr", "ccpa")
LETTER_TYPES = ("deletion", "opt-out")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="data-deletion-request",
        description=(
            "Draft GDPR/CCPA data-deletion and opt-out letters locally from "
            "templates. Prints to stdout; never sends automatically."
        ),
    )
    parser.add_argument(
        "--regulation",
        choices=REGULATIONS,
        required=True,
        help="Data-protection regulation: gdpr or ccpa.",
    )
    parser.add_argument(
        "--type",
        dest="letter_type",
        choices=LETTER_TYPES,
        required=True,
        help="Letter type: deletion or opt-out.",
    )
    parser.add_argument("--name", required=True, help="Requester name.")
    parser.add_argument("--email", required=True, help="Requester contact email.")
    parser.add_argument("--address", default="", help="Requester postal address (optional).")
    parser.add_argument("--company", required=True, help="Organization receiving the letter.")
    parser.add_argument(
        "--date",
        default=None,
        help="Letter date (ISO YYYY-MM-DD). Defaults to today.",
    )
    parser.add_argument(
        "--polish",
        action="store_true",
        help="Optionally polish the drafted letter with an LLM.",
    )
    parser.add_argument(
        "--llm-endpoint",
        default=DEFAULT_LLM_ENDPOINT,
        help="OpenAI-compatible chat completions endpoint URL.",
    )
    parser.add_argument(
        "--llm-model",
        default=DEFAULT_LLM_MODEL,
        help="LLM model name used for polishing.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Write the letter to this file instead of stdout.",
    )
    return parser


def render_letter(
    *,
    regulation: str,
    letter_type: str,
    name: str,
    email: str,
    address: str,
    company: str,
    date: Optional[str] = None,
) -> str:
    """Render a letter from the Jinja2 template."""
    env = Environment(
        loader=PackageLoader("data_deletion_cli", "templates"),
        autoescape=select_autoescape(enabled_extensions=()),
        keep_trailing_newline=True,
    )
    template = env.get_template("base.j2")
    letter_date = date or _dt.date.today().isoformat()
    return template.render(
        regulation=regulation,
        letter_type=letter_type,
        name=name,
        email=email,
        address=address,
        company=company,
        date=letter_date,
    )


def polish_letter(
    letter: str,
    *,
    endpoint: str,
    model: str,
    timeout: float = 30.0,
) -> str:
    """Optionally polish the letter via an OpenAI-compatible chat endpoint.

    Best-effort: on any failure the original letter is returned unchanged and a
    warning is written to stderr.
    """
    system_prompt = (
        "You are a careful assistant that polishes formal data-deletion and "
        "opt-out letters. Preserve all facts, names, dates, addresses, and legal "
        "references exactly. Improve only clarity, tone, and grammar. Do not add "
        "new claims or personal data. Return only the polished letter, no extra "
        "commentary."
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": letter},
        ],
        "temperature": 0.2,
    }
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(endpoint, json=payload)
            response.raise_for_status()
            data = response.json()
        choices = data.get("choices") or []
        if not choices:
            raise ValueError("no choices returned")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if content:
            return content.strip()
    except Exception as exc:  # noqa: BLE001 - best-effort polish
        print(f"[warning] LLM polishing skipped: {exc}", file=sys.stderr)
    return letter


def write_output(letter: str, output: Optional[str]) -> None:
    if output:
        with open(output, "w", encoding="utf-8") as handle:
            handle.write(letter)
            if not letter.endswith("\n"):
                handle.write("\n")
    else:
        sys.stdout.write(letter)
        if not letter.endswith("\n"):
            sys.stdout.write("\n")


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Validate regulation/type combinations.
    if args.regulation == "gdpr" and args.letter_type == "opt-out":
        parser.error("--type opt-out is only valid with --regulation ccpa")

    letter = render_letter(
        regulation=args.regulation,
        letter_type=args.letter_type,
        name=args.name,
        email=args.email,
        address=args.address,
        company=args.company,
        date=args.date,
    )

    if args.polish:
        letter = polish_letter(
            letter,
            endpoint=args.llm_endpoint,
            model=args.llm_model,
        )

    write_output(letter, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
