"""Small terminal chat client for the running Cartwheel HTTP server.

Run from the repository root: uv run python -m scripts.chat
"""

import json
import os
import shutil
import sys
import textwrap
import urllib.error
import urllib.request


BASE_URL = "http://localhost:8010"
ROLES = {"1": "shopper", "2": "merchant", "3": "support"}


def color(text: str, code: str) -> str:
    if not sys.stdout.isatty() or os.getenv("NO_COLOR"):
        return text
    return f"\033[{code}m{text}\033[0m"


def panel(title: str, body: str, tone: str = "36") -> None:
    width = max(24, min(76, shutil.get_terminal_size((80, 24)).columns - 2))
    line = "─" * (width - 2)
    print(color(f"╭{line}╮", tone))
    print(color("│", tone) + f" {title}".ljust(width - 2) + color("│", tone))
    print(color(f"├{line}┤", tone))
    for paragraph in body.splitlines():
        for part in textwrap.wrap(paragraph, width=width - 4) or [""]:
            print(color("│", tone) + f" {part}".ljust(width - 2) + color("│", tone))
    print(color(f"╰{line}╯", tone))


def post(path: str, body: dict, token: str | None = None) -> dict:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(body).encode(),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        try:
            detail = json.load(exc).get("detail", exc.reason)
        except (ValueError, AttributeError):
            detail = exc.reason
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Cannot reach Cartwheel at {BASE_URL}: {exc.reason}") from exc


def main() -> None:
    panel("CARTWHEEL  /  terminal chat", "Type /signout to switch users or /quit to exit.")
    while True:
        print("\n" + color("CHOOSE A ROLE", "1;36"))
        print("  1  Shopper    2  Merchant    3  Support")
        choice = input(color("Role › ", "1;36")).strip().lower()
        if choice == "/quit":
            return
        role = ROLES.get(choice, choice)
        if role not in ROLES.values():
            print(color("Choose 1, 2, 3, or type a role name.", "33"))
            continue

        user_id = input(color("User ID › ", "1;36")).strip()
        if user_id == "/quit":
            return
        if not user_id.isdecimal():
            print(color("Enter a numeric user ID.", "33"))
            continue

        try:
            session = post("/sessions", {"user_id": int(user_id), "role": role})
            session_id, token = session["session_id"], session["token"]
        except (RuntimeError, KeyError, ValueError) as exc:
            print(color(f"Could not sign in: {exc}", "31"))
            continue

        print()
        panel("CONNECTED", f"{role.title()} #{user_id}\nSession {session_id}", "32")
        print(color("Type a message to start chatting.\n", "2"))
        while True:
            message = input(color("you › ", "1;34")).strip()
            if message == "/quit":
                return
            if message == "/signout":
                print(color("Signed out locally. Choose another user.", "33"))
                break
            if not message:
                continue
            try:
                print(color("Cartwheel is thinking…", "2"))
                result = post(
                    f"/sessions/{session_id}/messages", {"message": message}, token
                )
                print()
                panel("CARTWHEEL", result["reply"])
                print()
            except (RuntimeError, KeyError, ValueError) as exc:
                print(color(f"Message failed: {exc}\n", "31"))


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print()
