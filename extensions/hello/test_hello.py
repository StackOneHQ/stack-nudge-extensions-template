#!/usr/bin/env python3
"""Tests for the Hello extension, run with `python3 -m unittest discover extensions`
as scripts/test-extensions.sh and CI do.

They ship inside the package, like stack-nudge's own, and stay offline: state
goes to a temporary directory, never the extension's real one.
"""

import importlib.machinery
import importlib.util
import json
import os
import pathlib
import tempfile
import unittest

# The executable has no .py extension, since the host runs it by path, so it's
# loaded explicitly rather than imported.
_PATH = pathlib.Path(__file__).with_name("run")
_LOADER = importlib.machinery.SourceFileLoader("hello_run", str(_PATH))
_SPEC = importlib.util.spec_from_loader(_LOADER.name, _LOADER)
hello = importlib.util.module_from_spec(_SPEC)
_LOADER.exec_module(hello)


class Greeting(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.state = os.path.join(self.directory.name, "state.json")

    def tearDown(self):
        self.directory.cleanup()

    def test_greets_there_without_a_name(self):
        actual = hello.main(["run"], {}, self.state)

        self.assertEqual(actual["rows"][0]["title"], "Hello, there")
        self.assertNotIn("trailing", actual["header"])

    def test_greets_the_configured_name(self):
        actual = hello.main(["run"], {"STACKNUDGE_EXT_HELLO_NAME": " Ada "}, self.state)

        self.assertEqual(actual["rows"][0]["title"], "Hello, Ada")

    def test_greet_counts_across_runs(self):
        hello.main(["run", "--action", "greet"], {}, self.state)
        actual = hello.main(["run", "--action", "greet"], {}, self.state)

        self.assertEqual(actual["rows"][0]["value"], "2")
        self.assertEqual(actual["header"]["trailing"], "2 times")

    def test_a_refresh_leaves_the_count_alone(self):
        hello.main(["run", "--action", "greet"], {}, self.state)
        actual = hello.main(["run"], {}, self.state)

        self.assertEqual(actual["header"]["trailing"], "once")

    def test_a_broken_state_file_starts_again_from_zero(self):
        pathlib.Path(self.state).write_text("not json", encoding="utf-8")

        actual = hello.main(["run"], {}, self.state)

        self.assertEqual(actual["rows"][0]["value"], "0")

    def test_an_older_host_gets_an_error_document(self):
        actual = hello.main(["run"], {"STACKNUDGE_EXT_SCHEMA": "0"}, self.state)

        self.assertEqual(actual["state"], "error")

    def test_every_action_has_a_key_the_host_accepts(self):
        actual = hello.main(["run"], {}, self.state)

        for action in actual["actions"]:
            self.assertRegex(action["key"], r"^(?:[a-z0-9]|return)$")

    def test_the_document_is_json(self):
        actual = json.loads(json.dumps(hello.main(["run"], {}, self.state)))

        self.assertEqual(actual["schema"], 1)


if __name__ == "__main__":
    unittest.main()
