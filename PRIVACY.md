# Privacy

What each extension reads on the Mac, what it sends, and where it's kept. Update this in the
same pull request as any change to it.

## hello

- Reads its own `STACKNUDGE_EXT_HELLO_NAME` setting, and nothing else on the Mac.
- Keeps a count of greetings in `state.json` in its own directory.
- Sends nothing anywhere.
