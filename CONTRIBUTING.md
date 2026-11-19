# Contributing

How a change gets onto `main`, and from there to people's Macs. The short version: a branch,
small commits, `pnpm check` green, a pull request, squash merge. A merge that changes an
extension publishes a release by itself.

## Branches

Branch off `main`, named for what it does. A branch that hasn't merged is yours to rebase and
rewrite. `main` is never rewritten: a mistake on it is reverted
or fixed forward.

## Commits

- One logical change per commit, with a subject that says what it does. There's no format to
  follow.
- Every fix comes with a test that fails without it.
- `pnpm install` turns on the `pre-commit` hook in `.githooks/`, which formats staged JSON and
  scripts with Biome.

Pull requests squash, so the PR title becomes the commit on `main`.

## Adding an extension

stack-nudge's [extension docs](https://github.com/StackOneHQ/stack-nudge/blob/main/docs/extensions.md)
are the spec, nothing here changes it. `extensions/hello` is the smallest working example: a
config key, an action, and state kept in its own directory.

1. Create `extensions/<id>/`, where `<id>` matches the manifest's `id`.
2. Write the manifest and `run`. Start at `"schema": 1`, a view extension, unless it really has
   to stay running (see Tiers).
3. Put tests beside it as `test_*.py`. They ship in the package on purpose, and run offline:
   nothing reaches the network, the Keychain or a browser.
4. Add what it reads and sends to PRIVACY.md.
5. `pnpm check`.

To try it in stack-nudge first, copy the directory to `~/.stack-nudge/extensions/<id>`.

## Changing an extension

Bump `version` in its manifest. stack-nudge decides there's an update by comparing version
strings, so new files under an old version never reach anyone who already has it. The version
check in `pnpm check` and CI fails the change otherwise, tests included, since every file is in
the tarball.

## What review looks for

An extension runs on people's Macs as them. Nothing sandboxes it, and macOS may hand it
permissions stack-nudge already has, so review is the security control. Read it as code, not
content:

- every path in the package, and what `run` executes and where it writes
- every `config` key is something the user actually needs to decide, since each one becomes a
  field in Settings
- anything sent off the Mac: where, what, and whether PRIVACY.md says so
- secrets in the Keychain or a 0600 file under the extension's own directory. The exception is
  a token the user pastes into a `config` field, which stack-nudge keeps in
  `~/.stack-nudge/config` (mode 0600, and handed only to the extension that declares the key).
  That's fine for a token that does one job and can be revoked, like a reporter token, never
  for a password or a token with wider access
- nothing put into a shell, osascript or a URL except through argv or an encoder

## Tiers

The tier is the reviewers' decision, not the extension's, so it lives in `extensions/tiers.json`
rather than the manifest. Anything not listed is `view`. A service extension (`"schema": 2`,
`"mode": "service"`) needs `service`, and signals or hardware capabilities need `trusted`. Say in
the pull request why it needs more than `view`.

stack-nudge caps what a repo can grant by who owns it: only a StackOneHQ repo gets above `view`,
whatever `tiers.json` says. Anywhere else, list a tier only to record the review; it takes effect
if the extension moves to a StackOneHQ catalogue.
