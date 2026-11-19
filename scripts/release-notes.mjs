#!/usr/bin/env node
// The notes for an extensions release: every extension it publishes with its version and tier,
// marked new or updated against the release before it, and what that one had that this doesn't.
// release.yaml writes them from the index it is about to publish and the latest release's index.
//
//   node scripts/release-notes.mjs <index> [<previous index>] [<short sha>]
//
// A missing or unreadable previous index is treated as no previous release, so the first release
// lists everything as new.

import { readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

const readIndex = (path) => {
    if (!path) return [];
    try {
        const index = JSON.parse(readFileSync(path, 'utf8'));
        return Array.isArray(index.extensions) ? index.extensions : [];
    } catch {
        return [];
    }
};

// Names come from merged manifests, but they still land in markdown, so a pipe or a line break
// can't break the table.
const cell = (text) =>
    String(text ?? '')
        .replace(/[\r\n]+/g, ' ')
        .replace(/\|/g, '\\|')
        .trim();

const change = (entry, before) => {
    if (!before) return 'new';
    if (before.version !== entry.version) return `updated from ${cell(before.version)}`;
    if (before.tier !== entry.tier) return `tier was ${cell(before.tier ?? 'view')}`;
    return '';
};

export const releaseNotes = (current, previous = [], sha = '') => {
    const earlier = new Map(previous.map((entry) => [entry.id, entry]));
    const lines = [sha ? `Extensions as of ${cell(sha)}.` : 'Extensions in this release.', ''];
    if (current.length === 0) {
        lines.push('No extensions.');
    } else {
        lines.push('| Extension | Version | Tier | Since the last release |');
        lines.push('|---|---|---|---|');
        for (const entry of [...current].sort((left, right) => left.id.localeCompare(right.id))) {
            const name = `${cell(entry.name)} (\`${cell(entry.id)}\`)`;
            const status = change(entry, earlier.get(entry.id));
            lines.push(
                `| ${name} | ${cell(entry.version)} | ${cell(entry.tier ?? 'view')} | ${status} |`,
            );
        }
    }
    const kept = new Set(current.map((entry) => entry.id));
    const removed = previous.filter((entry) => !kept.has(entry.id));
    if (removed.length > 0) {
        const names = removed.map((entry) => `\`${cell(entry.id)}\` ${cell(entry.version)}`);
        lines.push('', `No longer published: ${names.join(', ')}.`);
    }
    return `${lines.join('\n')}\n`;
};

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
    const [indexPath, previousPath, sha] = process.argv.slice(2);
    if (!indexPath) {
        console.error('usage: release-notes.mjs <index> [<previous index>] [<short sha>]');
        process.exitCode = 2;
    } else {
        process.stdout.write(releaseNotes(readIndex(indexPath), readIndex(previousPath), sha));
    }
}
