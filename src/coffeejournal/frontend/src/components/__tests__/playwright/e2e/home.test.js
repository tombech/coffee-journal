import { test, expect } from '@playwright/test';
const TestDataManager = require('../../../../test-utils/testDataManager');
// Using semantic selectors - no need for helper functions that use brittle selectors

test.describe('Home Page', () => {
  let testData;

  test.beforeEach(async ({ page }, testInfo) => {
    testData = new TestDataManager(`home_${testInfo.title.replace(/\s+/g, '_')}`, 'http://localhost:5000/api', testInfo.project.name);
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

  test('displays welcome message and main sections', async ({ page }) => {
    await page.goto('/');
    
    // Check main heading and welcome message using semantic selectors
    await expect(page.locator('body')).toContainText('Welcome to your Coffee Journal!');
    await expect(page.getByRole('heading', { name: /recent.*brew.*sessions/i })).toBeVisible();
  });

  test('shows analytics sections when brew sessions exist', async ({ page }) => {
    // Create test data scenario to populate the home page
    const scenario = await testData.createTestScenario();
    
    await page.goto('/');
    
    // Wait for page to load and data to appear
    await expect(page.getByRole('heading', { name: 'My Coffee Journal' })).toBeVisible({ timeout: 2000 });
    
    // Should show analytics sections when data exists using semantic approach
    await expect(page.locator('body')).toContainText(/top.*brews/i, { timeout: 5000 });
    await expect(page.locator('body')).toContainText(/recent.*brew.*sessions/i, { timeout: 5000 });
    
    // Should show our test data somewhere on the page using semantic approach
    // Home page shows roaster and country in the "Top 5 Products" section, but not brew method
    await expect(page.locator('body')).toContainText(scenario.product.product_name);
    await expect(page.locator('body')).toContainText(scenario.roaster.name);
  });

  test('navigation header works correctly', async ({ page }) => {
    await page.goto('/');
    
    // Check navigation links using semantic selectors
    await expect(page.getByRole('link', { name: /home/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /brew.*sessions|all.*brews/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /settings/i })).toBeVisible();
    
    // Test navigation to settings using semantic actions
    await page.getByRole('link', { name: /settings/i }).click();
    await page.waitForURL('**/settings');
    await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible();
    
    // Navigate back to home
    await page.getByRole('link', { name: /home/i }).click();
    await page.waitForURL('/');
    await expect(page.locator('body')).toContainText('Welcome to your Coffee Journal!');
  });

  test('responsive design works on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.goto('/');
    
    // Main elements should still be visible on mobile
    await expect(page.locator('body')).toContainText('Welcome to your Coffee Journal!');
    await expect(page.getByRole('heading', { name: /recent.*brew.*sessions/i })).toBeVisible();
    
    // Navigation should still be accessible using semantic selectors
    await expect(page.getByRole('link', { name: /home/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /settings/i })).toBeVisible();
  });

  test('keyboard navigation works', async ({ page }) => {
    await page.goto('/');
    
    // Should be able to tab through navigation
    await page.keyboard.press('Tab');
    
    const homeLink = page.getByRole('link', { name: /home/i });
    await expect(homeLink).toBeFocused();
    
    await page.keyboard.press('Tab');
    const brewSessionsLink = page.getByRole('link', { name: /brew.*sessions|all.*brews/i });
    await expect(brewSessionsLink).toBeFocused();
    
    await page.keyboard.press('Tab');
    const settingsLink = page.getByRole('link', { name: /settings/i });
    await expect(settingsLink).toBeFocused();
    
    // Should be able to activate with Enter
    await page.keyboard.press('Enter');
    await expect(page).toHaveURL(/\/settings/);
  });
});