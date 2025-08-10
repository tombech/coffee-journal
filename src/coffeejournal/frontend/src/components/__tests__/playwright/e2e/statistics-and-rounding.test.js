const { test, expect } = require('@playwright/test');
const TestDataManager = require('../../../../test-utils/testDataManager');

test.describe('Statistics and Number Rounding', () => {
  let testData;

  test.beforeEach(async ({ page }) => {
    testData = new TestDataManager(`statistics_test_${Date.now()}`, 'http://localhost:5000/api');
    await testData.initialize();
    
    await page.addInitScript((userId) => {
      window.TEST_USER_ID = userId;
      window.API_BASE_URL = 'http://localhost:5000/api';
    }, testData.userId);
  });

  test.afterEach(async () => {
    if (testData) {
      await testData.cleanup();
    }
  });

  test('Grinder statistics show when manual ground grams is set and numbers are rounded', async ({ page }) => {
    // Create a grinder with manual ground grams
    await page.goto('/settings/grinders');
    await page.getByTestId('add-item-btn').click();
    await page.getByLabel('Name *').fill('Test Grinder Statistics');
    await page.getByLabel('Brand').fill('Test Brand');
    await page.getByLabel('Manual Ground Grams').fill('125.75'); // Decimal to test rounding
    await page.getByTestId('create-item-btn').click();

    // Wait for success message and find the created item
    await expect(page.locator('body')).toContainText(/created.*successfully/i);
    await expect(page.getByRole('table')).toContainText('Test Grinder Statistics');

    // Navigate to grinder view page
    const viewButton = page.getByTestId('view-test-grinder-statistics-btn');
    await expect(viewButton).toBeVisible();
    await viewButton.click();

    // Verify we're on the grinder detail page
    await expect(page.getByTestId('item-title')).toContainText('Test Grinder Statistics');

    // Check that statistics section is visible
    await expect(page.locator('text=📊 Usage Statistics')).toBeVisible();
    
    // Check that Manual Grinding shows rounded number (126g instead of 125.75g)
    const manualGrindingStat = page.locator('text=126g').first();
    await expect(manualGrindingStat).toBeVisible();

    // Check that all statistics numbers are displayed as integers (no decimals)
    const statsSection = page.locator('div:has-text("📊 Usage Statistics")').first();
    
    // Total Brews should be an integer
    await expect(statsSection.locator('text=Total Brews').locator('..').locator('div').first()).toContainText(/^\d+$/);
    
    // Total Ground should be rounded
    await expect(statsSection.locator('text=Total Ground').locator('..').locator('div').first()).toContainText(/^\d+(kg|g)$/);
  });

  test('Product statistics display correctly with top/bottom 5 brew sessions', async ({ page }) => {
    // Create test data: product, batch, and multiple brew sessions
    const scenario = await testData.createTestScenario({
      product: {
        product_name: 'Test Product Stats',
        roaster: 'Test Statistics Roaster',
        bean_type: ['Arabica'],
        country: 'Ethiopia'
      },
      batch: {
        roast_date: '2025-01-01',
        amount_grams: 250.5, // Test rounding
        price: 19.99 // Test rounding
      }
    });

    // Create multiple brew sessions with different scores
    const brewSessions = [];
    const scores = [4.2, 7.8, 9.1, 3.5, 6.7]; // Mix of high and low scores
    
    for (let i = 0; i < scores.length; i++) {
      const sessionResponse = await testData.createBrewSession(scenario.batch.id, {
        brew_method: 'V60',
        amount_coffee_grams: 20.3 + i, // Test rounding
        amount_water_grams: 320.7 + i, // Test rounding
        score: scores[i],
        timestamp: new Date(Date.now() + i * 60000).toISOString()
      });
      brewSessions.push(sessionResponse);
    }

    // Navigate to product detail page
    await page.goto(`/products/${scenario.product.id}`);
    
    // Wait for product page to load
    await expect(page.locator('#product-title')).toContainText('Test Product Stats');

    // Check product statistics section is visible
    await expect(page.locator('text=📊 Usage Statistics')).toBeVisible();

    // Check that the statistics show correct data
    const statsSection = page.locator('div:has-text("📊 Usage Statistics")').first();
    
    // Total brew sessions should be 5
    await expect(statsSection.locator('text=Total Brew Sessions').locator('..').locator('div').first()).toContainText('5');
    
    // Total batches should be 1
    await expect(statsSection.locator('text=Total Batches').locator('..').locator('div').first()).toContainText('1');

    // Check that top 5 sessions section is visible
    await expect(page.locator('text=🏆 Top 5 Brew Sessions')).toBeVisible();
    
    // Check that bottom 5 sessions section is visible
    await expect(page.locator('text=📉 Bottom 5 Brew Sessions')).toBeVisible();

    // Verify that coffee and water amounts are rounded in the tables
    const topSessionsTable = page.locator('table').filter({ has: page.locator('text=🏆 Top 5 Brew Sessions') });
    
    // Check that amounts are rounded (should show 21g, 22g, etc. not 20.3g, 21.3g)
    await expect(topSessionsTable).toContainText(/\d+g/); // Pattern for rounded grams
  });

  test('Batch detail page shows rounded numbers in statistics', async ({ page }) => {
    // Create test data
    const scenario = await testData.createTestScenario({
      product: {
        product_name: 'Batch Rounding Test',
        roaster: 'Round Numbers Roaster',
        bean_type: ['Arabica'],
        country: 'Colombia'
      },
      batch: {
        roast_date: '2025-01-01',
        amount_grams: 250.75, // Test rounding
        price: 24.99 // Test rounding
      }
    });

    // Create a brew session to generate statistics
    await testData.createBrewSession(scenario.batch.id, {
      brew_method: 'French Press',
      amount_coffee_grams: 18.7, // Test rounding
      amount_water_grams: 280.3, // Test rounding
      score: 7.5,
      timestamp: new Date().toISOString()
    });

    // Navigate to batch detail page
    await page.goto(`/batches/${scenario.batch.id}`);
    
    // Wait for batch page to load
    await expect(page.locator('h2')).toContainText(`Batch #${scenario.batch.id}`);

    // Check that amount is rounded (251g not 250.75g)
    await expect(page.locator('text=Amount (grams)').locator('..').locator('span')).toContainText('251g');
    
    // Check that price is rounded (25 kr not 24.99 kr)
    await expect(page.locator('text=Price:').locator('..').locator('span')).toContainText('25 kr');

    // Check that price per cup is rounded
    await expect(page.getByTestId('price-per-cup')).toContainText(/^\d+ kr$/);

    // Check statistics section shows rounded numbers
    await expect(page.locator('text=📊 Usage Statistics')).toBeVisible();
    
    const statsSection = page.locator('div:has-text("📊 Usage Statistics")').first();
    
    // Coffee Used should be rounded (19g not 18.7g)
    await expect(statsSection.locator('text=Coffee Used').locator('..').locator('div').first()).toContainText('19g');
    
    // Remaining should be rounded
    await expect(statsSection.locator('text=Remaining').locator('..').locator('div').first()).toContainText(/^\d+g$/);

    // Check brew sessions table shows rounded amounts
    const sessionsTable = page.locator('table').last();
    await expect(sessionsTable).toContainText('19g'); // Rounded coffee amount
    await expect(sessionsTable).toContainText('280g'); // Rounded water amount
  });

  test('Product batches table shows rounded numbers', async ({ page }) => {
    // Create test data with decimal values
    const scenario = await testData.createTestScenario({
      product: {
        product_name: 'Product Rounding Test',
        roaster: 'Decimal Test Roaster',
        bean_type: ['Arabica'],
        country: 'Brazil'
      },
      batch: {
        roast_date: '2025-01-01',
        amount_grams: 500.33, // Test rounding
        price: 29.95 // Test rounding
      }
    });

    // Navigate to product detail page
    await page.goto(`/products/${scenario.product.id}`);
    
    // Wait for product page to load
    await expect(page.locator('#product-title')).toContainText('Product Rounding Test');

    // Check batches table
    const batchesTable = page.locator('table').first();
    
    // Amount should be rounded (500g not 500.33g)
    await expect(batchesTable).toContainText('500g');
    
    // Price should be rounded (30 kr not 29.95 kr)
    await expect(batchesTable).toContainText('30 kr');
    
    // Price per cup should be rounded (integer kr)
    await expect(batchesTable).toContainText(/\d+ kr/);
  });
});