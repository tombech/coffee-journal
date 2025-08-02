const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  // Mock roasters API
  await page.route('**/api/roasters', (route) => {
    if (route.request().method() === 'GET') {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: 1, name: 'Blue Bottle Coffee', location: 'Oakland, CA', website: 'https://bluebottlecoffee.com' },
          { id: 2, name: 'Intelligentsia', location: 'Chicago, IL', website: 'https://intelligentsia.com' }
        ])
      });
    }
  });

  // Mock usage API - Blue Bottle in use, Intelligentsia not in use
  await page.route('**/api/roasters/usage', (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        1: { in_use: true, usage_count: 3, usage_type: 'products' },
        2: { in_use: false, usage_count: 0, usage_type: null }
      })
    });
  });
  
  // Mock individual usage checks
  await page.route('**/api/roasters/1/usage', (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ in_use: true, usage_count: 3, usage_type: 'products' })
    });
  });
  
  await page.route('**/api/roasters/2/usage', (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ in_use: false, usage_count: 0, usage_type: null })
    });
  });

  await page.goto('http://localhost:3000/settings/roasters');
  
  console.log('=== Testing Blue Bottle (in use) delete ===');
  
  // Wait for page to load
  await page.waitForSelector('[data-testid="delete-blue-bottle-coffee-btn"]');
  
  // Click delete for Blue Bottle (should be in use)
  await page.click('[data-testid="delete-blue-bottle-coffee-btn"]');
  
  // Wait a moment for modal to appear
  await page.waitForTimeout(1000);
  
  // Take screenshot and dump HTML
  await page.screenshot({ path: 'blue-bottle-delete-modal.png' });
  
  // Get all text content to see what's actually shown
  const bodyText = await page.locator('body').textContent();
  console.log('Page text content:', bodyText);
  
  // Check for modal elements
  const modalExists = await page.locator('div').filter({ hasText: 'Delete Roaster' }).count();
  console.log('Elements containing "Delete Roaster":', modalExists);
  
  if (modalExists > 0) {
    const modalText = await page.locator('div').filter({ hasText: 'Delete Roaster' }).first().textContent();
    console.log('Modal text:', modalText);
  }
  
  // Close modal if it exists
  const cancelBtn = page.getByRole('button', { name: 'Cancel' });
  if (await cancelBtn.count() > 0) {
    await cancelBtn.click();
  }
  
  console.log('\n=== Testing Intelligentsia (not in use) delete ===');
  
  // Wait a moment
  await page.waitForTimeout(500);
  
  // Click delete for Intelligentsia (should not be in use)
  await page.click('[data-testid="delete-intelligentsia-btn"]');
  
  // Wait a moment for modal to appear
  await page.waitForTimeout(1000);
  
  // Take screenshot 
  await page.screenshot({ path: 'intelligentsia-delete-modal.png' });
  
  // Get all text content
  const bodyText2 = await page.locator('body').textContent();
  console.log('Page text content for Intelligentsia:', bodyText2);
  
  // Check for modal elements
  const modalExists2 = await page.locator('div').filter({ hasText: 'Delete Roaster' }).count();
  console.log('Elements containing "Delete Roaster":', modalExists2);
  
  if (modalExists2 > 0) {
    const modalText2 = await page.locator('div').filter({ hasText: 'Delete Roaster' }).first().textContent();
    console.log('Modal text:', modalText2);
  }
  
  await browser.close();
})();