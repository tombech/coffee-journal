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

  test('home page product headings have view icons', async ({ page }) => {
    // Create test scenario with multiple products for analytics
    const scenario = await testData.createTestScenario();
    
    await page.goto('/');
    
    // Wait for home page to load
    await expect(page.getByRole('heading', { name: 'Welcome to your Coffee Journal!' })).toBeVisible();
    
    // Wait for product analytics to appear
    await expect(page.getByRole('heading', { name: /Top 5 Products/i })).toBeVisible();
    
    // Check if there are product headings with view icons
    const productHeadingsWithViewIcon = await page.locator('h4').filter({ hasText: /👁️/ }).count();
    
    // Should have at least 1 product heading with view icon
    expect(productHeadingsWithViewIcon).toBeGreaterThanOrEqual(1);
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

  test('view icon enhances visual accessibility', async ({ page }) => {
    // Create test scenario
    const scenario = await testData.createTestScenario();
    
    await page.goto('/');
    
    // Wait for home page and analytics to load
    await expect(page.getByRole('heading', { name: 'Welcome to your Coffee Journal!' })).toBeVisible();
    await expect(page.getByRole('heading', { name: /Top 5 Products/i })).toBeVisible();
    
    // Find a product link with view icon
    const productLink = page.locator('a').filter({ has: page.locator('h4').filter({ hasText: /👁️/ }) }).first();
    
    if (await productLink.count() > 0) {
      // Test that the product link is clickable and obvious
      await expect(productLink).toBeVisible();
      
      // Click the product link
      await productLink.click();
      
      // Should navigate to product detail page
      await expect(page.getByRole('heading', { name: scenario.product.product_name })).toBeVisible();
    }
  });

  test('product detail page batch headings have view icons', async ({ page }) => {
    // Create test scenario with batches
    const scenario = await testData.createTestScenario();
    
    await page.goto(`/products/${scenario.product.id}`);
    
    // Wait for product detail page to load
    await expect(page.getByRole('heading', { name: scenario.product.product_name })).toBeVisible();
    
    // Wait for batches section to appear
    await expect(page.locator('body')).toContainText('Batches for this Product');
    
    // Wait for the API call to complete and batches to render
    // Use a more specific wait that ensures the batch data is actually loaded
    await page.waitForFunction(() => {
      const batchElements = document.querySelectorAll('h4');
      return Array.from(batchElements).some(h => h.textContent.includes('Batch #'));
    }, { timeout: 10000 });
    
    // Now check for batch headings with view icons
    const batchHeadingsWithViewIcon = await page.locator('h4').filter({ hasText: /👁️.*Batch #/ }).count();
    
    // Should have at least 1 batch heading with view icon
    expect(batchHeadingsWithViewIcon).toBeGreaterThanOrEqual(1);
    
    // Test that clicking a batch heading with view icon works
    const batchLink = page.locator('a').filter({ has: page.locator('h4').filter({ hasText: /👁️.*Batch #/ }) }).first();
    if (await batchLink.count() > 0) {
      await batchLink.click();
      
      // Should navigate to batch detail page
      await expect(page.getByRole('heading', { name: /Batch #\d+/ })).toBeVisible();
    }
  });
});