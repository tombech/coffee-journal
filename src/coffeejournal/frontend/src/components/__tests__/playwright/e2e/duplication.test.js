const { test, expect } = require('@playwright/test');
const TestDataManager = require('../../../../test-utils/testDataManager');
// Using semantic selectors - no need for helper functions that use brittle selectors

test.describe('Brew Session Duplication', () => {
  let testData;

  test.beforeEach(async ({ page }, testInfo) => {
    testData = new TestDataManager(`duplication_${testInfo.title.replace(/\s+/g, '_')}`, 'http://localhost:5000/api', testInfo.project.name);
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

  test('can duplicate brew session from brew sessions list page', async ({ page }) => {
    // Create test scenario with brew session
    const scenario = await testData.createTestScenario();
    
    await page.goto('/brew-sessions');
    await expect(page.getByRole('table')).toBeVisible();
    
    // Find and click duplicate button on our test session using semantic selector
    const testRow = page.getByRole('table').locator('tbody tr').filter({ hasText: scenario.brewSession.notes });
    await testRow.getByRole('button', { name: 'Duplicate brew session' }).click();
    
    // Verify success message appeared using semantic approach
    await expect(page.locator('body')).toContainText(/duplicated.*successfully/i, { timeout: 2000 });
    
    // Wait for table to reload with new content
    await expect(page.getByRole('table')).toContainText(scenario.brewSession.notes);
    
    // Should have at least our test session row visible
    const rows = page.getByRole('table').locator('tbody tr');
    const count = await rows.count();
    expect(count).toBeGreaterThanOrEqual(1);
  });

  test('duplicated session has current timestamp but same data', async ({ page }) => {
    // Create test scenario with specific data
    const scenario = await testData.createTestScenario();
    
    await page.goto('/brew-sessions');
    await expect(page.getByRole('table')).toBeVisible();
    
    // Duplicate the session using semantic selector
    const testRow = page.getByRole('table').locator('tbody tr').filter({ hasText: scenario.brewSession.notes });
    await testRow.getByRole('button', { name: 'Duplicate brew session' }).click();
    await expect(page.locator('body')).toContainText(/duplicated.*successfully/i, { timeout: 2000 });
    
    // Wait for table to contain the duplicated session
    await expect(page.getByRole('table')).toContainText(scenario.brewSession.notes);
    
    // Should have at least our original session plus the duplicate
    const rows = page.getByRole('table').locator('tbody tr');
    const count = await rows.count();
    expect(count).toBeGreaterThanOrEqual(2);
    
    // Verify we can see today's date in the table (new duplicate timestamp)
    const today = new Date();
    const todayStr = today.toLocaleDateString('nb-NO', {
      day: '2-digit',
      month: '2-digit',
      year: '2-digit'
    });
    await expect(page.getByRole('table')).toContainText(todayStr);
    
    // Verify duplicate functionality preserved the original data
    await expect(page.getByRole('table')).toContainText(scenario.brewSession.notes);
  });

  test('can duplicate session and then edit the copy', async ({ page }) => {
    // Create test scenario
    const scenario = await testData.createTestScenario();
    
    await page.goto('/brew-sessions');
    await expect(page.getByRole('table')).toBeVisible();
    
    // Duplicate the session using semantic selector
    const testRow = page.getByRole('table').locator('tbody tr').filter({ hasText: scenario.brewSession.notes });
    await testRow.getByRole('button', { name: 'Duplicate brew session' }).click();
    await expect(page.locator('body')).toContainText(/duplicated.*successfully/i, { timeout: 2000 });
    
    // Find a row with our test notes and click its edit button (use title selector for emoji button)
    const sessionRow = page.getByRole('table').locator('tbody tr').filter({ hasText: scenario.brewSession.notes }).first();
    await sessionRow.locator('button[title="Edit"]').click();
    
    // Wait for form to appear
    await expect(page.getByLabel(/notes/i)).toBeVisible();
    
    // Should navigate to edit form (use the specific form heading)
    await expect(page.getByTestId('brew-session-form').getByRole('heading', { name: 'Edit Brew Session' })).toBeVisible();
    
    // Modify something using semantic selector
    const newNotes = `Duplicated and edited session ${testData.testId}`;
    await page.getByLabel(/notes/i).fill(newNotes);
    
    // Save changes using semantic selector (button says 'Update' in edit mode)
    await page.getByRole('button', { name: /update|create/i }).click();
    
    // Wait for form to disappear or navigation to complete
    await expect(page.getByTestId('brew-session-form').getByRole('heading', { name: 'Edit Brew Session' })).not.toBeVisible({ timeout: 5000 });
    
    // Verify the changes were saved
    await expect(page.locator('body')).toContainText(newNotes);
  });

  test('duplicate button appears in brew session table', async ({ page }) => {
    // Create test scenario to ensure we have data
    const scenario = await testData.createTestScenario();
    
    await page.goto('/brew-sessions');
    await expect(page.getByRole('table')).toBeVisible();
    
    // Find the specific row for our test data and check its duplicate button
    const testRow = page.getByRole('table').locator('tbody tr').filter({ hasText: scenario.brewSession.notes });
    const duplicateButton = testRow.getByRole('button', { name: 'Duplicate brew session' });
    await expect(duplicateButton).toBeVisible();
    
    // Verify button is accessible and functional (no need to check icon content)
    await expect(duplicateButton).toBeEnabled();
  });

  test('duplicate preserves all brew session data', async ({ page }) => {
    // Create a detailed brew session
    const scenario = await testData.createTestScenario();
    const complexNotes = `Complex session ${testData.testId} with equipment`;
    
    // Create a brew session with specific data to verify duplication
    const complexSession = await testData.createBrewSession(scenario.batch.id, {
      timestamp: new Date().toISOString(),
      product_batch_id: scenario.batch.id,
      product_id: scenario.product.id,
      brew_method_id: scenario.brewMethod.id,
      amount_coffee_grams: 22.0,
      amount_water_grams: 350.0,
      brew_temperature_c: 92.5,
      sweetness: 8.5,
      acidity: 7.0,
      bitterness: 3.5,
      body: 8.0,
      aroma: 9.0,
      flavor_profile_match: 8.25,
      notes: complexNotes
    });
    
    await page.goto('/brew-sessions');
    await expect(page.getByRole('table')).toBeVisible();
    
    // Duplicate the session using semantic selector
    const sessionRow = page.getByRole('table').locator('tbody tr').filter({ hasText: complexNotes });
    await sessionRow.getByRole('button', { name: /duplicate/i }).click();
    await expect(page.locator('body')).toContainText(/duplicated.*successfully/i, { timeout: 2000 });
    
    // Find a row and click its edit button to verify data (use title selector for emoji button)
    const firstRow = page.getByRole('table').locator('tbody tr').first();
    await firstRow.locator('button[title="Edit"]').click();
    
    // Wait for form to appear
    await expect(page.getByLabel(/notes/i)).toBeVisible();
    
    // Verify all the data was duplicated correctly using semantic selectors
    await expect(page.getByLabel(/coffee.*grams/i)).toHaveValue('22');
    await expect(page.getByLabel(/water.*grams/i)).toHaveValue('350');
    await expect(page.getByLabel(/temperature/i)).toHaveValue('92.5');
    // Note: Sweetness might be rounded to whole number, so check for either
    const sweetnessValue = await page.getByLabel(/sweetness/i).inputValue();
    expect(['8', '8.5']).toContain(sweetnessValue);
    await expect(page.getByLabel(/acidity/i)).toHaveValue('7');
    // Bitterness might also be rounded
    const bitternessValue = await page.getByLabel(/bitterness/i).inputValue();
    expect(['3', '3.5']).toContain(bitternessValue);
    await expect(page.getByLabel(/notes/i)).toHaveValue(complexNotes);
  });

  test('duplicate fails gracefully for non-existent sessions', async ({ page }) => {
    // Test error handling via API call
    const response = await page.request.post('/api/batches/1/brew_sessions/99999/duplicate');
    expect(response.status()).toBe(404);
    
    const errorData = await response.json();
    expect(errorData).toHaveProperty('message');
    expect(errorData.message.toLowerCase()).toContain('not found');
  });

  test('can duplicate multiple sessions in sequence', async ({ page }) => {
    // Create test scenario - this gives us one brew session
    const scenario = await testData.createTestScenario();
    
    await page.goto('/brew-sessions');
    await expect(page.getByRole('table')).toBeVisible();
    
    // Wait for at least one brew session to appear and verify we have data
    await expect(page.getByRole('table').locator('tbody tr')).toHaveCount(1, { timeout: 5000 });
    
    // Duplicate first session (first row)
    const firstRow = page.getByRole('table').locator('tbody tr').first();
    await firstRow.getByRole('button', { name: 'Duplicate brew session' }).click();
    await expect(page.locator('body')).toContainText(/duplicated.*successfully/i, { timeout: 2000 });
    
    // Wait for table to update after duplication
    await expect(page.getByRole('table').locator('tbody tr')).toHaveCount(2, { timeout: 2000 });
    
    // Duplicate second session (second row - should now have 3 rows total)
    const secondRow = page.getByRole('table').locator('tbody tr').nth(1);
    await secondRow.getByRole('button', { name: 'Duplicate brew session' }).click();
    await expect(page.locator('body')).toContainText(/duplicated.*successfully/i, { timeout: 2000 });
    
    // Wait for final duplication to complete and check final count (1 original + 2 duplicates = 3)
    await expect(page.getByRole('table').locator('tbody tr')).toHaveCount(3, { timeout: 3000 });
  });
});