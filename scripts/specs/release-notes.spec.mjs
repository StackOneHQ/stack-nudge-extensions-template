// Tests for scripts/release-notes.mjs, run by check.sh on vitest.

import { releaseNotes } from '../release-notes.mjs';

const entry = (id, version, tier = 'view', name = id) => ({ id, name, version, tier });

describe('release-notes', () => {
    describe('.releaseNotes', () => {
        describe('when there is no previous release', () => {
            it('lists every extension as new, by id', () => {
                const actual = releaseNotes(
                    [entry('zeta', '1.0.0'), entry('alpha', '0.1.0')],
                    [],
                    'abc1234',
                );

                expect(actual).toBe(
                    [
                        'Extensions as of abc1234.',
                        '',
                        '| Extension | Version | Tier | Since the last release |',
                        '|---|---|---|---|',
                        '| alpha (`alpha`) | 0.1.0 | view | new |',
                        '| zeta (`zeta`) | 1.0.0 | view | new |',
                        '',
                    ].join('\n'),
                );
            });
        });

        describe('when there is a previous release', () => {
            it('marks what was updated, leaves what is unchanged, and names what went', () => {
                const previous = [
                    entry('alpha', '0.1.0'),
                    entry('beta', '2.0.0'),
                    entry('gone', '1.0.0'),
                ];
                const current = [
                    entry('alpha', '0.2.0'),
                    entry('beta', '2.0.0'),
                    entry('fresh', '0.1.0'),
                ];

                const actual = releaseNotes(current, previous);

                expect(actual).toContain('| alpha (`alpha`) | 0.2.0 | view | updated from 0.1.0 |');
                expect(actual).toContain('| beta (`beta`) | 2.0.0 | view |  |');
                expect(actual).toContain('| fresh (`fresh`) | 0.1.0 | view | new |');
                expect(actual).toContain('No longer published: `gone` 1.0.0.');
            });

            it('says when only the tier changed', () => {
                const actual = releaseNotes(
                    [entry('alpha', '1.0.0', 'service')],
                    [entry('alpha', '1.0.0')],
                );

                expect(actual).toContain('| alpha (`alpha`) | 1.0.0 | service | tier was view |');
            });
        });

        describe('when a name has markdown in it', () => {
            it('keeps it inside its cell', () => {
                const actual = releaseNotes([entry('odd', '1', 'view', 'A | B\nC')]);

                expect(actual).toContain('| A \\| B C (`odd`) | 1 | view | new |');
            });
        });

        describe('when there are no extensions', () => {
            it('says so rather than printing an empty table', () => {
                const actual = releaseNotes([]);

                expect(actual).toBe('Extensions in this release.\n\nNo extensions.\n');
            });
        });
    });
});
