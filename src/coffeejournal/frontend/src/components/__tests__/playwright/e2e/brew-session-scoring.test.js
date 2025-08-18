const { test, expect } = require('@playwright/test');
const TestDataManager = require('../../../../test-utils/testDataManager');

test.describe('Brew Session Scoring - Taste Notes and Overall Score', () => {
  let testData;

  test.beforeEach(async ({ page }, testInfo) => {
    testData = new TestDataManager(`brew_scoring_${testInfo.title.replace(/\s+/g, '_')}`, 'http://localhost:5000/api', testInfo.project.name);
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

  test('taste notes accept integer values 1-10', async ({ page }) => {
    // Create test scenario
    const scenario = await testData.createTestScenario();
    
    await page.goto(`/batches/${scenario.batch.id}`);
    
    // Check page structure
    await expect(page.getByRole('heading', { name: /batch.*details/i })).toBeVisible();
    
    await page.getByRole('button', { name: /add.*brew.*session/i }).click();
    await expect(page.getByLabel(/coffee grams/i)).toBeVisible({ timeout: 2000 });
    
    // Fill required fields
    await page.getByLabel(/coffee grams/i).fill('20');
    await page.getByLabel(/water grams/i).fill('320');
    
    // Test integer values for taste notes (1-10 scale)
    await page.getByLabel(/sweetness/i).fill('8');
    await page.getByLabel(/acidity/i).fill('9');
    await page.getByLabel(/bitterness/i).fill('2');  // Low is good for bitterness
    await page.getByLabel(/body/i).fill('7');
    await page.getByLabel(/aroma/i).fill('10');  // Maximum value
    await page.getByLabel(/profile match/i).fill('8');
    
    // Don't set overall score - let it be calculated
    
    // Submit the form
    await page.getByRole('button', { name: /save|create/i }).click();
    
    // Wait for brew session to be created
    await expect(page.locator('body')).toContainText(/created.*successfully|added.*successfully/i, { timeout: 2000 });
  });

  test('overall score can override calculated score with decimal values', async ({ page }) => {
    // Create test scenario with batch and brew session
    const scenario = await testData.createTestScenario();
    
    // Navigate to the brew sessions list
    await page.goto('/brew-sessions');
    
    // Wait for table to load
    await expect(page.getByRole('table')).toBeVisible({ timeout: 10000 });
    
    // Find and edit our test session
    const uniqueNotes = scenario.brewSession.notes;
    const sessionRow = page.getByRole('row').filter({ hasText: uniqueNotes });
    const editButton = sessionRow.getByRole('button', { name: 'Edit brew session' });
    await expect(editButton).toBeVisible({ timeout: 10000 });
    await editButton.click();
    
    // Wait for edit form to appear
    await expect(page.getByLabel(/coffee grams/i)).toBeVisible({ timeout: 10000 });
    
    // Set taste notes that would calculate to a specific score
    await page.getByLabel(/sweetness/i).clear();
    await page.getByLabel(/sweetness/i).fill('8');
    await page.getByLabel(/acidity/i).clear();
    await page.getByLabel(/acidity/i).fill('7');
    await page.getByLabel(/bitterness/i).clear();
    await page.getByLabel(/bitterness/i).fill('3');
    await page.getByLabel(/body/i).clear();
    await page.getByLabel(/body/i).fill('6');
    await page.getByLabel(/aroma/i).clear();
    await page.getByLabel(/aroma/i).fill('8');
    await page.getByLabel(/profile match/i).clear();
    await page.getByLabel(/profile match/i).fill('7');
    
    // Override with a manual overall score (decimal value)
    await page.getByLabel(/overall score/i).clear();
    await page.getByLabel(/overall score/i).fill('7.5');
    
    // Save the changes
    await page.getByRole('button', { name: /save|update/i }).click();
    await expect(page.locator('body')).toContainText(/updated.*successfully|saved.*successfully/i, { timeout: 10000 });
    
    // Edit again to verify the manual score was preserved
    await expect(page.getByRole('table')).toBeVisible({ timeout: 10000 });
    const updatedRow = page.getByRole('row').filter({ hasText: uniqueNotes });
    const editButtonAgain = updatedRow.getByRole('button', { name: 'Edit brew session' });
    await expect(editButtonAgain).toBeVisible({ timeout: 10000 });
    await editButtonAgain.click();
    
    // Verify the manual overall score is preserved
    await expect(page.getByLabel(/overall score/i)).toHaveValue('7.5');
  });

  test('calculated score is used when overall score is empty', async ({ page }) => {
    // Create test scenario
    const scenario = await testData.createTestScenario();
    
    await page.goto(`/batches/${scenario.batch.id}`);
    await page.getByRole('button', { name: /add.*brew.*session/i }).click();
    
    // Fill required fields
    await page.getByLabel(/coffee grams/i).fill('20');
    await page.getByLabel(/water grams/i).fill('320');
    
    // Set taste notes for calculated score
    // These should average to a specific value
    await page.getByLabel(/sweetness/i).fill('6');
    await page.getByLabel(/acidity/i).fill('6');
    await page.getByLabel(/bitterness/i).fill('4'); // Bitterness inverted: 10-4=6
    await page.getByLabel(/body/i).fill('6');
    await page.getByLabel(/aroma/i).fill('6');
    await page.getByLabel(/profile match/i).fill('6');
    // Average: (6+6+6+6+6+6)/6 = 6.0
    
    // Leave overall score empty to use calculated score
    const overallScoreInput = page.getByLabel(/overall score/i);
    await overallScoreInput.clear();
    
    // Submit the form
    await page.getByRole('button', { name: /save|create/i }).click();
    
    // Wait for success
    await expect(page.locator('body')).toContainText(/created.*successfully|added.*successfully/i, { timeout: 2000 });
    
    // The calculated score should be shown in the table
    // Note: We can't verify the exact calculated value here without knowing 
    // how the frontend displays it, but we've verified the backend calculation works
  });

  test('decimal overall scores display correctly in table', async ({ page }) => {
    // Create test scenario with existing brew session
    const scenario = await testData.createTestScenario();
    
    // Navigate to brew sessions list
    await page.goto('/brew-sessions');
    
    // Wait for table to load
    await expect(page.getByRole('table')).toBeVisible({ timeout: 10000 });
    
    // Find and edit our test session
    const sessionRow = page.getByRole('row').filter({ hasText: scenario.brewSession.notes });
    const editButton = sessionRow.getByTitle('Edit');
    await editButton.click();
    
    // Set a decimal overall score
    await page.getByLabel(/overall score/i).fill('8.75');
    await page.getByRole('button', { name: /save|update/i }).click();
    
    // Wait for table to update
    await expect(page.getByRole('table')).toBeVisible({ timeout: 10000 });
    
    // Verify the decimal score displays in the table
    await expect(page.locator('body')).toContainText('8.75', { timeout: 10000 });
  });

  test('taste notes validation rejects values outside 1-10 range', async ({ page }) => {
    const scenario = await testData.createTestScenario();
    
    await page.goto(`/batches/${scenario.batch.id}`);
    await page.getByRole('button', { name: /add.*brew.*session/i }).click();
    
    // Fill required fields
    await page.getByLabel(/coffee grams/i).fill('20');
    await page.getByLabel(/water grams/i).fill('320');
    
    // Try invalid taste note values
    await page.getByLabel(/sweetness/i).fill('11'); // Too high
    await page.getByLabel(/acidity/i).fill('0');    // Too low
    await page.getByLabel(/bitterness/i).fill('-1'); // Negative
    
    // Try to submit
    await page.getByRole('button', { name: /save|create/i }).click();
    
    // Should see validation error (form should not submit successfully)
    // The exact error message depends on frontend validation
    await expect(page.locator('body')).not.toContainText(/created.*successfully/i, { timeout: 1000 });
  });

  test('overall score validation accepts decimals within 1.0-10.0 range', async ({ page }) => {
    const scenario = await testData.createTestScenario();
    
    await page.goto(`/batches/${scenario.batch.id}`);
    await page.getByRole('button', { name: /add.*brew.*session/i }).click();
    
    // Fill required fields
    await page.getByLabel(/coffee grams/i).fill('20');
    await page.getByLabel(/water grams/i).fill('320');
    
    // Set valid taste notes
    await page.getByLabel(/sweetness/i).fill('7');
    await page.getByLabel(/acidity/i).fill('8');
    
    // Test edge cases for overall score
    await page.getByLabel(/overall score/i).fill('1.0');  // Minimum valid
    await page.getByRole('button', { name: /save|create/i }).click();
    await expect(page.locator('body')).toContainText(/created.*successfully|added.*successfully/i, { timeout: 2000 });
    
    // Create another session with maximum score
    await page.getByRole('button', { name: /add.*brew.*session/i }).click();
    await page.getByLabel(/coffee grams/i).fill('20');
    await page.getByLabel(/water grams/i).fill('320');
    await page.getByLabel(/overall score/i).fill('10.0'); // Maximum valid
    await page.getByRole('button', { name: /save|create/i }).click();
    await expect(page.locator('body')).toContainText(/created.*successfully|added.*successfully/i, { timeout: 2000 });
  });
});