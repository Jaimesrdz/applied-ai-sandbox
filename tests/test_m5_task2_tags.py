"""Edge-case tests for M5 Task 2 — VALID_TAGS enforcement.

VALID_TAGS = {"personal", "work", "urgent"}
Only a tag in that set should be stored on the note; everything else
(unrecognised strings, wrong case, empty, whitespace-only, missing field)
must result in an empty tags list. The /notes/new page must also render
the dropdown with all three options.
"""
import pytest
from app import VALID_TAGS


def _post_note(client, title="Test Note", body="Test body", tag=None):
    data = {"title": title, "body": body}
    if tag is not None:
        data["tag"] = tag
    return client.post("/notes/new", data=data)


# ---------------------------------------------------------------------------
# Valid tags
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("tag", sorted(VALID_TAGS))
def test_valid_tag_is_stored(client, app, tag):
    app.notes.clear()
    _post_note(client, tag=tag)
    assert app.notes[-1]["tags"] == [tag]


@pytest.mark.parametrize("tag", sorted(VALID_TAGS))
def test_valid_tag_submission_redirects(client, app, tag):
    app.notes.clear()
    r = _post_note(client, tag=tag)
    assert r.status_code in (302, 303)


# ---------------------------------------------------------------------------
# Invalid / rejected tags
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_tag", [
    "spam",
    "random",
    "PERSONAL",
    "WORK",
    "URGENT",
    "Personal",
    "Work",
    "Urgent",
])
def test_invalid_tag_is_rejected(client, app, bad_tag):
    app.notes.clear()
    _post_note(client, tag=bad_tag)
    assert app.notes[-1]["tags"] == []


def test_empty_string_tag_is_rejected(client, app):
    app.notes.clear()
    _post_note(client, tag="")
    assert app.notes[-1]["tags"] == []


def test_whitespace_only_tag_is_rejected(client, app):
    app.notes.clear()
    _post_note(client, tag="   ")
    assert app.notes[-1]["tags"] == []


# ---------------------------------------------------------------------------
# Missing tag field
# ---------------------------------------------------------------------------

def test_no_tag_field_results_in_empty_tags(client, app):
    app.notes.clear()
    _post_note(client, tag=None)
    assert app.notes[-1]["tags"] == []


# ---------------------------------------------------------------------------
# Data shape guarantees
# ---------------------------------------------------------------------------

def test_tags_key_always_present_in_note(client, app):
    app.notes.clear()
    _post_note(client)
    assert "tags" in app.notes[-1]


def test_tags_value_is_a_list(client, app):
    app.notes.clear()
    _post_note(client, tag="work")
    assert isinstance(app.notes[-1]["tags"], list)


# ---------------------------------------------------------------------------
# Stripping behaviour
# ---------------------------------------------------------------------------

def test_tag_with_surrounding_whitespace_is_accepted(client, app):
    app.notes.clear()
    _post_note(client, tag=" personal ")
    assert app.notes[-1]["tags"] == ["personal"]


# ---------------------------------------------------------------------------
# Note integrity — invalid tag must not block creation
# ---------------------------------------------------------------------------

def test_invalid_tag_still_creates_note(client, app):
    app.notes.clear()
    r = _post_note(client, tag="spam")
    assert r.status_code in (302, 303)
    assert len(app.notes) == 1
    assert app.notes[0]["tags"] == []


# ---------------------------------------------------------------------------
# Dropdown HTML
# ---------------------------------------------------------------------------

def test_new_note_page_renders_tag_dropdown(client):
    r = client.get("/notes/new")
    body = r.data.decode()
    assert '<select' in body
    assert 'name="tag"' in body


@pytest.mark.parametrize("tag", sorted(VALID_TAGS))
def test_dropdown_contains_all_valid_options(client, tag):
    r = client.get("/notes/new")
    body = r.data.decode()
    assert f'value="{tag}"' in body
