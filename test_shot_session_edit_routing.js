/**
 * Quick test script to verify shot session edit routing works correctly
 */
const { test, expect } = require('@playwright/test');

test('shot session detail edit button routes correctly', async ({ page }) => {
  // Navigate to shot sessions list
  await page.goto('http://localhost:3000/shot-sessions');
  
  // Wait for the page to load
  await expect(page.getByRole('heading', { name: 'My Coffee Journal' })).toBeVisible();
  await expect(page.locator('#shot-session-list-page')).toBeVisible({ timeout: 10000 });
  
  // Wait for table to load
  await expect(page.getByRole('table')).toBeVisible();
  
  // Find the first shot session and click on its view link
  const firstSessionLink = page.getByTestId(/view-shot-session-\d+/).first();
  await firstSessionLink.click();
  
  // Wait for navigation to detail page
  await page.waitForURL('**/shot-sessions/**', { timeout: 5000 });
  
  // Should be on a shot session detail page
  await expect(page.locator('#shot-session-detail-page')).toBeVisible();
  
  // Click the edit button (pencil icon)
  const editButton = page.getByTitle('Edit Shot Session');
  await editButton.click();
  
  // Should navigate to edit route
  await page.waitForURL('**/shot-sessions/**/edit', { timeout: 5000 });
  
  // Should show the edit form
  await expect(page.getByLabel(/session.*name/i)).toBeVisible();
  await expect(page.getByLabel(/product/i)).toBeVisible();
  await expect(page.getByLabel(/batch/i)).toBeVisible();
  await expect(page.getByLabel(/brewer/i)).toBeVisible();
  
  console.log('✅ Shot session detail edit button routes correctly to edit form');
});

// Run if called directly
if (require.main === module) {
  const { chromium } = require('playwright');
  (async () => {
    const browser = await chromium.launch();
    const context = await browser.newContext();
    const page = await context.newPage();
    
    try {
      await test('shot session detail edit button routes correctly', async () => {}, { page });
      console.log('✅ Test passed!');
    } catch (error) {
      console.log('❌ Test failed:', error.message);
    } finally {
      await browser.close();
    }
  })();
}