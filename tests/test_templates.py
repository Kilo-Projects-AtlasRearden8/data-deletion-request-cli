"""Tests for template rendering in data-deletion-request-cli."""

import pytest

from data_deletion_cli.cli import render_letter

BASE_DATA = dict(
    regulation="gdpr",
    letter_type="deletion",
    name="Ada Lovelace",
    email="ada@example.test",
    address="123 Example Lane, London",
    company="Example Corp",
    date="2026-01-15",
)


def test_gdpr_deletion_contains_key_fields():
    letter = render_letter(**BASE_DATA)
    for needle in ("Ada Lovelace", "ada@example.test", "123 Example Lane",
                   "Example Corp", "2026-01-15", "erasure", "Article 17"):
        assert needle in letter


def test_ccpa_deletion_renders():
    data = dict(BASE_DATA, regulation="ccpa")
    letter = render_letter(**data)
    assert "California Consumer Privacy Act" in letter
    assert "deletion" in letter.lower()
    assert "sale" not in letter.lower()


def test_ccpa_opt_out_renders():
    data = dict(BASE_DATA, regulation="ccpa", letter_type="opt-out")
    letter = render_letter(**data)
    assert "opt out" in letter.lower()
    assert "sale and sharing" in letter.lower()
    assert "targeted advertising" in letter.lower()


def test_empty_address_omits_address_line():
    data = dict(BASE_DATA, address="")
    letter = render_letter(**data)
    assert "My address is" not in letter


def test_gdpr_rejects_opt_out(monkeypatch):
    # opt-out is CCPA-only; render itself should not crash but produce generic
    # fallback body. This guards the template macro fallback branch.
    data = dict(BASE_DATA, regulation="gdpr", letter_type="opt-out")
    letter = render_letter(**data)
    assert "applicable data protection law" in letter


def test_letter_ends_with_signature():
    letter = render_letter(**BASE_DATA)
    assert letter.rstrip().endswith("Ada Lovelace")
