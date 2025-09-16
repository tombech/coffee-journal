import { test, expect } from '@playwright/test';
const TestDataManager = require('../../../../test-utils/testDataManager');
// Using semantic selectors - no need for helper functions that use brittle selectors

test.describe('Brew Session Management', () => {
  let testData;

  test.beforeEach(async ({ page }, testInfo) => {
    testData = new TestDataManager(`brewsession_${testInfo.title.replace(/\s+/g, '_')}`, 'http://localhost:5000/api', testInfo.project.name);
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
  test('displays brew session list', async ({ page }) => {
    // Create test scenario first
    const scenario = await testData.createTestScenario();
    
    await page.goto('/brew-sessions');
    
    // Check that the main app is loaded
    await expect(page.getByRole('heading', { name: 'My Coffee Journal' })).toBeVisible();
    
    // Wait for the component to load and check for the actual heading in the component
    await expect(page.getByRole('heading', { name: 'All Brew Sessions' })).toBeVisible({ timeout: 10000 });
    
    // Wait for table to load - use semantic table role
    await expect(page.getByRole('table')).toBeVisible();
    
    // Verify table contains our test data - use semantic approach
    await expect(page.getByRole('table')).toContainText(scenario.brewSession.notes);
    // Brew method names are abbreviated in the table display
    // The TestDataManager creates methods like "Test Method brewsession_displays..." which gets abbreviated to "TMb"
    await expect(page.getByRole('table')).toContainText('TMb');
  });

  test('can view brew session details', async ({ page }) => {
    // Create test scenario first
    const scenario = await testData.createTestScenario();
    
    await page.goto('/brew-sessions');
    await expect(page.getByRole('table')).toBeVisible();
    
    // Click on our test brew session link to view details - use deterministic selector
    await page.getByTestId(`view-brew-session-${scenario.brewSession.id}`).click();
    
    // Wait for navigation to detail page with longer timeout
    await page.waitForURL(`**/brew-sessions/${scenario.brewSession.id}`, { timeout: 5000 });
    
    // Should show brew details using more specific semantic selector
    await expect(page.getByRole('heading', { name: /brew session/i })).toBeVisible();
    
    // Verify specific test data is displayed - use the unique test notes
    await expect(page.locator('body')).toContainText(scenario.brewSession.notes);
  });

  test('can create brew session from batch', async ({ page }) => {
    // Create test scenario with batch
    const scenario = await testData.createTestScenario();
    
    // Navigate directly to brew session form with batch ID
    await page.goto(`/brew-sessions/new?batch_id=${scenario.batch.id}`);

    // Wait for form to appear
    await expect(page.getByLabel(/coffee.*grams/i)).toBeVisible({ timeout: 2000 });
    
    // Should show brew session form
    await expect(page.getByRole('heading', { name: /add.*brew.*session/i })).toBeVisible();
    
    // Fill out form with semantic selectors
    // Wait for dropdown to be populated before selecting  
    await expect(page.getByLabel(/brew method/i)).toBeVisible({ timeout: 2000 });
    // Use test scenario brew method by label (more reliable than ID)
    await page.getByLabel(/brew method/i).selectOption({ label: scenario.brewMethod.name });
    await page.getByLabel(/coffee.*grams/i).fill('18');
    await page.getByLabel(/water.*grams/i).fill('300');
    await page.getByLabel(/temperature/i).fill('93');
    
    // Add ratings using semantic selectors
    await page.getByLabel(/sweetness/i).fill('8');
    await page.getByLabel(/acidity/i).fill('7');
    await page.getByLabel(/body/i).fill('8');
    await page.getByLabel(/aroma/i).fill('9');
    
    // Submit form using deterministic selector
    await page.getByTestId('submit-brew-session').click();
    
    // Wait for navigation back to batch page
    await page.waitForURL(`**/batches/${scenario.batch.id}`);
    
    // Wait for success message instead of count change
    await expect(page.locator('body')).toContainText(/created.*successfully|saved.*successfully/i, { timeout: 2000 });
    
    // Verify we're back on batch page with new session
    await expect(page.locator('body')).toContainText('8'); // Sweetness score visible on page
  });

  test('can edit brew session', async ({ page }) => {
    // Create test scenario first
    const scenario = await testData.createTestScenario();
    
    await page.goto(`/brew-sessions/${scenario.brewSession.id}`);
    
    // Click edit button using semantic selector
    await page.getByRole('button', { name: /edit/i }).click();
    
    // Wait for form to appear
    await expect(page.getByLabel(/notes/i)).toBeVisible();
    
    // Update notes using semantic selector
    const updatedNotes = `Updated notes ${testData.testId} - even better!`;
    await page.getByLabel(/notes/i).fill(updatedNotes);
    
    // Update sweetness score using semantic selector
    await page.getByLabel(/sweetness/i).fill('9');
    
    // Save changes using deterministic selector
    await page.getByTestId('submit-brew-session').click();
    
    // Wait for navigation back to detail page
    await page.waitForURL(`**/brew-sessions/${scenario.brewSession.id}`);
    
    // Should show updated data
    await expect(page.locator('body')).toContainText(updatedNotes);
    await expect(page.locator('body')).toContainText('9'); // Updated sweetness score
  });

  test('can delete brew session', async ({ page }) => {
    // Create test scenario with batch and brew session
    const scenario = await testData.createTestScenario();
    
    // Navigate to the brew sessions list page where delete buttons are available
    await page.goto('/brew-sessions');
    
    // Wait for page to load and brew sessions table to appear
    await expect(page.getByRole('heading', { name: 'All Brew Sessions' })).toBeVisible();
    await expect(page.getByRole('table')).toBeVisible();
    
    // Wait for our brew session to be visible in the table
    await expect(page.locator('body')).toContainText(scenario.brewSession.notes);
    
    // Handle the browser confirm dialog that will appear
    page.on('dialog', async dialog => {
      expect(dialog.message()).toContain('Are you sure you want to delete');
      await dialog.accept();
    });
    
    // Debug: Log the brew session ID we're looking for
    console.log(`Looking for delete button with test ID: delete-brew-session-${scenario.brewSession.id}`);
    
    // Find and click delete button for our specific brew session using deterministic selector
    await page.getByTestId(`delete-brew-session-${scenario.brewSession.id}`).click();
    
    // Wait for deletion to complete
    await expect(page.locator('body')).toContainText(/deleted.*successfully/i, { timeout: 5000 });
    
    // Should not show our test brew session anymore
    await expect(page.locator('body')).not.toContainText(scenario.brewSession.notes);
  });

  test('shows brew ratio calculation', async ({ page }) => {
    // Create test scenario first
    const scenario = await testData.createTestScenario();
    
    await page.goto(`/brew-sessions/${scenario.brewSession.id}`);
    
    // Should show brew ratio calculation
    await expect(page.locator('body')).toContainText(/brew ratio/i);
    await expect(page.locator('body')).toContainText(/1:\d+/);
  });

  test('can filter brew sessions', async ({ page }) => {
    // Create multiple test scenarios with different brew methods
    const scenario1 = await testData.createTestScenario();
    const anotherBrewMethod = await testData.createTestItem('brew_methods', {
      name: `Different Method ${testData.testId}`
    });
    
    // Create another brew session with different method using the proper endpoint
    await testData.createBrewSession(scenario1.batch.id, {
      timestamp: new Date().toISOString(),
      brew_method: anotherBrewMethod.name,
      recipe: scenario1.recipe.name,
      amount_coffee_grams: 18.0,
      amount_water_grams: 300.0,
      brew_temperature_c: 92.0,
      sweetness: 6,
      acidity: 7,
      bitterness: 4,
      body: 5,
      aroma: 7,
      flavor_profile_match: 6,
      notes: `Different method session ${testData.testId}`
    });
    
    await page.goto('/brew-sessions');
    await expect(page.getByRole('table')).toBeVisible();
    
    // Wait for table to contain both brew sessions - use unique test notes instead of method names
    await expect(page.locator('body')).toContainText(`Test notes for ${testData.testId}`);
    await expect(page.locator('body')).toContainText(`Different method session ${testData.testId}`);
    
    // Filter by first brew method using semantic selector
    // The filter uses method names, not IDs
    await page.getByLabel(/filter.*method|brew method.*filter/i).selectOption(scenario1.brewMethod.name);
    
    // Wait for filter to take effect - should still show first session, not show second
    await expect(page.locator('body')).toContainText(`Test notes for ${testData.testId}`);
    await expect(page.locator('body')).not.toContainText(`Different method session ${testData.testId}`);
  });

  test('shows equipment details', async ({ page }) => {
    // Create test scenario first
    const scenario = await testData.createTestScenario();
    
    await page.goto(`/brew-sessions/${scenario.brewSession.id}`);
    
    // Should show equipment sections (may show "N/A" if no equipment specified)
    await expect(page.locator('body')).toContainText(/grinder:/i);
    await expect(page.locator('body')).toContainText(/filter:/i);
    await expect(page.locator('body')).toContainText(/kettle:/i);
    await expect(page.locator('body')).toContainText(/scale:/i);
  });
});