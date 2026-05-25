"""Acceptance tests for the note search feature (GET /search)."""


def _seed(app, notes):
    app.notes.clear()
    app.notes.extend(notes)


def test_search_returns_title_match(client, app):
    _seed(app, [{"title": "Flask Tips", "body": "Some content"}])
    r = client.get("/search?q=Flask")
    assert r.status_code == 200
    # "Flask" is wrapped in <mark>; check the non-highlighted suffix still appears
    assert b"Tips" in r.data


def test_search_returns_body_match(client, app):
    _seed(app, [{"title": "My Note", "body": "This is about Python"}])
    r = client.get("/search?q=Python")
    assert r.status_code == 200
    assert b"My Note" in r.data


def test_search_case_insensitive(client, app):
    _seed(app, [{"title": "flask tutorial", "body": "intro content"}])
    r = client.get("/search?q=FLASK")
    assert r.status_code == 200
    # "flask" is wrapped in <mark>; check the non-highlighted suffix still appears
    assert b"tutorial" in r.data


def test_search_empty_query_redirects(client, app):
    r = client.get("/search?q=", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["Location"].endswith("/")


def test_search_empty_query_flash_message(client, app):
    r = client.get("/search?q=", follow_redirects=True)
    assert b"Enter something to search" in r.data


def test_search_whitespace_only_redirects(client, app):
    r = client.get("/search?q=   ", follow_redirects=False)
    assert r.status_code == 302


def test_search_long_query_truncated(client, app):
    _seed(app, [])
    long_q = "a" * 201
    r = client.get(f"/search?q={long_q}")
    assert r.status_code == 200
    assert b"trimmed" in r.data


def test_search_no_results_empty_state(client, app):
    _seed(app, [{"title": "Unrelated", "body": "Nothing here"}])
    r = client.get("/search?q=zzznomatch")
    assert r.status_code == 200
    assert b"Nothing matched" in r.data


def test_search_xss_query_escaped(client, app):
    _seed(app, [])
    r = client.get("/search?q=<script>alert(1)</script>")
    assert r.status_code == 200
    assert b"<script>" not in r.data
    assert b"&lt;script&gt;" in r.data


def test_search_title_match_before_body_match(client, app):
    _seed(app, [
        {"title": "Regular Note", "body": "contains the word needle here"},
        {"title": "needle in title", "body": "unrelated body"},
    ])
    r = client.get("/search?q=needle")
    html = r.data.decode()
    # "needle" is wrapped in <mark> in the title; look for the unhighlighted suffix
    title_pos = html.index("in title")
    body_pos = html.index("Regular Note")
    assert title_pos < body_pos


def test_search_no_notes_store(client, app):
    app.notes.clear()
    r = client.get("/search?q=anything")
    assert r.status_code == 200
    assert b"Nothing matched" in r.data


def test_search_note_with_empty_body(client, app):
    _seed(app, [{"title": "Empty Body Note", "body": ""}])
    r = client.get("/search?q=Empty")
    assert r.status_code == 200
    # "Empty" is wrapped in <mark>; check the non-highlighted suffix still appears
    assert b"Body Note" in r.data


def test_search_result_has_mark_tag(client, app):
    _seed(app, [{"title": "Hello World", "body": "Some text"}])
    r = client.get("/search?q=Hello")
    assert r.status_code == 200
    assert b"<mark>Hello</mark>" in r.data
