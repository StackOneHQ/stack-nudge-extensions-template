# stack-nudge extensions template

A starting point for a catalogue of [stack-nudge](https://github.com/StackOneHQ/stack-nudge)
extensions of your own, public or private. It has the same packaging, checks and release
layout stack-nudge uses for its built-in extensions, so stack-nudge installs and updates
yours the same way.

There's one example, `extensions/hello`, to copy from or delete.

## Starting a catalogue

1. **Use this template** on GitHub to make your repo. Private is fine.
2. Fill in `.github/CODEOWNERS` with your reviewers and `SECURITY.md` with where reports go.
3. Add your extensions under `extensions/`, one directory each (CONTRIBUTING.md has the steps).
4. Merge to `main`. `release.yaml` publishes a release named `extensions-<run>` with every
   package and the index.
5. Point stack-nudge at it, in `~/.stack-nudge/config`:

   ```
   STACKNUDGE_EXTENSIONS_SOURCES=your-org/your-repo
   ```

   Several repos go comma separated. For a private repo, sign in to GitHub in stack-nudge's
   Settings, or with the `gh` CLI. Your extensions then show in the browser beside the built-in
   ones, labelled with the repo.

This needs a stack-nudge that reads other catalogues
([StackOneHQ/stack-nudge#251](https://github.com/StackOneHQ/stack-nudge/pull/251)).

The template itself never publishes a release (`release.yaml` skips a template repo), so
pointing stack-nudge at this repo shows it as unreadable rather than installing the example.

## What stack-nudge reads

This is what `release.yaml` and `scripts/package-extensions.sh` produce. Keep to it if you
publish some other way.

- **The latest release.** stack-nudge reads `releases/latest`, which leaves out drafts and
  pre-releases. The tag's name doesn't matter, only that the newest release has the index.
- **`extensions-index.json`** lists each extension's `id`, `name`, `version`, `description`,
  `asset`, `sha256`, `requires`, `config`, `tier`, `capabilities` and `mode`. An entry can't
  say which repo it came from; stack-nudge stamps that itself.
- **`extension-<id>-<version>.tar.gz`** for each one, with a `.sha256` file beside it holding
  `<hash>  <file name>`. stack-nudge won't install a package without it, or one whose hash
  doesn't match.
- **Updates** are offered when the index's `version` for an installed extension differs from
  the installed one. New files under an old version never reach anyone who has it, which is
  why the version check fails a change that doesn't bump it.
- **Tiers** come from `extensions/tiers.json`, the reviewers' file, through the index. What
  stack-nudge actually grants is capped by who owns the repo, in stack-nudge itself: a
  StackOneHQ repo can grant up to `trusted`, any other repo is held to `view`. Anything not
  in `tiers.json` is `view`.

If a repo can't be read, stack-nudge names it in the browser with the reason and still loads
the rest. Its installed extensions keep their tiers until a later fetch reaches every repo.

## Layout

- `extensions/`: what stack-nudge installs, one directory per extension, plus `tiers.json`.
  Only this is packaged.
- `scripts/`: `check.sh` runs every check. `package-extensions.sh`, `test-extensions.sh` and
  `check-extension-versions.sh` are copied from stack-nudge, `check-workflows.mjs` from
  StackOne's agent-control.
- `vendor/`: stack-nudge's manifest enum, which the packager reads for the known capabilities.
- `.github/workflows/`: `ci.yml` checks the PR title and validates, tests and version-checks the
  extensions on every pull request, `release.yaml` publishes on every merge that changes an
  extension.

## What you need

- python3, for the extensions and their tests
- Node 22.23.4 (`.nvmrc`, or Volta reads it from `package.json`) and pnpm 11.17.0, which pnpm
  picks up from `packageManager` itself, for the lint, the script specs and the git hooks
- shellcheck and actionlint if you want those checks to run; they're skipped otherwise

```bash
pnpm install   # also turns on the git hooks in .githooks/
pnpm check     # scripts/check.sh: every part, one line each
```

To try an extension in stack-nudge before it's released, copy it in. It shows up as a tab:

```bash
cp -R extensions/hello ~/.stack-nudge/extensions/hello
```

## Where the docs are

- `CONTRIBUTING.md`: branches, commits, adding an extension and what review looks for
- `AGENTS.md`: the rules for agents (`CLAUDE.md` links to it)
- `SECURITY.md` and `PRIVACY.md`: reporting a problem, and what each extension reads and sends
- stack-nudge's [extension docs](https://github.com/StackOneHQ/stack-nudge/blob/main/docs/extensions.md),
  the spec for the manifest and the document an extension prints
