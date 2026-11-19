# stack-nudge extensions template: rules for agents

Read `README.md` first for the layout and what stack-nudge reads from a release. Then:

- Run `pnpm check` (`scripts/check.sh`) before you commit. It must be green.
- Everything under `extensions/` is packaged and shipped to Macs, so nothing else goes in it.
- StackOneHQ/stack-nudge's `docs/extensions.md` is the extension spec. Don't invent manifest
  fields.
- Any change to an extension directory, tests included, bumps `version` in its manifest. The
  host only offers an update when the version string changes.
- What an extension newly reads or sends goes in PRIVACY.md in the same commit.
- A service extension can't take key presses yet. Anything triggered from the tab means a view
  extension.
- Extension tests are Python `unittest` beside the script and offline: no network, no browser,
  and never the real Keychain. Inject them, as `hello` takes its state path.
- `extensions/tiers.json` is the reviewers' decision. Never raise a tier without saying why.
- `scripts/` and `vendor/` are copies, from StackOneHQ/stack-nudge (the packaging, test and
  version scripts, the manifest enum) and agent-control (`check-workflows.mjs`). Refresh a copy
  by copying it again. The local changes are in `check.sh`: the lint part in place of the
  workspace tasks, and skipping the extension tests while there are no extensions.
- `release.yaml` must skip a template repository. Don't remove that `if`.
- Add dependencies with `pnpm add`, never by editing `package.json`. Lint and format come from
  `@stackone/biome-config` through `biome.jsonc`; fix with `--write`, never `--unsafe`.
- GitHub Actions are pinned to full commit SHAs. `scripts/check-workflows.mjs` fails a tag.
- One logical change per commit, with a subject that says what it does. Never skip the
  pre-commit hook.
