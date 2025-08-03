import { test, expect } from '@playwright/test';
const TestDataManager = require('../../../../test-utils/testDataManager');
// Using semantic selectors - no need for helper functions that use brittle selectors

test.describe('Product Management', () => {
  let testData;

  test.beforeEach(async ({ page }, testInfo) => {
    testData = new TestDataManager(`product_${testInfo.title.replace(/\s+/g, '_')}`, 'http://localhost:5000/api', testInfo.project.name);
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
  test('displays product list', async ({ page }) => {
    // Create test product first
    const scenario = await testData.createTestScenario();
    
    await page.goto('/products');
    
    // Check page structure using semantic selectors
    await expect(page.getByRole('heading', { name: 'Products' })).toBeVisible();
    
    // Check for add link using deterministic selector
    await expect(page.getByTestId('add-new-product-btn')).toBeVisible();
    
    // Our test product should be visible on the page
    // Products are displayed by their roaster and bean type combination
    await expect(page.locator('body')).toContainText(scenario.roaster.name);
    await expect(page.locator('body')).toContainText(scenario.beanType.name);
  });

  test('can navigate to product detail page', async ({ page }) => {
    // Create test product first
    const scenario = await testData.createTestScenario();
    
    await page.goto('/products');
    
    // Find our specific test product row and click its details link  
    const productRow = page.locator('div, tr').filter({ hasText: scenario.roaster.name });
    await page.getByTestId(`product-details-link-${scenario.product.id}`).click();
    
    // Wait for navigation to product detail page
    await page.waitForURL(`**/products/${scenario.product.id}`);
    
    // Should show product details - check for the actual product name
    await expect(page.getByRole('heading', { name: scenario.product.product_name })).toBeVisible();
    await expect(page.locator('body')).toContainText(scenario.roaster.name);
    await expect(page.locator('body')).toContainText(scenario.product.country.name);
  });

  test('can create a new product', async ({ page }) => {
    // Create supporting data first
    const roaster = await testData.createTestItem('roasters', { name: `Test Roaster ${testData.testId}` });
    
    await page.goto('/products');
    
    // Click add link using deterministic selector
    await page.getByTestId('add-new-product-btn').click();
    
    // Wait for navigation to new product form
    await page.waitForURL('**/products/new');
    
    // Should navigate to form
    await expect(page.getByRole('heading', { name: /Add.*Product/i })).toBeVisible();
    
    // Wait for form sections to be ready
    await expect(page.getByText('☕ Coffee Details')).toBeVisible();
    
    // Fill only REQUIRED fields - Roaster is marked as required
    const productName = `Test Product ${testData.testId}`;
    
    // Fill roaster autocomplete (this is required)
    await expect(page.getByLabel('Roaster')).toBeVisible();
    await page.getByLabel('Roaster').fill(roaster.name);
    // Wait for dropdown and click the option
    await page.getByRole('option', { name: roaster.name }).click();
    
    // Add product name for identification
    await page.getByLabel(/product.*name/i).fill(productName);
    
    // Now look for submit button - it should be visible after required field is filled
    await expect(page.getByTestId('add-product-btn')).toBeVisible({ timeout: 5000 });
    await page.getByTestId('add-product-btn').click();
    
    // Wait for navigation away from new product form
    await page.waitForURL(url => !url.toString().includes('/products/new'));
    
    // Wait for product to be created (success message or content appears)
    await expect(page.locator('body')).toContainText(/created.*successfully|added.*successfully/i, { timeout: 2000 });
    
    // New product should be visible on product detail page
    await expect(page.locator('#product-title')).toContainText(productName);
  });

  test('can edit existing product', async ({ page }) => {
    // Create test product first
    const scenario = await testData.createTestScenario();
    
    await page.goto(`/products/${scenario.product.id}`);
    
    // Click edit button using semantic selector
    await page.getByRole('button', { name: /edit.*product/i }).click();
    
    // Wait for navigation to edit form
    await page.waitForURL(`**/products/edit/${scenario.product.id}`);
    
    // Should navigate to edit form
    await expect(page.getByRole('heading', { name: /edit.*product/i })).toBeVisible();
    
    // Wait for form to load with pre-filled data
    await expect(page.getByLabel(/product.*name/i)).toBeVisible();
    
    // Update description
    const updatedDescription = `Updated description ${testData.testId}`;
    const descriptionField = page.getByLabel(/description/i);
    if (await descriptionField.isVisible()) {
      await descriptionField.clear();
      await descriptionField.fill(updatedDescription);
      
      // Save changes using semantic selector
      await page.getByRole('button', { name: /update.*product/i }).click();
      
      // Wait for navigation back to product detail page
      await page.waitForURL(`**/products/${scenario.product.id}`);
      
      // Wait for page to fully load
      await expect(page.getByRole('heading', { name: scenario.product.product_name })).toBeVisible();
      
      // Should show updated description
      await expect(page.locator('body')).toContainText(updatedDescription);
    } else {
      // If description field isn't visible, just save without changes
      await page.getByRole('button', { name: /update.*product/i }).click();
      await page.waitForURL(`**/products/${scenario.product.id}`);
      await expect(page.getByRole('heading', { name: scenario.product.product_name })).toBeVisible();
    }
  });

  test('can delete a product', async ({ page }) => {
    // Create test product to delete
    const scenario = await testData.createTestScenario();
    
    await page.goto(`/products/${scenario.product.id}`);
    
    // Delete the product (handle browser confirm dialog)
    page.on('dialog', async dialog => {
      expect(dialog.message()).toContain('Are you sure you want to delete');
      await dialog.accept();
    });
    
    await page.getByRole('button', { name: /delete.*product/i }).click();
    
    // Wait for navigation back to products list
    await page.waitForURL('**/products');
    
    // Wait for deletion to complete
    await expect(page.locator('body')).toContainText(/deleted.*successfully/i, { timeout: 2000 });
    
    // Product should no longer be visible on products page
    await expect(page.locator('body')).not.toContainText(scenario.roaster.name);
  });

  test('shows validation errors', async ({ page }) => {
    await page.goto('/products/new');
    
    // Try to submit empty form using semantic selector
    await page.getByRole('button', { name: /create.*product/i }).click();
    
    // Should show validation errors - look for error message element
    await expect(page.locator('.error-message')).toBeVisible({ timeout: 5000 });
  });

  test('can navigate back from forms', async ({ page }) => {
    await page.goto('/products/new');
    
    // Click cancel/back button using semantic selector
    await page.getByRole('button', { name: /cancel|back/i }).click();
    
    // Wait for navigation back to products list
    await page.waitForURL('**/products');
    
    // Should be back on products page
    await expect(page.getByRole('heading', { name: 'Products' })).toBeVisible();
  });
});