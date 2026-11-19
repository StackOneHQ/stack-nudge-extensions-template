# stack-nudge extensions, the parts you need to write one

Distilled from StackOneHQ/stack-nudge `docs/extensions.md` and
`docs/design/service-extensions.md` at commit `03b559a`. Those are the spec. If
anything here disagrees with them, they win: read the original section before
relying on an edge case, and refresh this file when the spec changes.

## What an extension is

A directory with `manifest.json` and an executable. stack-nudge runs the
executable, reads one JSON document from its stdout and draws it, usually as a
tab. No API and no native code: anything that prints JSON works.

Extensions are curated, not sandboxed. `run` executes as the user, and macOS may
let it use permissions stack-nudge already holds. Review is the control.

## The manifest

```json
{
  "id": "derby",
  "name": "Token Derby",
  "description": "One line. It's all the Settings row has room for.",
  "version": "1.2.0",
  "schema": 1,
  "tab": { "label": "Derby" },
  "run": "./run",
  "requires": ["python3"],
  "config": ["STACKNUDGE_EXT_DERBY_ORG"],
  "refresh": { "onOpen": true, "intervalSeconds": 30, "whileFocusedOnly": true }
}
```

| Field | Required | Rules |
|---|---|---|
| `id` | yes | `^[a-z0-9][a-z0-9-]{0,31}$`, equal to the directory name |
| `name` | yes | Tab label when `tab.label` is absent |
| `description` | no | One line |
| `version` | yes | Yours. The host offers an update whenever the string changes, so bump it on every change |
| `schema` | yes | `1` for a view extension. `2` only for service mode |
| `tab.label` | no | Defaults to `name`, capped at 16 characters |
| `run` | no | Default `./run`. Relative, no `..`, no absolute or `~` path |
| `requires` | no | Interpreters, checked at install by running each one. `python3`, `swiftc` and so on |
| `config` | no | Keys passed to `run`. Each `^STACKNUDGE_EXT_[A-Z0-9_]+$`. See below |
| `refresh.onOpen` | no | Default `true` |
| `refresh.intervalSeconds` | no | Default off, minimum 5. Every tick is a process spawn |
| `refresh.whileFocusedOnly` | no | Default `true`. `false` keeps polling with the tab hidden, and runs it once soon after launch |
| `glance` | no | Default `false`. The widget shows the header badge while its tone is `warning` or `danger`. Pair with `whileFocusedOnly: false` |
| `surfaces` | no | Default `["tab"]`. `["settings"]` means no tab, just a page under Settings → Extensions, which suits set-and-forget extensions |
| `handshakeSeconds` | no | Service mode only, 10 to 120 |
| `mode`, `capabilities` | no | Service mode only, with `"schema": 2` |

A manifest that breaks a rule is refused with the reason, shown in Settings.
Unknown fields are ignored by older hosts, so only additive changes are safe.

### Config keys

Bare names or objects. The object form gives the Settings page a labelled row:

```json
"config": [
  "STACKNUDGE_EXT_DERBY_TRACE",
  { "key": "STACKNUDGE_EXT_DERBY_ORG", "label": "Organisation",
    "help": "Whose races to show.", "placeholder": "stackone" }
]
```

`type` picks the control: `text` (default), `toggle` (`"true"`/`"false"`),
`choice` (`options: [{"value", "label"}]`), `number` (`options: [15, 30, 60]`,
optional `"unit": "seconds"`), `dynamic` (service only, offered at run time). An
optional `default` is what the row shows while unset. Options: one line each, no
control characters, no surrounding spaces, at most 256 characters, at most 64.

Values live in `~/.stack-nudge/config` as `KEY=value`. A value can't contain a
line break, and a URL value must be `https`. An unset key is left out of the
environment rather than passed empty, so "missing" and "empty" are one case.

Every key is a field the user sees and a decision they have to make. Don't ask
for anything you can work out.

## The environment

`run` gets only this:

```
PATH                    a minimal system PATH
HOME
STACKNUDGE_EXT_ID       your id
STACKNUDGE_EXT_SCHEMA   the document schema this host reads
+ each declared STACKNUDGE_EXT_* key that has a value
```

The working directory is the extension's own directory. stdout is the document;
stderr is discarded, so use it for debugging. Budget: 12 seconds and 8 MB of
stdout per run. Past the time the run is killed; past the size output is cut.

