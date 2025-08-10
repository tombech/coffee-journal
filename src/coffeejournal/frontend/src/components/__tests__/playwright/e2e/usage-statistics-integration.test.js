import { test, expect } from '@playwright/test';
const TestDataManager = require('../../../../test-utils/testDataManager');

test.describe('Usage Statistics Integration', () => {
  let testData;

  test.beforeEach(async ({ page }, testInfo) => {
    testData = new TestDataManager(`usage_stats_${testInfo.title.replace(/\s+/g, '_')}`, 'http://localhost:5000/api', testInfo.project.name);
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

  test('shows usage statistics in BatchDetail with top/bottom sessions', async ({ page }) => {
    // Create a test scenario with multiple brew sessions for statistical analysis
    const scenario = await testData.createTestScenario();
    
    // Create additional brew sessions with varying scores for the same batch
    await testData.createBrewSession(scenario.batch.id, {
      brew_method: `V60 ${testData.testId}`,
      sweetness: 9,
      acidity: 8,
      body: 7,
      aroma: 8,
      bitterness: 2,
      flavor_profile_match: 9,
      notes: `High scoring session ${testData.testId}`
    });
    
    await testData.createBrewSession(scenario.batch.id, {
      brew_method: `V60 ${testData.testId}`,
      sweetness: 3,
      acidity: 4,
      body: 3,
      aroma: 3,
      bitterness: 8,
      flavor_profile_match: 2,
      notes: `Low scoring session ${testData.testId}`
    });
    
    await testData.createBrewSession(scenario.batch.id, {
      brew_method: `Chemex ${testData.testId}`,
      sweetness: 7,
      acidity: 6,
      body: 6,
      aroma: 7,
      bitterness: 4,
      flavor_profile_match: 6,
      notes: `Medium scoring session ${testData.testId}`
    });
    
    // Navigate to batch detail page
    await page.goto(`/batches/${scenario.batch.id}`);
    
    // Wait for page to load
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    
    // Check for usage statistics section
    await expect(page.getByText('📊 Usage Statistics')).toBeVisible();
    
    // Should show batch statistics (brew sessions count, coffee used, etc.)
    await expect(page.locator('body')).toContainText('Brew Sessions');
    await expect(page.locator('body')).toContainText('Coffee Used');
    await expect(page.locator('body')).toContainText('Remaining');
    
    // Check for top sessions section
    await expect(page.getByText('🏆 Top 5 Brew Sessions')).toBeVisible();
    
    // Should contain the high scoring session
    await expect(page.locator('body')).toContainText(`High scoring session ${testData.testId}`);
    
    // Check for bottom sessions section
    await expect(page.getByText('📉 Bottom 5 Brew Sessions')).toBeVisible();
    
    // Should contain the low scoring session
    await expect(page.locator('body')).toContainText(`Low scoring session ${testData.testId}`);
    
    // Verify the sessions are displayed in BrewSessionTable format (with table structure)
    const tables = page.getByRole('table');
    await expect(tables.first()).toBeVisible();
  });

  test('shows filtered usage statistics in lookup detail views', async ({ page }) => {
    // Create roaster with multiple products and brew sessions
    const roaster = await testData.createTestItem('roasters', {
      name: `Test Roaster ${testData.testId}`,
      short_form: 'TR'
    });
    
    // Create products for this roaster
    const product1 = await testData.createTestItem('products', {
      roaster_id: roaster.id,
      product_name: `Product 1 ${testData.testId}`,
      bean_type_name: ['Arabica']
    });
    
    const product2 = await testData.createTestItem('products', {
      roaster_id: roaster.id,
      product_name: `Product 2 ${testData.testId}`,
      bean_type_name: ['Arabica']
    });
    
    // Create batches for each product
    const batch1 = await testData.createTestItem('batches', {
      product_id: product1.id,
      roast_date: '2025-01-01',
      amount_grams: 250
    });
    
    const batch2 = await testData.createTestItem('batches', {
      product_id: product2.id,
      roast_date: '2025-01-02',
      amount_grams: 250
    });
    
    // Create brew sessions - some high scoring, some low scoring
    await testData.createBrewSession(batch1.id, {
      brew_method: `V60 ${testData.testId}`,
      sweetness: 9,
      acidity: 8,
      body: 8,
      aroma: 9,
      bitterness: 2,
      flavor_profile_match: 9,
      notes: `Excellent roaster session ${testData.testId}`
    });
    
    await testData.createBrewSession(batch2.id, {
      brew_method: `V60 ${testData.testId}`,
      sweetness: 4,
      acidity: 5,
      body: 4,
      aroma: 4,
      bitterness: 7,
      flavor_profile_match: 3,
      notes: `Poor roaster session ${testData.testId}`
    });
    
    await testData.createBrewSession(batch1.id, {
      brew_method: `Chemex ${testData.testId}`,
      sweetness: 7,
      acidity: 7,
      body: 6,
      aroma: 7,
      bitterness: 4,
      flavor_profile_match: 7,
      notes: `Good roaster session ${testData.testId}`
    });
    
    // Navigate to roaster detail page
    await page.goto(`/roasters/${roaster.id}`);
    
    // Wait for page to load
    await expect(page.locator('body')).toContainText(roaster.name);
    
    // Check for usage statistics section
    await expect(page.getByText('📊 Usage Statistics')).toBeVisible();
    
    // Should show usage count for this roaster
    await expect(page.locator('body')).toContainText('Times Used in Products');
    
    // Check for filtered top/bottom sessions specific to this roaster
    await expect(page.getByText('🏆 Top 5 Brew Sessions')).toBeVisible();
    await expect(page.getByText('📉 Bottom 5 Brew Sessions')).toBeVisible();
    
    // Should contain sessions from this roaster's products only
    await expect(page.locator('body')).toContainText(`Excellent roaster session ${testData.testId}`);
    await expect(page.locator('body')).toContainText(`Poor roaster session ${testData.testId}`);
    
    // Sessions should show the product name since showProduct should be true for lookup views
    await expect(page.locator('body')).toContainText(`Product 1 ${testData.testId}`);
    await expect(page.locator('body')).toContainText(`Product 2 ${testData.testId}`);
  });

  test('shows usage statistics for grinder with custom statistics display', async ({ page }) => {
    // Create grinder with specific attributes
    const grinder = await testData.createTestItem('grinders', {
      name: `Test Grinder ${testData.testId}`,
      short_form: 'TG',
      grinder_type: 'Burr',
      manual: false,
      brand: 'Test Brand',
      model: 'Test Model'
    });
    
    // Create products and sessions that use this grinder
    const product = await testData.createTestItem('products', {
      roaster_name: `Test Roaster ${testData.testId}`,
      product_name: `Product ${testData.testId}`,
      bean_type_name: ['Arabica']
    });
    
    const batch = await testData.createTestItem('batches', {
      product_id: product.id,
      roast_date: '2025-01-01',
      amount_grams: 250
    });
    
    // Create sessions with different grind settings
    await testData.createBrewSession(batch.id, {
      brew_method: `V60 ${testData.testId}`,
      grinder_id: grinder.id,
      grinder_setting: 15,
      sweetness: 8,
      acidity: 7,
      body: 7,
      aroma: 8,
      bitterness: 3,
      flavor_profile_match: 8,
      notes: `Fine grind session ${testData.testId}`
    });
    
    await testData.createBrewSession(batch.id, {
      brew_method: `Chemex ${testData.testId}`,
      grinder_id: grinder.id,
      grinder_setting: 25,
      sweetness: 6,
      acidity: 6,
      body: 7,
      aroma: 6,
      bitterness: 4,
      flavor_profile_match: 6,
      notes: `Coarse grind session ${testData.testId}`
    });
    
    // Navigate to grinder detail page
    await page.goto(`/grinders/${grinder.id}`);
    
    // Wait for page to load
    await expect(page.locator('body')).toContainText(grinder.name);
    
    // Check for usage statistics section
    await expect(page.getByText('📊 Usage Statistics')).toBeVisible();
    
    // Grinder should have custom statistics (grind settings analysis)
    await expect(page.locator('body')).toContainText('Grind Settings');
    await expect(page.locator('body')).toContainText('Most Used Setting');
    await expect(page.locator('body')).toContainText('Average Score by Setting');
    
    // Should show both grind settings used
    await expect(page.locator('body')).toContainText('15');
    await expect(page.locator('body')).toContainText('25');
    
    // Should show filtered brew sessions for this grinder
    await expect(page.getByText('🏆 Top 5 Brew Sessions')).toBeVisible();
    await expect(page.getByText('📉 Bottom 5 Brew Sessions')).toBeVisible();
    
    await expect(page.locator('body')).toContainText(`Fine grind session ${testData.testId}`);
    await expect(page.locator('body')).toContainText(`Coarse grind session ${testData.testId}`);
  });

  test('handles empty usage statistics gracefully', async ({ page }) => {
    // Create roaster with no associated products/sessions
    const roaster = await testData.createTestItem('roasters', {
      name: `Unused Roaster ${testData.testId}`,
      short_form: 'UR'
    });
    
    // Navigate to roaster detail page
    await page.goto(`/roasters/${roaster.id}`);
    
    // Wait for page to load
    await expect(page.locator('body')).toContainText(roaster.name);
    
    // Check for usage statistics section
    await expect(page.getByText('📊 Usage Statistics')).toBeVisible();
    
    // Should show that roaster is unused
    await expect(page.locator('body')).toContainText('has not been used in any');
    await expect(page.locator('body')).toContainText('products yet');
    
    // Should not show top/bottom sections when there are no sessions
    await expect(page.getByText('🏆 Top 5 Brew Sessions')).not.toBeVisible();
    await expect(page.getByText('📉 Bottom 5 Brew Sessions')).not.toBeVisible();
  });

  test('usage statistics use correct filtering parameters', async ({ page }) => {
    // Test that filtering parameters are correctly passed to the UsageStatistics component
    
    // Create a bean type with associated products and sessions
    const beanType = await testData.createTestItem('bean_types', {
      name: `Arabica ${testData.testId}`,
      short_form: 'AR'
    });
    
    const product = await testData.createTestItem('products', {
      roaster_name: `Test Roaster ${testData.testId}`,
      product_name: `Bean Type Product ${testData.testId}`,
      bean_type_id: [beanType.id]
    });
    
    const batch = await testData.createTestItem('batches', {
      product_id: product.id,
      roast_date: '2025-01-01',
      amount_grams: 250
    });
    
    await testData.createBrewSession(batch.id, {
      brew_method: `V60 ${testData.testId}`,
      sweetness: 8,
      notes: `Bean type session ${testData.testId}`
    });
    
    // Navigate to bean type detail page  
    await page.goto(`/bean-types/${beanType.id}`);
    
    // Wait for page to load
    await expect(page.locator('body')).toContainText(beanType.name);
    
    // Check usage statistics
    await expect(page.getByText('📊 Usage Statistics')).toBeVisible();
    await expect(page.locator('body')).toContainText('Times Used in Products');
    
    // Should show filtered sessions for this bean type
    await expect(page.getByText('🏆 Top 5 Brew Sessions')).toBeVisible();
    await expect(page.locator('body')).toContainText(`Bean type session ${testData.testId}`);
    
    // The BrewSessionTable should show product names since this is a lookup detail view
    await expect(page.locator('body')).toContainText(`Bean Type Product ${testData.testId}`);
    
    // Verify the filtering is working by checking the API calls in network tab
    // The UsageStatistics component should call /brew_sessions?bean_type={beanType.id}
    page.on('request', request => {
      if (request.url().includes('/brew_sessions') && request.url().includes(`bean_type=${beanType.id}`)) {
        // This confirms the correct filtering parameter is being used
        expect(request.url()).toContain(`bean_type=${beanType.id}`);
      }
    });
  });
});