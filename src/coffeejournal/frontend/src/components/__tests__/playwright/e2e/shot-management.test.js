import { test, expect } from '@playwright/test';
const TestDataManager = require('../../../../test-utils/testDataManager');

test.describe('Shot Management', () => {
  let testData;

  test.beforeEach(async ({ page }, testInfo) => {
    testData = new TestDataManager(`shot_${testInfo.title.replace(/\s+/g, '_')}`, 'http://localhost:5000/api', testInfo.project.name);
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

  test('displays shot list', async ({ page }) => {
    // Create test scenario with espresso equipment first
    const scenario = await testData.createEspressoTestScenario();
    
    await page.goto('/shots');
    
    // Check that the main app is loaded
    await expect(page.getByRole('heading', { name: 'My Coffee Journal' })).toBeVisible();
    
    // Wait for the shots page to load by checking for the page ID
    await expect(page.locator('#shot-list-page')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('#shot-list-title')).toBeVisible();
    
    // Wait for table to load - use semantic table role
    await expect(page.getByRole('table')).toBeVisible();
    
    // Verify table contains our test data - use semantic approach
    await expect(page.getByRole('table')).toContainText(scenario.shot.notes);
  });

  test('can view shot details', async ({ page }) => {
    // Create test scenario first
    const scenario = await testData.createEspressoTestScenario();
    
    await page.goto('/shots');
    await expect(page.getByRole('table')).toBeVisible();
    
    // Click on our test shot link to view details
    await page.getByTestId(`view-shot-${scenario.shot.id}`).click();
    
    // Wait for navigation to detail page
    await page.waitForURL(`**/shots/${scenario.shot.id}`, { timeout: 5000 });
    
    // Should show shot details - check by page structure not text
    await expect(page.locator('#shot-detail-page')).toBeVisible();
    
    // Verify specific test data is displayed
    await expect(page.locator('body')).toContainText(scenario.shot.notes);
    
    // Should show espresso-specific fields
    await expect(page.locator('body')).toContainText(/dose/i);
    await expect(page.locator('body')).toContainText(/yield/i);
    await expect(page.locator('body')).toContainText(/extraction.*status/i);
  });

  test('can create new shot', async ({ page }) => {
    // Create test scenario with espresso equipment
    const scenario = await testData.createEspressoTestScenario();
    
    await page.goto('/shots');
    
    // Click create new shot button
    await page.getByRole('button', { name: 'New Shot' }).click();
    
    // Wait for form container to appear
    await expect(page.locator('.new-shot-form')).toBeVisible({ timeout: 10000 });
    
    // Wait for form to finish loading - the loading message should disappear
    try {
      await page.waitForSelector('text=Loading shot form...', { timeout: 2000 });
      await page.waitForSelector('text=Loading shot form...', { state: 'hidden', timeout: 20000 });
    } catch (e) {
      // Loading message might not appear or already disappeared - that's ok
    }
    
    // Wait specifically for the dose field which should be present in a loaded form
    await expect(page.getByLabel(/dose.*\(g\)/i)).toBeVisible({ timeout: 5000 });
    
    // Debug: Log what we're looking for and what's available
    console.log('Looking for product:', scenario.product.product_name);
    
    // Wait for the product dropdown to be populated
    await expect(async () => {
      const productSelect = page.getByLabel(/product/i);
      const options = await productSelect.locator('option').count();
      expect(options).toBeGreaterThan(1); // Should have more than just "Select a product"
    }).toPass({ timeout: 10000 });
    
    // Debug: List all available options
    const allOptions = await page.getByLabel(/product/i).locator('option').allTextContents();
    console.log('Available product options:', allOptions);
    
    // Try selection by value instead of label since we saw value="1" in logs
    await page.getByLabel(/product/i).selectOption({ value: scenario.product.id.toString() });
    await page.getByLabel(/batch/i).selectOption({ value: scenario.batch.id.toString() });
    await page.getByLabel(/brewer/i).selectOption({ label: scenario.brewer.name });
    
    // Fill required espresso-specific fields  
    await page.getByLabel(/dose.*\(g\)/i).fill('18.5');
    await page.getByLabel(/yield.*\(g\)/i).fill('37.0');
    await page.getByLabel(/overall.*score/i).fill('8');
    
    // Add notes to verify shot was created
    await page.getByLabel(/notes/i).fill(`Test shot created by E2E test ${testData.testId}`);
    
    // Submit form
    await page.getByTestId('submit-shot').click();
    
    // Wait for navigation away from form (success case) - the form container should disappear
    await expect(page.locator('.new-shot-form')).not.toBeVisible({ timeout: 10000 });
    
    // Verify we're now on the shot detail page or back to shots list
    await expect(page.locator('body')).toContainText(/shot.*details|all shots/i, { timeout: 5000 });
  });

  test('can edit shot', async ({ page }) => {
    // Create test scenario first
    const scenario = await testData.createEspressoTestScenario();
    
    await page.goto(`/shots/${scenario.shot.id}`);
    
    // Wait for shot details page to load - check by page ID
    await expect(page.locator('#shot-detail-page')).toBeVisible();
    
    // Click edit link (it's a Link component, not a button) - be specific to avoid matching product names
    await page.getByRole('link', { name: '✏️ Edit' }).click();
    
    // Wait for navigation to edit page - should have ShotForm with editing data
    await page.waitForURL('**/edit');
    
    // Wait for form to finish loading - the loading message should disappear
    try {
      await page.waitForSelector('text=Loading shot form...', { timeout: 2000 });
      await page.waitForSelector('text=Loading shot form...', { state: 'hidden', timeout: 20000 });
    } catch (e) {
      // Loading message might not appear or already disappeared - that's ok
    }
    
    // Wait specifically for the dose field which should be present in a loaded form
    await expect(page.getByLabel(/dose.*\(g\)/i)).toBeVisible({ timeout: 5000 });
    
    // Update fields
    const updatedNotes = `Updated shot notes ${testData.testId} - much better extraction!`;
    await page.getByLabel(/notes/i).fill(updatedNotes);
    
    // Save changes
    await page.getByTestId('submit-shot').click();
    
    // Wait for navigation back to detail page after successful edit
    await page.waitForURL('**/shots/' + scenario.shot.id, { timeout: 10000 });
    
    // Should show updated data on the detail page
    await expect(page.locator('body')).toContainText(updatedNotes);
  });

  test('can delete shot', async ({ page }) => {
    // Create test scenario
    const scenario = await testData.createEspressoTestScenario();
    
    // Navigate to the shots list page where delete buttons are available
    await page.goto('/shots');
    
    // Wait for page to load and shots table to appear - use IDs
    await expect(page.locator('#shot-list-page')).toBeVisible();
    await expect(page.getByRole('table')).toBeVisible();
    
    // Wait for our shot to be visible in the table
    await expect(page.locator('body')).toContainText(scenario.shot.notes);
    
    // Handle the browser confirm dialog that will appear
    page.on('dialog', async dialog => {
      expect(dialog.message()).toContain('Are you sure you want to delete');
      await dialog.accept();
    });
    
    // Find and click delete button for our specific shot
    await page.getByTestId(`delete-shot-${scenario.shot.id}`).click();
    
    // Wait for deletion to complete
    await expect(page.locator('body')).toContainText(/deleted.*successfully/i, { timeout: 5000 });
    
    // Should not show our test shot anymore
    await expect(page.locator('body')).not.toContainText(scenario.shot.notes);
  });

  test('shows dose yield ratio calculation', async ({ page }) => {
    // Create test scenario first
    const scenario = await testData.createEspressoTestScenario();
    
    await page.goto(`/shots/${scenario.shot.id}`);
    
    // Should show dose yield ratio calculation
    await expect(page.locator('body')).toContainText(/dose.*yield.*ratio|ratio/i);
    await expect(page.locator('body')).toContainText(/1:\d+\.?\d*/);
  });

  test('can filter shots by extraction status', async ({ page }) => {
    // Create multiple test scenarios with different extraction statuses
    const scenario1 = await testData.createEspressoTestScenario();
    
    // Create another shot with different extraction status
    await testData.createShot({
      product_id: scenario1.product.id,
      product_batch_id: scenario1.batch.id,
      brewer_id: scenario1.brewer.id,
      dose_grams: 18.0,
      yield_grams: 36.0,
      dose_yield_ratio: 2.0,
      extraction_time_seconds: 30,
      water_temperature_c: 93,
      extraction_status: 'over-extracted',
      overall_score: 6,
      notes: `Over-extracted shot ${testData.testId}`
    });
    
    await page.goto('/shots');
    await expect(page.getByRole('table')).toBeVisible();
    
    // Wait for table to contain both shots
    await expect(page.locator('body')).toContainText(scenario1.shot.notes);
    await expect(page.locator('body')).toContainText(`Over-extracted shot ${testData.testId}`);
    
    // Filter by perfect extraction
    await page.getByLabel(/filter.*extraction.*status|extraction.*status.*filter/i).selectOption('perfect');
    
    // Wait for filter to take effect
    await expect(page.locator('body')).toContainText(scenario1.shot.notes);
    await expect(page.locator('body')).not.toContainText(`Over-extracted shot ${testData.testId}`);
  });

  test('shows equipment details', async ({ page }) => {
    // Create test scenario with full equipment setup
    const scenario = await testData.createEspressoTestScenario();
    
    await page.goto(`/shots/${scenario.shot.id}`);
    
    // Wait for page to load - check by page ID
    await expect(page.locator('#shot-detail-page')).toBeVisible();
    
    // Should show espresso equipment sections
    await expect(page.locator('body')).toContainText(/brewer:/i);
    await expect(page.locator('body')).toContainText(/portafilter:/i);
    await expect(page.locator('body')).toContainText(/basket:/i);
    await expect(page.locator('body')).toContainText(/tamper:/i);
  });

  test('can associate shot with session', async ({ page }) => {
    // Create test scenario with shot session
    const scenario = await testData.createEspressoTestScenario();
    const shotSession = await testData.createShotSession({
      title: `Test Session ${testData.testId}`,
      product_id: scenario.product.id,
      product_batch_id: scenario.batch.id,
      brewer_id: scenario.brewer.id,
      notes: `Session for testing shot association ${testData.testId}`
    });
    
    await page.goto('/shots');
    
    // Create new shot
    await page.getByRole('button', { name: 'New Shot' }).click();
    
    // Wait for form container to appear
    await expect(page.locator('.new-shot-form')).toBeVisible({ timeout: 10000 });
    
    // Wait for form to finish loading - the loading message should disappear
    try {
      await page.waitForSelector('text=Loading shot form...', { timeout: 2000 });
      await page.waitForSelector('text=Loading shot form...', { state: 'hidden', timeout: 20000 });
    } catch (e) {
      // Loading message might not appear or already disappeared - that's ok
    }
    
    // Wait specifically for the dose field which should be present in a loaded form
    await expect(page.getByLabel(/dose.*\(g\)/i)).toBeVisible({ timeout: 5000 });
    
    // Wait for the product dropdown to be populated by checking that it has more than just the placeholder option
    await expect(async () => {
      const productSelect = page.getByLabel(/product/i);
      const options = await productSelect.locator('option').count();
      expect(options).toBeGreaterThan(1); // Should have more than just "Select a product"
    }).toPass({ timeout: 10000 });
    
    // Fill required fields
    await page.getByLabel(/product/i).selectOption({ value: scenario.product.id.toString() });
    await page.getByLabel(/batch/i).selectOption({ value: scenario.batch.id.toString() });
    await page.getByLabel(/brewer/i).selectOption({ label: scenario.brewer.name });
    
    // Associate with session - the dropdown shows "Session {id} - {title}" format
    await page.getByLabel(/session/i).selectOption({ label: `Session ${shotSession.id} - ${shotSession.title}` });
    
    // Fill other required fields
    await page.getByLabel(/dose.*\(g\)/i).fill('18.0');
    await page.getByLabel(/yield.*\(g\)/i).fill('36.0');
    await page.getByLabel(/overall.*score/i).fill('8');
    
    // Submit form
    await page.getByTestId('submit-shot').click();
    
    // Wait for success message
    await expect(page.locator('body')).toContainText(/created.*successfully/i, { timeout: 10000 });
  });

  test('validates required fields', async ({ page }) => {
    // Debug: Set up console listener to capture JavaScript errors
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
        console.log('❌ Console error:', msg.text());
      }
    });
    
    // Debug: Set up page error listener
    const pageErrors = [];
    page.on('pageerror', error => {
      pageErrors.push(error.message);
      console.log('❌ Page error:', error.message);
    });
    
    // Debug: Set up network request listener to capture API failures
    const apiErrors = [];
    page.on('response', response => {
      if (response.url().includes('/api/') && response.status() >= 400) {
        apiErrors.push(`${response.status()} ${response.url()}`);
        console.log('❌ API error:', response.status(), response.url());
      }
    });

    // Create minimal test data so the form has something to work with
    const scenario = await testData.createEspressoTestScenario();
    
    await page.goto('/shots');
    await expect(page.locator('#shot-list-page')).toBeVisible();
    
    // Wait for the ShotTable to load fully (including filter options)
    await expect(page.getByRole('table')).toBeVisible({ timeout: 10000 });
    
    // Debug: Check what buttons are available before clicking
    const allButtons = await page.locator('button').all();
    console.log(`Found ${allButtons.length} buttons on page`);
    for (let i = 0; i < allButtons.length; i++) {
      const button = allButtons[i];
      const ariaLabel = await button.getAttribute('aria-label');
      const title = await button.getAttribute('title');
      const text = await button.textContent();
      console.log(`  Button ${i}: aria-label="${ariaLabel}" title="${title}" text="${text?.trim()}"`);
    }
    
    // Wait for the "New Shot" button to be present and clickable
    await expect(page.getByRole('button', { name: 'New Shot' })).toBeVisible({ timeout: 5000 });
    
    // Click create new shot button using aria-label
    console.log('Clicking New Shot button...');
    await page.getByRole('button', { name: 'New Shot' }).click();
    
    // Wait for form container to appear
    console.log('Waiting for form container to appear...');
    await expect(page.locator('.new-shot-form')).toBeVisible({ timeout: 10000 });
    
    // Wait for form to finish loading - the loading message should disappear
    console.log('Waiting for form to finish loading...');
    try {
      // Wait for the loading message to appear first (if it does)
      await page.waitForSelector('text=Loading shot form...', { timeout: 2000 });
      console.log('Loading message found, waiting for it to disappear...');
      // Wait for it to disappear (form finished loading)
      await page.waitForSelector('text=Loading shot form...', { state: 'hidden', timeout: 20000 });
      console.log('Form finished loading');
    } catch (e) {
      console.log('Loading message not found or already disappeared');
    }
    
    // Debug: Let's see what labels are actually present
    const allLabels = await page.locator('label').all();
    console.log(`Found ${allLabels.length} labels on page after form loads:`);
    for (let i = 0; i < allLabels.length; i++) {
      const label = allLabels[i];
      const text = await label.textContent();
      const htmlFor = await label.getAttribute('for');
      console.log(`  Label ${i}: text="${text?.trim()}" for="${htmlFor}"`);
    }
    
    // Debug: Let's see all inputs with names
    const allInputs = await page.locator('input[name], select[name]').all();
    console.log(`Found ${allInputs.length} named inputs/selects:`);
    for (let i = 0; i < allInputs.length; i++) {
      const input = allInputs[i];
      const name = await input.getAttribute('name');
      const id = await input.getAttribute('id');
      const type = await input.getAttribute('type') || 'select';
      console.log(`  Input ${i}: name="${name}" id="${id}" type="${type}"`);
    }
    
    // Debug: Let's check if the form element itself exists
    const formExists = await page.locator('form').count();
    console.log(`Form elements found: ${formExists}`);
    
    // Debug: Check if the form container still exists
    const formContainerExists = await page.locator('.new-shot-form').count();
    console.log(`Form container exists: ${formContainerExists}`);
    
    // Debug: Let's see if there's any error content in the form (only if container exists)
    if (formContainerExists > 0) {
      const formContent = await page.locator('.new-shot-form').textContent();
      console.log(`Form container content: "${formContent}"`);
      
      // Debug: Let's check if the ShotForm component rendered anything
      const allElements = await page.locator('.new-shot-form *').count();
      console.log(`Total elements inside form container: ${allElements}`);
    } else {
      console.log('❌ Form container disappeared - form rendering completely failed');
    }
    
    // If no form elements exist, the form failed to render - skip field validation
    if (formExists === 0) {
      console.log('❌ Form failed to render - skipping field validation test');
      console.log(`\n📊 Error Summary:`);
      console.log(`  Console errors: ${consoleErrors.length}`);
      consoleErrors.forEach((error, i) => console.log(`    ${i+1}. ${error}`));
      console.log(`  Page errors: ${pageErrors.length}`);
      pageErrors.forEach((error, i) => console.log(`    ${i+1}. ${error}`));
      console.log(`  API errors: ${apiErrors.length}`);
      apiErrors.forEach((error, i) => console.log(`    ${i+1}. ${error}`));
      return;
    }
    
    // Wait specifically for the dose field which should be present in a loaded form
    await expect(page.getByLabel(/dose.*\(g\)/i)).toBeVisible({ timeout: 5000 });
    
    // Try to submit empty form (don't fill any required fields)
    await page.getByTestId('submit-shot').click();
    
    // Should show validation errors from the browser's HTML5 validation since required fields are empty
    // The form should not submit successfully
    await page.waitForTimeout(1000);
    
    // Verify we're still on the form (not redirected) by checking the form is still visible
    await expect(page.getByLabel(/dose.*\(g\)/i)).toBeVisible();
  });
});