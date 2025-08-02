const { test, expect } = require('@playwright/test');
const TestDataManager = require('../../../../test-utils/testDataManager');

test.describe('Region Form Common Properties', () => {
  // Merged test: combines form properties validation, creation with all fields, editing, and validation
  test('Region forms - complete workflow (properties, create, edit, validate)', async ({ page }) => {
    const testData = new TestDataManager(`region_form_complete_${Date.now()}`, 'http://localhost:5000/api');
    await testData.initialize();
    
    await page.addInitScript((userId) => {
      window.TEST_USER_ID = userId;
      window.API_BASE_URL = 'http://localhost:5000/api';
    }, testData.userId);
    
    try {
      // First create a country to work with
      await page.goto('/settings/countries');
      
      const countryName = `Test Country ${Date.now()}`;
      await page.getByTestId('add-item-btn').click();
      await page.getByLabel('Name *').fill(countryName);
      await page.getByLabel('Description').fill('Test country for region testing');
      await page.getByTestId('create-country-btn').click();
      
      await expect(page.locator('body')).toContainText(/created.*successfully/i);
      
      // Navigate to country edit page
      const countryRow = page.getByRole('row').filter({ hasText: countryName });
      await countryRow.getByRole('button', { name: /edit/i }).click();
      await expect(page.locator('body')).toContainText(`Edit Country:`);
      
      // 1. Test region form includes all common properties
      await page.getByRole('button', { name: 'Add Region' }).click();
      await expect(page.getByLabel('Region Name *')).toBeVisible();
      
      // Verify all form fields are present
      await expect(page.getByLabel('Region Name *')).toBeVisible();
      await expect(page.locator('#region-short-form')).toBeVisible();
      await expect(page.locator('#region-description')).toBeVisible();
      await expect(page.locator('#region-notes')).toBeVisible();
      await expect(page.locator('#region-url')).toBeVisible();
      await expect(page.locator('#region-image-url')).toBeVisible();
      await expect(page.getByLabel(/set as default/i)).toBeVisible();
      
      // 2. Create region with all properties filled
      const regionName = `Comprehensive Region ${Date.now()}`;
      await page.getByTestId('region-name-input').fill(regionName);
      await page.getByTestId('region-short-form-input').fill('CR');
      await page.getByTestId('region-description-input').fill('A comprehensive test region with all properties');
      await page.getByTestId('region-notes-input').fill('Detailed notes about this test region');
      await page.getByTestId('region-url-input').fill('https://example.com/region');
      await page.getByTestId('region-image-url-input').fill('https://example.com/region.jpg');
      await page.getByLabel(/set as default/i).check();
      
      await page.getByTestId('save-region-button').click();
      await expect(page.locator('body')).toContainText(/region.*created.*successfully/i);
      await expect(page.getByTestId('region-list')).toContainText(regionName);
      
      // 3. Edit the region and modify properties
      const regionRow = page.getByTestId('region-item').filter({ hasText: regionName });
      await regionRow.getByRole('button', { name: /edit/i }).click();
      
      await expect(page.getByTestId('region-name-input')).toHaveValue(regionName);
      
      // Modify properties
      const updatedName = `Updated ${regionName}`;
      await page.getByTestId('region-name-input').fill(updatedName);
      await page.getByTestId('region-description-input').fill('Updated comprehensive description');
      await page.getByTestId('region-short-form-input').fill('UCR');
      
      await page.getByTestId('save-region-button').click();
      await expect(page.locator('body')).toContainText(/region.*updated.*successfully/i);
      await expect(page.getByTestId('region-list')).toContainText(updatedName);
      
    } finally {
      await testData.cleanup();
    }
  });

  // Test region deletion workflow
  test('Region deletion workflow with confirmation', async ({ page }) => {
    const testData = new TestDataManager(`region_deletion_${Date.now()}`, 'http://localhost:5000/api');
    await testData.initialize();
    
    await page.addInitScript((userId) => {
      window.TEST_USER_ID = userId;
      window.API_BASE_URL = 'http://localhost:5000/api';
    }, testData.userId);
    
    try {
      // Create country and region for deletion test
      await page.goto('/settings/countries');
      
      const countryName = `Delete Test Country ${Date.now()}`;
      await page.getByTestId('add-item-btn').click();
      await page.getByLabel('Name *').fill(countryName);
      await page.getByTestId('create-country-btn').click();
      await expect(page.locator('body')).toContainText(/created.*successfully/i);
      
      // Navigate to edit and add region
      const countryRow = page.getByRole('row').filter({ hasText: countryName });
      await countryRow.getByRole('button', { name: /edit/i }).click();
      await expect(page.locator('body')).toContainText(`Edit Country:`);
      
      await page.getByRole('button', { name: 'Add Region' }).click();
      
      const regionName = `Delete Test Region ${Date.now()}`;
      await page.getByTestId('region-name-input').fill(regionName);
      await page.getByTestId('save-region-button').click();
      
      await expect(page.locator('body')).toContainText(/region.*created.*successfully/i);
      
      // Test deletion - handle browser confirmation dialog
      const regionRow = page.getByTestId('region-item').filter({ hasText: regionName });
      
      // Set up dialog handler before clicking delete
      page.on('dialog', async dialog => {
        await dialog.accept();
      });
      
      await regionRow.getByRole('button', { name: /remove/i }).click();
      
      await expect(page.locator('body')).toContainText(/region.*deleted.*successfully/i);
      // After deletion, should show "No regions defined" message
      await expect(page.getByTestId('no-regions-message')).toBeVisible();
      
    } finally {
      await testData.cleanup();
    }
  });
});