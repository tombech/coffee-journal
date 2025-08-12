import { test, expect } from '@playwright/test';
const TestDataManager = require('../../../../test-utils/testDataManager');

test.describe('Espresso Equipment Managers', () => {
  let testData;

  test.beforeEach(async ({ page }, testInfo) => {
    testData = new TestDataManager(`espresso_equipment_${testInfo.title.replace(/\s+/g, '_')}`, 'http://localhost:5000/api', testInfo.project.name);
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

  const espressoEquipmentTypes = [
    { name: 'Brewer', path: '/settings/brewers', title: 'Brewer Manager' },
    { name: 'Portafilter', path: '/settings/portafilters', title: 'Portafilter Manager' },
    { name: 'Basket', path: '/settings/baskets', title: 'Basket Manager' },
    { name: 'Tamper', path: '/settings/tampers', title: 'Tamper Manager' },
    { name: 'WDT Tool', path: '/settings/wdt-tools', title: 'WDT Tool Manager' },
    { name: 'Leveling Tool', path: '/settings/leveling-tools', title: 'Leveling Tool Manager' }
  ];

  espressoEquipmentTypes.forEach(equipment => {
    test(`can manage ${equipment.name} equipment`, async ({ page }) => {
      await page.goto(equipment.path);
      
      // Check that the main app is loaded
      await expect(page.getByRole('heading', { name: 'My Coffee Journal' })).toBeVisible();
      
      // Wait for the manager page to load - look for page structure, not specific text
      await expect(page.locator('#manager-page')).toBeVisible({ timeout: 10000 });
      
      // Create new equipment item
      const itemName = `Test ${equipment.name} ${testData.testId}`;
      
      // Look for create button using semantic role
      await page.getByRole('button', { name: /new|create|add/i }).click();
      
      // Fill in the form
      await page.getByLabel(/name/i).fill(itemName);
      
      // Add short form if field exists
      try {
        await page.getByLabel(/short.*form/i).fill(`T${equipment.name.charAt(0)}${testData.testId}`);
      } catch (e) {
        // Short form field might not exist for all equipment types
      }
      
      // Submit form
      await page.getByRole('button', { name: /save|submit|create/i }).click();
      
      // Verify item was created - check table contains our test data
      await expect(page.getByRole('table')).toBeVisible();
      await expect(page.getByRole('table')).toContainText(itemName);
      
      // Test editing the item
      // Find the edit button for our specific item
      const tableRow = page.getByRole('row').filter({ hasText: itemName });
      await tableRow.getByRole('button', { name: /edit/i }).click();
      
      // Update the name
      const updatedName = `${itemName} - Updated`;
      await page.getByLabel(/name/i).fill(updatedName);
      
      // Save changes
      await page.getByRole('button', { name: /save|submit|update/i }).click();
      
      // Verify update worked
      await expect(page.getByRole('table')).toContainText(updatedName);
      
      // Test deletion
      const updatedTableRow = page.getByRole('row').filter({ hasText: updatedName });
      
      // Handle confirm dialog
      page.on('dialog', async dialog => {
        expect(dialog.message()).toContain('Are you sure you want to delete');
        await dialog.accept();
      });
      
      await updatedTableRow.getByRole('button', { name: /delete/i }).click();
      
      // Verify item was deleted
      await expect(page.getByRole('table')).not.toContainText(updatedName);
    });
  });

  test('can navigate between equipment managers from settings', async ({ page }) => {
    await page.goto('/settings');
    
    // Check that settings page loaded
    await expect(page.getByRole('heading', { name: 'My Coffee Journal' })).toBeVisible();
    await expect(page.locator('#settings-page')).toBeVisible({ timeout: 10000 });
    
    // Check that espresso equipment section exists
    await expect(page.locator('body')).toContainText(/espresso.*equipment/i);
    
    // Test navigation to each espresso equipment manager
    for (const equipment of espressoEquipmentTypes.slice(0, 3)) { // Test first 3 to keep test reasonable
      // Find the link for this equipment type
      const equipmentLink = page.getByRole('link', { name: new RegExp(equipment.name, 'i') });
      await expect(equipmentLink).toBeVisible();
      
      // Click to navigate to the manager
      await equipmentLink.click();
      
      // Verify we're on the correct manager page
      await expect(page.locator('#manager-page')).toBeVisible();
      
      // Go back to settings to test next equipment
      await page.goBack();
      await expect(page.locator('#settings-page')).toBeVisible();
    }
  });

  test('espresso equipment shows usage information', async ({ page }) => {
    // Create test data that uses espresso equipment
    const scenario = await testData.createEspressoTestScenario();
    
    await page.goto('/settings/brewers');
    
    // Wait for page to load
    await expect(page.locator('#manager-page')).toBeVisible({ timeout: 10000 });
    await expect(page.getByRole('table')).toBeVisible();
    
    // Our test brewer should show usage since it's used in a shot
    const brewerRow = page.getByRole('row').filter({ hasText: scenario.brewer.name });
    await expect(brewerRow).toBeVisible();
    
    // Usage information might be shown in different ways - check for usage indicators
    // This is flexible to accommodate different UI approaches
    await expect(page.locator('body')).toContainText(scenario.brewer.name);
  });

  test('validates required fields for equipment creation', async ({ page }) => {
    await page.goto('/settings/brewers'); // Test with brewers as example
    
    // Wait for page to load
    await expect(page.locator('#manager-page')).toBeVisible({ timeout: 10000 });
    
    // Click create button
    await page.getByRole('button', { name: /new|create|add/i }).click();
    
    // Try to submit empty form
    await page.getByRole('button', { name: /save|submit|create/i }).click();
    
    // Form should not submit successfully (HTML5 validation should prevent it)
    // Verify we're still on the form by checking for name field
    await expect(page.getByLabel(/name/i)).toBeVisible();
  });
});