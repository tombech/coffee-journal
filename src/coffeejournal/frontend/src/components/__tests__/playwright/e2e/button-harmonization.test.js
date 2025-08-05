import { test, expect } from '@playwright/test';
const TestDataManager = require('../../../../test-utils/testDataManager');

test.describe('Button Harmonization', () => {
  let testData;

  test.beforeEach(async ({ page }, testInfo) => {
    testData = new TestDataManager(`button_harmonization_${testInfo.title.replace(/\s+/g, '_')}`, 'http://localhost:5000/api', testInfo.project.name);
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

  test('buttons use semantic aria-labels instead of text content', async ({ page }) => {
    // Create test scenario first
    const scenario = await testData.createTestScenario();
    
    await page.goto('/products');
    
    // Wait for the page to load
    await expect(page.getByRole('heading', { name: 'My Coffee Journal' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Products' })).toBeVisible();
    
    // Wait for products to load first, then check action buttons
    await expect(page.locator('body')).toContainText(scenario.product.product_name);
    
    // Check that action buttons have proper aria-labels for semantic testing
    // Edit is a link in ProductList, Delete is a button
    await expect(page.getByRole('link', { name: /edit/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /delete/i })).toBeVisible();
    
    // Navigate to brew sessions page  
    await page.goto('/brew-sessions');
    await expect(page.getByRole('heading', { name: 'All Brew Sessions' })).toBeVisible();
    
    // Check that brew session action buttons have proper aria-labels
    await expect(page.getByRole('button', { name: /edit.*brew.*session/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /delete.*brew.*session/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /duplicate.*brew.*session/i })).toBeVisible();
  });

  test('create buttons are consistently labeled', async ({ page }) => {
    // Create test scenario first
    const scenario = await testData.createTestScenario();
    
    // Check products page - uses testId for icon link
    await page.goto('/products');
    await expect(page.getByTestId('add-new-product-btn')).toBeVisible();
    
    // Check brew sessions page - button has aria-label "New Brew Session"
    await page.goto('/brew-sessions');
    await expect(page.getByRole('button', { name: 'New Brew Session' })).toBeVisible();
    
    // Check product detail page for batch creation
    await page.goto(`/products/${scenario.product.id}`);
    await expect(page.getByRole('button', { name: /add.*batch|new.*batch/i })).toBeVisible();
  });

  test('edit and delete buttons consistently use semantic patterns', async ({ page }) => {
    // Create test scenario first
    const scenario = await testData.createTestScenario();
    
    await page.goto('/brew-sessions');
    await expect(page.getByRole('table')).toBeVisible();
    
    // All edit buttons should have semantic aria-labels
    const editButtons = page.getByRole('button', { name: /edit/i });
    const editButtonCount = await editButtons.count();
    expect(editButtonCount).toBeGreaterThan(0);
    
    // All delete buttons should have semantic aria-labels  
    const deleteButtons = page.getByRole('button', { name: /delete/i });
    const deleteButtonCount = await deleteButtons.count();
    expect(deleteButtonCount).toBeGreaterThan(0);
    
    // All duplicate buttons should have semantic aria-labels
    const duplicateButtons = page.getByRole('button', { name: /duplicate/i });
    const duplicateButtonCount = await duplicateButtons.count();
    expect(duplicateButtonCount).toBeGreaterThan(0);
  });

  test('cancel buttons use consistent patterns', async ({ page }) => {
    // Create test scenario first
    const scenario = await testData.createTestScenario();
    
    // Go to product creation form
    await page.goto('/products/new');
    await expect(page.getByRole('heading', { name: /add.*coffee.*product/i })).toBeVisible();
    
    // Cancel button should have semantic label
    await expect(page.getByRole('button', { name: /cancel/i })).toBeVisible();
    
    // Go to brew session form
    await page.goto('/brew-sessions');
    await page.getByRole('button', { name: 'New Brew Session' }).click();
    
    // Cancel button should have semantic label in brew session form too - use first one
    await expect(page.getByRole('button', { name: /cancel/i }).first()).toBeVisible();
  });

  test('save/update buttons use consistent patterns', async ({ page }) => {
    // Create test scenario first
    const scenario = await testData.createTestScenario();
    
    // Go to product creation form
    await page.goto('/products/new');
    await expect(page.getByRole('heading', { name: /add.*coffee.*product/i })).toBeVisible();
    
    // Create button should have semantic aria-label - now using icon buttons
    await expect(page.getByRole('button', { name: /create.*product/i })).toBeVisible();
    
    // Go to product edit form
    await page.goto(`/products/edit/${scenario.product.id}`);
    await expect(page.getByRole('heading', { name: /edit.*coffee.*product/i })).toBeVisible();
    
    // Update button should have semantic aria-label - now using icon buttons
    await expect(page.getByRole('button', { name: /update.*product/i })).toBeVisible();
  });
});