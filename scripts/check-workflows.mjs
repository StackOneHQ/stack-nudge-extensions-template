#!/usr/bin/env node
// Copied from agent-control's scripts/check-workflows.mjs.
// The GitHub workflows' actions, each pinned to a full commit sha with its version in a comment:
//
//   uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
//
// A tag or a branch can be moved to other code after it was reviewed; a commit can't. The comment
// says which release the sha is, for whoever updates it. An action in this repository (`./...`) is
// the commit's own and needs no pin.
//
//   node scripts/check-workflows.mjs [workflow files...]   (default: .github/workflows/*.y*ml)

import { readdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const WORKFLOWS = join(ROOT, '.github', 'workflows');

const PINNED = /^[\w.-]+\/[\w.-]+(\/[\w./-]+)?@[0-9a-f]{40} # v\d+(\.\d+){0,2}$/;

// problemsOf(text, file): one line per `uses:` that isn't pinned as above.
export const problemsOf = (text, file) =>
    text.split('\n').flatMap((line, index) => {
        const uses = line.match(/^\s*(?:-\s+)?uses:\s*(.+?)\s*$/)?.[1];
        if (uses === undefined || uses.startsWith('./')) return [];
        return PINNED.test(uses)
            ? []
            : [`${file}:${index + 1}: ${uses} is not owner/repo@<full sha> # v<version>`];
    });

const main = (files) => {
    const paths =
        files.length > 0
            ? files
            : readdirSync(WORKFLOWS)
                  .filter((name) => /\.ya?ml$/.test(name))
                  .map((name) => join(WORKFLOWS, name));
    const problems = paths.flatMap((path) =>
        problemsOf(readFileSync(path, 'utf8'), path.replace(`${ROOT}/`, '')),
    );
    for (const problem of problems) console.error(`check-workflows: ${problem}`);
    if (problems.length === 0)
        console.log(`every action in ${paths.length} workflows is pinned to a commit`);
    return problems.length === 0 ? 0 : 1;
};

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
    process.exitCode = main(process.argv.slice(2));
}
