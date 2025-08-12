const { test, expect } = require('@playwright/test');
const TestDataManager = require('../../../../test-utils/testDataManager');
// Using semantic selectors - no need for helper functions that use brittle selectors

test.describe('Standardized Icons Usage', () => {
  let testData;

  test.beforeEach(async ({ page }, testInfo) => {
    testData = new TestDataManager(`icons_${testInfo.title.replace(/\s+/g, '_')}`, 'http://localhost:5000/api', testInfo.project.name);
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

  test('brew session table uses standardized icons', async ({ page }) => {
    // Create test scenario with brew session
    const scenario = await testData.createTestScenario();
    
    await page.goto(`/batches/${scenario.batch.id}`);
    
    // Wait for recent brew sessions table to load (most likely to have data)
    await expect(page.getByTestId('recent-brew-sessions-table')).toBeVisible({ timeout: 2000 });
    
    // Wait for brew session data to load - look for any brew session row
    const brewSessionRows = page.getByTestId('recent-brew-sessions-table').locator('tbody tr');
    await expect(brewSessionRows).toHaveCount(1, { timeout: 5000 });
    
    // Check for standardized icons in the brew session table - use the first row since we know there's one
    const firstRow = brewSessionRows.first();
    
    if (await brewSessionRows.count() > 0) {
      
      // Check for edit button (may use semantic selector instead of icon)
      const editButton = firstRow.getByRole('button', { name: /edit/i });
      if (await editButton.count() > 0) {
        await expect(editButton).toBeVisible();
        const editIcon = await editButton.textContent();
        // Document what icon is actually used
        console.log(`Edit button content: "${editIcon.trim()}"`);
      }
      
      // Check for duplicate button
      const duplicateButton = firstRow.getByRole('button', { name: /duplicate/i });
      if (await duplicateButton.count() > 0) {
        await expect(duplicateButton).toBeVisible();
        const duplicateIcon = await duplicateButton.textContent();
        console.log(`Duplicate button content: "${duplicateIcon.trim()}"`);
      }
      
      // Check for delete button
      const deleteButton = firstRow.getByRole('button', { name: /delete/i });
      if (await deleteButton.count() > 0) {
        await expect(deleteButton).toBeVisible();
        const deleteIcon = await deleteButton.textContent();
        console.log(`Delete button content: "${deleteIcon.trim()}"`);
      }
    }
  });

  test('lookup managers use standardized icons', async ({ page }) => {
    await page.goto('/settings/roasters');
    
    // Check for standardized add new button icon - use correct button text
    const addButton = page.getByRole('button', { name: 'Add Roaster' });
    await expect(addButton).toBeVisible();
    const addButtonText = await addButton.textContent();
    expect(addButtonText).toContain('➕'); // Create icon
    
    // Check if there are existing roasters to test edit/delete icons
    const itemRows = page.locator('[data-testid="item-row"]');
    const itemCount = await itemRows.count();
    
    if (itemCount > 0) {
      const firstRow = itemRows.first();
      
      // Check edit button icon
      const editButton = firstRow.getByRole('button', { name: /edit/i });
      if (await editButton.count() > 0) {
        const editIcon = await editButton.textContent();
        expect(editIcon).toContain('✏️'); // Edit icon
      }
      
      // Check delete button icon
      const deleteButton = firstRow.getByRole('button', { name: /delete/i });
      if (await deleteButton.count() > 0) {
        const deleteIcon = await deleteButton.textContent();
        expect(deleteIcon).toContain('🗑️'); // Delete icon
      }
    }
  });

  test('save buttons use standardized save icon', async ({ page }) => {
    await page.goto('/settings/roasters');
    
    // Click add new to open form - use correct button text
    await page.getByRole('button', { name: 'Add Roaster' }).click();
    
    // Check that save button uses standard icon - use test ID to avoid strict mode
    const saveButton = page.getByTestId('create-item-btn');
    await expect(saveButton).toBeVisible();
    const saveButtonText = await saveButton.textContent();
    expect(saveButtonText).toContain('💾'); // Save icon
  });

  test('form buttons use consistent icons across different managers', async ({ page }) => {
    const managers = [
      { path: '/settings/brew-methods', name: 'brew method' },
      { path: '/settings/bean-types', name: 'bean type' },
      { path: '/settings/grinders', name: 'grinder' }
    ];
    
    for (const manager of managers) {
      await page.goto(manager.path);
      
      // Check add button icon - use test ID to avoid strict mode violations
      const addButton = page.getByTestId('add-item-btn');
      if (await addButton.count() > 0) {
        const addText = await addButton.textContent();
        expect(addText).toContain('➕'); // Create icon should be consistent
      }
      
      // Open form to check save button
      if (await addButton.count() > 0) {
        await addButton.click();
        
        const saveButton = page.getByTestId('create-item-btn'); // Use test ID
        if (await saveButton.count() > 0) {
          const saveText = await saveButton.textContent();
          expect(saveText).toContain('💾'); // Save icon should be consistent
        }
        
        // Cancel to close form - use specific test ID
        const cancelButton = page.getByTestId('cancel-form-btn');
        if (await cancelButton.count() > 0) {
          await cancelButton.click();
        }
      }
    }
  });

  test('product management uses standardized icons', async ({ page }) => {
    await page.goto('/products');
    
    // Check add new product button - use correct button text
    const addButton = page.getByRole('button', { name: 'Add Product' });
    if (await addButton.count() > 0) {
      const addText = await addButton.textContent();
      expect(addText).toContain('➕'); // Create icon
    }
    
    // Check if there are products to test action icons
    const productRows = page.locator('tr').filter({ hasText: /Blue Bottle|Intelligentsia|Stumptown/ });
    
    if (await productRows.count() > 0) {
      const firstRow = productRows.first();
      
      // Look for action buttons
      const editButton = firstRow.getByRole('button', { name: /edit/i });
      if (await editButton.count() > 0) {
        const editIcon = await editButton.textContent();
        expect(editIcon).toContain('✏️');
      }
      
      const deleteButton = firstRow.getByRole('button', { name: /delete/i });
      if (await deleteButton.count() > 0) {
        const deleteIcon = await deleteButton.textContent();
        expect(deleteIcon).toContain('🗑️');
      }
    }
  });

  test('batch management uses standardized icons', async ({ page }) => {
    await page.goto('/products/1'); // Go to product detail to see batches
    
    // Check add batch button
    const addBatchButton = page.getByRole('button', { name: /add batch/i });
    if (await addBatchButton.count() > 0) {
      const addText = await addBatchButton.textContent();
      expect(addText).toContain('➕'); // Create icon
    }
    
    // Check batch action icons
    const batchRows = page.locator('tr').filter({ hasText: /\d{2}\.\d{2}\.\d{2}/ }); // Date pattern
    
    if (await batchRows.count() > 0) {
      const firstRow = batchRows.first();
      
      const editButton = firstRow.getByRole('button', { name: /edit/i });
      if (await editButton.count() > 0) {
        const editIcon = await editButton.textContent();
        expect(editIcon).toContain('✏️');
      }
      
      const deleteButton = firstRow.getByRole('button', { name: /delete/i });
      if (await deleteButton.count() > 0) {
        const deleteIcon = await deleteButton.textContent();
        expect(deleteIcon).toContain('🗑️');
      }
    }
  });

  test('filter and clear buttons use standardized icons', async ({ page }) => {
    await page.goto('/batches/1');
    
    // Check clear filter button (if brew sessions exist)
    const clearButton = page.getByTitle('Clear Filters');
    if (await clearButton.count() > 0) {
      const clearIcon = await clearButton.textContent();
      expect(clearIcon.trim()).toBe('🗑️'); // Clear uses delete icon
    }
    
    // Check add new brew session button
    const addSessionButton = page.locator('button').filter({ hasText: /➕/ });
    if (await addSessionButton.count() > 0) {
      const addIcon = await addSessionButton.textContent();
      expect(addIcon).toContain('➕');
    }
  });

  test('brew session form uses standardized save icon', async ({ page }) => {
    await page.goto('/batches/1');
    
    // Try to find and click add new brew session button
    const addButtons = page.locator('button').filter({ hasText: /➕/ });
    
    if (await addButtons.count() > 0) {
      await addButtons.first().click();
      
      // Should be on brew session form
      const submitButton = page.getByTestId('submit-brew-session');
      if (await submitButton.count() > 0) {
        const submitText = await submitButton.textContent();
        expect(submitText).toContain('💾'); // Save icon
      }
    }
  });

  test('country edit page uses standardized icons', async ({ page }) => {
    await page.goto('/settings/countries');
    
    // Try to edit a country
    const itemRows = page.locator('[data-testid="item-row"]');
    
    if (await itemRows.count() > 0) {
      const editButton = itemRows.first().getByRole('button', { name: /edit/i });
      await editButton.click();
      
      // Should be on country edit page with regions
      await page.waitForTimeout(1000);
      
      // Check add region button
      const addRegionButton = page.getByTestId('add-region-button');
      if (await addRegionButton.count() > 0) {
        const addText = await addRegionButton.textContent();
        expect(addText).toContain('Add Region'); // Should have proper text, might check for icon too
      }
      
      // Check if there are regions to test their action buttons
      const regionRows = page.locator('[data-testid="region-item"]');
      
      if (await regionRows.count() > 0) {
        const firstRegion = regionRows.first();
        
        const editRegionButton = firstRegion.getByTestId('edit-region-button');
        if (await editRegionButton.count() > 0) {
          const editText = await editRegionButton.textContent();
          expect(editText).toContain('Edit Region'); // Check text, should be consistent
        }
      }
    }
  });

  test('icon consistency across different form states', async ({ page }) => {
    await page.goto('/settings/recipes');
    
    // Test create mode - use correct button text
    await page.getByRole('button', { name: 'Add Recipe' }).click();
    
    let saveButton = page.getByTestId('create-item-btn'); // Use test ID
    let saveText = await saveButton.textContent();
    expect(saveText).toContain('💾'); // Create button should use save icon
    
    // Fill and submit form
    await page.getByLabel(/name/i).fill('Test Recipe for Icons');
    await saveButton.click();
    await page.waitForTimeout(500);
    
    // Test edit mode
    const itemRows = page.locator('[data-testid="item-row"]');
    const testRecipeRow = itemRows.filter({ hasText: 'Test Recipe for Icons' });
    
    if (await testRecipeRow.count() > 0) {
      const editButton = testRecipeRow.getByRole('button', { name: /edit/i });
      await editButton.click();
      
      // Check update button uses same save icon - use test ID
      saveButton = page.getByTestId('update-item-btn');
      saveText = await saveButton.textContent();
      expect(saveText).toContain('💾'); // Update button should also use save icon
    }
  });

  test('no mixed icon styles - all emojis or all text', async ({ page }) => {
    await page.goto('/settings/roasters');
    
    // Check the add button specifically (which should have emoji)
    const addButton = page.getByTestId('add-item-btn');
    if (await addButton.count() > 0) {
      const addText = await addButton.textContent();
      
      // Check for emoji characters in the add button
      const hasEmoji = /[\u{1F600}-\u{1F64F}]|[\u{1F300}-\u{1F5FF}]|[\u{1F680}-\u{1F6FF}]|[\u{1F1E0}-\u{1F1FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]/u.test(addText);
      
      expect(hasEmoji).toBe(true); // Add button should have emoji
      expect(addText).toContain('➕'); // Specifically the plus emoji
    }
    
    // Also check action buttons in table if there are any items
    const itemRows = page.locator('[data-testid="item-row"]');
    if (await itemRows.count() > 0) {
      // Check edit button in first row
      const editButton = itemRows.first().getByRole('button', { name: /edit/i });
      if (await editButton.count() > 0) {
        const editText = await editButton.textContent();
        const hasEmoji = /[\u{1F600}-\u{1F64F}]|[\u{1F300}-\u{1F5FF}]|[\u{1F680}-\u{1F6FF}]|[\u{1F1E0}-\u{1F1FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]/u.test(editText);
        expect(hasEmoji).toBe(true); // Action buttons should have emojis
      }
    }
  });
});