---
name: review-extension
description: Review a change to a stack-nudge extension in this catalogue repo, before it merges and ships to people's Macs. Walks CONTRIBUTING.md's review list against the diff (paths and what run executes, config keys, what leaves the Mac against PRIVACY.md, secrets, injection, version bump, tier requests) and reports findings without fixing them. Use when asked to review an extension, an extension PR, or whether one is safe to merge.
---

# Review an extension

A merged extension runs on people's Macs as them, unsandboxed, and macOS may
let it use permissions stack-nudge already holds. Review is the only control,
so read it as code, not content. Report what you find; don't fix it unless
asked.

## 1. Get the change

The diff against the base (a PR's base, else `main`), for `extensions/`,
`PRIVACY.md` and `extensions/tiers.json`:

```bash
git diff --stat main...HEAD -- extensions PRIVACY.md
git diff main...HEAD -- extensions PRIVACY.md
```

For a new extension, read every file in its directory in full, not just the
diff hunks. Then run `scripts/package-extensions.sh validate` and the
extension's tests (`scripts/test-extensions.sh`), which catch symlinks, bad
paths and broken manifests that a diff doesn't show.

## 2. Check, in this order

1. **Every path in the package.** List the directory (`find extensions/<id>
   -ls`). Anything that isn't plainly part of the extension, any symlink, and
   anything `run` executes or writes outside its own directory.
2. **What `run` does.** Every subprocess, file write and network call. Commands
   built from config values, API responses or file contents are the main risk:
   nothing may reach a shell, `osascript` or a URL except as a separate argv
   entry or through a proper encoder.
3. **What leaves the Mac.** Each request: where to, what's in it, and whether
   PRIVACY.md says so in the same change. `https` only, with a timeout and a cap
   on what it reads.
4. **Secrets.** In the Keychain or a 0600 file in its own directory. A token the
   user pastes into a config field is fine only if it does one job and can be
   revoked (CONTRIBUTING.md). Never a password, never a broad token, and never
   printed to stdout or a log.
5. **Config keys.** Each one is a field the user must fill in. Ask of each
   whether the extension could work it out instead. Names follow
   `STACKNUDGE_EXT_<ID>_...`; URL values must be `https`.
6. **The manifest against the spec.** Use the new-extension skill's
   `references/extension-spec.md`: no invented fields, `refresh` sensible for
   what it does (an interval under 30 s, or `whileFocusedOnly: false`, costs a
   process spawn per tick on every Mac), every action has a pressable key.
7. **Version.** Any change in the directory, tests included, bumps `version`.
   `scripts/check-extension-versions.sh main` checks it.
8. **Tier.** Anything above `view` needs a reason in the PR, and the reviewers'
   decision in `extensions/tiers.json`. A service at `view` or `bluetooth` below
   `trusted` fails validation. Remember only the catalogues stack-nudge names can
   grant above `view` at all.
9. **Tests.** Offline, covering each state and action, and a default that fails
   if a test reaches the network.

Running it with the try-extension skill is a quick way to confirm what the
code reading suggests.

## 3. Report

One finding per line, most serious first: the file and line, what's wrong, and
what it allows or breaks for someone who installs it. Say plainly when a check
found nothing. Don't approve or post anything to the PR unless the user asks.
