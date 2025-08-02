import { test, expect } from '@playwright/test';
const TestDataManager = require('../../../../test-utils/testDataManager');
// Simplified roaster test to debug form submission issues

test.describe('Roaster Management - Simple Test', () => {
  let testData;

  test.beforeEach(async ({ page }, testInfo) => {
    testData = new TestDataManager(`simple_roaster_${testInfo.title.replace(/\s+/g, '_')}`, 'http://localhost:5000/api', testInfo.project.name);
    await testData.initialize();
    
    // Set up frontend to use backend API directly
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

  test('can add new roaster using proper form submission', async ({ page }) => {
    await page.goto('/settings/roasters');
    
    // Verify page loaded
    await expect(page.getByRole('heading', { name: 'Roasters' })).toBeVisible();
    
    // Click add button using semantic selector
    await page.getByRole('button', { name: 'Add Roaster' }).click();
    
    // Wait for form to appear
    await expect(page.getByRole('heading', { name: 'Add New Roaster' })).toBeVisible();
    
    // Fill out form - just name is required
    const roasterName = `Simple Test Roaster ${testData.testId}`;
    await page.getByLabel('Name *:').fill(roasterName);
    
    // Add a small delay before clicking submit to ensure form is ready
    await page.waitForTimeout(100);
    
    // Submit form - the button has aria-label 'Create'
    await page.getByTestId('create-item-btn').click();
    
    // Wait a bit for form processing
    await page.waitForTimeout(500);
    
    // Check if form closed (success indication)
    await expect(page.getByRole('heading', { name: 'Add New Roaster' })).not.toBeVisible();
    
    // New roaster should be visible in page content
    await expect(page.locator('body')).toContainText(roasterName);
  });
});