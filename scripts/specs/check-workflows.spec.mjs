// Tests for scripts/check-workflows.mjs, copied from agent-control's, run by check.sh on vitest.

import { problemsOf } from '../check-workflows.mjs';

const SHA = '3d3c42e5aac5ba805825da76410c181273ba90b1';

describe('check-workflows', () => {
    describe('pins', () => {
        it('passes a full sha with its version', () => {
            const actual = problemsOf(`      - uses: actions/checkout@${SHA} # v7.0.1\n`, 'ci.yml');

            expect(actual).toStrictEqual([]);
        });

        it('passes an action in a subfolder, and a major-only version', () => {
            const actual = problemsOf(
                `      - uses: actions/cache/restore@${SHA} # v6\n`,
                'ci.yml',
            );

            expect(actual).toStrictEqual([]);
        });

        it('passes a local action', () => {
            const actual = problemsOf('      - uses: ./.github/actions/setup\n', 'ci.yml');

            expect(actual).toStrictEqual([]);
        });

        it('passes uses: on its own line under a step name', () => {
            const actual = problemsOf(
                `      - name: Checkout\n        uses: actions/checkout@${SHA} # v7.0.1\n`,
                'ci.yml',
            );

            expect(actual).toStrictEqual([]);
        });
    });

    describe('refusals', () => {
        it('refuses a tag', () => {
            const actual = problemsOf('      - uses: actions/checkout@v4\n', 'ci.yml');

            expect(actual).toStrictEqual([
                'ci.yml:1: actions/checkout@v4 is not owner/repo@<full sha> # v<version>',
            ]);
        });

        it('refuses a short sha', () => {
            const actual = problemsOf(
                '      - uses: actions/checkout@3d3c42e # v7.0.1\n',
                'ci.yml',
            ).length;

            expect(actual).toBe(1);
        });

        it('refuses a full sha with no version comment', () => {
            const actual = problemsOf(`      - uses: actions/checkout@${SHA}\n`, 'ci.yml').length;

            expect(actual).toBe(1);
        });

        it('refuses a docker image by tag', () => {
            const actual = problemsOf('      - uses: docker://alpine:3.20\n', 'ci.yml').length;

            expect(actual).toBe(1);
        });

        it('names the line', () => {
            const actual = problemsOf(
                `name: x\njobs:\n  a:\n    steps:\n      - uses: owner/repo@main\n`,
                'x.yml',
            );
            expect(actual[0]).toMatch(/^x\.yml:5: /);
        });
    });
});
