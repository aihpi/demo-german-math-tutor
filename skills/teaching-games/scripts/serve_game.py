#!/usr/bin/env python3
"""Serve the directory holding a generated game over localhost.

    serve_game.py                      # serves /tmp, prints http://127.0.0.1:8080/game.html
    serve_game.py --file /tmp/game.html --port 8080

Idempotent: if something is already listening on the port, this assumes it is a
previous instance of this server and just prints the URL. Pass --restart to kill
whatever holds the port and take it over.
"""
import argparse, http.server, functools, os, pathlib, signal, socket, subprocess, sys, threading


def port_busy(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.4)
        return s.connect_ex(("127.0.0.1", port)) == 0


def free_port(port: int) -> None:
    """Kill whatever is listening. Only reachable via --restart."""
    try:
        pids = subprocess.run(["lsof", "-ti", f"tcp:{port}"], capture_output=True, text=True).stdout.split()
    except FileNotFoundError:
        print("lsof not available; cannot free the port automatically", file=sys.stderr)
        return
    for pid in pids:
        os.kill(int(pid), signal.SIGTERM)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--file", default="/tmp/game.html", help="the generated game to link to")
    p.add_argument("--port", type=int, default=8080)
    p.add_argument("--restart", action="store_true", help="kill an existing listener and take the port")
    p.add_argument("--foreground", action="store_true", help="block instead of detaching into a daemon thread")
    a = p.parse_args()

    game = pathlib.Path(a.file).resolve()
    if not game.exists():
        print(f"{game} does not exist — run generate_game.py first", file=sys.stderr)
        return 2

    url = f"http://127.0.0.1:{a.port}/{game.name}"
    if port_busy(a.port):
        if not a.restart:
            # Re-serving the same directory, so an existing server already works.
            print(url)
            return 0
        free_port(a.port)

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(game.parent))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", a.port), handler)
    print(url, flush=True)
    if a.foreground:
        httpd.serve_forever()
    else:
        threading.Thread(target=httpd.serve_forever, daemon=False).start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
