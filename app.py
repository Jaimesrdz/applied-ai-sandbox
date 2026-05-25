"""Tiny Flask app — applied-ai-sandbox.

Each task in tasks/ asks you to add or fix one piece. The tests in tests/
describe exactly what "done" means.
"""
from __future__ import annotations

from flask import Flask, render_template, request, redirect, url_for, flash
from markupsafe import Markup, escape


def _make_highlight(text: str, query: str) -> Markup:
    """Escape text, then wrap case-insensitive query matches in <mark>."""
    escaped_text = str(escape(text))
    escaped_query = str(escape(query))
    result, i = [], 0
    lower_text = escaped_text.lower()
    lower_query = escaped_query.lower()
    qlen = len(lower_query)
    while i < len(escaped_text):
        pos = lower_text.find(lower_query, i)
        if pos == -1:
            result.append(escaped_text[i:])
            break
        result.append(escaped_text[i:pos])
        result.append(f"<mark>{escaped_text[pos:pos+qlen]}</mark>")
        i = pos + qlen
    return Markup("".join(result))


def _make_snippet(body: str, query: str, max_len: int = 150) -> str:
    """Return a short excerpt of body centered on the first match."""
    if not body:
        return ""
    trimmed = body[:10000]
    pos = trimmed.lower().find(query.lower())
    if pos == -1:
        return body[:max_len]
    half = max_len // 2
    start = max(0, pos - half)
    end = min(len(trimmed), pos + len(query) + half)
    snippet = trimmed[start:end]
    if start > 0:
        snippet = "…" + snippet
    if end < len(trimmed):
        snippet = snippet + "…"
    return snippet


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "sandbox-not-a-real-secret"

    # In-memory store for the sandbox. Resets on every restart, which is
    # fine for practice. Real apps use a database.
    app.notes: list[dict] = []  # type: ignore[attr-defined]

    @app.route("/")
    def home():
        return render_template("home.html", notes=app.notes)

    @app.route("/notes/new", methods=["GET", "POST"])
    def new_note():
        if request.method == "POST":
            title = (request.form.get("title") or "").strip()
            body = (request.form.get("body") or "").strip()
            # TASK 01 will add validation here.
            app.notes.append({"title": title, "body": body})
            return redirect(url_for("home"))
        return render_template("new_note.html")

    # TASK 02 will add a /notes/<idx>/delete route here.

    @app.route("/search")
    def search():
        q = request.args.get("q", "").strip()
        if not q:
            flash("Enter something to search.")
            return redirect(url_for("home"))

        truncated = False
        if len(q) > 200:
            q = q[:200]
            truncated = True

        q_lower = q.lower()
        title_matches, body_matches = [], []

        for note in app.notes:  # single-threaded dev server; concurrent writes not a concern
            title = note.get("title") or ""
            body = note.get("body") or ""
            in_title = q_lower in title.lower()
            in_body = q_lower in body[:10000].lower()
            if not (in_title or in_body):
                continue
            snippet = _make_snippet(body, q)
            result = {
                "title": title or "Untitled",
                "highlighted_title": _make_highlight(title or "Untitled", q),
                "highlighted_snippet": _make_highlight(snippet, q) if snippet else None,
                "in_title": in_title,
                "in_body": in_body,
            }
            (title_matches if in_title else body_matches).append(result)

        return render_template(
            "search_results.html",
            query=q,
            results=title_matches + body_matches,
            truncated=truncated,
        )

    return app


if __name__ == "__main__":
    create_app().run(debug=True, port=5000)
