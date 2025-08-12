import { test, expect } from '@playwright/test';
const TestDataManager = require('../../../../test-utils/testDataManager');
// Using semantic selectors - no need for helper functions that use brittle selectors

test.describe('Settings Page', () => {
  let testData;

  test.beforeEach(async ({ page }, testInfo) => {
    testData = new TestDataManager(`settings_${testInfo.title.replace(/\s+/g, '_')}`, 'http://localhost:5000/api', testInfo.project.name);
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

  test('displays main settings page with all navigation cards', async ({ page }) => {
    await page.goto('/settings');
    
    // Use semantic selectors - check for main heading
    await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible();
    await expect(page.locator('body')).toContainText('Manage your coffee journal configuration and data.');
    
    // Check that all main setting categories are present using data-testid for reliability
    const expectedSettings = [
      'Products',
      'Brew Methods', 
      'Recipes',
      'Bean Types',
      'Roasters',
      'Countries',
      'Grinders',
      'Filters', 
      'Kettles',
      'Scales',
      'Decaf Methods',
      'Brewers',
      'Portafilters',
      'Baskets',
      'Tampers',
      'WDT Tools',
      'Leveling Tools'
    ];
    
    for (const setting of expectedSettings) {
      // Convert to testid format: lowercase, replace spaces with dashes
      const testId = `settings-link-${setting.toLowerCase().replace(/\s+/g, '-')}`;
      await expect(page.getByTestId(testId)).toBeVisible();
    }
  });

  test('can navigate to roaster management', async ({ page }) => {
    await page.goto('/settings');
    
    // Click on roasters card using semantic selector and proper wait
    await page.getByRole('link', { name: /roasters/i }).click();
    await page.waitForURL('**/settings/roasters');
    
    // Should show roasters page
    await expect(page.getByRole('heading', { name: 'Roasters' })).toBeVisible();
  });

  test('setting cards are keyboard accessible', async ({ page }) => {
    await page.goto('/settings');
    
    // Products link should be focusable
    const productsLink = page.getByRole('link', { name: /products/i });
    await productsLink.focus();
    await expect(productsLink).toBeFocused();
    
    // Should be able to activate with Enter
    await page.keyboard.press('Enter');
    await expect(page).toHaveURL(/\/products/);
  });
});