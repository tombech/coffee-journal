import { test, expect } from '@playwright/test';
const TestDataManager = require('../../../../test-utils/testDataManager');

test.describe('Shot Session Management', () => {
  let testData;

  test.beforeEach(async ({ page }, testInfo) => {
    testData = new TestDataManager(`shot_session_${testInfo.title.replace(/\s+/g, '_')}`, 'http://localhost:5000/api', testInfo.project.name);
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

  test('displays shot session list', async ({ page }) => {
    // Create test scenario with shot session
    const scenario = await testData.createEspressoTestScenario();
    const shotSession = await testData.createShotSession({
      title: `Test Session ${testData.testId}`,
      product_id: scenario.product.id,
      product_batch_id: scenario.batch.id,
      brewer_id: scenario.brewer.id,
      notes: `Test session notes ${testData.testId}`
    });
    
    await page.goto('/shot-sessions');
    
    // Check that the main app is loaded
    await expect(page.getByRole('heading', { name: 'My Coffee Journal' })).toBeVisible();
    
    // Wait for the component to load by checking page ID
    await expect(page.locator('#shot-session-list-page')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('#shot-session-list-title')).toBeVisible();
    
    // Wait for table to load - use semantic table role
    await expect(page.getByRole('table')).toBeVisible();
    
    // Verify table contains our test data
    await expect(page.getByRole('table')).toContainText(shotSession.title);
  });

  test('can create new shot session', async ({ page }) => {
    // Create test scenario with espresso equipment
    const scenario = await testData.createEspressoTestScenario();
    
    await page.goto('/shot-sessions');
    
    // Click create new shot session button
    await page.getByTestId('new-shot-session-btn').click();
    
    // Wait for form container to appear
    await expect(page.locator('.new-shot-session-form')).toBeVisible({ timeout: 10000 });
    
    // Fill in required fields
    const sessionName = `Test Session ${testData.testId}`;
    await page.getByLabel(/session.*name/i).fill(sessionName);
    
    // Wait for product dropdown to be populated
    await expect(async () => {
      const productSelect = page.getByLabel(/product/i);
      const options = await productSelect.locator('option').count();
      expect(options).toBeGreaterThan(1); // Should have more than just "Select a product"
    }).toPass({ timeout: 10000 });
    
    // Select product and batch using value-based selection
    await page.getByLabel(/product/i).selectOption({ value: scenario.product.id.toString() });
    await page.getByLabel(/batch/i).selectOption({ value: scenario.batch.id.toString() });
    await page.getByLabel(/brewer/i).selectOption({ label: scenario.brewer.name });
    
    // Add notes to verify session was created
    const notes = `Test session created by E2E test ${testData.testId}`;
    await page.getByLabel(/notes/i).fill(notes);
    
    // Submit form
    await page.getByTestId('submit-shot-session').click();
    
    // Wait for navigation away from form (success case) - the form container should disappear
    await expect(page.locator('.new-shot-session-form')).not.toBeVisible({ timeout: 10000 });
    
    // Verify we can see the created session in the table
    await expect(page.getByRole('table')).toContainText(sessionName);
    // Note: notes are not displayed in the table, only in the detail view
  });

  test('can edit shot session', async ({ page }) => {
    // Create test scenario first
    const scenario = await testData.createEspressoTestScenario();
    const shotSession = await testData.createShotSession({
      title: `Test Session ${testData.testId}`,
      product_id: scenario.product.id,
      product_batch_id: scenario.batch.id,
      brewer_id: scenario.brewer.id,
      notes: `Original notes ${testData.testId}`
    });
    
    await page.goto('/shot-sessions');
    await expect(page.getByRole('table')).toBeVisible();
    
    // Click edit button for our specific session
    await page.getByTestId(`edit-shot-session-${shotSession.id}`).click();
    
    // Wait for edit form to appear
    await expect(page.locator('.edit-shot-session-form')).toBeVisible({ timeout: 10000 });
    
    // Update fields
    const updatedName = `Updated Session ${testData.testId}`;
    const updatedNotes = `Updated notes ${testData.testId} - much better!`;
    
    await page.getByLabel(/session.*name/i).fill(updatedName);
    await page.getByLabel(/notes/i).fill(updatedNotes);
    
    // Save changes
    await page.getByTestId('submit-shot-session').click();
    
    // Wait for edit form to disappear
    await expect(page.locator('.edit-shot-session-form')).not.toBeVisible({ timeout: 10000 });
    
    // Should show updated data in the table
    await expect(page.getByRole('table')).toContainText(updatedName);
    // Note: notes are not displayed in the table, only in the detail view
  });

  test('can delete shot session', async ({ page }) => {
    // Create test scenario
    const scenario = await testData.createEspressoTestScenario();
    const shotSession = await testData.createShotSession({
      title: `Delete Me Session ${testData.testId}`,
      product_id: scenario.product.id,
      product_batch_id: scenario.batch.id,
      brewer_id: scenario.brewer.id,
      notes: `Session to be deleted ${testData.testId}`
    });
    
    // Navigate to the shot sessions list page
    await page.goto('/shot-sessions');
    
    // Wait for page to load and shot sessions table to appear - use IDs
    await expect(page.locator('#shot-session-list-page')).toBeVisible();
    await expect(page.getByRole('table')).toBeVisible();
    
    // Wait for our session to be visible in the table
    await expect(page.locator('body')).toContainText(shotSession.title);
    
    // Handle the browser confirm dialog that will appear
    page.on('dialog', async dialog => {
      expect(dialog.message()).toContain('Are you sure you want to delete');
      await dialog.accept();
    });
    
    // Find and click delete button for our specific session
    await page.getByTestId(`delete-shot-session-${shotSession.id}`).click();
    
    // Wait for deletion to complete
    await expect(page.locator('body')).toContainText(/deleted.*successfully/i, { timeout: 5000 });
    
    // Should not show our test session anymore
    await expect(page.locator('body')).not.toContainText(shotSession.title);
  });

  test('can view shot session details', async ({ page }) => {
    // Create test scenario first
    const scenario = await testData.createEspressoTestScenario();
    const shotSession = await testData.createShotSession({
      title: `Detail View Session ${testData.testId}`,
      product_id: scenario.product.id,
      product_batch_id: scenario.batch.id,
      brewer_id: scenario.brewer.id,
      notes: `Session for detail view testing ${testData.testId}`
    });
    
    await page.goto('/shot-sessions');
    await expect(page.getByRole('table')).toBeVisible();
    
    // Click on our test session link to view details
    await page.getByTestId(`view-shot-session-${shotSession.id}`).click();
    
    // Wait for navigation to detail page
    await page.waitForURL(`**/shot-sessions/${shotSession.id}`, { timeout: 5000 });
    
    // Should show session details - check by page ID
    await expect(page.locator('#shot-session-detail-page')).toBeVisible();
    
    // Verify specific test data is displayed
    await expect(page.locator('body')).toContainText(shotSession.title);
    await expect(page.locator('body')).toContainText(shotSession.notes);
    
    // Should show espresso-specific information
    await expect(page.locator('body')).toContainText(/brewer:/i);
    await expect(page.locator('body')).toContainText(/product:/i);
    await expect(page.locator('body')).toContainText(/batch:/i);
  });

  test('can duplicate shot session', async ({ page }) => {
    // Create test scenario
    const scenario = await testData.createEspressoTestScenario();
    const shotSession = await testData.createShotSession({
      title: `Original Session ${testData.testId}`,
      product_id: scenario.product.id,
      product_batch_id: scenario.batch.id,
      brewer_id: scenario.brewer.id,
      notes: `Session to be duplicated ${testData.testId}`
    });
    
    await page.goto('/shot-sessions');
    await expect(page.getByRole('table')).toBeVisible();
    
    // Wait for our session to be visible
    await expect(page.locator('body')).toContainText(shotSession.title);
    
    // Click duplicate button for our specific session
    await page.getByTestId(`duplicate-shot-session-${shotSession.id}`).click();
    
    // Wait for duplication to complete by checking that we have more sessions in the table
    await expect(async () => {
      const sessionCount = await page.locator('tbody tr').count();
      expect(sessionCount).toBeGreaterThanOrEqual(2); // At least original + duplicate
    }).toPass({ timeout: 10000 });
    
    // Should see both the original and duplicated session
    // The duplicate should have the same base name but be distinguishable
  });

  test('can filter sessions by product', async ({ page }) => {
    // Create first test scenario  
    const scenario1 = await testData.createEspressoTestScenario();
    
    // Create second product with clearly different name
    const product2 = await testData.createItem('products', {
      product_name: `Test Espresso Product ALT ${testData.testId}`,
      roaster: `Test Roaster ALT ${testData.testId}`,
      bean_type: ['Arabica'],
      country: 'Ethiopia',
      region_id: []
    });
    
    const batch2 = await testData.createBatch(product2.id, {
      purchase_date: new Date().toISOString().split('T')[0],
      roast_date: new Date().toISOString().split('T')[0],
      amount_grams: 250,
      purchase_price: 19.99
    });
    
    const brewer2 = await testData.createItem('brewers', {
      name: `Test Espresso Machine ALT ${testData.testId}`,
      type: 'Espresso Machine'
    });
    
    const scenario2 = { product: product2, batch: batch2, brewer: brewer2 };
    
    const session1 = await testData.createShotSession({
      title: `Product 1 Session ${testData.testId}`,
      product_id: scenario1.product.id,
      product_batch_id: scenario1.batch.id,
      brewer_id: scenario1.brewer.id,
      notes: `Session for product 1 ${testData.testId}`
    });
    
    const session2 = await testData.createShotSession({
      title: `Product 2 Session ${testData.testId}`,
      product_id: scenario2.product.id,
      product_batch_id: scenario2.batch.id,
      brewer_id: scenario2.brewer.id,
      notes: `Session for product 2 ${testData.testId}`
    });
    
    await page.goto('/shot-sessions');
    await expect(page.getByRole('table')).toBeVisible();
    
    // Wait for table to contain both sessions
    await expect(page.locator('body')).toContainText(session1.title);
    await expect(page.locator('body')).toContainText(session2.title);
    
    // Filter by first product - target by placeholder text since there's no label
    await page.locator('select').filter({ hasText: 'All Products...' }).selectOption(scenario1.product.id.toString());
    
    // Wait for filter to take effect
    await expect(page.locator('body')).toContainText(session1.title);
    await expect(page.locator('body')).not.toContainText(session2.title);
  });

  test('validates required fields', async ({ page }) => {
    // Create minimal test data so the form has something to work with
    const scenario = await testData.createEspressoTestScenario();
    
    await page.goto('/shot-sessions');
    await expect(page.locator('#shot-session-list-page')).toBeVisible();
    
    // Click create new shot session button
    await page.getByTestId('new-shot-session-btn').click();
    
    // Wait for form container to appear
    await expect(page.locator('.new-shot-session-form')).toBeVisible({ timeout: 10000 });
    
    // Try to submit empty form (don't fill any required fields)
    await page.getByTestId('submit-shot-session').click();
    
    // Should show validation errors from the browser's HTML5 validation since required fields are empty
    // The form should not submit successfully
    await page.waitForTimeout(1000);
    
    // Verify we're still on the form (not redirected) by checking the form is still visible
    await expect(page.getByLabel(/session.*name/i)).toBeVisible();
  });
});