import { test, expect } from '@playwright/test';
const TestDataManager = require('../../../../test-utils/testDataManager');

test('debug table contents', async ({ page }, testInfo) => {
  const testData = new TestDataManager(`table_debug_${Date.now()}`, 'http://localhost:5000/api', testInfo.project.name);
  await testData.initialize();
  
  try {
    // Create test scenario
    const scenario = await testData.createTestScenario();
    console.log('Created scenario with brew method:', scenario.brewMethod.name);
    
    await page.goto('/brew-sessions');
    
    // Wait for main app to load
    await expect(page.getByRole('heading', { name: 'My Coffee Journal' })).toBeVisible();
    
    // Wait a bit for data to load
    await page.waitForTimeout(3000);
    
    // Check what's in the table
    const tableContent = await page.locator('table').textContent();
    console.log('Table content:', tableContent);
    
    // Check tbody specifically
    const tbodyContent = await page.locator('tbody').textContent();
    console.log('Tbody content:', tbodyContent);
    
    // Check all text content on page
    const pageText = await page.locator('body').textContent();
    console.log('Page contains brew session notes?', pageText.includes(scenario.brewSession.notes));
    console.log('Page contains brew method name?', pageText.includes(scenario.brewMethod.name));
    
  } finally {
    await testData.cleanup();
  }
});