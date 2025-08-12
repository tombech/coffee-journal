// @ts-check
const { defineConfig, devices } = require('@playwright/test');

/**
 * Grouped test configuration with tiered worker counts for optimal performance.
 * 
 * Strategy:
 * - Stable tests run with 6 workers for maximum speed
 * - Problematic tests degrade gracefully to 4, 2, or sequential execution
 * - Each group can be run independently for debugging
 */

// Helper to determine optimal worker count based on CI environment
const getWorkerCount = (preferred) => {
  // In CI, use much lower worker counts to avoid resource contention and timeouts
  // GitHub Actions has limited resources and concurrent tests cause instability
  if (process.env.CI) {
    return preferred <= 2 ? preferred : (preferred > 4 ? 2 : 1);
  }
  return preferred;
};

module.exports = defineConfig({
  testDir: './src/components/__tests__/playwright/e2e',
  timeout: process.env.CI ? 120 * 1000 : 30 * 1000, // Much longer timeout in CI
  expect: {
    timeout: process.env.CI ? 15000 : 5000 // Longer wait in CI
  },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? 'github' : 'list',
  
  use: {
    actionTimeout: 0,
    baseURL: 'http://localhost:3000',
    trace: process.env.CI ? 'retain-on-failure' : 'on-first-retry',
    screenshot: 'only-on-failure',
    video: process.env.CI ? 'retain-on-failure' : 'retain-on-failure',
    // Add more debugging context in CI
    contextOptions: process.env.CI ? {
      reducedMotion: 'reduce',
      colorScheme: 'light',
    } : {},
  },

  projects: [
    // Group 1A: Basic Manager Tests (2 workers)
    {
      name: 'basic-managers',
      testMatch: [
        '**/all-managers.test.js'
      ],
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
      },
      workers: getWorkerCount(2),
      retries: 2,
    },

    // Group 1B1: Roaster Views (1 worker)
    {
      name: 'roaster-views',
      testMatch: [
        '**/lookup-view-functionality.test.js'
      ],
      testIgnore: [],
      grep: /Roasters|should display item details correctly|should maintain user isolation/,
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
      },
      workers: getWorkerCount(1),
      retries: 2,
    },

    // Group 1B2: Brew Method Views (1 worker)
    {
      name: 'brew-method-views',
      testMatch: [
        '**/lookup-view-functionality.test.js'
      ],
      grep: /Brew Methods/,
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
      },
      workers: getWorkerCount(1),
      retries: 2,
    },

    // Group 1B3: Recipe Views (1 worker)
    {
      name: 'recipe-views',
      testMatch: [
        '**/lookup-view-functionality.test.js'
      ],
      grep: /Recipes/,
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
      },
      workers: getWorkerCount(1),
      retries: 2,
    },

    // Group 1B4: Bean Type Views (1 worker)
    {
      name: 'bean-type-views',
      testMatch: [
        '**/lookup-view-functionality.test.js'
      ],
      grep: /Bean Types/,
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
      },
      workers: getWorkerCount(1),
      retries: 2,
    },

    // Group 1B5: Equipment Views (2 workers - multiple types)
    {
      name: 'equipment-views',
      testMatch: [
        '**/lookup-view-functionality.test.js'
      ],
      grep: /Grinders|Filters|Kettles|Scales|Decaf Methods/,
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
      },
      workers: getWorkerCount(2),
      retries: 2,
    },

    // Group 1B6: Country Views (1 worker - special handling)
    {
      name: 'country-views',
      testMatch: [
        '**/lookup-view-functionality.test.js'
      ],
      grep: /should display view button for Countries/,
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
      },
      workers: getWorkerCount(1),
      retries: 2,
    },

    // Group 1C: Country Management (1 worker - most problematic)
    {
      name: 'country-management',
      testMatch: [
        '**/country-management.test.js'
      ],
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
      },
      workers: getWorkerCount(1), // Most sensitive to race conditions
      retries: 2,
    },

    // Group 1D: Roaster Management (1 worker - complex operations)
    {
      name: 'roaster-management', 
      testMatch: [
        '**/roaster-management.test.js'
      ],
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
      },
      workers: getWorkerCount(1),
      retries: 2,
    },

    // Group 2A: Product Management (4 workers)
    {
      name: 'product-management',
      testMatch: [
        '**/product-management.test.js'
      ],
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
      },
      workers: getWorkerCount(4),
      retries: 2,
    },

    // Group 2B: Batch Management (4 workers)
    {
      name: 'batch-management',
      testMatch: [
        '**/batch-management.test.js'
      ],
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
      },
      workers: getWorkerCount(4),
      retries: 2,
    },

    // Group 2C: Brew Session Management (4 workers)
    {
      name: 'brew-session-management',
      testMatch: [
        '**/brew-session-management.test.js'
      ],
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
      },
      workers: getWorkerCount(4),
      retries: 2,
    },
    // Group 2D: Shot Management (4 workers)
    {
      name: 'shot-management',
      testMatch: [
        '**/shot-management.test.js'
      ],
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
      },
      workers: getWorkerCount(4),
      retries: 2,
    },

    // Group 2E: Shot Session Management (4 workers)
    {
      name: 'shot-session-management',
      testMatch: [
        '**/shot-session-management.test.js'
      ],
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
      },
      workers: getWorkerCount(4),
      retries: 2,
    },

    // Group 2F: Session Duplication (2 workers)
    {
      name: 'session-duplication',
      testMatch: [
        '**/duplication.test.js'
      ],
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
      },
      workers: getWorkerCount(2),
      retries: 2,
    },

    // Group 3: UI/UX Tests (STABLE - 6 workers)
    {
      name: 'ui-ux',
      testMatch: [
        '**/home.test.js',
        '**/settings.test.js',
        '**/button-harmonization.test.js',
        '**/standardized-icons.test.js',
        '**/view-icon-enhancement.test.js',
        '**/default-item-visualization.test.js'
      ],
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
      },
      workers: getWorkerCount(6),
    },

    // Group 4: Form/Input Tests (MODERATE - 4 workers)
    {
      name: 'forms-inputs',
      testMatch: [
        '**/half-star-ratings.test.js',
        '**/is-default-checkbox.test.js',
        '**/smart-defaults.test.js',
        '**/region-form-properties.test.js'
      ],
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
      },
      workers: getWorkerCount(4),
    },

    // Group 5: Debug/Utility Tests (SEQUENTIAL - 1 worker)
    {
      name: 'debug-utilities',
      testMatch: [
        '**/api-debug.test.js',
        '**/debug-page.test.js',
        '**/table-debug.test.js',
        '**/roaster-simple.test.js'
      ],
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
      },
      workers: 1, // Debug tests should run sequentially
    },
  ],

  /* Run your local dev server before starting the tests */
  webServer: [
    {
      command: process.env.CI 
        ? 'cd ../../.. && PYTHONPATH="$(pwd)/src" DATA_DIR="$(pwd)/test_data" uv run gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 4 --timeout 120 coffeejournal.wsgi:app'
        : 'cd ../../../ && PYTHONPATH=src uv run gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 4 --timeout 120 coffeejournal.wsgi:app',
      port: 5000,
      reuseExistingServer: !process.env.CI,
      timeout: process.env.CI ? 240 * 1000 : 120 * 1000, // Even longer startup timeout in CI
    },
    {
      command: 'npm run start',
      port: 3000,
      reuseExistingServer: !process.env.CI,
      timeout: process.env.CI ? 240 * 1000 : 120 * 1000, // Even longer startup timeout in CI
    }
  ],
});