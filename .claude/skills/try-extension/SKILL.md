---
name: try-extension
description: Run a stack-nudge extension from this repo the way the app does, before it's released. Runs extensions/<id>/run with the host's restricted environment, each action, and checks the printed document against the host's rules and limits; then, if wanted, installs it into ~/.stack-nudge/extensions to see it in the panel. Use when asked to try, run, test by hand, preview, debug or check what an extension shows.
---

# Try an extension

The tests check the logic. This checks what the app would actually get: the same
environment, working directory, time limit and output limit, and a document the
host will draw as meant.

## Before running anything

This runs the extension's real code, as the user. It reads what the extension
reads and sends what it sends, so an extension that calls a service, reads the
Keychain or posts the user's data will do that for real, with their real
credentials if it finds them. Read `run` first. If it talks to anything outside
its own directory, ask the user before running it, and say what it will touch;
otherwise rely on its tests, which fake all of that.

## 1. Run it like the host

```bash
python3 .claude/skills/try-extension/scripts/run_like_host.py extensions/<id>
```

- `--set STACKNUDGE_EXT_<KEY>=value` passes a config value, as if set in
  Settings. Repeat it per key. An undeclared key is reported, since the host
  would never pass it.
- `--from-config` takes the declared keys from `~/.stack-nudge/config` instead.
  Only with the user's say-so: it may hold their real tokens.
- `--action <id>` (and `--row <id>`) runs an action, as a key press would.

Run it with no config, with each key set, and once per action the document
offers. A run that changes state (an action writing its state file) changes
the next one, so look at the extension's directory afterwards and remove any
state file you created.

Reading the result:

- `FAIL` lines are what the user would see as broken or stale: a non-zero exit,
  a timeout at 12 s, output that isn't JSON, or more than 8 MB.
- `warn` lines are things the host silently drops, clamps or ignores: a row
  without an id or title, a repeated id, an action whose key can't be pressed,
  a bad tint, text past 256 characters, too many rows or actions. Fix them; the
  app won't say anything.
- stderr is shown because the host throws it away. Anything only said there
  will never reach the user, so a failure worth seeing belongs in
  `{"state": "error", "message": ...}`.

A service extension (`"mode": "service"`) is long-running and isn't run by the
script. Use its own tests.

## 2. See it in the panel (optional)

Only with the user's go-ahead, since it changes their installed extensions:

```bash
cp -R extensions/<id> ~/.stack-nudge/extensions/<id>
```

It shows up as a tab, or under Settings → Extensions for
`"surfaces": ["settings"]`. If it doesn't, the reason is in Settings →
Extensions and in `~/.stack-nudge/app.log`. Copied in by hand it has no tier
record, so it runs as `view` whatever `tiers.json` says.

Remove it when done (`rm -rf ~/.stack-nudge/extensions/<id>`), or the user keeps
a copy that never updates: an extension that wasn't installed from a catalogue
isn't offered updates from one.
