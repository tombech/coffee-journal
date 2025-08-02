const { test, expect } = require('@playwright/test');
const TestDataManager = require('../../../../test-utils/testDataManager');

test.describe('Lookup View Functionality', () => {
  const lookupTypes = [
    { name: 'Roasters', path: '/settings/roasters', viewPath: '/roasters' },
    { name: 'Brew Methods', path: '/settings/brew-methods', viewPath: '/brew-methods' },
    { name: 'Bean Types', path: '/settings/bean-types', viewPath: '/bean-types' },
    { name: 'Recipes', path: '/settings/recipes', viewPath: '/recipes' },
    { name: 'Grinders', path: '/settings/grinders', viewPath: '/grinders' },
    { name: 'Filters', path: '/settings/filters', viewPath: '/filters' },
    { name: 'Kettles', path: '/settings/kettles', viewPath: '/kettles' },
    { name: 'Scales', path: '/settings/scales', viewPath: '/scales' },
    { name: 'Decaf Methods', path: '/settings/decaf-methods', viewPath: '/decaf-methods' }
  ];

  // Merged test: combines view button display, navigation, edit/delete buttons, and edit navigation
  for (const lookupType of lookupTypes) {
    test(`${lookupType.name} - complete view functionality workflow`, async ({ page }) => {
      const testData = new TestDataManager(`${lookupType.name.toLowerCase().replace(/\s+/g, '_')}_view_test_${Date.now()}`, 'http://localhost:5000/api');
      await testData.initialize();
      
      await page.addInitScript((userId) => {
        window.TEST_USER_ID = userId;
        window.API_BASE_URL = 'http://localhost:5000/api';
      }, testData.userId);
      
      try {
        const itemName = `Test ${lookupType.name} ${Date.now()}`;
        
        // 1. Create test item
        await page.goto(lookupType.path);
        await expect(page.getByRole('heading', { name: lookupType.name })).toBeVisible();
        
        await page.getByTestId('add-item-btn').click();
        await page.getByLabel('Name *').fill(itemName);
        await page.getByLabel('Description').fill('Test description for view functionality');
        await page.getByTestId('create-item-btn').click();
        
        await expect(page.locator('body')).toContainText(/created.*successfully/i);
        await expect(page.getByRole('table')).toContainText(itemName);
        
        // 2. Verify view button is present with correct attributes
        const viewButtonSelector = `view-${itemName.toLowerCase().replace(/\s+/g, '-')}-btn`;
        const viewButton = page.getByTestId(viewButtonSelector);
        await expect(viewButton).toBeVisible();
        await expect(viewButton).toHaveAttribute('title', `View ${itemName}`);
        
        // 3. Navigate to view page
        await viewButton.click();
        await expect(page).toHaveURL(new RegExp(`${lookupType.viewPath}/\\d+`));
        await expect(page.getByTestId('item-title')).toContainText(itemName);
        
        // 4. Verify edit and delete buttons on view page
        const editButton = page.getByTestId('edit-item-btn');
        const deleteButton = page.getByTestId('delete-item-btn');
        
        await expect(editButton).toBeVisible();
        await expect(editButton).toHaveAttribute('title', `Edit ${itemName}`);
        await expect(deleteButton).toBeVisible();
        await expect(deleteButton).toHaveAttribute('title', `Delete ${itemName}`);
        
        // 5. Test edit navigation
        await editButton.click();
        await expect(page).toHaveURL(lookupType.path);
        
        // 6. Test delete confirmation (navigate back to view page first)
        await page.getByTestId(viewButtonSelector).click();
        await expect(page.getByTestId('item-title')).toContainText(itemName);
        
        await deleteButton.click();
        await expect(page.getByTestId('delete-modal-overlay')).toBeVisible();
        await expect(page.getByTestId('delete-modal-content')).toBeVisible();
      } finally {
        await testData.cleanup();
      }
    });
  }

  // Special test for Countries (uses different button selector)
  test('Countries - complete view functionality with special handling', async ({ page }) => {
    const testData = new TestDataManager(`countries_view_test_${Date.now()}`, 'http://localhost:5000/api');
    await testData.initialize();
    
    await page.addInitScript((userId) => {
      window.TEST_USER_ID = userId;
      window.API_BASE_URL = 'http://localhost:5000/api';
    }, testData.userId);
    
    try {
      const countryName = `Test Country ${Date.now()}`;
      
      await page.goto('/settings/countries');
      await expect(page.getByRole('heading', { name: 'Countries' })).toBeVisible();
      
      await page.getByTestId('add-item-btn').click();
      await page.getByLabel('Name *').fill(countryName);
      await page.getByLabel('Description').fill('Test description for country view');
      await page.getByTestId('create-country-btn').click();
      
      await expect(page.locator('body')).toContainText(/created.*successfully/i);
      await expect(page.getByRole('table')).toContainText(countryName);
      
      // Navigate to view page
      const viewButton = page.getByTestId(`view-${countryName.toLowerCase().replace(/\s+/g, '-')}-btn`);
      await expect(viewButton).toBeVisible();
      await viewButton.click();
      
      await expect(page).toHaveURL(/\/countries\/\d+/);
      await expect(page.getByTestId('item-title')).toContainText(countryName);
      
      // Verify buttons are present
      await expect(page.getByTestId('edit-item-btn')).toBeVisible();
      await expect(page.getByTestId('delete-item-btn')).toBeVisible();
    } finally {
      await testData.cleanup();
    }
  });

  // Merged test: item details display + user isolation
  test('Roasters - detailed view with user isolation verification', async ({ page }, testInfo) => {
    const testData = new TestDataManager(`roasters_detailed_view_${Date.now()}`, 'http://localhost:5000/api');
    await testData.initialize();
    
    await page.addInitScript((userId) => {
      window.TEST_USER_ID = userId;
      window.API_BASE_URL = 'http://localhost:5000/api';
    }, testData.userId);
    
    try {
      const roasterName = `Test Detailed Roaster ${Date.now()}`;
      
      // Create detailed roaster
      await page.goto('/settings/roasters');
      await page.getByTestId('add-item-btn').click();
      await page.getByLabel('Name *').fill(roasterName);
      await page.getByLabel('Short Form').fill('TDR');
      await page.getByLabel('Description').fill('A comprehensive test roaster with all fields');
      await page.getByLabel('Notes').fill('Detailed notes about the roaster');
      await page.getByTestId('roasters-url-input').fill('https://example.com');
      await page.getByLabel('Location').fill('Test City, State');
      await page.getByTestId('create-item-btn').click();
      
      await expect(page.locator('body')).toContainText(/created.*successfully/i);
      
      // Navigate to view page and verify all details
      const viewButton = page.getByTestId(`view-${roasterName.toLowerCase().replace(/\s+/g, '-')}-btn`);
      await viewButton.click();
      await expect(page.getByTestId('item-title')).toContainText(roasterName);
      
      // Verify all details are displayed
      await expect(page.locator('body')).toContainText('A comprehensive test roaster with all fields');
      await expect(page.locator('body')).toContainText('Detailed notes about the roaster');
      await expect(page.locator('body')).toContainText('https://example.com');
      
      // Test user isolation with second context
      const context2 = await page.context().browser().newContext();
      const page2 = await context2.newPage();
      
      const testData2 = new TestDataManager(`roasters_isolation_${Date.now()}`, 'http://localhost:5000/api');
      await testData2.initialize();
      
      await page2.addInitScript((userId) => {
        window.TEST_USER_ID = userId;
        window.API_BASE_URL = 'http://localhost:5000/api';
      }, testData2.userId);
      
      await page2.goto('/settings/roasters');
      await expect(page2.getByRole('heading', { name: 'Roasters' })).toBeVisible();
      
      // Verify isolation - roaster should not be visible in second context
      await expect(page2.locator('body')).not.toContainText(roasterName);
      
      await testData2.cleanup();
      await context2.close();
    } finally {
      await testData.cleanup();
    }
  });
});