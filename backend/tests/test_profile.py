from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from jarvis.agent.prompts import render_profile_section
from jarvis.core.profile import FileProfileStore, Profile


def test_blank_profile_is_empty() -> None:
    assert Profile().is_empty is True
    assert Profile(preferred_name="  ").is_empty is True
    assert Profile(preferred_name="Kenny").is_empty is False


def test_profile_rejects_overlong_about() -> None:
    with pytest.raises(ValidationError):
        Profile(about="x" * 4001)


def test_file_store_round_trip(tmp_path: Path) -> None:
    store = FileProfileStore(tmp_path)
    saved = Profile(preferred_name="Kenny", location="New York", about="Builds assistants.")
    store.save("local", saved)
    loaded = store.load("local")
    assert loaded.preferred_name == "Kenny"
    assert loaded.location == "New York"
    assert loaded.about == "Builds assistants."


def test_missing_profile_is_empty_not_an_error(tmp_path: Path) -> None:
    assert FileProfileStore(tmp_path).load("local").is_empty is True


def test_corrupt_profile_falls_back_to_empty(tmp_path: Path) -> None:
    path = tmp_path / "local.json"
    path.write_text("{not json")
    assert FileProfileStore(tmp_path).load("local").is_empty is True


def test_empty_profile_adds_nothing_to_the_prompt() -> None:
    assert render_profile_section(Profile()) == ""


def test_filled_profile_is_appended_as_a_named_section() -> None:
    fragment = render_profile_section(
        Profile(
            preferred_name="Kenny",
            occupation="Engineer",
            location="New York",
            about="Works on Jarvis.",
            preferences="Be terse.",
        )
    )
    assert fragment.startswith("\n# About him\n")
    assert "He goes by Kenny." in fragment
    assert "Work: Engineer" in fragment
    assert "Based in New York." in fragment
    assert "Works on Jarvis." in fragment
    assert "Be terse." in fragment
    assert "Do not recite it back" in fragment
