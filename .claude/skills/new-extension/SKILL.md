---
name: new-extension
description: Build a new stack-nudge extension in this catalogue repo, from a description of what it should show or do. Writes extensions/<id>/ (manifest.json, an executable run and offline test_*.py), adds its PRIVACY.md entry, and gets pnpm check green. Use when asked to create, add, scaffold or write an extension, a stack-nudge tab, or a widget for stack-nudge here.
---

# New extension

An extension here is a directory under `extensions/` that stack-nudge installs on
people's Macs and runs as them. Everything in it ships. Read
`references/extension-spec.md` before writing anything: it is the manifest, the
environment, the document and the limits in one place, so nothing gets invented.

## 1. Pin down the shape

Settle these with the user before writing, unless the request already answers
them. Each changes what gets written.

- **What it shows.** Rows of text and bars (a view extension), or nothing but
  settings (`"surfaces": ["settings"]`).
- **When it runs.** On opening the tab only, every N seconds while the tab is
  open, or in the background too (`whileFocusedOnly: false`, needed for a widget
  chip with `"glance": true`).
- **What it reads and sends.** Files on the Mac, APIs it calls, and what leaves
  the Mac. This becomes its PRIVACY.md entry and is what review looks at hardest.
- **What the user must set.** Each config key is a field in Settings. Keep to the
  ones only the user can answer.
- **Whether it needs more than `view`.** Only for a long-running service, signals
  or hardware. Default to a view extension: a service can't take key presses yet,
  and it needs the reviewers to grant a tier.

Pick an `id` (`^[a-z0-9][a-z0-9-]{0,31}$`) that isn't already in `extensions/`.

## 2. Write it

Start from `extensions/hello` in StackOneHQ/stack-nudge-extensions-template (in
this repo if this is the template): a config key, an action, and state kept in
its own directory.

- `extensions/<id>/manifest.json`: two-space indent, `"schema": 1`,
  `"version": "0.1.0"`, a one-line `description`, `"requires": ["python3"]` for a
  Python `run`. Config keys as objects with `label` and `help`, named
  `STACKNUDGE_EXT_<ID>_<WHAT>`.
- `extensions/<id>/run`: executable (`chmod +x`), with a shebang. Python unless
  there is a reason not to. Structure it so the logic is testable without a
  process:
  - a `main(argv, environ, ...)` that returns the document as a dict, with
    paths, clocks and network openers passed in;
  - argument handling for `--action <id>` and `--row <id>`;
  - one `print(json.dumps(...))` at the end, exit 0.
- Report its own failures as `{"schema": 1, "state": "error", "message": "..."}`
  rather than raising. A non-zero exit shows the last good document as stale.
- Network: `https` only, a timeout well inside the 12 s budget, a cap on how much
  it reads, and nothing from the user or a response built into a shell command or
  osascript. Secrets go in the Keychain or a 0600 file in its own directory; a
  revocable single-purpose token may be a config field (see CONTRIBUTING.md).
- State: a JSON file in its own directory, written to a temp file and renamed.
- Every action gets a `key`: one letter or digit, or `"return"`.

## 3. Test it

`extensions/<id>/test_<id>.py`, `unittest`, loading `run` with
`importlib.machinery.SourceFileLoader` (it has no `.py` extension), as `hello`
does. Offline: no network, no browser, never the real Keychain. Pass a temp
directory for state and a fake opener for HTTP, and make the default opener in
tests raise if called, so a test that reaches the network fails rather than
silently passing. Cover each state the document can be in, each action, and each
config case including unset.

## 4. Record and check

- Add a `## <id>` section to PRIVACY.md: what it reads, what it sends and where,
  what it keeps. Same pull request.
- If it needs more than `view`, don't edit `extensions/tiers.json` yourself: say
  in the pull request what it needs and why, for the reviewers to decide.
- Run it the way the host does with the `try-extension` skill.
- `pnpm check` must be green. It validates the package, runs every extension's
  tests and checks versions against `main`.

## Changing an existing one

Bump `version` in its manifest for any change in its directory, tests included,
or nobody who has it gets the change. Update PRIVACY.md if what it reads or sends
changes.
