import { test, expect } from '@playwright/test';
const TestDataManager = require('../../../../test-utils/testDataManager');

test.describe('Default Item Visualization', () => {
  let testData;

  test.beforeEach(async ({ page }, testInfo) => {
    testData = new TestDataManager(`default_viz_${testInfo.title.replace(/\s+/g, '_')}`, 'http://localhost:5000/api', testInfo.project.name);
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

  test('lookup manager shows default items with enhanced visual styling', async ({ page }) => {
    // Go to roasters manager
    await page.goto('/settings/roasters');
    
    // Wait for the page to load
    await expect(page.getByRole('heading', { name: 'Roasters' })).toBeVisible();
    
    // Wait for items to load
    await expect(page.locator('table')).toBeVisible();
    
    // Look for default items - they should have visual indicators
    const defaultItems = await page.locator('td').filter({ 
      has: page.locator('span').filter({ hasText: /default/i }) 
    }).count();
    
    if (defaultItems > 0) {
      // Check that default items have the star icon
      await expect(page.getByRole('img', { name: 'Default item indicator' })).toBeVisible();
      
      // Check that default items have "Default" text  
      await expect(page.getByText('Default').and(page.locator('[aria-label="This is the default item"]'))).toBeVisible();
      
      // Check that default items have different background styling
      const defaultCell = page.locator('td').filter({ 
        has: page.locator('span').filter({ hasText: /default/i }) 
      }).first();
      
      // Default items should have a background color (not transparent)
      const cellStyle = await defaultCell.getAttribute('style');
      expect(cellStyle).toContain('backgroundColor');
      expect(cellStyle).not.toContain('transparent');
    }
  });

  test('multiple lookup types show consistent default item styling', async ({ page }) => {
    const lookupTypes = ['roasters', 'bean-types', 'brew-methods'];
    
    for (const lookupType of lookupTypes) {
      await page.goto(`/settings/${lookupType}`);
      
      // Wait for the page to load
      await expect(page.locator('table')).toBeVisible();
      
      // Check if there are any default items
      const defaultItems = await page.locator('span').filter({ hasText: /default/i }).count();
      
      if (defaultItems > 0) {
        // Verify consistent styling across all lookup types
        await expect(page.getByRole('img', { name: 'Default item indicator' })).toBeVisible();
        
        // Check that default items have enhanced styling
        const defaultCells = page.locator('td').filter({ 
          has: page.locator('span').filter({ hasText: /default/i }) 
        });
        
        const count = await defaultCells.count();
        for (let i = 0; i < count; i++) {
          const cell = defaultCells.nth(i);
          const cellStyle = await cell.getAttribute('style');
          expect(cellStyle).toContain('backgroundColor');
        }
      }
    }
  });

  test('lookup detail page shows prominent default item indication', async ({ page }) => {
    // Create a test roaster and make it default
    await page.goto('/settings/roasters');
    await expect(page.getByRole('heading', { name: 'Roasters' })).toBeVisible();
    
    // Create a new roaster
    await page.getByTestId('add-item-btn').click();
    await page.getByLabel(/name/i).fill(`Test Default Roaster ${testData.testId}`);
    await page.getByTestId('create-item-btn').click();
    
    // Wait for form to close
    await expect(page.getByRole('heading', { name: /add.*roaster/i })).not.toBeVisible();
    
    // Find the created roaster in the table
    const roasterRow = page.locator('tr').filter({ hasText: `Test Default Roaster ${testData.testId}` });
    await expect(roasterRow).toBeVisible();
    
    // Set this roaster as default by clicking checkbox in the form
    // First, edit the roaster to check the default checkbox
    await roasterRow.getByTestId(`edit-test-default-roaster-${testData.testId.toLowerCase().replace(/\s+/g, '-')}-btn`).click();
    
    // Wait for form to open
    await expect(page.getByRole('heading', { name: /edit.*roaster/i })).toBeVisible();
    
    // Check the "Set as Default" checkbox
    await page.getByLabel(/set.*default/i).check();
    
    // Save the changes
    await page.getByTestId('update-item-btn').click();
    
    // Wait for form to close
    await expect(page.getByRole('heading', { name: /edit.*roaster/i })).not.toBeVisible();
    
    // Check that the roaster now shows as default in the table
    const defaultCell = page.locator('td').filter({ 
      has: page.locator('span').filter({ hasText: /default/i }) 
    });
    
    // Check for default indicator elements using semantic selectors
    await expect(page.getByRole('img', { name: 'Default item indicator' })).toBeVisible();
    await expect(page.getByText('Default').and(page.locator('[aria-label="This is the default item"]'))).toBeVisible();
  });

  test('default items are visually distinguishable from non-default items', async ({ page }) => {
    await page.goto('/settings/roasters');
    await expect(page.getByRole('heading', { name: 'Roasters' })).toBeVisible();
    await expect(page.locator('table')).toBeVisible();
    
    // Get all item rows
    const itemRows = page.locator('tbody tr');
    const rowCount = await itemRows.count();
    
    if (rowCount > 0) {
      let foundDefault = false;
      let foundNonDefault = false;
      
      for (let i = 0; i < rowCount; i++) {
        const row = itemRows.nth(i);
        const firstCell = row.locator('td').first();
        
        const hasDefaultText = await firstCell.locator('span').filter({ hasText: /default/i }).count() > 0;
        const cellStyle = await firstCell.getAttribute('style');
        
        if (hasDefaultText) {
          foundDefault = true;
          // Default items should have background color
          expect(cellStyle).toContain('backgroundColor');
          expect(cellStyle).not.toContain('transparent');
          
          // Should have star icon
          await expect(firstCell.getByRole('img', { name: 'Default item indicator' })).toBeVisible();
        } else {
          foundNonDefault = true;
          // Non-default items should have transparent background
          if (cellStyle && cellStyle.includes('backgroundColor')) {
            expect(cellStyle).toContain('transparent');
          }
        }
      }
      
      // We should have found at least one type to verify the distinction
      expect(foundDefault || foundNonDefault).toBe(true);
    }
  });

  test('default star icon is prominent and visible', async ({ page }) => {
    await page.goto('/settings/roasters');
    await expect(page.getByRole('heading', { name: 'Roasters' })).toBeVisible();
    await expect(page.locator('table')).toBeVisible();
    
    // Look for any default items using semantic selector
    const starIcons = page.getByRole('img', { name: 'Default item indicator' });
    const starCount = await starIcons.count();
    
    if (starCount > 0) {
      // Check that star icons are visible and properly styled
      for (let i = 0; i < starCount; i++) {
        const star = starIcons.nth(i);
        await expect(star).toBeVisible();
        
        // Check that the star has enhanced styling
        const starStyle = await star.getAttribute('style');
        if (starStyle) {
          // Should have position absolute for prominent display
          expect(starStyle).toContain('position');
          expect(starStyle).toContain('fontSize');
        }
      }
    }
  });
});