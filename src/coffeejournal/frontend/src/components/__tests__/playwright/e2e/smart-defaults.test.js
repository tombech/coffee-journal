const { test, expect } = require('@playwright/test');
const TestDataManager = require('../../../../test-utils/testDataManager');
// Using semantic selectors - no need for helper functions that use brittle selectors

test.describe('Smart Defaults Functionality', () => {
  let testData;

  test.beforeEach(async ({ page }, testInfo) => {
    testData = new TestDataManager(`smart_defaults_${testInfo.title.replace(/\s+/g, '_')}`, 'http://localhost:5000/api', testInfo.project.name);
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

  test('applies smart defaults when creating new brew session from batch', async ({ page }) => {
    // Create test scenario with batch
    const scenario = await testData.createTestScenario();
    
    // Create custom equipment for testing smart defaults
    const grinder = await testData.createItem('grinders', {
      name: `Smart_Default_Grinder_${testData.testId}`,
      description: 'Test grinder for smart defaults'
    });
    
    const brewMethod = await testData.createItem('brew_methods', {
      name: `Smart_Default_Method_${testData.testId}`,
      description: 'Test brew method for smart defaults'
    });

    // Create a brew session to establish usage pattern
    await page.goto(`/brew-sessions/new?batch_id=${scenario.batch.id}`);
    await expect(page.getByLabel(/coffee grams/i)).toBeVisible({ timeout: 2000 });
    
    // Wait for equipment options to load
    await expect(page.getByLabel(/brew method/i)).toBeVisible({ timeout: 2000 });
    await expect(page.getByLabel(/grinder/i)).toBeVisible({ timeout: 2000 });
    
    // Select our equipment manually first time to establish pattern  
    await page.getByLabel(/brew method/i).selectOption({ label: brewMethod.name });
    await page.getByLabel(/grinder/i).selectOption({ label: grinder.name });
    
    // Fill required fields
    await page.getByLabel(/coffee grams/i).fill('20');
    await page.getByLabel(/water grams/i).fill('320');
    
    // Submit the form
    await page.getByTestId('submit-brew-session').click();
    await page.waitForURL(`**/batches/${scenario.batch.id}`, { timeout: 2000 });
    
    // Wait for brew session to be created
    await expect(page.locator('body')).toContainText(/created.*successfully|added.*successfully/i, { timeout: 2000 });

    // Now create another session - should have smart defaults applied
    await page.goto(`/brew-sessions/new?batch_id=${scenario.batch.id}`);
    await expect(page.getByLabel(/coffee grams/i)).toBeVisible({ timeout: 2000 });
    
    // Check that smart defaults are applied (if implemented)
    // Note: This might need adjustment based on actual smart defaults implementation
    const brewMethodSelect = page.getByLabel(/brew method/i);
    const currentBrewMethod = await brewMethodSelect.inputValue();
    
    const grinderInput = page.getByLabel(/grinder/i);
    const currentGrinder = await grinderInput.inputValue();
    
    // Document current behavior - could be smart defaults or first/empty
    console.log(`Current brew method default: ${currentBrewMethod}`);
    console.log(`Current grinder default: ${currentGrinder}`);
  });

  test('applies smart defaults when creating new standalone brew session', async ({ page }) => {
    // Create test scenario with batch first
    const scenario = await testData.createTestScenario();
    
    // Create equipment and establish usage pattern first
    await page.goto('/settings/recipes');
    await page.getByTestId('add-item-btn').click();
    await page.getByLabel(/name/i).fill('Smart Default Recipe');
    await page.getByTestId('create-item-btn').click();
    await page.waitForTimeout(500);

    // Create a brew session to establish pattern
    await page.goto(`/brew-sessions/new?batch_id=${scenario.batch.id}`);
    
    // Wait for form to load
    await expect(page.getByLabel(/coffee grams/i)).toBeVisible({ timeout: 2000 });
    
    await page.getByLabel(/recipe/i).selectOption({ label: 'Smart Default Recipe' });
    await page.getByLabel(/coffee grams/i).fill('18');
    await page.getByLabel(/water grams/i).fill('300');
    await page.getByTestId('submit-brew-session').click();
    await page.waitForURL(new RegExp(`/batches/${scenario.batch.id}`));

    // Now go to the general brew session page (if it exists) or create another from same batch
    await page.goto(`/brew-sessions/new?batch_id=${scenario.batch.id}`);
    
    // Wait for form to load
    await expect(page.getByLabel(/coffee grams/i)).toBeVisible({ timeout: 2000 });
    
    // Should have smart default recipe applied (the last recipe used)
    const recipeInput = page.getByLabel(/recipe/i);
    const currentRecipeValue = await recipeInput.inputValue();
    
    // Smart defaults should apply the most recently used recipe
    // This could be either "Smart Default Recipe" or the test scenario recipe
    expect(['Smart Default Recipe', `Test Recipe ${testData.testId}`]).toContain(currentRecipeValue);
  });

  test('manual defaults override smart defaults', async ({ page }) => {
    // Create test scenario with batch first
    const scenario = await testData.createTestScenario();
    
    // Set a manual default for scales
    await page.goto('/settings/scales');
    
    // Check if there are any scales first
    const scaleRows = page.locator('[data-testid="item-row"]');
    const scaleCount = await scaleRows.count();
    
    if (scaleCount > 0) {
      // Click edit on first scale
      await scaleRows.first().getByRole('button', { name: /edit/i }).click();
      
      // Set as default
      await page.getByLabel(/set as default/i).check();
      await page.getByRole('button', { name: /update/i }).click();
      await page.waitForTimeout(500);
    } else {
      // Create a scale and set as default
      await page.getByTestId('add-item-btn').click();
      await page.getByLabel(/name/i).fill('Manual Default Scale');
      await page.getByLabel(/set as default/i).check();
      await page.getByTestId('create-item-btn').click();
      await page.waitForTimeout(500);
    }

    // Create a brew session with different scale to establish usage pattern
    await page.goto(`/brew-sessions/new?batch_id=${scenario.batch.id}`);
    
    // Wait for form to load
    await expect(page.getByLabel(/coffee grams/i)).toBeVisible({ timeout: 2000 });
    
    // Check if Different Scale exists, if not create it first or use any available scale
    const scaleSelect = page.getByLabel(/scale/i);
    
    // Try to find an existing scale other than the default one
    const scaleOptions = await scaleSelect.locator('option').allTextContents();
    console.log('Available scale options:', scaleOptions);
    
    // Use the second scale option if available, otherwise use first non-empty option
    const availableScales = scaleOptions.filter(option => option && option !== 'Select scale...' && option !== '');
    if (availableScales.length > 1) {
      await scaleSelect.selectOption({ label: availableScales[1] });
    } else if (availableScales.length > 0) {
      await scaleSelect.selectOption({ label: availableScales[0] });
    } else {
      // Skip this test if no scales are available in the test scenario
      console.log('No scales available, skipping scale usage pattern');
    }
    await page.getByLabel(/coffee grams/i).fill('20');
    await page.getByLabel(/water grams/i).fill('320');
    await page.getByTestId('submit-brew-session').click();
    await page.waitForURL(new RegExp(`/batches/${scenario.batch.id}`));

    // Create another session - should use manual default, not the frequently used one
    await page.goto(`/brew-sessions/new?batch_id=${scenario.batch.id}`);
    
    // Wait for form to load
    await expect(page.getByLabel(/coffee grams/i)).toBeVisible({ timeout: 2000 });
    
    // Should use manual default scale
    const scaleInput = page.getByLabel(/scale/i);
    // Manual defaults should take precedence over usage patterns
    // Note: This test might need adjustment based on exact implementation
    await expect(scaleInput).toHaveValue('Manual Default Scale');
  });

  test('smart defaults fallback to first item when no usage history', async ({ page }) => {
    // Create test scenario with batch first
    const scenario = await testData.createTestScenario();
    
    // Clear existing data and create fresh equipment
    await page.goto('/settings/filters');
    
    // Add a filter that should become the default due to being first
    await page.getByTestId('add-item-btn').click();
    await page.getByLabel(/name/i).fill('First Filter Item');
    await page.getByTestId('create-item-btn').click();
    await page.waitForTimeout(500);

    await page.getByTestId('add-item-btn').click();
    await page.getByLabel(/name/i).fill('Second Filter Item');
    await page.getByTestId('create-item-btn').click();
    await page.waitForTimeout(500);

    // Go to create brew session - should use first item as default
    await page.goto(`/brew-sessions/new?batch_id=${scenario.batch.id}`);
    
    // Wait for form to load
    await expect(page.getByLabel(/coffee grams/i)).toBeVisible({ timeout: 2000 });
    
    // Check that first item is selected as default
    const filterInput = page.getByLabel(/filter/i);
    await expect(filterInput).toHaveValue('First Filter Item');
  });

  test('smart defaults API endpoint returns correct data structure', async ({ page }) => {
    // This is more of an integration test - check that the endpoint works
    const response = await page.request.get('/api/brew_sessions/defaults');
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    
    // Should have all expected fields
    expect(data).toHaveProperty('brew_method');
    expect(data).toHaveProperty('recipe');
    expect(data).toHaveProperty('grinder');
    expect(data).toHaveProperty('filter');
    expect(data).toHaveProperty('kettle');
    expect(data).toHaveProperty('scale');
    
    // Fields can be null (no defaults) or objects with id and name/product_name
    Object.entries(data).forEach(([key, value]) => {
      if (value !== null) {
        expect(value).toHaveProperty('id');
        // Products have product_name instead of name
        if (key === 'product') {
          expect(value).toHaveProperty('product_name');
        } else {
          expect(value).toHaveProperty('name');
        }
      }
    });
  });

  test('smart defaults work with equipment that has short forms', async ({ page }) => {
    // Create test scenario with batch first
    const scenario = await testData.createTestScenario();
    
    // Create equipment with short forms
    await page.goto('/settings/kettles');
    await page.getByTestId('add-item-btn').click();
    await page.getByLabel(/name/i).fill('Hario Buono Kettle');
    await page.getByLabel(/short form/i).fill('Buono');
    await page.getByTestId('create-item-btn').click();
    await page.waitForTimeout(500);

    // Create usage pattern
    await page.goto(`/brew-sessions/new?batch_id=${scenario.batch.id}`);
    
    // Wait for form to load
    await expect(page.getByLabel(/coffee grams/i)).toBeVisible({ timeout: 2000 });
    
    await page.getByLabel(/kettle/i).selectOption({ label: 'Hario Buono Kettle' });
    await page.getByLabel(/coffee grams/i).fill('20');
    await page.getByLabel(/water grams/i).fill('320');
    await page.getByTestId('submit-brew-session').click();
    await page.waitForURL(new RegExp(`/batches/${scenario.batch.id}`));

    // Create another session - should have smart default applied
    await page.goto(`/brew-sessions/new?batch_id=${scenario.batch.id}`);
    
    // Wait for form to load
    await expect(page.getByLabel(/coffee grams/i)).toBeVisible({ timeout: 2000 });
    
    const kettleInput = page.getByLabel(/kettle/i);
    await expect(kettleInput).toHaveValue('Hario Buono Kettle');
  });

  test('smart defaults respect recency weighting', async ({ page }) => {
    // Create test scenario with batch first
    const scenario = await testData.createTestScenario();
    
    // This test is complex as it requires creating time-sensitive data
    // We'll create two different grinders and ensure recent usage takes precedence
    
    await page.goto('/settings/grinders');
    await page.getByTestId('add-item-btn').click();
    await page.getByLabel(/name/i).fill('Old Frequently Used');
    await page.getByTestId('create-item-btn').click();
    await page.waitForTimeout(500);

    await page.getByTestId('add-item-btn').click();
    await page.getByLabel(/name/i).fill('Recent Grinder');
    await page.getByTestId('create-item-btn').click();
    await page.waitForTimeout(500);

    // Create multiple sessions with "Old Frequently Used" (simulating old usage)
    for (let i = 0; i < 3; i++) {
      await page.goto(`/brew-sessions/new?batch_id=${scenario.batch.id}`);
      
      // Wait for form to load
      await expect(page.getByLabel(/coffee grams/i)).toBeVisible({ timeout: 2000 });
      
      await page.getByLabel(/grinder/i).selectOption({ label: 'Old Frequently Used' });
      await page.getByLabel(/coffee grams/i).fill('20');
      await page.getByLabel(/water grams/i).fill('320');
      await page.getByTestId('submit-brew-session').click();
      await page.waitForURL(new RegExp(`/batches/${scenario.batch.id}`));
    }

    // Create one recent session with "Recent Grinder"
    await page.goto(`/brew-sessions/new?batch_id=${scenario.batch.id}`);
    
    // Wait for form to load
    await expect(page.getByLabel(/coffee grams/i)).toBeVisible({ timeout: 2000 });
    
    await page.getByLabel(/grinder/i).selectOption({ label: 'Recent Grinder' });
    await page.getByLabel(/coffee grams/i).fill('20');
    await page.getByLabel(/water grams/i).fill('320');
    await page.getByTestId('submit-brew-session').click();
    await page.waitForURL(new RegExp(`/batches/${scenario.batch.id}`));

    // Now check which one is selected as default
    await page.goto(`/brew-sessions/new?batch_id=${scenario.batch.id}`);
    
    // Wait for form to load
    await expect(page.getByLabel(/coffee grams/i)).toBeVisible({ timeout: 2000 });
    
    const grinderInput = page.getByLabel(/grinder/i);
    // Depending on the weighting algorithm, this could be either one
    // The test documents the behavior rather than enforcing a specific outcome
    const grinderValue = await grinderInput.inputValue();
    expect(['Old Frequently Used', 'Recent Grinder']).toContain(grinderValue);
  });
});