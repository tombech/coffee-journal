import { test, expect } from '@playwright/test';
import { TestDataManager } from '../helpers/testDataManager';

test.describe('Coffee Age Display', () => {
  let testData;

  test.beforeEach(async ({ page }) => {
    testData = new TestDataManager('coffee_age_display');
    await testData.initialize();
    
    await page.addInitScript((userId) => {
      window.TEST_USER_ID = userId;
    }, testData.userId);
  });

  test.afterEach(async () => {
    if (testData) {
      await testData.cleanup();
    }
  });

  test('displays coffee age in brew session table', async ({ page }) => {
    // Create test scenario with known roast date
    const scenario = await testData.createTestScenario({
      product: {
        product_name: `Test Coffee Age Product ${testData.testId}`,
        roaster: `Test Roaster ${testData.testId}`,
        bean_type: ['Arabica'],
        country: 'Ethiopia'
      },
      batch: {
        roast_date: '2024-12-01', // About 8 months ago - should show as weeks
        amount_grams: 250,
        price: 24.99
      },
      brewSession: {
        brew_method: `V60 ${testData.testId}`,
        amount_coffee_grams: 20,
        amount_water_grams: 320,
        notes: `Brew session for coffee age testing ${testData.testId}`
      }
    });

    // Navigate to brew sessions page
    await page.goto('/brew_sessions');
    await expect(page.getByRole('heading', { name: 'All Brew Sessions' })).toBeVisible();

    // Wait for brew sessions table to load
    await expect(page.getByRole('table')).toBeVisible();

    // Check that coffee age column header exists
    await expect(page.locator('th').filter({ hasText: '🕒' })).toBeVisible();

    // Look for our specific brew session and verify coffee age is displayed
    const sessionRow = page.locator('tr').filter({ hasText: scenario.brewSession.notes });
    await expect(sessionRow).toBeVisible();

    // Find the coffee age cell in this row
    const coffeeAgeCell = sessionRow.locator('[data-testid="brew-session-coffee-age"]');
    await expect(coffeeAgeCell).toBeVisible();

    // Verify coffee age is displayed (should be weeks since roast date is months ago)
    const coffeeAgeText = await coffeeAgeCell.textContent();
    expect(coffeeAgeText).toMatch(/\d+\s+weeks?/); // Should match "X weeks" or "X week"
    expect(coffeeAgeText).not.toBe('-'); // Should not be empty
  });

  test('displays coffee age in shot table', async ({ page }) => {
    // Create test scenario for shots
    const scenario = await testData.createTestScenario({
      product: {
        product_name: `Test Shot Coffee Age Product ${testData.testId}`,
        roaster: `Test Shot Roaster ${testData.testId}`,
        bean_type: ['Arabica'],
        country: 'Colombia'
      },
      batch: {
        roast_date: '2024-11-15', // A few months ago - should show as weeks
        amount_grams: 250,
        price: 19.99
      }
    });

    // Create a brewer for the shot
    await page.goto('/settings');
    await page.getByRole('link', { name: 'Brewers' }).click();
    
    await page.getByTestId('create-item-btn').click();
    await page.getByLabel(/name/i).fill(`Test Shot Brewer ${testData.testId}`);
    await page.getByTestId('submit-btn').click();
    
    // Wait for brewer to be created and get its data
    await expect(page.getByRole('table')).toContainText(`Test Shot Brewer ${testData.testId}`);

    // Navigate to shots page and create a shot
    await page.goto('/shots');
    await expect(page.getByRole('heading', { name: 'All Shots' })).toBeVisible();

    // Create a new shot using the filter controls
    await page.getByTitle('New Shot').click();
    
    // Fill in shot form
    await page.getByLabel(/dose.*grams/i).fill('18');
    await page.getByLabel(/yield.*grams/i).fill('36');
    
    // Select the product and batch we created
    const productSelect = page.getByLabel(/product/i);
    await productSelect.selectOption({ label: new RegExp(scenario.product.product_name) });
    
    const batchSelect = page.getByLabel(/batch/i);
    await batchSelect.selectOption({ value: scenario.batch.id.toString() });
    
    // Select the brewer
    const brewerSelect = page.getByLabel(/brewer/i);
    await brewerSelect.selectOption({ label: new RegExp(`Test Shot Brewer ${testData.testId}`) });
    
    // Add notes to identify our shot
    await page.getByLabel(/notes/i).fill(`Shot for coffee age testing ${testData.testId}`);
    
    // Submit the shot
    await page.getByRole('button', { name: /save|submit/i }).click();
    
    // Wait for shot to be created and form to disappear
    await expect(page.getByRole('heading', { name: 'Add New Shot' })).not.toBeVisible();

    // Check that coffee age column header exists in shots table
    await expect(page.locator('th').filter({ hasText: '🕒' })).toBeVisible();

    // Look for our specific shot and verify coffee age is displayed
    const shotRow = page.locator('tr').filter({ hasText: `Shot for coffee age testing ${testData.testId}` });
    await expect(shotRow).toBeVisible();

    // Find the coffee age cell in this row
    const coffeeAgeCell = shotRow.locator('[data-testid="shot-coffee-age"]');
    await expect(coffeeAgeCell).toBeVisible();

    // Verify coffee age is displayed (should be weeks since roast date is months ago)
    const coffeeAgeText = await coffeeAgeCell.textContent();
    expect(coffeeAgeText).toMatch(/\d+\s+weeks?/); // Should match "X weeks" or "X week"
    expect(coffeeAgeText).not.toBe('-'); // Should not be empty
  });

  test('shows dash when coffee age cannot be calculated', async ({ page }) => {
    // Create a product and batch without roast date
    const scenario = await testData.createTestScenario({
      product: {
        product_name: `No Age Coffee Product ${testData.testId}`,
        roaster: `No Age Roaster ${testData.testId}`,
        bean_type: ['Robusta']
      },
      batch: {
        // No roast_date provided
        amount_grams: 200,
        price: 15.00
      },
      brewSession: {
        brew_method: `AeroPress ${testData.testId}`,
        amount_coffee_grams: 15,
        amount_water_grams: 240,
        notes: `No age brew session ${testData.testId}`
      }
    });

    // Navigate to brew sessions page
    await page.goto('/brew_sessions');
    await expect(page.getByRole('heading', { name: 'All Brew Sessions' })).toBeVisible();

    // Look for our specific brew session
    const sessionRow = page.locator('tr').filter({ hasText: scenario.brewSession.notes });
    await expect(sessionRow).toBeVisible();

    // Find the coffee age cell and verify it shows dash for missing data
    const coffeeAgeCell = sessionRow.locator('[data-testid="brew-session-coffee-age"]');
    await expect(coffeeAgeCell).toBeVisible();
    await expect(coffeeAgeCell).toContainText('-');
  });

  test('coffee age column is sortable', async ({ page }) => {
    // Create multiple brew sessions with different roast dates
    const scenarios = [];
    for (let i = 0; i < 3; i++) {
      const daysAgo = (i + 1) * 30; // 30, 60, 90 days ago
      const roastDate = new Date();
      roastDate.setDate(roastDate.getDate() - daysAgo);
      
      const scenario = await testData.createTestScenario({
        product: {
          product_name: `Sort Test Coffee ${i + 1} ${testData.testId}`,
          roaster: `Sort Test Roaster ${i + 1}`,
          bean_type: ['Arabica']
        },
        batch: {
          roast_date: roastDate.toISOString().split('T')[0], // YYYY-MM-DD format
          amount_grams: 250,
          price: 20.00
        },
        brewSession: {
          brew_method: 'V60',
          amount_coffee_grams: 20,
          amount_water_grams: 320,
          notes: `Sort test session ${i + 1} ${testData.testId}`
        }
      });
      scenarios.push(scenario);
    }

    // Navigate to brew sessions page
    await page.goto('/brew_sessions');
    await expect(page.getByRole('heading', { name: 'All Brew Sessions' })).toBeVisible();
    await expect(page.getByRole('table')).toBeVisible();

    // Click on coffee age column header to sort
    const coffeeAgeHeader = page.locator('th').filter({ hasText: '🕒' });
    await coffeeAgeHeader.click();

    // Wait a moment for sorting to apply
    await page.waitForTimeout(500);

    // Verify that sort icons appear (indicating sorting is working)
    // The header should show either ↑ or ↓ to indicate sort direction
    const headerText = await coffeeAgeHeader.textContent();
    expect(headerText).toMatch(/[↑↓]/);
  });

  test('coffee age displays different formats correctly', async ({ page }) => {
    // Create test scenarios with specific age ranges
    const testCases = [
      { daysAgo: 0, expectedPattern: /same day/, label: 'same day' },
      { daysAgo: 1, expectedPattern: /1 day/, label: '1 day' },
      { daysAgo: 5, expectedPattern: /5 days/, label: '5 days' },
      { daysAgo: 14, expectedPattern: /2 weeks?/, label: '2 weeks' }
    ];

    const scenarios = [];
    for (const testCase of testCases) {
      const roastDate = new Date();
      roastDate.setDate(roastDate.getDate() - testCase.daysAgo);
      
      const scenario = await testData.createTestScenario({
        product: {
          product_name: `${testCase.label} Coffee ${testData.testId}`,
          roaster: `Format Test Roaster`,
          bean_type: ['Arabica']
        },
        batch: {
          roast_date: roastDate.toISOString().split('T')[0],
          amount_grams: 250,
          price: 20.00
        },
        brewSession: {
          brew_method: 'V60',
          amount_coffee_grams: 20,
          amount_water_grams: 320,
          notes: `${testCase.label} test session ${testData.testId}`
        }
      });
      scenarios.push({ ...scenario, ...testCase });
    }

    // Navigate to brew sessions page
    await page.goto('/brew_sessions');
    await expect(page.getByRole('heading', { name: 'All Brew Sessions' })).toBeVisible();

    // Check each scenario's coffee age display
    for (const scenario of scenarios) {
      const sessionRow = page.locator('tr').filter({ hasText: scenario.brewSession.notes });
      await expect(sessionRow).toBeVisible();

      const coffeeAgeCell = sessionRow.locator('[data-testid="brew-session-coffee-age"]');
      await expect(coffeeAgeCell).toBeVisible();

      const coffeeAgeText = await coffeeAgeCell.textContent();
      expect(coffeeAgeText).toMatch(scenario.expectedPattern);
    }
  });
});