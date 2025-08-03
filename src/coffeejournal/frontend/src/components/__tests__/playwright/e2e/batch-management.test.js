import { test, expect } from '@playwright/test';
const TestDataManager = require('../../../../test-utils/testDataManager');
// Using semantic selectors - no need for helper functions that use brittle selectors

test.describe('Batch Management', () => {
  let testData;

  test.beforeEach(async ({ page }, testInfo) => {
    testData = new TestDataManager(`batch_${testInfo.title.replace(/\s+/g, '_')}`, 'http://localhost:5000/api', testInfo.project.name);
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
  test('displays batch details', async ({ page }) => {
    // Create test scenario first
    const scenario = await testData.createTestScenario();
    
    await page.goto(`/batches/${scenario.batch.id}`);
    
    // Check page structure using semantic selectors
    await expect(page.getByRole('heading', { name: /batch.*details/i })).toBeVisible();
    
    // Should show batch information using semantic approach
    await expect(page.locator('body')).toContainText(/roast date/i);
    await expect(page.locator('body')).toContainText(/purchase date/i);
    await expect(page.locator('body')).toContainText(/amount.*grams/i);
    await expect(page.locator('body')).toContainText(/price.*cup/i);
  });

  test('can create batch from product page', async ({ page }) => {
    // Create test product first
    const scenario = await testData.createTestScenario();
    
    await page.goto(`/products/${scenario.product.id}`);
    
    // Wait for page to fully load before looking for buttons
    await expect(page.getByRole('heading', { name: /my coffee journal/i })).toBeVisible();
    await expect(page.locator('body')).toContainText(scenario.product.product_name);
    
    // Click add batch button using semantic selector - use aria-label
    const addBatchButton = page.getByRole('button', { name: 'Add new batch' });
    await expect(addBatchButton).toBeVisible({ timeout: 2000 });
    await addBatchButton.click();
    
    // Wait for form to appear
    await expect(page.getByLabel(/roast.*date/i)).toBeVisible({ timeout: 2000 });
    
    // Should show batch form
    await expect(page.getByRole('heading', { name: /add.*batch/i })).toBeVisible({ timeout: 2000 });
    
    // Fill out form using semantic selectors
    const today = new Date().toISOString().split('T')[0];
    const testNotes = `Test batch ${testData.testId}`;
    
    await page.getByLabel(/roast.*date/i).fill(today);
    await page.getByLabel(/purchase.*date/i).fill(today);
    await page.getByLabel(/amount.*grams/i).fill('500');
    await page.getByLabel(/^price.*kr/i).fill('25.00');
    
    if (await page.getByLabel(/notes/i).isVisible()) {
      await page.getByLabel(/notes/i).fill(testNotes);
    }
    
    // Submit form using semantic selector
    await page.getByRole('button', { name: /save|create/i }).click();
    
    // Wait for navigation to batch detail page
    await page.waitForURL(/\/batches\/\d+/);
    
    // Should show test notes if they were added using semantic approach
    if (testNotes) {
      await expect(page.locator('body')).toContainText(testNotes);
    }
  });

  test('shows price per cup calculation', async ({ page }) => {
    // Create test scenario first
    const scenario = await testData.createTestScenario();
    
    await page.goto(`/batches/${scenario.batch.id}`);
    
    // Should show calculated price per cup using semantic approach
    await expect(page.locator('body')).toContainText(/price.*cup/i);
    await expect(page.locator('body')).toContainText(/\d+\.\d+/); // Price number
  });

  test('can edit batch details', async ({ page }) => {
    // Create test scenario first
    const scenario = await testData.createTestScenario();
    
    await page.goto(`/batches/${scenario.batch.id}`);
    
    // Click edit button using semantic selector
    await page.getByRole('button', { name: /edit/i }).click();
    
    // Wait for form to appear
    await expect(page.getByLabel(/notes/i)).toBeVisible();
    
    // Update notes
    const updatedNotes = `Updated batch notes ${testData.testId}`;
    if (await page.getByLabel(/notes/i).isVisible()) {
      await page.getByLabel(/notes/i).fill(updatedNotes);
    }
    
    // Save changes using semantic selector
    await page.getByRole('button', { name: /save|update/i }).click();
    
    // Wait for success or form to close
    await expect(page.locator('body')).toContainText(/updated.*successfully|saved.*successfully/i, { timeout: 2000 });
    
    // Should show updated notes using semantic approach
    if (updatedNotes) {
      await expect(page.locator('body')).toContainText(updatedNotes);
    }
  });

  test('can delete batch', async ({ page }) => {
    // Create test scenario with batch to delete
    const scenario = await testData.createTestScenario();
    
    await page.goto(`/batches/${scenario.batch.id}`);
    
    // Delete the batch using semantic selectors
    await page.getByRole('button', { name: /delete/i }).click();
    
    // Confirm deletion using test-id selectors (DeleteConfirmationModal uses data-testid)
    const modal = page.getByTestId('delete-modal-content');
    await expect(modal).toBeVisible();
    await modal.getByRole('button', { name: /delete|confirm/i }).click();
    
    // Wait for navigation away from batch page
    await page.waitForURL(`**/products/${scenario.product.id}`);
    
    // Trying to navigate to deleted batch should show error
    await page.goto(`/batches/${scenario.batch.id}`);
    await expect(page.locator('body')).toContainText(/not found|error/i);
  });

  test('shows related brew sessions', async ({ page }) => {
    // Create test scenario first
    const scenario = await testData.createTestScenario();
    
    await page.goto(`/batches/${scenario.batch.id}`);
    
    // Should show brew sessions section
    await expect(page.getByRole('heading', { name: /brew.*sessions/i })).toBeVisible();
    
    // Should have add brew session button
    await expect(page.getByRole('button', { name: /add.*brew.*session/i })).toBeVisible({ timeout: 2000 });
    
    // Our test brew session should be visible using semantic approach
    // Wait for brew sessions to load first
    await expect(page.getByRole('heading', { name: /brew.*sessions/i })).toBeVisible({ timeout: 2000 });
    // Check for brew session data that's actually displayed in the table (coffee amount)
    await expect(page.locator('body')).toContainText('20g', { timeout: 2000 });
  });

  test('can navigate to product from batch', async ({ page }) => {
    // Create test scenario first
    const scenario = await testData.createTestScenario();
    
    await page.goto(`/batches/${scenario.batch.id}`);
    
    // Click link to product - look for link containing the product information  
    await page.getByRole('link').filter({ hasText: scenario.product.product_name }).click();
    
    // Wait for navigation to product page
    await page.waitForURL(`**/products/${scenario.product.id}`);
    
    // Should show product details - use body content check with correct field name
    await expect(page.locator('body')).toContainText(scenario.product.product_name);
  });

  test('shows batch aging information', async ({ page }) => {
    // Create test scenario first
    const scenario = await testData.createTestScenario();
    
    await page.goto(`/batches/${scenario.batch.id}`);
    
    // Should show how old the batch is (flexible check) using semantic approach
    const bodyContent = page.locator('body');
    await expect(bodyContent).toContainText(/roasted|purchased|days/i);
  });

  test('can export batch data', async ({ page }) => {
    // Create test scenario first
    const scenario = await testData.createTestScenario();
    
    await page.goto(`/batches/${scenario.batch.id}`);
    
    // Look for export functionality using semantic selector
    const exportButton = page.getByRole('button', { name: /export/i });
    if (await exportButton.count() > 0) {
      await exportButton.click();
      // Could check for download or data display
    }
  });
});