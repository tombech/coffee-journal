import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './src/components/__tests__/playwright',
  // Enable parallel execution for better performance
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,  // No retries locally for faster debugging
  // Allow more workers but keep reasonable for hobby project
  workers: process.env.CI ? 2 : 2,
  reporter: [
    ['list'] // Just console output, no HTML server for speed
  ],
  // Remove global setup - we'll handle data per test
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    // Very short timeouts - local operations should be instant
    actionTimeout: 1000,
    navigationTimeout: 2000,
    // Global test timeout - fail fast
    timeout: 10000,
    // Add CSS to disable webpack overlay that blocks clicks
    extraHTTPHeaders: {
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }
  },

  projects: [
    {
      name: 'e2e',
      testMatch: '**/e2e/**/*.test.js',
      use: { 
        ...devices['Desktop Chrome'],
        // Very short timeout for E2E tests - local CRUD should be instant
        timeout: 10000
      },
    },
  ],

  // Run both backend and frontend servers
  webServer: [
    {
      command: 'cd ../../.. && PYTHONPATH=src uv run gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 4 --timeout 120 coffeejournal.wsgi:app',
      url: 'http://localhost:5000/api/countries',
      reuseExistingServer: !process.env.CI,
      timeout: 30 * 1000,  // Shorter backend startup timeout
      env: {
        PYTHONPATH: 'src'
      }
    },
    {
      command: 'npm start',
      url: 'http://localhost:3000',
      reuseExistingServer: !process.env.CI, // Reuse existing server for speed
      timeout: 30 * 1000,  // Shorter frontend startup timeout
    }
  ],
});