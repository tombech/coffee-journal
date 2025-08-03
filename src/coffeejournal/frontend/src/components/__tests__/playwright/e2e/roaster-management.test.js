import { test, expect } from '@playwright/test';
const TestDataManager = require('../../../../test-utils/testDataManager');
// Using semantic selectors - no need for helper functions that use brittle selectors

test.describe('Roaster Management', () => {
  let testData;

  test.beforeEach(async ({ page }, testInfo) => {
    testData = new TestDataManager(`roaster_${testInfo.title.replace(/\s+/g, '_')}`, 'http://localhost:5000/api', testInfo.project.name);
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

  test('displays roaster list in a table', async ({ page }) => {
    // Create test scenario to ensure we have roasters to display
    const scenario = await testData.createTestScenario();
    
    await page.goto('/settings/roasters');
    
    // Check page structure using semantic selectors
    await expect(page.getByRole('heading', { name: 'Roasters' })).toBeVisible();
    
    // Should have a table
    await expect(page.getByRole('table')).toBeVisible();
    
    // Should have add button
    await expect(page.getByRole('button', { name: 'Add Roaster' })).toBeVisible();
    
    // Should have back button
    await expect(page.getByRole('button', { name: 'Back to Settings' })).toBeVisible();
    
    // Our test roaster should be visible in the page content
    await expect(page.locator('body')).toContainText(scenario.roaster.name);
  });

  test('can add new roaster', async ({ page }) => {
    await page.goto('/settings/roasters');
    
    // Click add button using semantic selector
    await page.getByRole('button', { name: 'Add Roaster' }).click();
    
    // Wait for form to appear - look for the heading change
    await expect(page.getByRole('heading', { name: 'Add New Roaster' })).toBeVisible();
    
    // Fill out form using semantic selectors - getByLabel is correct here because LookupManager uses proper <label htmlFor=""> elements
    const roasterName = `Test Roaster ${testData.testId}`;
    
    await page.getByLabel('Name *').fill(roasterName);
    await page.getByLabel('Short Form').fill('AT');
    await page.getByLabel('Description').fill('Test roaster created by Playwright');
    
    // Submit form using semantic button selector
    await page.getByTestId('create-item-btn').click();
    
    // Wait for success toast message
    await expect(page.locator('body')).toContainText(/roaster.*created.*successfully/i, { timeout: 10000 });
    
    // Wait for form to close - form heading should disappear
    await expect(page.getByRole('heading', { name: 'Add New Roaster' })).not.toBeVisible();
    
    // New roaster should be visible in page content
    await expect(page.locator('body')).toContainText(roasterName);
  });

  test('shows usage warning when trying to delete roaster in use', async ({ page }) => {
    // Create test scenario with roaster that has products (in use)
    const scenario = await testData.createTestScenario();
    
    await page.goto('/settings/roasters');
    
    // Click delete button for our test roaster (which is in use by the product)
    await page.getByRole('button', { name: `Delete ${scenario.roaster.name}` }).click();
    
    // Wait for delete confirmation modal
    await expect(page.getByTestId('delete-modal-content')).toBeVisible();
    
    // Check for usage warning message
    await expect(page.locator('body')).toContainText(/This roaster is currently being used in \d+ products?/);
    
    // Check that radio buttons are present (indicating in-use scenario)
    await expect(page.getByRole('radio', { name: /cancel deletion/i })).toBeVisible();
    await expect(page.getByRole('radio', { name: /remove all references/i })).toBeVisible();
    
    // Cancel the deletion using semantic selector
    await page.getByRole('button', { name: 'Cancel' }).click();
    
    // Wait for modal to close
    await expect(page.getByTestId('delete-modal-content')).not.toBeVisible();
    
    // Roaster should still be visible in page content
    await expect(page.locator('body')).toContainText(scenario.roaster.name);
  });

  test('can delete roaster not in use', async ({ page }) => {
    await page.goto('/settings/roasters');
    
    // Generate unique name using timestamp to avoid conflicts from parallel test runs
    const timestamp = Date.now();
    const roasterName = `DeleteTest${timestamp}`;
    
    // First create a roaster that won't be in use
    await page.getByRole('button', { name: 'Add Roaster' }).click();
    
    // Wait for form to appear
    await expect(page.getByRole('heading', { name: 'Add New Roaster' })).toBeVisible();
    
    await page.getByLabel('Name *').fill(roasterName);
    
    await page.getByTestId('create-item-btn').click();
    
    // Wait for success toast message
    await expect(page.locator('body')).toContainText(/roaster.*created.*successfully/i, { timeout: 10000 });
    
    // Wait for form to close
    await expect(page.getByRole('heading', { name: 'Add New Roaster' })).not.toBeVisible();
    
    // Now try to delete the new roaster (it should not be in use since we just created it)
    await page.getByRole('button', { name: `Delete ${roasterName}` }).click();
    
    // Wait for delete confirmation modal
    await expect(page.getByTestId('delete-modal-content')).toBeVisible();
    
    // Should show simple confirmation without usage warning
    await expect(page.locator('body')).toContainText(`Are you sure you want to delete "${roasterName}"? This action cannot be undone.`);
    
    // Should not show usage warning or radio options
    await expect(page.locator('body')).not.toContainText(/currently being used/i);
    
    // Confirm deletion using semantic selector
    await page.getByTestId('delete-modal-content').getByRole('button', { name: 'Delete' }).click();
    
    // Wait for success message
    await expect(page.locator('body')).toContainText(/roaster.*deleted.*successfully/i, { timeout: 10000 });
    
    // Wait for modal to close
    await expect(page.getByTestId('delete-modal-content')).not.toBeVisible();
    
    // Roaster should no longer be visible in page content
    await expect(page.locator('body')).not.toContainText(roasterName);
  });

  test('can edit existing roaster', async ({ page }) => {
    // Create test scenario to ensure we have a roaster to edit
    const scenario = await testData.createTestScenario();
    
    await page.goto('/settings/roasters');
    
    // Click edit button for our test roaster using semantic selector
    await page.getByRole('button', { name: `Edit ${scenario.roaster.name}` }).click();
    
    // Wait for form to appear
    await expect(page.getByRole('heading', { name: `Edit Roaster` })).toBeVisible();
    
    // Add description to the roaster
    const updatedDescription = `Updated description ${testData.testId}`;
    await page.getByLabel('Description').fill(updatedDescription);
    
    // Submit update using semantic selector
    await page.getByRole('button', { name: 'Update' }).click();
    
    // Wait for success toast message
    await expect(page.locator('body')).toContainText(/roaster.*updated.*successfully/i, { timeout: 10000 });
    
    // Wait for form to close (form should disappear)
    await expect(page.getByRole('heading', { name: `Edit Roaster` })).not.toBeVisible();
    
    // Updated data should be visible in the page content - check for truncated version
    const truncatedDesc = updatedDescription.length > 50 ? updatedDescription.substring(0, 47) : updatedDescription;
    await expect(page.locator('body')).toContainText(truncatedDesc);
  });

  test('can navigate back to settings', async ({ page }) => {
    await page.goto('/settings/roasters');
    
    // Click back button using semantic selector with proper wait
    await page.getByRole('button', { name: 'Back to Settings' }).click();
    
    // Wait for navigation to settings
    await page.waitForURL('**/settings');
    
    // Should show settings page
    await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible();
  });
});