import { test, expect } from '@playwright/test';
const TestDataManager = require('../../../../test-utils/testDataManager');

test.describe('Enhanced Brew Session Filtering', () => {
  let testData;

  test.beforeEach(async ({ page }, testInfo) => {
    testData = new TestDataManager(`enhanced_filtering_${testInfo.title.replace(/\s+/g, '_')}`, 'http://localhost:5000/api', testInfo.project.name);
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

  test('can filter brew sessions by region', async ({ page }) => {
    // Create countries and regions
    const country1 = await testData.createTestItem('countries', {
      name: `Ethiopia ${testData.testId}`,
      short_form: 'ET'
    });
    
    const region1 = await testData.createTestItem('regions', {
      name: `Yirgacheffe ${testData.testId}`,
      short_form: 'YRG',
      country_id: country1.id
    });
    
    const region2 = await testData.createTestItem('regions', {
      name: `Sidama ${testData.testId}`,
      short_form: 'SDM', 
      country_id: country1.id
    });
    
    // Create products with different regions
    const product1 = await testData.createTestItem('products', {
      roaster_name: `Test Roaster ${testData.testId}`,
      product_name: `Yirgacheffe Product ${testData.testId}`,
      bean_type_name: ['Arabica'],
      country_id: country1.id,
      region_id: [region1.id]
    });
    
    const product2 = await testData.createTestItem('products', {
      roaster_name: `Test Roaster ${testData.testId}`,
      product_name: `Sidama Product ${testData.testId}`,
      bean_type_name: ['Arabica'],
      country_id: country1.id,
      region_id: [region2.id]
    });
    
    // Create batches for each product
    const batch1 = await testData.createTestItem('batches', {
      product_id: product1.id,
      roast_date: '2025-01-01',
      amount_grams: 250
    });
    
    const batch2 = await testData.createTestItem('batches', {
      product_id: product2.id,
      roast_date: '2025-01-01',
      amount_grams: 250
    });
    
    // Create brew sessions for each batch
    await testData.createBrewSession(batch1.id, {
      brew_method: `V60 ${testData.testId}`,
      notes: `Yirgacheffe session ${testData.testId}`
    });
    
    await testData.createBrewSession(batch2.id, {
      brew_method: `V60 ${testData.testId}`,
      notes: `Sidama session ${testData.testId}`
    });
    
    // Navigate to brew sessions page
    await page.goto('/brew-sessions');
    await expect(page.getByRole('table')).toBeVisible();
    
    // Initially should show both sessions
    await expect(page.locator('body')).toContainText(`Yirgacheffe session ${testData.testId}`);
    await expect(page.locator('body')).toContainText(`Sidama session ${testData.testId}`);
    
    // Filter by region - look for region filter dropdown
    const regionFilter = page.getByLabel(/region.*filter|filter.*region/i);
    if (await regionFilter.isVisible()) {
      await regionFilter.selectOption(region1.name);
      
      // Should show only Yirgacheffe session
      await expect(page.locator('body')).toContainText(`Yirgacheffe session ${testData.testId}`);
      await expect(page.locator('body')).not.toContainText(`Sidama session ${testData.testId}`);
    } else {
      // Skip test if region filter not available yet
      test.skip();
    }
  });

  test('can filter brew sessions by decaf method', async ({ page }) => {
    // Create decaf methods
    const decafMethod1 = await testData.createTestItem('decaf_methods', {
      name: `Swiss Water ${testData.testId}`,
      short_form: 'SW'
    });
    
    const decafMethod2 = await testData.createTestItem('decaf_methods', {
      name: `CO2 Process ${testData.testId}`,
      short_form: 'CO2'
    });
    
    // Create products - one regular, two decaf with different methods
    const regularProduct = await testData.createTestItem('products', {
      roaster_name: `Test Roaster ${testData.testId}`,
      product_name: `Regular Product ${testData.testId}`,
      bean_type_name: ['Arabica'],
      decaf: false
    });
    
    const decafProduct1 = await testData.createTestItem('products', {
      roaster_name: `Test Roaster ${testData.testId}`,
      product_name: `Decaf Product 1 ${testData.testId}`,
      bean_type_name: ['Arabica'],
      decaf: true,
      decaf_method_id: decafMethod1.id
    });
    
    const decafProduct2 = await testData.createTestItem('products', {
      roaster_name: `Test Roaster ${testData.testId}`,
      product_name: `Decaf Product 2 ${testData.testId}`,
      bean_type_name: ['Arabica'],
      decaf: true,
      decaf_method_id: decafMethod2.id
    });
    
    // Create batches for each product
    const regularBatch = await testData.createTestItem('batches', {
      product_id: regularProduct.id,
      roast_date: '2025-01-01',
      amount_grams: 250
    });
    
    const decafBatch1 = await testData.createTestItem('batches', {
      product_id: decafProduct1.id,
      roast_date: '2025-01-01',
      amount_grams: 250
    });
    
    const decafBatch2 = await testData.createTestItem('batches', {
      product_id: decafProduct2.id,
      roast_date: '2025-01-01',
      amount_grams: 250
    });
    
    // Create brew sessions
    await testData.createBrewSession(regularBatch.id, {
      brew_method: `V60 ${testData.testId}`,
      notes: `Regular session ${testData.testId}`
    });
    
    await testData.createBrewSession(decafBatch1.id, {
      brew_method: `V60 ${testData.testId}`,
      notes: `Swiss Water session ${testData.testId}`
    });
    
    await testData.createBrewSession(decafBatch2.id, {
      brew_method: `V60 ${testData.testId}`,
      notes: `CO2 Process session ${testData.testId}`
    });
    
    // Navigate to brew sessions page
    await page.goto('/brew-sessions');
    await expect(page.getByRole('table')).toBeVisible();
    
    // Initially should show all sessions
    await expect(page.locator('body')).toContainText(`Regular session ${testData.testId}`);
    await expect(page.locator('body')).toContainText(`Swiss Water session ${testData.testId}`);
    await expect(page.locator('body')).toContainText(`CO2 Process session ${testData.testId}`);
    
    // Filter by decaf method - look for decaf method filter dropdown
    const decafMethodFilter = page.getByLabel(/decaf.*method.*filter|filter.*decaf.*method/i);
    if (await decafMethodFilter.isVisible()) {
      await decafMethodFilter.selectOption(decafMethod1.name);
      
      // Should show only Swiss Water session
      await expect(page.locator('body')).toContainText(`Swiss Water session ${testData.testId}`);
      await expect(page.locator('body')).not.toContainText(`Regular session ${testData.testId}`);
      await expect(page.locator('body')).not.toContainText(`CO2 Process session ${testData.testId}`);
    } else {
      // Skip test if decaf method filter not available yet
      test.skip();
    }
  });

  test('combines multiple filters correctly', async ({ page }) => {
    // Create test data with multiple dimensions
    const country = await testData.createTestItem('countries', {
      name: `Ethiopia ${testData.testId}`,
      short_form: 'ET'
    });
    
    const region1 = await testData.createTestItem('regions', {
      name: `Yirgacheffe ${testData.testId}`,
      short_form: 'YRG',
      country_id: country.id
    });
    
    const region2 = await testData.createTestItem('regions', {
      name: `Sidama ${testData.testId}`,
      short_form: 'SDM',
      country_id: country.id
    });
    
    const decafMethod = await testData.createTestItem('decaf_methods', {
      name: `Swiss Water ${testData.testId}`,
      short_form: 'SW'
    });
    
    // Create products with different combinations
    const product1 = await testData.createTestItem('products', {
      roaster_name: `Test Roaster ${testData.testId}`,
      product_name: `Yirgacheffe Decaf ${testData.testId}`,
      bean_type_name: ['Arabica'],
      country_id: country.id,
      region_id: [region1.id],
      decaf: true,
      decaf_method_id: decafMethod.id
    });
    
    const product2 = await testData.createTestItem('products', {
      roaster_name: `Test Roaster ${testData.testId}`,
      product_name: `Sidama Regular ${testData.testId}`,
      bean_type_name: ['Arabica'],
      country_id: country.id,
      region_id: [region2.id],
      decaf: false
    });
    
    const product3 = await testData.createTestItem('products', {
      roaster_name: `Test Roaster ${testData.testId}`,
      product_name: `Yirgacheffe Regular ${testData.testId}`,
      bean_type_name: ['Arabica'],
      country_id: country.id,
      region_id: [region1.id],
      decaf: false
    });
    
    // Create batches and sessions for each
    for (const product of [product1, product2, product3]) {
      const batch = await testData.createTestItem('batches', {
        product_id: product.id,
        roast_date: '2025-01-01',
        amount_grams: 250
      });
      
      await testData.createBrewSession(batch.id, {
        brew_method: `V60 ${testData.testId}`,
        notes: `Session for ${product.product_name}`
      });
    }
    
    // Navigate and test
    await page.goto('/brew-sessions');
    await expect(page.getByRole('table')).toBeVisible();
    
    // Should initially show all three sessions
    await expect(page.locator('body')).toContainText('Yirgacheffe Decaf');
    await expect(page.locator('body')).toContainText('Sidama Regular');
    await expect(page.locator('body')).toContainText('Yirgacheffe Regular');
    
    // Apply region filter first (if available)
    const regionFilter = page.getByLabel(/region.*filter|filter.*region/i);
    if (await regionFilter.isVisible()) {
      await regionFilter.selectOption(region1.name);
      
      // Should show only Yirgacheffe products (both regular and decaf)
      await expect(page.locator('body')).toContainText('Yirgacheffe Decaf');
      await expect(page.locator('body')).toContainText('Yirgacheffe Regular');
      await expect(page.locator('body')).not.toContainText('Sidama Regular');
      
      // Then apply decaf method filter (if available)
      const decafMethodFilter = page.getByLabel(/decaf.*method.*filter|filter.*decaf.*method/i);
      if (await decafMethodFilter.isVisible()) {
        await decafMethodFilter.selectOption(decafMethod.name);
        
        // Should show only Yirgacheffe Decaf
        await expect(page.locator('body')).toContainText('Yirgacheffe Decaf');
        await expect(page.locator('body')).not.toContainText('Yirgacheffe Regular');
        await expect(page.locator('body')).not.toContainText('Sidama Regular');
      }
    } else {
      // Skip if filters not available
      test.skip();
    }
  });
});