"""#95375 on a reflowing terminal: resizing the classic CLI leaves every transcript line in
tmux's scrollback + screen exactly once, with no stray blank or prompt rows.

A real ``reign chat --cli`` runs in a private tmux server against the scripted fake provider.
One session goes through a resize storm while a reply streams, a shrink while idle, and a
two-step shrink while the next reply streams; ``capture-pane -J`` then joins tmux's re-wrapped
rows back into lines. Reply lines are 146 columns, so each one wraps at every width here, and
the two-step shrink lands as a line is committed — when the chrome may reach tmux before or
after it narrows. Mocked-renderer unit tests cannot see this: what lands in scrollback is
decided by how the terminal re-wraps the rows prompt_toolkit already wrote.
"""

from __future__ import annotations

import base64
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
import uuid
import zlib
from collections import Counter
from pathlib import Path

import pytest

from tests.fakes.fake_llm_provider import FakeLLMServer, Text, write_reign_home

pytestmark = pytest.mark.skipif(shutil.which("tmux") is None, reason="needs tmux")

REPO_ROOT = Path(__file__).resolve().parents[4]
WORDS = {1: 60, 2: 260, 3: 130}
# pipe-pane target: every byte the CLI wrote to the pane, stamped with the system-wide monotonic clock.
RECORDER = ("import base64, os, sys, time\n"
            "while chunk := os.read(0, 65536):\n"
            "    sys.stdout.write(f'{time.monotonic():.6f} {base64.b64encode(chunk).decode()}\\n'); sys.stdout.flush()\n")


def _reply(turn: int) -> str:
    words = [f"t{turn}w{i:03d}" for i in range(WORDS[turn])]
    return "\n".join(" ".join(words[j:j + 21]) for j in range(0, len(words), 21))


def test_resizes_keep_each_transcript_line_once_in_tmux_scrollback(tmp_path: Path) -> None:
    sock = f"reign-e2e-{uuid.uuid4().hex[:8]}"
    tmux_version = subprocess.run(["tmux", "-V"], capture_output=True, text=True, timeout=30).stdout.strip()
    home = tmp_path / "home"
    (tmp_path / "work").mkdir()

    def tmux(*args: str) -> str:
        return subprocess.run(["tmux", "-L", sock, *args], capture_output=True, text=True, timeout=30).stdout

    def transcript() -> str:
        return tmux("capture-pane", "-p", "-J", "-t", "p", "-S", "-", "-E", "-")

    def wait_for(needle: str, timeout: float = 60.0) -> None:
        end = time.monotonic() + timeout
        while needle not in transcript():
            assert time.monotonic() < end, f"{needle!r} never appeared:\n{transcript()[-3000:]}"
            time.sleep(0.1)

    resizes: list[tuple[float, int]] = []

    def resize(cols: int) -> None:
        resizes.append((time.monotonic(), cols))
        tmux("resize-window", "-t", "p", "-x", str(cols), "-y", "24")

    def report(text: str) -> str:
        """*text* plus what a replay needs: the CLI's output stream and the resizes, timed alike."""
        raw = (tmp_path / "pane.raw").read_text() if (tmp_path / "pane.raw").exists() else ""
        blob = json.dumps({"tmux": tmux_version, "resizes": resizes, "output": raw}).encode()
        return f"{text}\n--- replay ({tmux_version}): zlib+base64 JSON ---\n" + base64.b64encode(
            zlib.compress(blob, 9)).decode()

    def ask(turn: int) -> None:
        tmux("send-keys", "-t", "p", "-l", f"question zq{turn}q please")
        # An Enter read within 50 ms of the last text change is a pasted newline, not a submit. On
        # a busy runner the UI loop can stall long enough to read text and Enter as one batch, so
        # wait until the text has been processed (drawn), then leave a real gap.
        wait_for(f"zq{turn}q please")
        time.sleep(0.5)
        tmux("send-keys", "-t", "p", "Enter")

    def reply_done(turn: int) -> None:
        wait_for(f"t{turn}w{WORDS[turn] - 1:03d}")
        time.sleep(2.0)

    script = [Text(_reply(t), chunk_chars=10, delay_per_chunk=0.03) for t in WORDS]
    with FakeLLMServer(script, aux=lambda _r: Text("Scripted session title")) as llm:
        write_reign_home(home / ".reign", llm.base_url)
        env = {k: v for k, v in os.environ.items() if not k.startswith(("REIGN_", "TMUX"))}
        env.update(HOME=str(home), REIGN_HOME=str(home / ".reign"), PYTHONPATH=str(REPO_ROOT),
                   TERM="xterm-256color")
        argv = [sys.executable, "-m", "reign_cli.main", "chat", "--cli", "--yolo"]
        subprocess.run(["tmux", "-L", sock, "-f", os.devnull, "new-session", "-d", "-s", "p", "-x", "120",
                        "-y", "24", "-c", str(tmp_path / "work"), *argv], env=env, check=True, timeout=30)
        try:
            tmux("set", "-g", "window-size", "manual")
            tmux("pipe-pane", "-o", "-t", "p",
                 f"{sys.executable} -c {shlex.quote(RECORDER)} > {shlex.quote(str(tmp_path / 'pane.raw'))}")
            wait_for("Welcome to Reign", timeout=120)
            time.sleep(2.0)

            ask(1)
            reply_done(1)
            ask(2)
            wait_for("t2w040")
            for cols in (110, 95, 80, 70, 90, 85, 100):  # a drag: 7 resizes in 0.35 s
                resize(cols)
                time.sleep(0.05)
            reply_done(2)
            resize(80)  # idle shrink
            time.sleep(1.5)
            ask(3)
            wait_for("t3w020")  # the end of the first line: its commit repaints the chrome
            resize(70)  # two-step shrink mid-stream
            time.sleep(0.8)
            resize(60)
            reply_done(3)
            final = transcript()
        finally:
            tmux("kill-server")

    # A streaming-preview row painted as tmux narrowed may have been re-wrapped or clipped: it is
    # left rather than erased (a stale chrome row is benign, an erased transcript row is lost) —
    # at most one per mid-stream recovery: the drag's and each step's (#95375).
    lines = final.split("\n")
    stale_preview = [line for line in lines if line.lstrip().startswith("\u2026")]
    assert len(stale_preview) <= 3, report(final)
    words = Counter(re.findall(r"\bt\dw\d{3}\b", "\n".join(ln for ln in lines if ln not in stale_preview)))
    expected = {f"t{t}w{i:03d}" for t, n in WORDS.items() for i in range(n)}
    assert sorted(w for w in expected if words[w] != 1) == [], report(final)
    assert [final.count(f"zq{t}q") for t in WORDS] == [1, 1, 1], report(final)
    assert sum(1 for line in final.split("\n") if line.lstrip().startswith("❯")) == 1, report(final)
    blank_runs = [len(run) for run in re.findall(r"(?:^[ \t]*\n)+", final, flags=re.M)]
    assert max(blank_runs, default=0) <= 2, report(final)  # the reply panel's own spacing, nothing more
