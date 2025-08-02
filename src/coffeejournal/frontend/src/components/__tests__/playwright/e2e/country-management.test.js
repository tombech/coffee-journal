import { test, expect } from '@playwright/test';
const TestDataManager = require('../../../../test-utils/testDataManager');

test.describe('Country Management', () => {
  // Merged test: combines country display, creation, editing, navigation, and region count
  test('Countries - complete management workflow (create, edit, display, regions)', async ({ page }) => {
    const testData = new TestDataManager(`country_management_${Date.now()}`, 'http://localhost:5000/api');
    await testData.initialize();
    
    await page.addInitScript((userId) => {
      window.API_BASE_URL = 'http://localhost:5000/api';
      window.TEST_USER_ID = userId;
    }, testData.userId);
    
    try {
      // 1. Test country creation
      await page.goto('/settings/countries');
      await expect(page.getByRole('heading', { name: 'Countries' })).toBeVisible();
      
      const countryName = `Test Country ${Date.now()}`;
      await page.getByTestId('add-item-btn').click();
      await expect(page.getByLabel('Name *')).toBeVisible();
      
      await page.getByLabel('Name *').fill(countryName);
      await page.getByLabel('Description').fill('Test country for management workflow');
      await page.getByTestId('create-country-btn').click();
      
      await expect(page.locator('body')).toContainText(/created.*successfully/i);
      
      // 2. Verify country displays in list
      await expect(page.getByRole('table')).toBeVisible();
      await expect(page.getByRole('table')).toContainText(countryName);
      
      // 3. Test country editing and region management
      const countryRow = page.getByRole('row').filter({ hasText: countryName });
      await countryRow.getByRole('button', { name: /edit.*regions/i }).click();
      await expect(page.locator('body')).toContainText(`Edit Country:`);
      
      // 4. Update country details
      const updatedDescription = `Updated description ${Date.now()}`;
      await page.getByLabel(/description/i).fill(updatedDescription);
      await page.getByRole('button', { name: /save.*country/i }).click();
      await expect(page.getByLabel(/description/i)).toHaveValue(updatedDescription);
      
      // 5. Add region to country
      const regionName = `Test Region ${Date.now()}`;
      await page.getByRole('button', { name: 'Add Region' }).click();
      await expect(page.getByLabel('Region Name *')).toBeVisible();
      
      await page.getByTestId('region-name-input').fill(regionName);
      await page.getByTestId('region-description-input').fill('Test region description');
      await page.getByTestId('save-region-button').click();
      
      await expect(page.locator('body')).toContainText(/region.*created.*successfully/i);
      await expect(page.getByTestId('region-list')).toContainText(regionName);
      
      // 6. Edit the region
      const regionRow = page.getByTestId('region-item').filter({ hasText: regionName });
      await regionRow.getByRole('button', { name: /edit/i }).click();
      
      const updatedRegionName = `Updated ${regionName}`;
      await page.getByTestId('region-name-input').fill(updatedRegionName);
      await page.getByTestId('save-region-button').click();
      
      await expect(page.locator('body')).toContainText(/region.*updated.*successfully/i);
      await expect(page.getByTestId('region-list')).toContainText(updatedRegionName);
      
      // 7. Test navigation back to countries list
      await page.getByRole('button', { name: /back.*countries/i }).click();
      await expect(page).toHaveURL(/\/settings\/countries$/);
      await expect(page.getByRole('heading', { name: 'Countries' })).toBeVisible();
      
      // 8. Verify region count is shown (country should show it has regions)
      await expect(page.getByRole('table')).toContainText(countryName);
      
    } finally {
      await testData.cleanup();
    }
  });

  // Merged test: region deletion and country isolation
  test('Region deletion and country isolation verification', async ({ page }) => {
    const testData = new TestDataManager(`country_isolation_${Date.now()}`, 'http://localhost:5000/api');
    await testData.initialize();
    
    await page.addInitScript((userId) => {
      window.API_BASE_URL = 'http://localhost:5000/api';
      window.TEST_USER_ID = userId;
    }, testData.userId);
    
    try {
      // Create two countries for isolation testing
      await page.goto('/settings/countries');
      
      const country1Name = `Country One ${Date.now()}`;
      const country2Name = `Country Two ${Date.now()}`;
      
      // Create first country with region
      await page.getByTestId('add-item-btn').click();
      await page.getByLabel('Name *').fill(country1Name);
      await page.getByTestId('create-country-btn').click();
      await expect(page.locator('body')).toContainText(/created.*successfully/i);
      
      const country1Row = page.getByRole('row').filter({ hasText: country1Name });
      await country1Row.getByRole('button', { name: /edit.*regions/i }).click();
      await expect(page.locator('body')).toContainText(`Edit Country:`);
      
      const region1Name = `Region One ${Date.now()}`;
      await page.getByRole('button', { name: 'Add Region' }).click();
      await page.getByTestId('region-name-input').fill(region1Name);
      await page.getByTestId('save-region-button').click();
      await expect(page.locator('body')).toContainText(/region.*created.*successfully/i);
      
      // Test region deletion - handle browser confirmation dialog
      const regionRow = page.getByTestId('region-item').filter({ hasText: region1Name });
      
      // Set up dialog handler before clicking delete
      page.on('dialog', async dialog => {
        await dialog.accept();
      });
      
      await regionRow.getByRole('button', { name: /remove/i }).click();
      
      await expect(page.locator('body')).toContainText(/region.*deleted.*successfully/i);
      await expect(page.getByTestId('no-regions-message')).toBeVisible();
      
      // Go back and create second country
      await page.getByRole('button', { name: /back.*countries/i }).click();
      
      await page.getByTestId('add-item-btn').click();
      await page.getByLabel('Name *').fill(country2Name);
      await page.getByTestId('create-country-btn').click();
      await expect(page.locator('body')).toContainText(/created.*successfully/i);
      
      // Edit second country and add region
      const country2Row = page.getByRole('row').filter({ hasText: country2Name });
      await country2Row.getByRole('button', { name: /edit.*regions/i }).click();
      
      const region2Name = `Region Two ${Date.now()}`;
      await page.getByRole('button', { name: 'Add Region' }).click();
      await page.getByTestId('region-name-input').fill(region2Name);
      await page.getByTestId('save-region-button').click();
      await expect(page.locator('body')).toContainText(/region.*created.*successfully/i);
      
      // Verify isolation - should only see region2, not region1
      await expect(page.getByTestId('region-list')).toContainText(region2Name);
      await expect(page.getByTestId('region-list')).not.toContainText(region1Name);
      
    } finally {
      await testData.cleanup();
    }
  });
});