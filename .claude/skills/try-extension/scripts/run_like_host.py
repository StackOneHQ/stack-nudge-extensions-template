#!/usr/bin/env python3
"""Runs an extension the way stack-nudge does and checks what it prints.

    python3 run_like_host.py extensions/<id> [--action ID [--row ID]]
                             [--set KEY=VALUE ...] [--from-config]

The environment is the host's: a minimal PATH, HOME, STACKNUDGE_EXT_ID,
STACKNUDGE_EXT_SCHEMA and only the declared STACKNUDGE_EXT_* keys that have a
value (from --set, or ~/.stack-nudge/config with --from-config). The working
directory is the extension's, the run is killed at 12 s and stdout is read up
to 8 MB. Then the document is checked against the rules in
references/extension-spec.md of the new-extension skill.

Exits 0 when the run would be shown as intended, 1 when it wouldn't. Service
extensions (schema 2, mode service) are long-running and aren't run here.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time

HOST_PATH = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
DOCUMENT_SCHEMA = "1"
TIMEOUT_SECONDS = 12
MAX_STDOUT = 8 * 1024 * 1024
MAX_ROWS = 500
MAX_ACTIONS = 16
MAX_TEXT = 256
KEY_PATTERN = re.compile(r"^STACKNUDGE_EXT_[A-Z0-9_]+$")
TINT_PATTERN = re.compile(r"^#(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$")
ACTION_KEY_PATTERN = re.compile(r"^(?:[A-Za-z0-9]|return)$")
TONES = {"neutral", "success", "warning", "danger"}
STATES = {"ok", "empty", "error"}
ANCHORS = {"fill-edge", "leading", "trailing"}


def declared_keys(manifest):
    keys = []
    for entry in manifest.get("config") or []:
        key = entry.get("key") if isinstance(entry, dict) else entry
        if isinstance(key, str):
            keys.append(key)
    return keys


def read_config(path):
    values = {}
    try:
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip().strip('"').strip("'")
    except OSError:
        pass
    return values


def host_environment(manifest, values):
    environment = {
        "PATH": HOST_PATH,
        "HOME": os.path.expanduser("~"),
        "STACKNUDGE_EXT_ID": manifest.get("id", ""),
        "STACKNUDGE_EXT_SCHEMA": DOCUMENT_SCHEMA,
    }
    for key in declared_keys(manifest):
        if KEY_PATTERN.match(key) and values.get(key):
            environment[key] = values[key]
    return environment


def text_problems(where, value):
    if isinstance(value, str) and len(value) > MAX_TEXT:
        return ["%s is %d characters; the host cuts it at %d" % (where, len(value), MAX_TEXT)]
    return []


def action_problems(where, actions):
    problems = []
    if not isinstance(actions, list):
        return ["%s isn't a list" % where]
    if len(actions) > MAX_ACTIONS:
        problems.append("%s has %d actions; only the first %d are kept" % (where, len(actions), MAX_ACTIONS))
    for index, action in enumerate(actions):
        label = "%s[%d]" % (where, index)
        if not isinstance(action, dict) or not isinstance(action.get("id"), str):
            problems.append("%s has no id" % label)
            continue
        key = action.get("key")
        if not isinstance(key, str) or not ACTION_KEY_PATTERN.match(key):
            problems.append("%s (%s) has no usable key, so nothing can trigger it: one letter or digit, "
                            "or \"return\"" % (label, action["id"]))
    return problems


def ornament_problems(where, ornament):
    problems = []
    if not isinstance(ornament, dict):
        return ["%s isn't an object" % where]
    if ornament.get("kind") != "sprite":
        problems.append("%s kind isn't \"sprite\", so it's dropped" % where)
    if ornament.get("anchor", "fill-edge") not in ANCHORS:
        problems.append("%s anchor isn't one of %s" % (where, ", ".join(sorted(ANCHORS))))
    frames = ornament.get("frames")
    if not isinstance(frames, list) or not frames:
        return problems + ["%s has no frames" % where]
    if len(frames) > 32:
        problems.append("%s has %d frames; the cap is 32" % (where, len(frames)))
    rows = max((len(frame) for frame in frames if isinstance(frame, list)), default=0)
    columns = max((len(row) for frame in frames if isinstance(frame, list) for row in frame
                   if isinstance(row, str)), default=0)
    if rows > 24 or columns > 64:
        problems.append("%s is %d x %d; the cap is 24 rows by 64 columns" % (where, rows, columns))
    return problems


def document_problems(document):
    """What would make the host draw this differently from what was meant."""
    if not isinstance(document, dict):
        return ["the output is JSON but not an object"]
    problems = []
    if document.get("schema") != 1:
        problems.append("schema is %r; a view document is 1" % document.get("schema"))
    state = document.get("state", "ok")
    if state not in STATES:
        problems.append("state %r isn't ok, empty or error" % state)
    problems += text_problems("message", document.get("message"))
    header = document.get("header")
    if header is not None:
        if not isinstance(header, dict) or not isinstance(header.get("title"), str):
            problems.append("header has no title")
        else:
            badge = header.get("badge")
            if isinstance(badge, dict) and badge.get("tone", "neutral") not in TONES:
                problems.append("badge tone %r isn't one of %s" % (badge.get("tone"), ", ".join(sorted(TONES))))
            for field in ("title", "trailing"):
                problems += text_problems("header." + field, header.get(field))
    rows = document.get("rows", [])
    if not isinstance(rows, list):
        problems.append("rows isn't a list")
        rows = []
    if len(rows) > MAX_ROWS:
        problems.append("%d rows; only the first %d are kept" % (len(rows), MAX_ROWS))
    seen = set()
    for index, row in enumerate(rows):
        where = "rows[%d]" % index
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not isinstance(row.get("title"), str):
            problems.append("%s is dropped: it needs an id and a title" % where)
            continue
        if row["id"] in seen:
            problems.append("%s repeats id %r, so it's dropped" % (where, row["id"]))
        seen.add(row["id"])
        for field in ("lead", "title", "subtitle", "value", "footnote"):
            problems += text_problems("%s.%s" % (where, field), row.get(field))
        track = row.get("track")
        if isinstance(track, dict):
            for field in ("fill", "ghost"):
                value = track.get(field)
                if value is not None and (not isinstance(value, (int, float)) or not 0 <= value <= 1):
                    problems.append("%s.track.%s is %r; it's clamped to 0...1" % (where, field, value))
            tint = track.get("tint")
            if tint is not None and not (isinstance(tint, str) and TINT_PATTERN.match(tint)):
                problems.append("%s.track.tint %r isn't #RGB or #RRGGBB, so the accent colour is used" % (where, tint))
        ornaments = ([row["ornament"]] if "ornament" in row else []) + list(row.get("ornaments") or [])
        if len(ornaments) > 4:
            problems.append("%s has %d ornaments; the cap is 4" % (where, len(ornaments)))
        for number, ornament in enumerate(ornaments):
            problems += ornament_problems("%s ornament %d" % (where, number + 1), ornament)
        if "actions" in row:
            problems += action_problems(where + ".actions", row["actions"])
    if "actions" in document:
        problems += action_problems("actions", document["actions"])
    return problems


def main(argv):
    parser = argparse.ArgumentParser(description="Run an extension the way stack-nudge does.")
    parser.add_argument("directory")
    parser.add_argument("--action")
    parser.add_argument("--row")
    parser.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    parser.add_argument("--from-config", action="store_true",
                        help="take declared keys from ~/.stack-nudge/config")
    args = parser.parse_args(argv)

    directory = os.path.abspath(args.directory)
    try:
        with open(os.path.join(directory, "manifest.json"), encoding="utf-8") as handle:
            manifest = json.load(handle)
    except (OSError, ValueError) as error:
        print("FAIL can't read manifest.json: %s" % error)
        return 1
    if manifest.get("mode") == "service":
        print("SKIP %s is a service; run its own tests instead" % manifest.get("id"))
        return 0

    values = read_config(os.path.expanduser("~/.stack-nudge/config")) if args.from_config else {}
    for pair in args.set:
        key, _, value = pair.partition("=")
        values[key] = value
    undeclared = sorted(key for key in values if key.startswith("STACKNUDGE_EXT_")
                        and key not in declared_keys(manifest) and not args.from_config)
    environment = host_environment(manifest, values)

    command = [os.path.join(directory, manifest.get("run", "./run"))]
    if args.action:
        command += ["--action", args.action]
        if args.row:
            command += ["--row", args.row]
    started = time.monotonic()
    try:
        completed = subprocess.run(command, cwd=directory, env=environment, capture_output=True,
                                   timeout=TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        print("FAIL killed at %d s; the host shows the last good document as stale" % TIMEOUT_SECONDS)
        return 1
    except OSError as error:
        print("FAIL couldn't run %s: %s (missing, or not executable)" % (command[0], error))
        return 1
    elapsed = time.monotonic() - started

    print("ran   %s in %.2f s, exit %d, %d bytes" % (" ".join(command[1:]) or "(no action)", elapsed,
                                                    completed.returncode, len(completed.stdout)))
    print("env   %s" % ", ".join(sorted(key for key in environment if key.startswith("STACKNUDGE_EXT_")
                                          and key not in ("STACKNUDGE_EXT_ID", "STACKNUDGE_EXT_SCHEMA"))
                                   or ["no config keys set"]))
    for key in undeclared:
        print("note  %s isn't declared in the manifest, so the host would never pass it" % key)
    if completed.stderr:
        print("stderr (the host discards this):")
        print("  " + completed.stderr.decode("utf-8", "replace").strip().replace("\n", "\n  "))

    failed = False
    if completed.returncode != 0:
        print("FAIL non-zero exit; the host treats it as transient and shows the last good document")
        failed = True
    if len(completed.stdout) > MAX_STDOUT:
        print("FAIL over 8 MB of output; the host cuts it")
        failed = True
    try:
        document = json.loads(completed.stdout.decode("utf-8"))
    except ValueError as error:
        print("FAIL output isn't JSON (%s); the host shows it as malformed" % error)
        return 1
    problems = document_problems(document)
    for problem in problems:
        print("warn  %s" % problem)
    state = document.get("state", "ok") if isinstance(document, dict) else "?"
    rows = len(document.get("rows") or []) if isinstance(document, dict) else 0
    print("doc   state %s, %d rows%s" % (state, rows, ", message: %s" % document.get("message")
                                          if isinstance(document, dict) and document.get("message") else ""))
    return 1 if failed or problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
