"""data-deletion-request-cli: draft GDPR/CCPA letters locally."""

from .cli import main, build_parser, render_letter, polish_letter

__all__ = ["main", "build_parser", "render_letter", "polish_letter"]
__version__ = "0.1.0"
