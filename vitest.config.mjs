import { defineConfig } from 'vitest/config';

// The scripts' specs, each a project of its own so check.sh runs one by name
// (`pnpm exec vitest run --project <name>`).
export default defineConfig({
    test: {
        maxWorkers: 4,
        projects: [
            {
                test: {
                    name: 'workflow-pins',
                    environment: 'node',
                    globals: true,
                    include: ['scripts/specs/check-workflows.spec.mjs'],
                    testTimeout: 20_000,
                },
            },
        ],
    },
});
