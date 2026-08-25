#!/usr/bin/env python3
"""Publish a generated game on loopback http, and hand back its URL.

    serve_game.py --file /tmp/game.html          # -> http://127.0.0.1:8732/<hash>.html

Also importable:  from serve_game import publish; url = publish(html_text)

Why http and not a file:// path or a data: URI — the desktop app's renderer
rejects data: URIs and its hermes-media:// scheme carries audio/video only, so a
loopback origin is the only way anything renders inline. Same conclusion the
math-tutor skill reached for its SVG figures; this is that mechanism with the
port moved so the two skills never fight over it.
"""
import argparse, hashlib, pathlib, socket, subprocess, sys, tempfile, time, urllib.parse

PORT = 8732                                                    # math-tutor holds 8731
DIR = pathlib.Path(tempfile.gettempdir()) / "teaching-agent"


def serving() -> bool:
    with socket.socket() as sock:
        sock.settimeout(0.3)
        return sock.connect_ex(("127.0.0.1", PORT)) == 0


def ensure_server() -> None:
    """Start the static server if it isn't already up, detached from this process.

    start_new_session keeps it alive after the calling shell exits — the agent's
    terminal tool must be able to return, so this can never block or be a child
    that dies with the command.
    """
    if serving():
        return
    DIR.mkdir(exist_ok=True)
    # ponytail: stdlib http.server, single-threaded. It serves one HTML file per
    # round to one localhost viewer; swap it if that ever stops being true.
    subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT),
         "--bind", "127.0.0.1", "--directory", str(DIR)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    for _ in range(40):                                        # ~4s, plenty for a local bind
        if serving():
            return
        time.sleep(0.1)
    raise RuntimeError(f"could not bring up the game server on port {PORT}")


def publish(html: str) -> str:
    """Write the page under a content-hashed name and return its URL.

    Hashing the content means "make it harder" always produces a NEW url, so the
    preview rail can never show a cached copy of the previous round.
    """
    DIR.mkdir(exist_ok=True)
    name = f"{hashlib.sha1(html.encode()).hexdigest()[:12]}.html"
    (DIR / name).write_text(html)
    ensure_server()
    return f"http://127.0.0.1:{PORT}/{name}"


def preview_marker(url: str) -> str:
    """Two lines: the desktop preview card, then a link that always shows.

    Line 1 is the only form the desktop app turns into a preview: it renders a
    card with an "Open preview" button, and an http(s) target resolves to
    kind:'url', which is a live web view — the page's JavaScript runs.

    Line 2 exists because line 1 is *removed* from the visible message by
    stripPreviewTargets(). On any surface without the rail — the CLI, the TUI,
    Telegram — line 1 alone leaves the user staring at nothing. A markdown link
    survives: the local-URL stripper only eats URLs preceded by whitespace or
    start-of-string, and here the URL sits behind a "(".
    """
    # Must match JS encodeURIComponent, which leaves -_.!~*'() unescaped.
    encoded = urllib.parse.quote(url, safe="-_.!~*'()")
    name = url.rsplit("/", 1)[-1]
    return f"[Preview: {name}](#preview/{encoded})\n[Open in a browser instead]({url})"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--file", default="/tmp/game.html", help="the generated game to publish")
    p.add_argument("--url-only", action="store_true", help="print the bare URL instead of the preview marker")
    a = p.parse_args()
    src = pathlib.Path(a.file)
    if not src.exists():
        print(f"{src} does not exist — run generate_game.py first", file=sys.stderr)
        return 2
    url = publish(src.read_text())
    print(url if a.url_only else preview_marker(url))
    return 0


if __name__ == "__main__":
    sys.exit(main())
