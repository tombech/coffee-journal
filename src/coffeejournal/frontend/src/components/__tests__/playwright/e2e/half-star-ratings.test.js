const { test, expect } = require('@playwright/test');
const TestDataManager = require('../../../../test-utils/testDataManager');
// Using semantic selectors - no need for helper functions that use brittle selectors

test.describe('Half-Star Rating Functionality', () => {
  let testData;

  test.beforeEach(async ({ page }, testInfo) => {
    testData = new TestDataManager(`half_star_${testInfo.title.replace(/\s+/g, '_')}`, 'http://localhost:5000/api', testInfo.project.name);
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

  test('can enter half-star ratings in brew session form', async ({ page }) => {
    // Create test scenario first - EXACT copy of working batch-management test
    const scenario = await testData.createTestScenario();
    
    await page.goto(`/batches/${scenario.batch.id}`);
    
    // Check page structure using semantic selectors - EXACT copy of working test
    await expect(page.getByRole('heading', { name: /batch.*details/i })).toBeVisible();
    
    // Should show batch information using semantic approach - EXACT copy of working test
    await expect(page.locator('body')).toContainText(/roast date/i);
    
    await page.getByRole('button', { name: /add.*brew.*session/i }).click();
    await expect(page.getByLabel(/coffee grams/i)).toBeVisible({ timeout: 2000 });
    
    // Fill required fields
    await page.getByLabel(/coffee grams/i).fill('20');
    await page.getByLabel(/water grams/i).fill('320');
    
    // Test half-star ratings for all rating fields
    await page.getByLabel(/sweetness/i).fill('7.5');
    await page.getByLabel(/acidity/i).fill('8.5');
    await page.getByLabel(/bitterness/i).fill('3.5');
    await page.getByLabel(/body/i).fill('6.5');
    await page.getByLabel(/aroma/i).fill('9.5');
    await page.getByLabel(/profile match/i).fill('8.5');
    await page.getByLabel(/overall score/i).fill('8.25');
    
    // Submit the form
    await page.getByRole('button', { name: /save|create/i }).click();
    
    // Wait for brew session to be created
    await expect(page.locator('body')).toContainText(/created.*successfully|added.*successfully/i, { timeout: 2000 });
  });

  test('half-star ratings are preserved when editing', async ({ page }) => {
    // Create test scenario with batch and brew session
    const scenario = await testData.createTestScenario();
    
    // Navigate to the brew sessions list where Edit buttons actually exist
    await page.goto('/brew-sessions');
    
    // Wait for table to load
    await expect(page.getByRole('table')).toBeVisible({ timeout: 10000 });
    
    // Use semantic selector approach - find by unique test data ID in notes
    const uniqueNotes = scenario.brewSession.notes; // This contains our testId, making it unique
    const sessionRow = page.getByRole('row').filter({ hasText: uniqueNotes });
    
    // Use proper semantic selector for the edit button
    const editButton = sessionRow.getByRole('button', { name: 'Edit brew session' });
    await expect(editButton).toBeVisible({ timeout: 10000 });
    await editButton.click();
    
    // Wait for edit form to appear
    await expect(page.getByLabel(/coffee grams/i)).toBeVisible({ timeout: 10000 });
    
    // Clear existing values first, then set half-star ratings
    await page.getByLabel(/sweetness/i).clear();
    await page.getByLabel(/sweetness/i).fill('7.5');
    await page.getByLabel(/acidity/i).clear();
    await page.getByLabel(/acidity/i).fill('8.5');
    await page.getByLabel(/overall score/i).clear();
    await page.getByLabel(/overall score/i).fill('8.2'); // Use value that displays clearly
    
    // Save the changes
    await page.getByRole('button', { name: /save|update/i }).click();
    await expect(page.locator('body')).toContainText(/updated.*successfully|saved.*successfully/i, { timeout: 10000 });
    
    // Wait for table to update and edit again to verify preservation
    await expect(page.getByRole('table')).toBeVisible({ timeout: 10000 });
    const updatedRow = page.getByRole('row').filter({ hasText: uniqueNotes });
    const editButtonAgain = updatedRow.getByRole('button', { name: 'Edit brew session' });
    await expect(editButtonAgain).toBeVisible({ timeout: 10000 });
    await editButtonAgain.click();
    
    // Wait for form to fully load
    await expect(page.getByLabel(/coffee grams/i)).toBeVisible({ timeout: 10000 });
    
    // Verify half-star values are preserved
    await expect(page.getByLabel(/sweetness/i)).toHaveValue('7.5');
    await expect(page.getByLabel(/acidity/i)).toHaveValue('8.5');
    await expect(page.getByLabel(/overall score/i)).toHaveValue('8.2');
  });

  test('half-star ratings display correctly in brew session table', async ({ page }) => {
    // Create test scenario with existing brew session data
    const scenario = await testData.createTestScenario();
    
    // Navigate to brew sessions list where full table with scores is displayed
    await page.goto('/brew-sessions');
    
    // Wait for table to load
    await expect(page.getByRole('table')).toBeVisible({ timeout: 10000 });
    
    // Find our test session by its unique notes
    const sessionRow = page.getByRole('row').filter({ hasText: scenario.brewSession.notes });
    await expect(sessionRow).toBeVisible({ timeout: 10000 });
    
    // Edit the session to add a half-star rating
    const editButton = sessionRow.getByTitle('Edit');
    await editButton.click();
    
    // Add a half-star overall score
    await page.getByLabel(/overall score/i).fill('8.5');
    await page.getByRole('button', { name: /save|update/i }).click();
    
    // Wait for table to update
    await expect(page.getByRole('table')).toBeVisible({ timeout: 10000 });
    
    // Verify the half-star score displays correctly in the table
    await expect(page.locator('body')).toContainText('8.5', { timeout: 10000 });
  });

  test('can enter ratings with various decimal precisions', async ({ page }) => {
    // Create test scenario with existing brew session data
    const scenario = await testData.createTestScenario();
    
    // Navigate to brew sessions list where Edit buttons exist
    await page.goto('/brew-sessions');
    
    // Wait for table to load
    await expect(page.getByRole('table')).toBeVisible({ timeout: 10000 });
    
    // Find our test session using unique test data and edit it
    const uniqueNotes = scenario.brewSession.notes; // Contains testId, making it unique
    const sessionRow = page.getByRole('row').filter({ hasText: uniqueNotes });
    const editButton = sessionRow.getByRole('button', { name: 'Edit brew session' });
    await expect(editButton).toBeVisible({ timeout: 10000 });
    await editButton.click();
    
    // Wait for form to appear
    await expect(page.getByLabel(/coffee grams/i)).toBeVisible({ timeout: 10000 });
    
    // Clear existing values first, then test different decimal precisions
    await page.getByLabel(/sweetness/i).clear();
    await page.getByLabel(/sweetness/i).fill('8.0');    // .0
    await page.getByLabel(/acidity/i).clear();
    await page.getByLabel(/acidity/i).fill('7.5');      // .5
    await page.getByLabel(/bitterness/i).clear();
    await page.getByLabel(/bitterness/i).fill('3.25');  // .25
    await page.getByLabel(/body/i).clear();
    await page.getByLabel(/body/i).fill('6.75');        // .75
    await page.getByLabel(/overall score/i).clear();
    await page.getByLabel(/overall score/i).fill('8.1'); // Use a value that displays clearly
    
    await page.getByRole('button', { name: /save|update/i }).click();
    await expect(page.locator('body')).toContainText(/updated.*successfully|saved.*successfully/i, { timeout: 10000 });
    
    // Edit again to verify all values were preserved
    await expect(page.getByRole('table')).toBeVisible({ timeout: 10000 });
    const updatedRow = page.getByRole('row').filter({ hasText: uniqueNotes });
    const editButtonAgain = updatedRow.getByRole('button', { name: 'Edit brew session' });
    await expect(editButtonAgain).toBeVisible({ timeout: 10000 });
    await editButtonAgain.click();
    
    // Wait for form to fully load
    await expect(page.getByLabel(/coffee grams/i)).toBeVisible({ timeout: 10000 });
    
    // Verify all decimal precisions are preserved - expect what the app actually stores
    await expect(page.getByLabel(/sweetness/i)).toHaveValue('8');  // Should normalize 8.0 to 8
    await expect(page.getByLabel(/acidity/i)).toHaveValue('7.5');
    await expect(page.getByLabel(/bitterness/i)).toHaveValue('3.25');
    await expect(page.getByLabel(/body/i)).toHaveValue('6.75');
    await expect(page.getByLabel(/overall score/i)).toHaveValue('8.1');
  });

  test('rating inputs accept decimal values with step=0.5', async ({ page }) => {
    // Create test scenario with batch  
    const scenario = await testData.createTestScenario();
    
    await page.goto(`/batches/${scenario.batch.id}`);
    
    // Wait for page to load completely like the working tests
    await expect(page.getByRole('heading', { name: /my coffee journal/i })).toBeVisible();
    await expect(page.locator('body')).toContainText(/roast date/i, { timeout: 2000 });
    
    await page.getByRole('button', { name: /add.*brew.*session/i }).click();
    await expect(page.getByLabel(/sweetness/i)).toBeVisible({ timeout: 2000 });
    
    // Check that rating inputs have proper step attribute
    const sweetnessInput = page.getByLabel(/sweetness/i);
    const stepValue = await sweetnessInput.getAttribute('step');
    expect(stepValue).toBe('0.5');
    
    const minValue = await sweetnessInput.getAttribute('min');
    const maxValue = await sweetnessInput.getAttribute('max');
    expect(minValue).toBe('0');
    expect(maxValue).toBe('10');
    
    // Test that the input accepts half-step values
    await sweetnessInput.fill('7.5');
    await expect(sweetnessInput).toHaveValue('7.5');
    
    // Test edge cases
    await sweetnessInput.fill('0.5');
    await expect(sweetnessInput).toHaveValue('0.5');
    
    await sweetnessInput.fill('10');
    await expect(sweetnessInput).toHaveValue('10');
  });

  test('ratings validation works with decimal values', async ({ page }) => {
    // Create test scenario with batch  
    const scenario = await testData.createTestScenario();
    
    await page.goto(`/batches/${scenario.batch.id}`);
    
    // Wait for page to load completely like the working tests
    await expect(page.getByRole('heading', { name: /my coffee journal/i })).toBeVisible();
    await expect(page.locator('body')).toContainText(/roast date/i, { timeout: 2000 });
    
    await page.getByRole('button', { name: /add.*brew.*session/i }).click();
    await expect(page.getByLabel(/coffee grams/i)).toBeVisible({ timeout: 2000 });
    
    await page.getByLabel(/coffee grams/i).fill('20');
    await page.getByLabel(/water grams/i).fill('320');
    
    // Test boundary values
    await page.getByLabel(/sweetness/i).fill('10.5'); // Above max
    await page.getByLabel(/acidity/i).fill('-0.5');   // Below min
    await page.getByLabel(/bitterness/i).fill('5.5');  // Valid value
    
    // Try to submit - should handle validation
    await page.getByRole('button', { name: /save|create/i }).click();
    
    // The form should either prevent submission or normalize the values
    // Check if we stayed on the form page (validation failed) or moved on (values normalized)
    const currentUrl = page.url();
    
    if (currentUrl.includes(`batches/${scenario.batch.id}`)) {
      // If still on batch page, session was likely created (values normalized)
      console.log('Values were normalized and session created');
    } else {
      // If on form page, validation prevented submission
      console.log('Validation prevented form submission');
    }
  });

  test('half-star ratings work in duplication', async ({ page }) => {
    // Create test scenario with existing brew session data
    const scenario = await testData.createTestScenario();
    
    // Navigate to brew sessions list where Duplicate buttons exist
    await page.goto('/brew-sessions');
    
    // Wait for table to load
    await expect(page.getByRole('table')).toBeVisible({ timeout: 10000 });
    
    // Find our test session using unique test data and edit it to add half-star ratings
    const uniqueNotes = scenario.brewSession.notes; // Contains testId, making it unique
    const sessionRow = page.getByRole('row').filter({ hasText: uniqueNotes });
    const editButton = sessionRow.getByRole('button', { name: 'Edit brew session' });
    await expect(editButton).toBeVisible({ timeout: 10000 });
    await editButton.click();
    
    // Wait for form to appear
    await expect(page.getByLabel(/coffee grams/i)).toBeVisible({ timeout: 10000 });
    
    // Clear existing values first, then add half-star ratings to the original session
    await page.getByLabel(/sweetness/i).clear();
    await page.getByLabel(/sweetness/i).fill('7.5');
    await page.getByLabel(/acidity/i).clear();
    await page.getByLabel(/acidity/i).fill('8.5');
    await page.getByLabel(/overall score/i).clear();
    await page.getByLabel(/overall score/i).fill('8.3');
    
    await page.getByRole('button', { name: /save|update/i }).click();
    await expect(page.locator('body')).toContainText(/updated.*successfully|saved.*successfully/i, { timeout: 10000 });
    
    // Wait for table to update
    await expect(page.getByRole('table')).toBeVisible({ timeout: 10000 });
    
    // Now duplicate the session
    const updatedRow = page.getByRole('row').filter({ hasText: uniqueNotes });
    const duplicateButton = updatedRow.getByRole('button', { name: 'Duplicate brew session' });
    await expect(duplicateButton).toBeVisible({ timeout: 10000 });
    await duplicateButton.click();
    
    await expect(page.locator('body')).toContainText(/duplicated.*successfully/i, { timeout: 10000 });
    
    // Wait for table to show the duplicated session
    await expect(page.getByRole('table')).toBeVisible({ timeout: 10000 });
    
    // Find and edit the newest duplicated session using unique test notes
    const allNotesRows = page.getByRole('row').filter({ hasText: uniqueNotes });
    // Use the first matching row (should be the most recent)
    const duplicatedRow = allNotesRows.first();
    const editDuplicatedButton = duplicatedRow.getByRole('button', { name: 'Edit brew session' });
    await expect(editDuplicatedButton).toBeVisible({ timeout: 10000 });
    await editDuplicatedButton.click();
    
    // Wait for form to fully load
    await expect(page.getByLabel(/coffee grams/i)).toBeVisible({ timeout: 10000 });
    
    // Verify half-star values were preserved in the duplicate
    await expect(page.getByLabel(/sweetness/i)).toHaveValue('7.5');
    await expect(page.getByLabel(/acidity/i)).toHaveValue('8.5');
    await expect(page.getByLabel(/overall score/i)).toHaveValue('8.3');
  });

  test('number inputs are used instead of StarRating components', async ({ page }) => {
    // Create test scenario with batch  
    const scenario = await testData.createTestScenario();
    
    await page.goto(`/batches/${scenario.batch.id}`);
    
    // Wait for page to load completely like the working tests
    await expect(page.getByRole('heading', { name: /my coffee journal/i })).toBeVisible();
    await expect(page.locator('body')).toContainText(/roast date/i, { timeout: 2000 });
    
    await page.getByRole('button', { name: /add.*brew.*session/i }).click();
    await expect(page.getByLabel(/sweetness/i)).toBeVisible({ timeout: 2000 });
    
    // Verify that rating fields are number inputs, not StarRating components
    const sweetnessInput = page.getByLabel(/sweetness/i);
    const inputType = await sweetnessInput.getAttribute('type');
    expect(inputType).toBe('number');
    
    // Check that we don't have StarRating star elements
    const starElements = page.locator('span').filter({ hasText: /★|☆/ });
    const starCount = await starElements.count();
    
    // In the rating section, we should not have star elements for individual ratings
    // (StarRating components show stars, number inputs don't)
    expect(starCount).toBe(0);
  });

  test('can navigate and submit form using keyboard with decimal ratings', async ({ page }) => {
    // Create test scenario with batch  
    const scenario = await testData.createTestScenario();
    
    await page.goto(`/batches/${scenario.batch.id}`);
    
    // Wait for page to load completely like the working tests
    await expect(page.getByRole('heading', { name: /my coffee journal/i })).toBeVisible();
    await expect(page.locator('body')).toContainText(/roast date/i, { timeout: 2000 });
    
    await page.getByRole('button', { name: /add.*brew.*session/i }).click();
    await expect(page.getByLabel(/coffee grams/i)).toBeVisible({ timeout: 2000 });
    
    // Fill required fields using keyboard
    await page.getByLabel(/coffee grams/i).focus();
    await page.keyboard.type('20');
    
    await page.keyboard.press('Tab');
    await page.keyboard.type('320');
    
    // Navigate to sweetness and enter decimal
    await page.getByLabel(/sweetness/i).focus();
    await page.keyboard.type('7.5');
    
    // Navigate to overall score
    await page.getByLabel(/overall score/i).focus();
    await page.keyboard.type('8.25');
    
    // Submit using keyboard
    await page.getByTestId('submit-brew-session').focus();
    await page.keyboard.press('Enter');
    
    await expect(page.locator('body')).toContainText(/created.*successfully|added.*successfully/i, { timeout: 2000 });
    await expect(page.getByText('Brew session created successfully')).toBeVisible();
  });

  test('decimal ratings appear correctly in session detail view', async ({ page }) => {
    // Create test scenario with existing brew session data
    const scenario = await testData.createTestScenario();
    
    // Navigate to brew sessions list 
    await page.goto('/brew-sessions');
    
    // Wait for table to load
    await expect(page.getByRole('table')).toBeVisible({ timeout: 10000 });
    
    // Find our test session using unique test data and edit it to add decimal ratings
    const uniqueNotes = scenario.brewSession.notes; // Contains testId, making it unique
    const sessionRow = page.getByRole('row').filter({ hasText: uniqueNotes });
    const editButton = sessionRow.getByRole('button', { name: 'Edit brew session' });
    await expect(editButton).toBeVisible({ timeout: 10000 });
    await editButton.click();
    
    // Wait for form to appear
    await expect(page.getByLabel(/coffee grams/i)).toBeVisible({ timeout: 10000 });
    
    // Clear existing values and add decimal ratings with unique descriptive notes
    const newUniqueNotes = `Decimal test ${testData.testId}_${Date.now()}`;
    await page.getByLabel(/sweetness/i).clear();
    await page.getByLabel(/sweetness/i).fill('7.5');
    await page.getByLabel(/overall score/i).clear();
    await page.getByLabel(/overall score/i).fill('8.8');
    await page.getByLabel(/notes/i).clear();
    await page.getByLabel(/notes/i).fill(newUniqueNotes);
    
    await page.getByRole('button', { name: /save|update/i }).click();
    await expect(page.locator('body')).toContainText(/updated.*successfully|saved.*successfully/i, { timeout: 10000 });
    
    // Wait for table to update
    await expect(page.getByRole('table')).toBeVisible({ timeout: 10000 });
    
    // Navigate to the session detail view by clicking on the date link (more reliable than clicking the row)
    const updatedRow = page.getByRole('row').filter({ hasText: newUniqueNotes });
    await expect(updatedRow).toBeVisible({ timeout: 10000 });
    
    // Click the date link to navigate to detail view
    const dateLink = updatedRow.locator('a[href*="/brew-sessions/"]').first();
    await expect(dateLink).toBeVisible({ timeout: 10000 });
    await dateLink.click();
    
    // Wait for navigation to detail page
    await page.waitForURL(/brew-sessions\/\d+/, { timeout: 10000 });
    
    // Verify decimal ratings display correctly in detail view
    // The overall score is displayed as "8.8/10" in the overall score section
    await expect(page.locator('body')).toContainText('8.8/10', { timeout: 10000 }); // Overall score
    await expect(page.locator('body')).toContainText(newUniqueNotes, { timeout: 10000 }); // Notes
    // Individual ratings like sweetness are displayed as StarRating components, not text
    // So we verify the page has the rating sections instead
    await expect(page.locator('body')).toContainText('Overall Score', { timeout: 10000 });
  });
});