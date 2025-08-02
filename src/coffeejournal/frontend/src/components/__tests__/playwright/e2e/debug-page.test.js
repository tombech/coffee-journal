import { test, expect } from '@playwright/test';

test('debug what appears on brew sessions page after proxy fix', async ({ page }) => {
  // Intercept API calls and redirect them to the backend like in the main test
  await page.route('**/api/**', (route) => {
    const url = route.request().url();
    const newUrl = url.replace('http://localhost:3000/api', 'http://localhost:5000/api');
    console.log('API request redirected:', url, '->', newUrl);
    route.continue({ url: newUrl });
  });
  
  await page.goto('/brew-sessions');
  
  // Wait for page to load
  await page.waitForTimeout(5000);
  
  // Get visible text
  const bodyText = await page.locator('body').textContent();
  console.log('Page text:', bodyText);
  
  // Check if there are any headings
  const headings = await page.locator('h1, h2, h3, h4, h5, h6').allTextContents();
  console.log('All headings:', headings);
  
  // Check if there are any errors
  const errors = await page.locator('.error-message, .error').allTextContents();
  console.log('Errors:', errors);
  
  // Check for loading message
  const loading = await page.locator('.loading-message').allTextContents();
  console.log('Loading messages:', loading);
});