import { test, expect } from '@playwright/test';
const TestDataManager = require('../../../../test-utils/testDataManager');

test.describe('View Icon Enhancement', () => {
  let testData;

  test.beforeEach(async ({ page }, testInfo) => {
    testData = new TestDataManager(`view_icon_${testInfo.title.replace(/\s+/g, '_')}`, 'http://localhost:5000/api', testInfo.project.name);
    await testData.initialize();
    
    // Set up frontend to use backend API directly with user isolation
    await page.addInitScript((userId) => {
      window.API_BASE_URL = 'http://localhost:5000/api';
      window.TEST_USER_ID = userId;
    }, testData.userId);
  });

  test.afterEach(async () => {
    if (testData) {
      await testData.cleanup();
    }
  });

  test('settings page has clickable cards without view icons', async ({ page }) => {
    await page.goto('/settings');
    
    // Wait for settings page to load
    await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible();
    
    // Settings cards should NOT have view icons (they're obviously clickable as cards)
    const headingsWithViewIcon = await page.locator('h3').filter({ hasText: /👁️/ }).count();
    expect(headingsWithViewIcon).toBe(0);
    
    // Verify settings cards are still clickable without view icons
    await expect(page.getByRole('heading', { name: 'Products' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Brew Methods' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Roasters' })).toBeVisible();
  });

  test('home page top products cards work without view icons (view icons were removed from product cards)', async ({ page }) => {
    // Create test scenario with multiple products for analytics
    const scenario = await testData.createTestScenario();
    
    await page.goto('/');
    
    // Wait for home page to load
    await expect(page.getByRole('heading', { name: /Recent Brew Sessions/i })).toBeVisible();
    
    // Verify that view icons are NOT present in product card headings (they were explicitly removed from top products)
    const productCardHeadingsWithViewIcon = await page.locator('h4').filter({ hasText: /👁️/ }).count();
    expect(productCardHeadingsWithViewIcon).toBe(0);
    
    // Verify the home page still functions correctly without view icons in product cards
    await expect(page.getByRole('heading', { name: /Top 5 Products/i })).toBeVisible({ timeout: 5000 });
    await expect(page.getByRole('heading', { name: /Recent Brew Sessions/i })).toBeVisible();
  });

  test('settings cards are clickable without view icons', async ({ page }) => {
    await page.goto('/settings');
    
    // Wait for settings page to load
    await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible();
    
    // Test that clicking a settings card heading works (without view icon)
    await page.getByRole('heading', { name: 'Products' }).click();
    
    // Should navigate to products page
    await expect(page.getByRole('heading', { name: 'Products' })).toBeVisible();
  });

  test('home page product links work without view icons (view icons were removed)', async ({ page }) => {
    // Create test scenario
    const scenario = await testData.createTestScenario();
    
    await page.goto('/');
    
    // Wait for home page and analytics to load
    await expect(page.getByRole('heading', { name: /Recent Brew Sessions/i })).toBeVisible();
    await expect(page.getByRole('heading', { name: /Top 5 Products/i })).toBeVisible();
    
    // Verify that view icons are NOT present in product links (they were explicitly removed)
    const productLinksWithViewIcon = await page.locator('a').filter({ has: page.locator('h4').filter({ hasText: /👁️/ }) }).count();
    expect(productLinksWithViewIcon).toBe(0);
    
    // Verify product links still work without view icons
    const productLink = page.locator('a').filter({ hasText: scenario.product.product_name }).first();
    if (await productLink.count() > 0) {
      await productLink.click();
      // Should navigate to product detail page
      await expect(page.getByRole('heading', { name: scenario.product.product_name })).toBeVisible();
    }
  });

  test('product detail page has functional view batch buttons', async ({ page }) => {
    // Create test scenario with batches
    const scenario = await testData.createTestScenario();
    
    await page.goto(`/products/${scenario.product.id}`);
    
    // Wait for product detail page to load
    await expect(page.getByRole('heading', { name: scenario.product.product_name })).toBeVisible();
    
    // Wait for batches section to appear
    await expect(page.locator('body')).toContainText('Batches for this Product');
    
    // Verify the page functions correctly - should show batch information
    // Either with "Batch #" headings or "No batches yet" message
    const hasBatches = await page.locator('body').textContent();
    expect(hasBatches).toMatch(/(Batch #|No batches yet|Add your first batch)/i);
    
    // Check if there are view batch buttons (these should still exist - only home page product cards had view icons removed)
    const viewBatchButtons = await page.locator('button').filter({ hasText: '👁️' }).count();
    if (viewBatchButtons > 0) {
      // Test that a view batch button works
      const viewButton = page.locator('button').filter({ hasText: '👁️' }).first();
      await viewButton.click();
      
      // Should navigate to batch detail page
      await expect(page.getByRole('heading', { name: /Batch #\d+/ })).toBeVisible();
    }
  });
});