## The view document

One JSON object on stdout. Only `schema` is required.

```json
{
  "schema": 1,
  "state": "ok",
  "header": { "title": "League", "badge": { "text": "LIVE", "tone": "success" }, "trailing": "5h44m" },
  "rows": [
    {
      "id": "h1", "lead": "1", "title": "black & white", "subtitle": "Yashika",
      "value": "14.5M", "footnote": "36K/15m",
      "track": { "fill": 0.52, "ghost": 0.60, "tint": "#7FD1B9" },
      "actions": [{ "id": "open", "label": "Open", "key": "return" }]
    }
  ],
  "actions": [{ "id": "refresh", "label": "Sync now", "key": "r" }]
}
```

- `state`: `ok`, `empty` or `error`, with an optional `message`. `empty` and
  `error` show the message instead of the rows. For partial data with a warning,
  send `ok` with a `warning` badge.
- `header`: `title` is required if there is a header. `badge.tone` is `neutral`
  (default), `success`, `warning` or `danger`. `trailing` is monospaced, good
  for a countdown.
- `rows`: `id` and `title` required, ids unique. A bad row is dropped on its own.
- `track`: `fill` and `ghost` from 0 to 1, `tint` `#RGB` or `#RRGGBB`. Colours are
  adjusted for legibility, so they only need to be roughly right.
- `ornament` / `ornaments`: animated pixel grids on the track, up to 4 per row.
  `kind: "sprite"`, `fps` (0 is still, max 30), `anchor` (`fill-edge`, `leading`,
  `trailing`), `palette` (one character to a colour, `.` transparent), `frames`
  (each a list of row strings). At most 32 frames, 24 rows, 64 columns.
- Text fields are cut at 256 characters.

Caps: 500 rows, 16 actions per list. Past a cap the host truncates rather than
failing.

### Actions

When one fires, `run` runs again with arguments, and prints a fresh document:

```
run --action refresh
run --action open --row h1
```

`run` keeps no state between runs. Anything it must remember goes in a file in
its own directory (`state.json` is ignored by git here). Only one run at a time;
presses during a run are ignored.

`key` is one ASCII letter or digit, or `"return"`. Nothing else is accepted, and
there are no buttons, so an action without a valid key can't be reached.

## Failures

| | When | Shown as |
|---|---|---|
| missing | `run` gone or not executable | a broken install |
| transient | timeout, non-zero exit, killed, output cut | the last good document, marked older |
| malformed | output doesn't parse | the extension's bug |

A non-zero exit is transient even if stdout parsed. Report your own errors with
`"state": "error"` and exit 0.

## Tiers

| Tier | May hold |
|---|---|
| `view` | view mode only |
| `service` | service mode, `event:idle`, `event:panel`, `feed` |
| `trusted` | also `signal:*`, `event:session`, `event:nudge`, hardware such as `bluetooth` |

The tier comes from `extensions/tiers.json`, the reviewers' file, never the
manifest. Unlisted means `view`. stack-nudge also caps it by catalogue: only the
app's own repository and `StackOneHQ/stack-nudge-internal-marketplace` can grant
above `view`, a list compiled into the app. Validation refuses a service at
`view` and `bluetooth` at `service`.

## Service mode, in brief

`"schema": 2, "mode": "service", "capabilities": [...]` makes `run` a
long-running process. Newline-delimited JSON both ways:

- in: `hello` (with the granted capabilities), `config` (again whenever settings
  change), `event`, `ping`, `stop`
- out: `ready` (answering `hello`, within `handshakeSeconds`), `document`,
  `signal`, `feed`, `pong`, `choices`

A service can't take key presses yet, so anything triggered from a tab means a
view extension. Read `extensions/away` in StackOneHQ/stack-nudge and
`docs/design/service-extensions.md` before writing one.

## Validation and packaging

`scripts/package-extensions.sh validate` refuses: a manifest that doesn't parse
or whose `id` isn't the directory name; a bad `id` or `schema`; an absolute or
`..` run path; a `run` that is missing, not a regular file or not executable;
and any symlink or non-regular file anywhere in the package. Tests
(`extensions/<id>/test_*.py`) ship in the package and a suite with zero tests
fails.
