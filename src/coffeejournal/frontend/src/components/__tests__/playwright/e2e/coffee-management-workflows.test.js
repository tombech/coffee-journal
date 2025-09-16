import { test, expect } from '@playwright/test';
const TestDataManager = require('../../../../test-utils/testDataManager');

test.describe('Coffee Management Workflows', () => {
  // Merged test: combines product display, creation, navigation, and batch management
  test('Complete product and batch management workflow', async ({ page }) => {
    const testData = new TestDataManager(`coffee_workflow_${Date.now()}`, 'http://localhost:5000/api');
    await testData.initialize();
    
    await page.addInitScript((userId) => {
      window.API_BASE_URL = 'http://localhost:5000/api';
      window.TEST_USER_ID = userId;
    }, testData.userId);
    
    try {
      // 1. Create supporting lookup data
      const roaster = await testData.createTestItem('roasters', { name: `Test Roaster ${Date.now()}` });
      const country = await testData.createTestItem('countries', { name: `Test Country ${Date.now()}` });
      const beanType = await testData.createTestItem('bean_types', { name: `Test Bean ${Date.now()}` });
      
      // 2. Test product list display and creation
      await page.goto('/products');
      await expect(page.getByRole('heading', { name: 'Products' })).toBeVisible();
      await expect(page.getByTestId('add-new-product-btn')).toBeVisible();
      
      // Create new product
      await page.getByTestId('add-new-product-btn').click();
      await page.waitForURL('**/products/new');
      await expect(page.getByRole('heading', { name: /Add.*Product/i })).toBeVisible();
      
      const productName = `Test Product ${Date.now()}`;
      await page.getByLabel(/product.*name/i).fill(productName);
      
      // Fill autocomplete fields
      await page.getByLabel('Roaster').fill(roaster.name);
      await page.getByRole('option', { name: roaster.name }).click();
      
      await page.getByLabel('Bean Type').fill(beanType.name);
      await page.getByRole('option', { name: beanType.name }).click();
      
      await page.getByLabel('Country').fill(country.name);
      await page.getByRole('option', { name: country.name }).click();
      
      // Add optional fields if present
      if (await page.getByLabel(/roast.*type/i).isVisible()) {
        await page.getByLabel(/roast.*type/i).fill('3');
      }
      if (await page.getByLabel(/description/i).isVisible()) {
        await page.getByLabel(/description/i).fill('Test product description');
      }
      
      await page.getByRole('button', { name: /save.*product/i }).click();
      await expect(page.locator('body')).toContainText(/created.*successfully/i);
      
      // 3. Navigate to product detail page
      await page.goto('/products');
      const productRow = page.locator('div, tr').filter({ hasText: roaster.name });
      await productRow.getByTestId(/product-details-link-/).click();
      
      await expect(page.getByRole('heading', { name: productName })).toBeVisible();
      await expect(page.locator('body')).toContainText(roaster.name);
      
      // 4. Test batch management from product detail
      await expect(page.getByTestId('add-batch-btn')).toBeVisible();
      await page.getByTestId('add-batch-btn').click();
      
      // Fill batch form
      const batchDate = '2024-01-15';
      const roastDate = '2024-01-10';
      
      await page.getByLabel(/purchase.*date/i).fill(batchDate);
      await page.getByLabel(/roast.*date/i).fill(roastDate);
      await page.getByLabel(/amount.*grams/i).fill('500');
      await page.getByLabel(/purchase.*price/i).fill('24.99');
      
      if (await page.getByLabel(/notes/i).isVisible()) {
        await page.getByLabel(/notes/i).fill('Test batch notes');
      }
      
      await page.getByRole('button', { name: /save.*batch/i }).click();
      await expect(page.locator('body')).toContainText(/batch.*created.*successfully/i);
      
      // 5. Navigate to batch detail and test brew session creation
      await page.getByRole('link', { name: /view.*batch/i }).first().click();
      await expect(page.locator('body')).toContainText('Batch Details');
      
      // Create brew session from batch - extract batch ID from current URL
      const currentUrl = page.url();
      const batchId = currentUrl.match(/batches\/(\d+)/)?.[1];
      await page.goto(`/brew-sessions/new?batch_id=${batchId}`);
      await expect(page.getByRole('heading', { name: /Add.*Brew.*Session/i })).toBeVisible();
      
      // Fill brew session form
      await page.getByLabel(/coffee.*grams/i).fill('15');
      await page.getByLabel(/water.*grams/i).fill('250');
      await page.getByLabel(/brew.*time/i).fill('4:30');
      await page.getByLabel(/grind.*setting/i).fill('12');
      
      // Set rating
      await page.getByLabel(/overall.*rating/i).fill('4.5');
      
      if (await page.getByLabel(/notes/i).isVisible()) {
        await page.getByLabel(/notes/i).fill('Great brew session test');
      }
      
      await page.getByRole('button', { name: /save.*brew.*session/i }).click();
      await expect(page.locator('body')).toContainText(/brew.*session.*created.*successfully/i);
      
      // 6. Verify brew session appears in lists
      await page.goto('/brew-sessions');
      await expect(page.getByRole('heading', { name: /brew.*sessions/i })).toBeVisible();
      await expect(page.locator('body')).toContainText(roaster.name);
      
    } finally {
      await testData.cleanup();
    }
  });

  // Merged test: brew session duplication, editing, and detailed management
  test('Brew session duplication and advanced management', async ({ page }) => {
    const testData = new TestDataManager(`brew_session_advanced_${Date.now()}`, 'http://localhost:5000/api');
    await testData.initialize();
    
    await page.addInitScript((userId) => {
      window.API_BASE_URL = 'http://localhost:5000/api';
      window.TEST_USER_ID = userId;
    }, testData.userId);
    
    try {
      // Create test scenario with full data
      const scenario = await testData.createTestScenario();
      
      // 1. Navigate to brew sessions and verify display
      await page.goto('/brew-sessions');
      await expect(page.getByRole('heading', { name: /brew.*sessions/i })).toBeVisible();
      await expect(page.locator('body')).toContainText(scenario.roaster.name);
      
      // 2. Edit existing brew session
      const brewSessionRow = page.locator('.brew-session-card, [data-testid="brew-session-card"]').first();
      await brewSessionRow.getByRole('button', { name: /edit/i }).click();
      
      await expect(page.getByRole('heading', { name: /edit.*brew.*session/i })).toBeVisible();
      
      // Update brew session details
      await page.getByLabel(/coffee.*grams/i).fill('18');
      await page.getByLabel(/water.*grams/i).fill('300');
      await page.getByLabel(/overall.*rating/i).fill('5');
      
      const updatedNotes = `Updated brew notes ${Date.now()}`;
      await page.getByLabel(/notes/i).fill(updatedNotes);
      
      await page.getByRole('button', { name: /save.*brew.*session/i }).click();
      await expect(page.locator('body')).toContainText(/updated.*successfully/i);
      
      // 3. Test brew session duplication
      await page.goto('/brew-sessions');
      
      // Find the brew session we just updated and duplicate it
      const sessionCard = page.locator('.brew-session-card, [data-testid="brew-session-card"]').filter({ hasText: updatedNotes });
      await sessionCard.getByRole('button', { name: /duplicate/i }).click();
      
      await expect(page.getByRole('heading', { name: /duplicate.*brew.*session/i })).toBeVisible();
      
      // Verify fields are pre-filled from original
      await expect(page.getByLabel(/coffee.*grams/i)).toHaveValue('18');
      await expect(page.getByLabel(/water.*grams/i)).toHaveValue('300');
      
      // Modify duplicated session
      await page.getByLabel(/coffee.*grams/i).fill('16');
      const duplicateNotes = `Duplicated session ${Date.now()}`;
      await page.getByLabel(/notes/i).fill(duplicateNotes);
      
      await page.getByRole('button', { name: /save.*brew.*session/i }).click();
      await expect(page.locator('body')).toContainText(/created.*successfully/i);
      
      // 4. Verify both sessions exist
      await page.goto('/brew-sessions');
      await expect(page.locator('body')).toContainText(updatedNotes);
      await expect(page.locator('body')).toContainText(duplicateNotes);
      
      // 5. Test navigation to brew session detail
      const detailSessionCard = page.locator('.brew-session-card').filter({ hasText: duplicateNotes });
      await detailSessionCard.getByRole('link', { name: /view.*details/i }).click();
      
      await expect(page.locator('body')).toContainText('Brew Session Details');
      await expect(page.locator('body')).toContainText(duplicateNotes);
      await expect(page.locator('body')).toContainText(scenario.roaster.name);
      
    } finally {
      await testData.cleanup();
    }
  });

  // Test product validation and error handling
  test('Product creation validation and error handling', async ({ page }) => {
    const testData = new TestDataManager(`product_validation_${Date.now()}`, 'http://localhost:5000/api');
    await testData.initialize();
    
    await page.addInitScript((userId) => {
      window.API_BASE_URL = 'http://localhost:5000/api';
      window.TEST_USER_ID = userId;
    }, testData.userId);
    
    try {
      await page.goto('/products/new');
      await expect(page.getByRole('heading', { name: /Add.*Product/i })).toBeVisible();
      
      // 1. Test validation - try to save without required fields
      await page.getByRole('button', { name: /save.*product/i }).click();
      
      // Should stay on form or show validation messages
      await expect(page.getByRole('heading', { name: /Add.*Product/i })).toBeVisible();
      
      // 2. Test partial completion and validation
      const productName = `Validation Test Product ${Date.now()}`;
      await page.getByLabel(/product.*name/i).fill(productName);
      
      // Try to save with only name filled
      await page.getByRole('button', { name: /save.*product/i }).click();
      
      // Should require roaster field
      await expect(page.getByRole('heading', { name: /Add.*Product/i })).toBeVisible();
      
      // 3. Complete form properly
      const roaster = await testData.createTestItem('roasters', { name: `Validation Roaster ${Date.now()}` });
      const beanType = await testData.createTestItem('bean_types', { name: `Validation Bean ${Date.now()}` });
      
      await page.getByLabel('Roaster').fill(roaster.name);
      await page.getByRole('option', { name: roaster.name }).click();
      
      await page.getByLabel('Bean Type').fill(beanType.name);
      await page.getByRole('option', { name: beanType.name }).click();
      
      await page.getByRole('button', { name: /save.*product/i }).click();
      await expect(page.locator('body')).toContainText(/created.*successfully/i);
      
    } finally {
      await testData.cleanup();
    }
  });
});