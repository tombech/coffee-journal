const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  await page.goto('http://localhost:3000/products');
  
  // Wait for page to load
  await page.waitForTimeout(2000);
  
  // Get all links and their accessible names
  const links = await page.locator('a').all();
  console.log('All links found:');
  for (let i = 0; i < links.length; i++) {
    const text = await links[i].textContent();
    const title = await links[i].getAttribute('title');
    const href = await links[i].getAttribute('href');
    console.log(`  Link ${i}: text="${text}" title="${title}" href="${href}"`);
  }
  
  // Check if there are any buttons
  const buttons = await page.locator('button').all();
  console.log('\nAll buttons found:');
  for (let i = 0; i < buttons.length; i++) {
    const text = await buttons[i].textContent();
    const title = await buttons[i].getAttribute('title');
    console.log(`  Button ${i}: text="${text}" title="${title}"`);
  }
  
  // Look for anything with "New Product" in aria-label or title
  const newProductElements = await page.locator('[title*="New Product"], [aria-label*="New Product"]').all();
  console.log('\nElements with "New Product":');
  for (let i = 0; i < newProductElements.length; i++) {
    const tagName = await newProductElements[i].evaluate(el => el.tagName);
    const text = await newProductElements[i].textContent();
    const title = await newProductElements[i].getAttribute('title');
    const ariaLabel = await newProductElements[i].getAttribute('aria-label');
    console.log(`  Element ${i}: ${tagName} text="${text}" title="${title}" aria-label="${ariaLabel}"`);
  }
  
  await browser.close();
})();