# Security

A merged extension runs on people's Macs as them, with nothing sandboxing it, so a hole in one
matters. If you find one, report it privately rather than in an issue, a pull request or a
public channel.

## Reporting

If you made a catalogue from this template, replace this section with where reports to your
team go.

For the template itself, email support@stackone.com, saying in the subject that it's a security
report for stack-nudge-extensions-template. A problem in stack-nudge goes to stack-nudge's
own SECURITY.md.

- Say what you found, how to reproduce it and what it lets someone do, with the commit or
  release.
- Leave out real tokens and anyone's data. A stand-in shows the problem just as well.

Please give the team the chance to fix it before telling anyone else.

## What counts

Anything that lets an extension or a package do more than it should: an extension that runs or
writes outside its own directory, sends something PRIVACY.md doesn't list, or keeps a secret
anywhere but the Keychain; a package that gets past `package-extensions.sh validate` with a
symlink, an escaping path or a tier it wasn't given; a workflow that runs untrusted input or
leaves a write token behind.

## Supported versions

Only `main`. Nothing older gets a fix.
